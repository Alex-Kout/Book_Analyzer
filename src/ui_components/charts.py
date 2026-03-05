"""
All matplotlib chart rendering functions.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import streamlit as st

SPINE_COLOR = '#e8e4dc'
TICK_COLOR  = '#718096'
BG_COLOR    = '#fafaf8'


def _base_fig(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor(BG_COLOR)
    plt.rcParams['font.family'] = 'DejaVu Sans'
    for spine in ax.spines.values():
        spine.set_color(SPINE_COLOR)
    ax.tick_params(colors=TICK_COLOR, labelsize=7.5)
    return fig, ax


def _euro_fmt(x, _):
    return f'{x:,.0f}€'.replace(',', '.')


def chart_breakeven(units_range, revenues_r, costs_r,
                    breakeven_units, estimated_sales, quantity_produced, fmtu):
    fig, ax = _base_fig((10, 3.2))
    ax.plot(units_range, revenues_r, color='#52b788', linewidth=2.2, label='Revenue')
    ax.plot(units_range, costs_r,    color='#e07070', linewidth=2.2, linestyle='--', label='Total Costs')
    ax.fill_between(units_range, revenues_r, costs_r,
                    where=[r > c for r, c in zip(revenues_r, costs_r)],
                    alpha=0.35, color='#0d3320', label='Profit zone')
    ax.fill_between(units_range, revenues_r, costs_r,
                    where=[r <= c for r, c in zip(revenues_r, costs_r)],
                    alpha=0.35, color='#6b0f0f', label='Loss zone')
    if breakeven_units != float('inf') and breakeven_units <= quantity_produced:
        ax.axvline(x=breakeven_units, color='#f0c674', linewidth=1.8, linestyle=':',
                   label=f'Break-even ({fmtu(breakeven_units)} units)')
    ax.axvline(x=estimated_sales, color='#1a1a2e', linewidth=1.5, linestyle=':',
               label=f'Est. Sales ({fmtu(estimated_sales)} units)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_euro_fmt))
    ax.set_xlabel("Units Sold", fontsize=8.5, color='#4a5568')
    ax.set_ylabel("Amount (€)", fontsize=8.5, color='#4a5568')
    ax.legend(fontsize=7.5, framealpha=0.85, loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def chart_cumulative_cf(all_labels, all_cumul, recovery_month):
    bar_colors = ['#0d3320' if v >= 0 else '#6b0f0f' for v in all_cumul]
    fig, ax    = _base_fig((12, 3.8))
    ax.bar(range(len(all_labels)), all_cumul, color=bar_colors, alpha=0.85, width=0.6)
    ax.axhline(y=0, color='#1a1a2e', linewidth=1.2)
    if recovery_month:
        ax.axvline(x=recovery_month, color='#f0c674', linewidth=1.8,
                   linestyle=':', label=f'Recovery: Month {recovery_month}')
        ax.legend(fontsize=7.5, framealpha=0.85)
    ax.set_xticks(range(len(all_labels)))
    ax.set_xticklabels(all_labels, rotation=45, ha='right', fontsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_euro_fmt))
    ax.set_xlabel("Period", fontsize=8.5, color='#4a5568')
    ax.set_ylabel("Cumulative Cash (€)", fontsize=8.5, color='#4a5568')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def chart_stock_depletion(all_labels, stock_levels):
    fig, ax = _base_fig((12, 2.8))
    ax.fill_between(range(len(all_labels)), stock_levels, alpha=0.3, color='#2d3561')
    ax.plot(range(len(all_labels)), stock_levels, color='#6b8cff', linewidth=2.2)
    ax.set_xticks(range(len(all_labels)))
    ax.set_xticklabels(all_labels, rotation=45, ha='right', fontsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'.replace(',', '.')))
    ax.set_xlabel("Period", fontsize=8.5, color='#4a5568')
    ax.set_ylabel("Units in Stock", fontsize=8.5, color='#4a5568')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def chart_npv_sensitivity(cf_series, discount_rate):
    rates      = np.linspace(0.01, 1.0, 200)
    npv_values = []
    for r in rates:
        mr = (1 + r) ** (1/12) - 1
        npv_values.append(sum(cf / (1 + mr) ** t for t, cf in enumerate(cf_series)))
    fig, ax = _base_fig((10, 3.2))
    ax.plot(rates * 100, npv_values, color='#6b8cff', linewidth=2.2)
    ax.axhline(y=0, color='#1a1a2e', linewidth=1.0)
    ax.axvline(x=discount_rate * 100, color='#f0c674', linewidth=1.8,
               linestyle=':', label=f'Your rate: {discount_rate*100:.1f}%')
    ax.fill_between(rates * 100, npv_values, 0,
                    where=[v >= 0 for v in npv_values], alpha=0.2, color='#0d3320', label='NPV > 0')
    ax.fill_between(rates * 100, npv_values, 0,
                    where=[v < 0 for v in npv_values],  alpha=0.2, color='#6b0f0f', label='NPV < 0')
    ax.set_xlim(1, 100)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_euro_fmt))
    ax.set_xlabel("Discount Rate (%)", fontsize=8.5, color='#4a5568')
    ax.set_ylabel("NPV (€)", fontsize=8.5, color='#4a5568')
    ax.legend(fontsize=7.5, framealpha=0.85)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def chart_scenario_comparison(scenarios_l, revenues_s, costs_s, profits_s):
    bcs = ['#52b788' if p >= 0 else '#e07070' for p in profits_s]
    x   = np.arange(3)
    w   = 0.28
    fig, ax = _base_fig((9, 3.5))
    ax.bar(x - w, revenues_s, w, label='Net Revenue', color='#6b8cff', alpha=0.85)
    ax.bar(x,     costs_s,    w, label='Total Costs',  color='#e07070', alpha=0.85)
    ax.bar(x + w, profits_s,  w, label='Gross Profit', color=bcs,       alpha=0.85)
    ax.axhline(y=0, color='#1a1a2e', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios_l, fontsize=9, color='#4a5568')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:,.0f}€'.replace(',', '.')))
    ax.legend(fontsize=7.5, framealpha=0.85)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
