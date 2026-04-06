"""
forecast.py — Lagged regression early warning model
Uses confirmed arrest→death +4mo lead-lag to project future OD deaths
"""
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

LAG_MONTHS = 4  # Confirmed from cross-correlation: arrests lead deaths by 4 months


def _load_vsrr_validation(future_dates, future_preds, std_err, data_dir):
    """
    Load CDC VSRR provisional county-level overdose data for Jackson County.
    Returns a validation dict comparing our forecast to 2025 actuals.
    VSRR tracks all-cause OD deaths (rolling 12-month); we compute YoY monthly delta
    as a directional proxy for validating our Alcohol-Induced specific model.
    """
    vsrr_path = os.path.join(data_dir, 'vsrr_jackson_county.csv')
    if not os.path.exists(vsrr_path):
        return None
    try:
        vsrr = pd.read_csv(vsrr_path)
        vsrr['month_date'] = pd.to_datetime(
            vsrr['year'].astype(str) + '-' + vsrr['month'].astype(str).str.zfill(2) + '-01'
        )
        vsrr['rolling12'] = pd.to_numeric(vsrr['provisional_drug_overdose'], errors='coerce')
        vsrr = vsrr.sort_values('month_date').reset_index(drop=True)
        vsrr['yoy_delta'] = vsrr['rolling12'].diff()  # deaths[M] - deaths[M-12]

        # Year totals (rolling12 at December = annual total)
        year_totals = {}
        for yr in [2020, 2021, 2022, 2023, 2024]:
            row = vsrr[vsrr['month_date'] == f'{yr}-12-01']
            if not row.empty:
                year_totals[yr] = int(row['rolling12'].values[0])

        # Monthly YoY deltas for the forecast window (Jan-Apr 2025)
        months_validation = []
        for i, fdate in enumerate(future_dates):
            label = fdate.strftime('%b %Y')
            row = vsrr[vsrr['month_date'] == fdate]
            if row.empty:
                continue
            delta = float(row['yoy_delta'].values[0])
            r12 = float(row['rolling12'].values[0])
            predicted = round(float(future_preds[i]), 1)
            # Avg monthly deaths = rolling12 / 12 (rough all-cause rate)
            all_cause_monthly_rate = round(r12 / 12, 1)
            within_ci = (predicted - 1.645 * std_err) <= all_cause_monthly_rate <= (predicted + 1.645 * std_err)
            months_validation.append({
                'label': label,
                'date': int(fdate.timestamp() * 1000),
                'predicted_alcohol': predicted,
                'vsrr_rolling12': int(r12),
                'vsrr_monthly_rate': all_cause_monthly_rate,
                'yoy_delta': int(delta),
                'within_ci': within_ci,
            })

        net_delta = int(vsrr[vsrr['month_date'].isin(future_dates)]['yoy_delta'].sum())
        data_as_of = vsrr['data_as_of'].iloc[-1][:10] if 'data_as_of' in vsrr.columns else 'Jan 2026'

        return {
            'year_totals': year_totals,
            'months': months_validation,
            'net_yoy_delta_q1': net_delta,
            'trend_2024': 'declining' if year_totals.get(2024, 0) < year_totals.get(2023, 0) else 'rising',
            'data_as_of': data_as_of,
            'note': (
                'VSRR tracks all-cause OD deaths (rolling 12-month); '
                'model predicts Alcohol-Induced specifically. '
                'YoY delta used as directional proxy for validation.'
            ),
        }
    except Exception as e:
        return {'error': str(e)}


