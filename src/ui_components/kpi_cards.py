"""
Reusable UI components: formatters and KPI cards.
"""
import streamlit as st


def fmt(n):
    return f"{n:,.0f}€".replace(",", ".")

def fmt2(n):
    return f"{n:,.2f}€".replace(",", ".")

def fmtu(n):
    return f"{int(n):,}".replace(",", ".")


def kpi_card(label, value, border_color, delta="", value_color=None):
    st.markdown(f"""
        <div class="kpi-box" style="border-top:3px solid {border_color};">
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
            <p class="kpi-delta">{delta}</p>
        </div>
    """, unsafe_allow_html=True)


def scenario_row(label, color, border, sc, fmt_fn, fmtu_fn):
    pc = "#1a5c3a" if sc["Profit"] >= 0 else "#8b1a1a"
    st.markdown(f"""
        <div style="background:{color}; border:1px solid {border};
                    border-left:5px solid {border}; border-radius:10px;
                    padding:1rem 1.4rem; margin-bottom:0.8rem;">
            <p style="font-family:Helvetica,Arial,sans-serif; font-size:0.85rem;
                      font-weight:700; color:#2d3748; margin:0 0 0.8rem 0;">{label}</p>
            <div style="display:grid; grid-template-columns:repeat(6,1fr); gap:1rem;">
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">Units Sold</p>
                    <p style="font-size:1rem; font-weight:700; color:#1a1a2e; margin:0;">{fmtu_fn(sc["Units"])}</p>
                </div>
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">Net Revenue</p>
                    <p style="font-size:1rem; font-weight:700; color:#1a1a2e; margin:0;">{fmt_fn(sc["Revenue"])}</p>
                </div>
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">Total Costs</p>
                    <p style="font-size:1rem; font-weight:700; color:#8b1a1a; margin:0;">{fmt_fn(sc["Costs"])}</p>
                </div>
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">Gross Profit</p>
                    <p style="font-size:1rem; font-weight:700; color:{pc}; margin:0;">{fmt_fn(sc["Profit"])}</p>
                </div>
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">Margin</p>
                    <p style="font-size:1rem; font-weight:700; color:{pc}; margin:0;">{sc["Margin"]:.1f}%</p>
                </div>
                <div>
                    <p style="font-size:0.62rem; color:#718096; text-transform:uppercase;
                              letter-spacing:0.06em; margin:0 0 0.2rem 0; font-weight:600;">ROI</p>
                    <p style="font-size:1rem; font-weight:700; color:{pc}; margin:0;">{sc["ROI"]:.1f}%</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
