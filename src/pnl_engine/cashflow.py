"""
Cash flow projection calculations.
Payment timing is configurable:
- Editorial fees: always paid at month 0 (upfront)
- Printing cost: paid at a user-defined month
- Royalties: paid every N months (user-defined)
"""


def compute_cf(pct_list, upfront_editorial, printing_cost, estimated_sales,
               quantity_produced, net_receipt_per_unit, royalty_per_unit,
               printing_delay_months=5, royalty_payment_every_n=3):
    """
    - Editorial fees (translation, design, digital): paid at month 0 (upfront)
    - Printing cost: paid at month = printing_delay_months
    - Royalties: accumulated and paid every N months
    - Inflows: received the month the sale happens
    """
    units_l=[]; inflows_l=[]; outflows_l=[]; net_l=[]; cum_l=[]; remain_l=[]
    cum               = -upfront_editorial
    stock             = int(quantity_produced)
    accrued_royalties = 0.0

    for month_idx, p in enumerate(pct_list):
        month_num = month_idx + 1

        units  = min(int(estimated_sales * p / 100), stock)
        stock -= units
        inflow = net_receipt_per_unit * units

        accrued_royalties += royalty_per_unit * units
        royalty_payment    = 0.0
        if month_num % royalty_payment_every_n == 0:
            royalty_payment   = accrued_royalties
            accrued_royalties = 0.0

        printing_payment = printing_cost if month_num == printing_delay_months else 0.0

        outflow = royalty_payment + printing_payment
        net     = inflow - outflow
        cum    += net

        units_l.append(units)
        inflows_l.append(round(inflow, 2))
        outflows_l.append(round(outflow, 2))
        net_l.append(round(net, 2))
        cum_l.append(round(cum, 2))
        remain_l.append(stock)

    return units_l, inflows_l, outflows_l, net_l, cum_l, remain_l


def compute_dcf(cf_series, monthly_rate):
    import numpy as np
    disc_factors  = [1 / (1 + monthly_rate) ** t for t in range(len(cf_series))]
    pv_flows      = [cf * df for cf, df in zip(cf_series, disc_factors)]
    cumulative_pv = list(np.cumsum(pv_flows))
    npv           = sum(pv_flows)
    return disc_factors, pv_flows, cumulative_pv, npv


def compute_npv(cf_series, monthly_rate):
    return sum(cf / (1 + monthly_rate) ** t for t, cf in enumerate(cf_series))


def get_monthly_rate(annual_rate):
    return (1 + annual_rate) ** (1 / 12) - 1


def get_peak_deficit(upfront, cumulative):
    return min([-upfront] + cumulative)


def get_recovery_month(cumulative):
    return next((i + 1 for i, c in enumerate(cumulative) if c >= 0), None)
