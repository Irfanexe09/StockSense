"""
StockSense — Analytics service.

Implements aggregation queries for sales performance, trends over time,
product rankings, category breakdowns, and inventory valuation metrics.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.analytics import (
    CategorySalesShare,
    DailySalesTrend,
    ExpiryRiskExposure,
    InventoryAnalyticsResponse,
    InventoryValuationSummary,
    LowStockExposure,
    SalesAnalyticsResponse,
    SalesSummaryKPIs,
    TopSellingProduct,
)


def resolve_date_range(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[date, date, datetime, datetime]:
    """
    Resolves client preset or custom dates to concrete date and UTC datetime boundaries.
    """
    today = datetime.now(timezone.utc).date()

    if preset == "today":
        resolved_start = today
        resolved_end = today
    elif preset == "7d":
        resolved_start = today - timedelta(days=6)
        resolved_end = today
    elif preset == "30d":
        resolved_start = today - timedelta(days=29)
        resolved_end = today
    elif preset == "90d":
        resolved_start = today - timedelta(days=89)
        resolved_end = today
    elif preset == "all":
        # Earliest recorded sale or fallback to 30 days ago
        earliest_dt = db.scalar(select(func.min(Sale.created_at)))
        resolved_start = earliest_dt.date() if earliest_dt else (today - timedelta(days=29))
        resolved_end = today
    elif preset == "custom":
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date are required for 'custom' preset.")
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date}).")
        resolved_start = start_date
        resolved_end = end_date
    else:
        raise ValueError(f"Invalid preset: '{preset}'. Use today, 7d, 30d, 90d, all, or custom.")

    start_dt = datetime.combine(resolved_start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(resolved_end, time.max, tzinfo=timezone.utc)
    return resolved_start, resolved_end, start_dt, end_dt


def get_sales_analytics(
    db: Session,
    preset: str = "30d",
    start_date: date | None = None,
    end_date: date | None = None,
) -> SalesAnalyticsResponse:
    """
    Calculates sales revenue, order counts, daily trends, top products,
    and category revenue breakdown for the specified period.
    """
    resolved_start, resolved_end, start_dt, end_dt = resolve_date_range(
        db, preset=preset, start_date=start_date, end_date=end_date
    )

    # 1. Fetch sales in date range
    sales_stmt = (
        select(Sale)
        .where(Sale.created_at >= start_dt, Sale.created_at <= end_dt)
        .order_by(Sale.created_at.asc())
    )
    sales = list(db.scalars(sales_stmt).all())

    sale_ids = [s.id for s in sales]

    # 2. Fetch sale items for these sales
    items: list[SaleItem] = []
    if sale_ids:
        items_stmt = select(SaleItem).where(SaleItem.sale_id.in_(sale_ids))
        items = list(db.scalars(items_stmt).all())

    total_revenue = sum((s.total_amount for s in sales), Decimal("0.00"))
    order_count = len(sales)
    units_sold = sum((item.quantity for item in items), 0)
    aov = (
        (total_revenue / order_count).quantize(Decimal("0.01"))
        if order_count > 0
        else Decimal("0.00")
    )

    summary = SalesSummaryKPIs(
        total_revenue=total_revenue,
        order_count=order_count,
        units_sold=units_sold,
        average_order_value=aov,
    )

    # 3. Daily trends series (initialize every day in range with 0)
    daily_map: dict[date, dict] = {}
    current_day = resolved_start
    while current_day <= resolved_end:
        daily_map[current_day] = {
            "date": current_day,
            "revenue": Decimal("0.00"),
            "order_count": 0,
            "units_sold": 0,
        }
        current_day += timedelta(days=1)

    for sale in sales:
        day = sale.created_at.date()
        if day in daily_map:
            daily_map[day]["revenue"] += sale.total_amount
            daily_map[day]["order_count"] += 1

    # Map units to day
    sale_date_lookup = {s.id: s.created_at.date() for s in sales}
    for item in items:
        day = sale_date_lookup.get(item.sale_id)
        if day and day in daily_map:
            daily_map[day]["units_sold"] += item.quantity

    daily_trends = [
        DailySalesTrend(
            date=val["date"],
            revenue=val["revenue"],
            order_count=val["order_count"],
            units_sold=val["units_sold"],
        )
        for val in sorted(daily_map.values(), key=lambda x: x["date"])
    ]

    # 4. Top selling products
    prod_agg: dict[str, dict] = {}
    for item in items:
        key = f"{item.product_sku}-{item.product_name}"
        if key not in prod_agg:
            prod_agg[key] = {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_sku": item.product_sku,
                "units_sold": 0,
                "total_revenue": Decimal("0.00"),
                "sales_seen": set(),
            }
        prod_agg[key]["units_sold"] += item.quantity
        prod_agg[key]["total_revenue"] += item.line_total
        prod_agg[key]["sales_seen"].add(item.sale_id)

    top_products_list = sorted(
        prod_agg.values(),
        key=lambda x: (x["units_sold"], x["total_revenue"]),
        reverse=True,
    )[:10]

    top_products = [
        TopSellingProduct(
            product_id=p["product_id"],
            product_name=p["product_name"],
            product_sku=p["product_sku"],
            units_sold=p["units_sold"],
            total_revenue=p["total_revenue"],
            order_count=len(p["sales_seen"]),
        )
        for p in top_products_list
    ]

    # 5. Category breakdown
    # To get category names, map product_id -> category
    category_agg: dict[str, dict] = {}
    if items:
        product_ids = {it.product_id for it in items if it.product_id is not None}
        prods = list(
            db.scalars(
                select(Product).where(Product.id.in_(product_ids))
            ).all()
        )
        prod_to_cat: dict[int, tuple[int | None, str]] = {}
        for p in prods:
            if p.category:
                prod_to_cat[p.id] = (p.category.id, p.category.name)
            else:
                prod_to_cat[p.id] = (None, "Uncategorized")

        for item in items:
            cat_id, cat_name = prod_to_cat.get(item.product_id, (None, "Uncategorized"))
            if cat_name not in category_agg:
                category_agg[cat_name] = {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "units_sold": 0,
                    "total_revenue": Decimal("0.00"),
                }
            category_agg[cat_name]["units_sold"] += item.quantity
            category_agg[cat_name]["total_revenue"] += item.line_total

    cat_breakdown: list[CategorySalesShare] = []
    for c in sorted(category_agg.values(), key=lambda x: x["total_revenue"], reverse=True):
        rev = c["total_revenue"]
        pct = (
            float((rev / total_revenue) * 100)
            if total_revenue > Decimal("0.00")
            else 0.0
        )
        cat_breakdown.append(
            CategorySalesShare(
                category_id=c["category_id"],
                category_name=c["category_name"],
                units_sold=c["units_sold"],
                total_revenue=rev,
                revenue_percentage=round(pct, 1),
            )
        )

    return SalesAnalyticsResponse(
        start_date=resolved_start,
        end_date=resolved_end,
        summary=summary,
        daily_trends=daily_trends,
        top_products=top_products,
        category_breakdown=cat_breakdown,
    )


def get_inventory_analytics(db: Session) -> InventoryAnalyticsResponse:
    """
    Calculates inventory valuation, gross margin spread, low-stock deficit,
    and batch expiration risk exposure.
    """
    today = datetime.now(timezone.utc).date()
    cutoff_30d = today + timedelta(days=30)

    # 1. Product catalog valuation
    products = list(db.scalars(select(Product)).all())

    total_products_count = len(products)
    total_stock_units = sum(p.stock_quantity for p in products)

    total_cost_value = sum(
        (Decimal(str(p.cost_price)) * p.stock_quantity for p in products),
        Decimal("0.00"),
    )
    total_retail_value = sum(
        (Decimal(str(p.selling_price)) * p.stock_quantity for p in products),
        Decimal("0.00"),
    )
    potential_margin_value = total_retail_value - total_cost_value
    potential_margin_percent = (
        float((potential_margin_value / total_retail_value) * 100)
        if total_retail_value > Decimal("0.00")
        else 0.0
    )

    valuation = InventoryValuationSummary(
        total_products_count=total_products_count,
        total_stock_units=total_stock_units,
        total_cost_value=total_cost_value,
        total_retail_value=total_retail_value,
        potential_margin_value=potential_margin_value,
        potential_margin_percent=round(potential_margin_percent, 1),
    )

    # 2. Low-stock exposure
    low_stock_prods = [p for p in products if p.stock_quantity <= p.reorder_level]
    total_deficit = sum(max(0, p.reorder_level - p.stock_quantity) for p in low_stock_prods)
    restock_cost = sum(
        (
            Decimal(str(p.cost_price)) * max(0, p.reorder_level - p.stock_quantity)
            for p in low_stock_prods
        ),
        Decimal("0.00"),
    )

    low_stock = LowStockExposure(
        low_stock_products_count=len(low_stock_prods),
        total_units_deficit=total_deficit,
        estimated_restock_cost=restock_cost,
    )

    # 3. Expiry risk exposure from active batches
    active_batches = list(
        db.scalars(
            select(Batch)
            .where(Batch.quantity > 0, Batch.expiry_date.is_not(None))
        ).all()
    )

    # Map product_id to cost_price
    prod_cost_map = {p.id: Decimal(str(p.cost_price)) for p in products}

    expired_batches = [b for b in active_batches if b.expiry_date < today]
    expired_units = sum(b.quantity for b in expired_batches)
    expired_cost_val = sum(
        (prod_cost_map.get(b.product_id, Decimal("0.00")) * b.quantity for b in expired_batches),
        Decimal("0.00"),
    )

    expiring_soon = [
        b for b in active_batches if today <= b.expiry_date <= cutoff_30d
    ]
    expiring_soon_units = sum(b.quantity for b in expiring_soon)
    expiring_soon_cost_val = sum(
        (prod_cost_map.get(b.product_id, Decimal("0.00")) * b.quantity for b in expiring_soon),
        Decimal("0.00"),
    )

    expiry_risk = ExpiryRiskExposure(
        expired_batches_count=len(expired_batches),
        expired_units=expired_units,
        expired_cost_value=expired_cost_val,
        expiring_soon_batches_count=len(expiring_soon),
        expiring_soon_units=expiring_soon_units,
        expiring_soon_cost_value=expiring_soon_cost_val,
    )

    return InventoryAnalyticsResponse(
        valuation=valuation,
        low_stock_exposure=low_stock,
        expiry_risk=expiry_risk,
    )