def build_forecast(arrests_ts, drug_ts, lag=LAG_MONTHS, horizon=4, data_dir=None):
    """
    Train a lagged linear regression:
      X = monthly arrest volume at time t
      y = Alcohol-Induced deaths at time t + lag

    Returns a dict suitable for JSON serialization.
    """
    # Primary target: Alcohol-Induced (only category with p<0.05)
    target_col = None
    for col in drug_ts.columns:
        if 'Alcohol-Induced' in col:
            target_col = col
            break
    if target_col is None:
        target_col = drug_ts.columns[0]

    od_col = None
    for col in drug_ts.columns:
        if 'Unintentional' in col or 'OD' in col:
            od_col = col
            break

    deaths = drug_ts[target_col]
    total_deaths = drug_ts.sum(axis=1)

    # Align on common index
    common = arrests_ts.index.intersection(deaths.index)
    if len(common) < lag + 10:
        return None

    arr = arrests_ts.loc[common, 'Arrests'].values.astype(float)
    dth = deaths.loc[common].values.astype(float)
    tot = total_deaths.loc[common].values.astype(float)
    n = len(arr)

    # Lagged training pairs: arrests[t] → deaths[t + lag]
    X_train = arr[:n - lag].reshape(-1, 1)
    y_train = dth[lag:]
    y_tot_train = tot[lag:]

    model = LinearRegression()
    model.fit(X_train, y_train)

    # In-sample fit
    y_fitted = model.predict(X_train)
    residuals = y_train - y_fitted
    std_err = float(np.std(residuals))
    r2 = float(model.score(X_train, y_train))

    # Forward forecast: use last `lag` months of arrests → next `lag` months of deaths
    future_arr = arr[-lag:].reshape(-1, 1)
    future_preds = model.predict(future_arr)

    # Future dates: starting the month after the last death date
    last_death_date = deaths.loc[common].index[-1]
    future_dates = [last_death_date + pd.DateOffset(months=i + 1) for i in range(lag)]

    # Historical stats for alert thresholds
    hist_mean = float(dth.mean())
    hist_std = float(dth.std())
    max_pred = float(future_preds.max())
    next_q_sum = float(future_preds[:3].sum())

    if max_pred > hist_mean + 2.0 * hist_std:
        alert = 'critical'
        alert_color = '#ff2d78'
        recommendation = (
            f"CRITICAL: Model predicts {int(max_pred)} {target_col} deaths — "
            f"{((max_pred - hist_mean) / hist_std):.1f}σ above average. "
            "Immediate naloxone pre-positioning and outreach surge recommended."
        )
    elif max_pred > hist_mean + 1.0 * hist_std:
        alert = 'elevated'
        alert_color = '#ffab00'
        recommendation = (
            f"ELEVATED: Predicted {int(max_pred)} {target_col} deaths — above 1σ threshold. "
            "Recommend alerting treatment centers and increasing mobile harm reduction patrols."
        )
    elif max_pred > hist_mean:
        alert = 'moderate'
        alert_color = '#7dfbff'
        recommendation = (
            f"MODERATE: Predicted deaths above average baseline ({int(hist_mean)}). "
            "Maintain standard naloxone distribution. Monitor arrest trends weekly."
        )
    else:
        alert = 'normal'
        alert_color = '#00ffcc'
        recommendation = (
            f"NORMAL: Predicted deaths below historical average ({int(hist_mean)}). "
            "Standard harm reduction operations sufficient."
        )

    # In-sample dates (for chart — shifted by lag)
    in_sample_dates = [common[i + lag] for i in range(len(X_train))]

    # ── VSRR validation: 2025 actuals from CDC provisional county data ────────
    _data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    validation = _load_vsrr_validation(future_dates, future_preds, std_err, _data_dir)

    return {
        'target_col': target_col,
        'lag_months': lag,
        'forecast_dates': [int(d.timestamp() * 1000) for d in future_dates],
        'forecast_labels': [d.strftime('%b %Y') for d in future_dates],
        'predicted': [round(float(p), 1) for p in future_preds],
        'lower_90': [round(max(0.0, float(p) - 1.645 * std_err), 1) for p in future_preds],
        'upper_90': [round(float(p) + 1.645 * std_err, 1) for p in future_preds],
        'alert': alert,
        'alert_color': alert_color,
        'recommendation': recommendation,
        'r2': round(r2, 3),
        'std_err': round(std_err, 1),
        'hist_mean': round(hist_mean, 1),
        'hist_std': round(hist_std, 1),
        'coef': round(float(model.coef_[0]), 5),
        'next_quarter_total': int(round(next_q_sum)),
        'in_sample_dates': [int(d.timestamp() * 1000) for d in in_sample_dates],
        'in_sample_fitted': [round(float(v), 1) for v in y_fitted],
        'historical_dates': [int(d.timestamp() * 1000) for d in common],
        'historical_deaths': [round(float(v), 1) for v in dth],
        'historical_arrests': [round(float(v), 1) for v in arr],
        'validation': validation,
    }
