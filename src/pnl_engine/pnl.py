"""
P&L calculations for the Book Profit & Loss Analyzer.
"""


def compute_pnl(
    retail_price, vat_pct, wholesale_discount_pct,
    quantity_produced, unit_cost,
    translation_fee, design_fee, digital_files_cost,
    royalty_rate, advance, estimated_sales,
):
    price_excl_vat        = retail_price / (1 + vat_pct)
    net_receipt_per_unit  = retail_price * (1 - wholesale_discount_pct)
    revenue               = float(net_receipt_per_unit * estimated_sales)
    total_fixed_sunk      = (translation_fee + design_fee + digital_files_cost
                             + unit_cost * quantity_produced)
    royalty_per_unit      = price_excl_vat * royalty_rate
    total_royalty_cost    = float(royalty_per_unit * estimated_sales)
    total_costs           = float(total_fixed_sunk + total_royalty_cost)
    gross_profit          = float(revenue - total_costs)
    margin_pct            = (gross_profit / revenue * 100) if revenue > 0 else 0
    contribution_margin   = net_receipt_per_unit - royalty_per_unit
    breakeven_units       = (total_fixed_sunk / contribution_margin
                             if contribution_margin > 0 else float("inf"))
    total_cost_per_unit   = (total_costs / estimated_sales) if estimated_sales > 0 else 0
    gross_margin_per_unit = (
        net_receipt_per_unit - royalty_per_unit
        - (total_fixed_sunk / estimated_sales if estimated_sales > 0 else 0)
    )
    roi               = (gross_profit / total_fixed_sunk * 100) if total_fixed_sunk > 0 else 0
    printing_cost     = unit_cost * quantity_produced
    upfront_editorial = translation_fee + design_fee + digital_files_cost + advance
    upfront           = upfront_editorial + printing_cost

    return {
        "price_excl_vat":        price_excl_vat,
        "net_receipt_per_unit":  net_receipt_per_unit,
        "revenue":               revenue,
        "total_fixed_sunk":      total_fixed_sunk,
        "royalty_per_unit":      royalty_per_unit,
        "total_royalty_cost":    total_royalty_cost,
        "total_costs":           total_costs,
        "gross_profit":          gross_profit,
        "margin_pct":            margin_pct,
        "contribution_margin":   contribution_margin,
        "breakeven_units":       breakeven_units,
        "total_cost_per_unit":   total_cost_per_unit,
        "gross_margin_per_unit": gross_margin_per_unit,
        "roi":                   roi,
        "upfront":               upfront,
        "upfront_editorial":     upfront_editorial,
        "printing_cost":         printing_cost,
    }


def calc_scenario(sell_pct, quantity_produced, net_receipt_per_unit,
                  royalty_per_unit, total_fixed_sunk):
    s = int(quantity_produced * sell_pct / 100)
    r = net_receipt_per_unit * s
    c = total_fixed_sunk + royalty_per_unit * s
    p = r - c
    return {
        "Units":   s,
        "Revenue": r,
        "Costs":   c,
        "Profit":  p,
        "Margin":  (p / r * 100) if r > 0 else 0,
        "ROI":     (p / total_fixed_sunk * 100) if total_fixed_sunk > 0 else 0,
    }