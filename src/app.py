"""
PubPro — Book Profit & Loss Analyzer
Run with: streamlit run app.py (from inside the src/ folder)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from pnl_engine import (
    compute_pnl, calc_scenario,
    compute_cf, compute_dcf, compute_npv,
    get_monthly_rate, get_peak_deficit, get_recovery_month,
)
from ui_components import (
    fmt, fmt2, fmtu,
    kpi_card, scenario_row,
    chart_breakeven, chart_cumulative_cf, chart_stock_depletion,
    chart_npv_sensitivity, chart_scenario_comparison,
)

st.set_page_config(page_title='PubPro: Title P&L', layout='wide', page_icon="📚")

css_path = Path(__file__).parent / "styles" / "main.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown("""
    <div class="app-header">
        <h1>📚 Know Before You Print</h1>
        <p>Profitability, cash flow, break-even and investment analysis for any publishing title</p>
    </div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:

    with st.expander("Book Name", expanded=True):
        title = st.text_input("Book Title", placeholder="e.g. The Lord of the rings")

    with st.expander("Pricing & Tax", expanded=True):
        retail_price = st.number_input("Retail Price (€)", value=17.50, step=0.10, format="%.2f")
        vat_pct = st.number_input("VAT (%)", value=6.0, step=0.5, format="%.1f") / 100
        wholesale_discount_pct = st.number_input("Wholesale Discount (%)", value=40.0, step=1.0, format="%.1f")/ 100

    with st.expander("Production", expanded=True):
        quantity_produced = st.number_input("Print Run (units)", value=20000, step=100)
        unit_cost = st.number_input("Unit Production Cost (€)", value=2.50, step=0.05, format="%.2f")

    with st.expander("Editorial Fees", expanded=True):
        translation_fee    = st.number_input("Translation Fees (€)", value=1500, step=50,)
        design_fee         = st.number_input("Design Fees (€)", value=1500, step=50,)
        digital_files_cost = st.number_input("Digital Files Cost (€)", value=1000, step=50,)

    with st.expander("Rights & Royalties", expanded=True):
        royalty_rate = st.number_input("Royalty Rate (%)", value=10.0, step=0.5, format="%.1f") / 100
        advance = st.number_input("Author Advance (€)", value=1000, step=100)
        estimated_sales = st.number_input("Estimated Sales (units)",
            value=quantity_produced, max_value=int(quantity_produced), step=100)

    with st.expander("Payment Timing", expanded=True):
        st.markdown("""
            <p style='color:#94a3b8; font-size:0.72rem; text-transform:uppercase;
                      letter-spacing:0.05em; margin-bottom:0.6rem;'>
                When are costs actually paid?
            </p>
        """, unsafe_allow_html=True)
        printing_delay_months = st.number_input(
            "Printing cost paid at month", value=5, min_value=1, max_value=24, step=1,)
        royalty_payment_every_n = st.number_input(
            "Royalties paid every N months", value=3, min_value=1, max_value=12, step=1,)

    with st.expander("Monthly Estimated Sales", expanded=True):
        st.markdown("""
            <p style='color:#94a3b8; font-size:0.72rem; text-transform:uppercase;
                      letter-spacing:0.05em; margin-bottom:0.6rem;'>
                Insert the monthly estimated sales as % of total quantity (must total 100%)
            </p>
        """, unsafe_allow_html=True)
        default_curve = [15,12,10,8,7,6,5,4,4,3,3,3,2,2,2,2,1,1,1,1,1,0,0,0]
        df_pct_sidebar = pd.DataFrame({
            "Month":   [f"Month {i+1}" for i in range(24)],
            "Sales %": [float(d) for d in default_curve],
        })
        edited_pct = st.data_editor(
            df_pct_sidebar, use_container_width=True, hide_index=True,
            disabled=["Month"],
            column_config={
                "Month":   st.column_config.TextColumn("Month", width="small"),
                "Sales %": st.column_config.NumberColumn(
                    "Sales %", min_value=0.0, max_value=100.0, step=0.5, format="%.1f %%"),
            },
            key="cf_editor"
        )
        pct_per_month = edited_pct["Sales %"].fillna(0).tolist()

    with st.expander("Investment Analysis", expanded=True):
        discount_rate = st.number_input("Discount Rate (% annual)", value=10.0, step=0.5, format="%.1f") / 100

    filled = sum([
        bool(title), retail_price > 0, quantity_produced > 0, unit_cost > 0,
        translation_fee > 0 or design_fee > 0 or digital_files_cost > 0,
        royalty_rate > 0,
    ])
    pct_filled = int((filled / 6) * 100)
    bar_color  = "#52b788" if pct_filled == 100 else "#f0c674" if pct_filled >= 50 else "#e07070"



# ══════════════════════════════════════════════════════════════
# CALCULATIONS
# ══════════════════════════════════════════════════════════════
p = compute_pnl(
    retail_price, vat_pct, wholesale_discount_pct,
    quantity_produced, unit_cost,
    translation_fee, design_fee, digital_files_cost,
    royalty_rate, advance, estimated_sales,
)

revenue               = p["revenue"]
total_fixed_sunk      = p["total_fixed_sunk"]
royalty_per_unit      = p["royalty_per_unit"]
net_receipt_per_unit  = p["net_receipt_per_unit"]
price_excl_vat        = p["price_excl_vat"]
total_royalty_cost    = p["total_royalty_cost"]
total_costs           = p["total_costs"]
gross_profit          = p["gross_profit"]
margin_pct            = p["margin_pct"]
breakeven_units       = p["breakeven_units"]
total_cost_per_unit   = p["total_cost_per_unit"]
gross_margin_per_unit = p["gross_margin_per_unit"]
roi                   = p["roi"]
upfront               = p["upfront"]
upfront_editorial     = p["upfront_editorial"]
printing_cost         = p["printing_cost"]

units_per_month, inflows, outflows, net_cf, cumulative, remaining = compute_cf(
    pct_per_month,
    upfront_editorial=upfront_editorial,
    printing_cost=printing_cost,
    estimated_sales=estimated_sales,
    quantity_produced=quantity_produced,
    net_receipt_per_unit=net_receipt_per_unit,
    royalty_per_unit=royalty_per_unit,
    printing_delay_months=int(printing_delay_months),
    royalty_payment_every_n=int(royalty_payment_every_n),
)
peak_deficit   = get_peak_deficit(upfront_editorial, cumulative)
recovery_month = get_recovery_month(cumulative)
total_inflow   = sum(inflows)
total_outflow  = upfront_editorial + sum(outflows)

monthly_rate      = get_monthly_rate(discount_rate)
cf_series         = [-upfront_editorial] + net_cf
_, pv_flows, cumulative_pv, npv = compute_dcf(cf_series, monthly_rate)
pv_inf            = sum(cf / (1 + monthly_rate) ** t for t, cf in enumerate(cf_series) if cf > 0)
pi                = pv_inf / upfront if upfront > 0 else 0
cum_pb            = [-upfront_editorial] + cumulative
payback_m         = next((i for i, c in enumerate(cum_pb) if c >= 0), None)

month_labels = [f"Month {i+1}" for i in range(24)]
all_labels   = ["Pre-launch"] + month_labels


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Summary",
    "Profit & Loss Overview",
    "Cash Flow Projection",
    "Investment Analysis",
    "Scenario Comparison",
])


# ── TAB 0: EXECUTIVE SUMMARY ─────────────────────────────────
with tab0:
    book_name    = title if title else "Untitled Book"
    recovery_str = f"Month {recovery_month}" if recovery_month else "outside the 24-month window"
    be_str       = fmtu(breakeven_units) if breakeven_units != float('inf') else "N/A"

    st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Executive Summary</div>
            <p style="font-family:Helvetica,Arial,sans-serif; font-size:0.95rem;
                      color:#2d3748; line-height:1.8; margin:0;">
                <b>"{book_name}"</b> has a retail price of <b>{fmt2(retail_price)}</b> and a print run
                of <b>{fmtu(quantity_produced)} units</b> at a unit cost of <b>{fmt2(unit_cost)}</b>.
                At the estimated sales volume of <b>{fmtu(estimated_sales)} units</b>, the title generates
                <b style="color:{'#1a5c3a' if revenue > 0 else '#8b1a1a'};">{fmt(revenue)}</b> in net
                revenue against <b style="color:#8b1a1a;">{fmt(total_costs)}</b> in total costs,
                yielding a gross profit of
                <b style="color:{'#1a5c3a' if gross_profit >= 0 else '#8b1a1a'};">{fmt(gross_profit)}</b>
                ({margin_pct:.1f}% margin).
            </p>
            <p style="font-family:Helvetica,Arial,sans-serif; font-size:0.95rem;
                      color:#2d3748; line-height:1.8; margin:0.8rem 0 0 0;">
                The title breaks even at <b>{be_str} units</b> and delivers a return on investment
                of <b>{roi:.1f}%</b>. Cash flow turns positive by <b>{recovery_str}</b>, with a
                peak financing requirement of <b style="color:#8b1a1a;">{fmt(abs(peak_deficit))}</b>.
                Printing costs of <b>{fmt(printing_cost)}</b> are due at month {int(printing_delay_months)};
                royalties are settled every {int(royalty_payment_every_n)} months.
            </p>
            <p style="font-family:Helvetica,Arial,sans-serif; font-size:0.95rem;
                      color:#2d3748; line-height:1.8; margin:0.8rem 0 0 0;">
                The discounted analysis at a <b>{discount_rate*100:.1f}% hurdle rate</b> yields an
                NPV of <b style="color:{'#1a5c3a' if npv >= 0 else '#8b1a1a'};">{fmt(npv)}</b>.
                The profitability index is <b>{pi:.2f}x</b>
                ({'above' if pi >= 1 else 'below'} the 1.0x threshold).
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Key Metrics</div>',
                unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    for col, label, value, color, delta in [
        (m1, "Net Revenue",  fmt(revenue),  "#6b8cff", ""),
        (m2, "Gross Profit", fmt(gross_profit), "#52b788" if gross_profit >= 0 else "#e07070", f"{margin_pct:.1f}% margin"),
        (m3, "Break-Even",   f"{be_str} units", "#f0c674", "units to cover all costs"),
        (m4, "Return on Investment",          f"{roi:.1f}%", "#52b788" if roi >= 0 else "#e07070", "on fixed cost investment"),
    ]:
        with col:
            kpi_card(label, value, color, delta)

    st.markdown("<br>", unsafe_allow_html=True)
    m5, m6, m7, m8 = st.columns(4)
    for col, label, value, color, delta in [
        (m5, "NPV",                fmt(npv),    "#52b788" if npv >= 0 else "#e07070", f"at {discount_rate*100:.1f}% discount rate"),
        (m6, "Cash Recovery",      recovery_str,"#52b788" if recovery_month else "#e07070", "first month CF positive"),
        (m7, "Peak Financing",     fmt(abs(peak_deficit)), "#90cdf4", "max cash needed upfront"),
        (m8, "Profitability Index", f"{pi:.2f}x","#52b788" if pi >= 1 else "#e07070", "PV inflows / investment"),
    ]:
        with col:
            kpi_card(label, value, color, delta)
    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 1: P&L OVERVIEW ──────────────────────────────────────
with tab1:

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Net Revenue", fmt(revenue), "#6b8cff")
    with k2: kpi_card("Total Costs", fmt(total_costs), "#e07070")
    with k3:
        kpi_card("Gross Profit / Loss", fmt(gross_profit),
                 "#52b788" if gross_profit >= 0 else "#e07070",
                 f"{margin_pct:.1f}% margin",
                 "#1a5c3a" if gross_profit >= 0 else "#8b1a1a")
    with k4:
        be_val = f"{fmtu(breakeven_units)} units" if breakeven_units != float('inf') else "N/A"
        kpi_card("Break-Even Quantity", be_val, "#f0c674")

    st.markdown("<br>", unsafe_allow_html=True)
    k5, k6, k7 = st.columns(3)
    with k5: kpi_card("Total Cost per Unit Sold", fmt2(total_cost_per_unit), "#90cdf4", "all costs ÷ units sold")
    with k6:
        kpi_card("Gross Margin per Unit", fmt2(gross_margin_per_unit), "#52b788",
                 "net receipt − royalty − fixed cost/unit",
                 "#1a5c3a" if gross_margin_per_unit >= 0 else "#8b1a1a")
    with k7:
        kpi_card("Return on Investment", f"{roi:.1f}%", "#f0c674",
                 "gross profit ÷ total fixed costs",
                 "#1a5c3a" if roi >= 0 else "#8b1a1a")

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns(2, gap="large")
    with cl:
        st.markdown('<div class="section-card"><div class="section-title">Cost Breakdown</div>', unsafe_allow_html=True)
        df_costs = pd.DataFrame({
            "Category":   ["Production","Translation","Design","Digital Files","Royalties"],
            "Amount (€)": [unit_cost*quantity_produced, translation_fee,
                           design_fee, digital_files_cost, total_royalty_cost],
        })
        df_costs["Amount (€)"] = df_costs["Amount (€)"].map(lambda x: f"{x:,.0f}€".replace(",","."))
        st.dataframe(df_costs, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cr:
        st.markdown('<div class="section-card"><div class="section-title">P&L Summary</div>', unsafe_allow_html=True)
        df_pl = pd.DataFrame({
            "Category":   ["Gross Revenue","VAT Deduction","Wholesale Discount",
                           "Net Revenue","Total Costs","Gross Profit"],
            "Amount (€)": [retail_price*estimated_sales,
                           -(retail_price-price_excl_vat)*estimated_sales,
                           -(price_excl_vat*wholesale_discount_pct*estimated_sales),
                           revenue, -total_costs, gross_profit],
        })
        def color_pl(val):
            return f"color: {'#1a5c3a' if val >= 0 else '#8b1a1a'}; font-weight: 600"
        styled = (df_pl.style.applymap(color_pl, subset=["Amount (€)"])
                  .format({"Amount (€)": lambda x: f"{x:,.0f}€".replace(",",".")}))
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Break-Even Analysis</div>', unsafe_allow_html=True)
    step        = max(1, int(quantity_produced // 60))
    units_range = list(range(0, int(quantity_produced)+1, step))
    revenues_r  = [net_receipt_per_unit * u for u in units_range]
    costs_r     = [total_fixed_sunk + royalty_per_unit * u for u in units_range]
    chart_breakeven(units_range, revenues_r, costs_r, breakeven_units, estimated_sales, quantity_produced, fmtu)
    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 2: CASH FLOW PROJECTION ──────────────────────────────
with tab2:

    st.markdown('<div class="section-card"><div class="section-title">Cash Flow Breakdown</div>', unsafe_allow_html=True)
    st.markdown(f"""
        <p style='color:#4a5568; font-size:0.88rem; margin-bottom:0.8rem;'>
            Editorial fees paid upfront. Printing ({fmt(printing_cost)}) due at
            <b>month {int(printing_delay_months)}</b>.
            Royalties settled every <b>{int(royalty_payment_every_n)} months</b>.
            Edit Sales % in the sidebar.
        </p>
    """, unsafe_allow_html=True)

    df_cf = pd.DataFrame({
        "Month":           ["Pre-launch"] + month_labels,
        "Sales %":         ["-"] + [f"{p:.1f}%" for p in pct_per_month],
        "Units Sold":      [0] + units_per_month,
        "Remaining Stock": [int(quantity_produced)] + remaining,
        "Inflows (€)":     [0.0] + inflows,
        "Outflows (€)":    [float(upfront_editorial)] + outflows,
        "Net CF (€)":      [-float(upfront_editorial)] + net_cf,
        "Cumulative (€)":  [-float(upfront_editorial)] + cumulative,
    })
    def color_cf(val):
        if isinstance(val, (int, float)):
            return f"color: {'#1a5c3a' if val >= 0 else '#8b1a1a'}; font-weight: 600"
        return ""
    styled_cf = (df_cf.style.applymap(color_cf, subset=["Net CF (€)","Cumulative (€)"])
                 .format({"Inflows (€)": lambda x: fmt(x), "Outflows (€)": lambda x: fmt(x),
                          "Net CF (€)": lambda x: fmt(x), "Cumulative (€)": lambda x: fmt(x)}))
    st.dataframe(styled_cf, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cf1, cf2, cf3, cf4 = st.columns(4)
    with cf1: kpi_card("Total Inflows", fmt(total_inflow), "#6b8cff")
    with cf2: kpi_card("Total Outflows", fmt(total_outflow), "#e07070")
    with cf3: kpi_card("Peak Financing Need", fmt(abs(peak_deficit)), "#8b1a1a", "", "#8b1a1a")
    with cf4:
        rec  = f"Month {recovery_month}" if recovery_month else "Not recovered"
        recc = "#1a5c3a" if recovery_month else "#8b1a1a"
        kpi_card("Cash Flow Recovery", rec, recc, "", recc)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-card"><div class="section-title">Cumulative Cash Position</div>', unsafe_allow_html=True)
    chart_cumulative_cf(all_labels, [-upfront_editorial] + cumulative, recovery_month)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Stock Depletion Over Time</div>', unsafe_allow_html=True)
    chart_stock_depletion(all_labels, [int(quantity_produced)] + remaining)
    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 3: INVESTMENT ANALYSIS ───────────────────────────────
with tab3:

    i1, i2, i3 = st.columns(3)
    with i1:
        kpi_card("Net Present Value", fmt(npv),
                 "#52b788" if npv >= 0 else "#e07070",
                 "Value created" if npv >= 0 else "Destroys value",
                 "#1a5c3a" if npv >= 0 else "#8b1a1a")
    with i2:
        pv_str = f"Month {payback_m}" if payback_m is not None else "Not recovered"
        kpi_card("Payback Period", pv_str,
                 "#52b788" if payback_m is not None else "#e07070",
                 "cumulative CF turns positive",
                 "#1a5c3a" if payback_m is not None else "#8b1a1a")
    with i3:
        kpi_card("Profitability Index", f"{pi:.2f}x",
                 "#52b788" if pi >= 1 else "#e07070",
                 "if > 1.0 — invest" if pi >= 1 else "if < 1.0 — don't invest",
                 "#1a5c3a" if pi >= 1 else "#8b1a1a")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Discounted Cash Flow Table</div>', unsafe_allow_html=True)
    disc_factors = [1 / (1 + monthly_rate) ** t for t in range(len(cf_series))]
    df_dcf = pd.DataFrame({
        "Period":            ["Pre-launch"] + [f"Month {i+1}" for i in range(24)],
        "Net CF (€)":        cf_series,
        "Discount Factor":   [f"{d:.4f}" for d in disc_factors],
        "PV of CF (€)":      pv_flows,
        "Cumulative PV (€)": cumulative_pv,
    })
    def color_dcf(val):
        if isinstance(val, (int, float)):
            return f"color: {'#1a5c3a' if val >= 0 else '#8b1a1a'}; font-weight: 600"
        return ""
    styled_dcf = (df_dcf.style.applymap(color_dcf, subset=["Net CF (€)","PV of CF (€)","Cumulative PV (€)"])
                  .format({"Net CF (€)": lambda x: fmt(x), "PV of CF (€)": lambda x: fmt(x),
                           "Cumulative PV (€)": lambda x: fmt(x)}))
    st.dataframe(styled_dcf, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">NPV Sensitivity to Discount Rate</div>', unsafe_allow_html=True)
    chart_npv_sensitivity(cf_series, discount_rate)
    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 4: SCENARIO COMPARISON ───────────────────────────────
with tab4:

    st.markdown('<div class="section-card"><div class="section-title">Scenario Parameters</div>',
                unsafe_allow_html=True)
    st.markdown("<p style='color:#4a5568; font-size:0.88rem; margin-bottom:1rem;'>Adjust sell-through rate per scenario. All other inputs come from the sidebar.</p>",
                unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown("<p style='color:#52b788; font-weight:700; font-size:0.85rem; margin-bottom:0.3rem;'>BEST CASE</p>", unsafe_allow_html=True)
        best_pct = st.slider("Sell-through %", 50, 100, 90, 5, key="best_pct")
    with sc2:
        st.markdown("<p style='color:#f0c674; font-weight:700; font-size:0.85rem; margin-bottom:0.3rem;'>BASE CASE</p>", unsafe_allow_html=True)
        base_pct = st.slider("Sell-through %", 50, 100, 70, 5, key="base_pct")
    with sc3:
        st.markdown("<p style='color:#e07070; font-weight:700; font-size:0.85rem; margin-bottom:0.3rem;'>WORST CASE</p>", unsafe_allow_html=True)
        worst_pct = st.slider("Sell-through %", 10, 70, 40, 5, key="worst_pct")
    st.markdown('</div>', unsafe_allow_html=True)

    best  = calc_scenario(best_pct,  quantity_produced, net_receipt_per_unit, royalty_per_unit, total_fixed_sunk)
    base  = calc_scenario(base_pct,  quantity_produced, net_receipt_per_unit, royalty_per_unit, total_fixed_sunk)
    worst = calc_scenario(worst_pct, quantity_produced, net_receipt_per_unit, royalty_per_unit, total_fixed_sunk)

    st.markdown("<br>", unsafe_allow_html=True)
    scenario_row("Best Case",  "#f0faf4", "#52b788", best,  fmt, fmtu)
    scenario_row("Base Case",  "#fffbea", "#f0c674", base,  fmt, fmtu)
    scenario_row("Worst Case", "#fff5f5", "#e07070", worst, fmt, fmtu)

    st.markdown('<div class="section-card"><div class="section-title">Scenario Profit Comparison</div>',
                unsafe_allow_html=True)
    chart_scenario_comparison(
        ["Best Case","Base Case","Worst Case"],
        [best["Revenue"], base["Revenue"], worst["Revenue"]],
        [best["Costs"],   base["Costs"],   worst["Costs"]],
        [best["Profit"],  base["Profit"],  worst["Profit"]],
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Scenario Summary Table</div>',
                unsafe_allow_html=True)
    df_sc = pd.DataFrame({
        "Metric":    ["Sell-Through %","Units Sold","Net Revenue",
                      "Total Costs","Gross Profit","Margin %","ROI %"],
        "Best":  [f"{best_pct}%",  fmtu(best["Units"]),  fmt(best["Revenue"]),
                     fmt(best["Costs"]),  fmt(best["Profit"]),
                     f"{best['Margin']:.1f}%",  f"{best['ROI']:.1f}%"],
        "Base":  [f"{base_pct}%",  fmtu(base["Units"]),  fmt(base["Revenue"]),
                     fmt(base["Costs"]),  fmt(base["Profit"]),
                     f"{base['Margin']:.1f}%",  f"{base['ROI']:.1f}%"],
        "Worst": [f"{worst_pct}%", fmtu(worst["Units"]), fmt(worst["Revenue"]),
                     fmt(worst["Costs"]), fmt(worst["Profit"]),
                     f"{worst['Margin']:.1f}%", f"{worst['ROI']:.1f}%"],
    })
    st.dataframe(df_sc, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
