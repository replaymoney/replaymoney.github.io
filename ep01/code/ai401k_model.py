"""AI bubble x your 401(k): illustrative Monte Carlo. NOT a forecast.

Market = two sleeves of a cap-weighted S&P 500 fund:
  AI   : the top-10 / AI-heavy giants, 37% of the index at the start (SPY holdings, 2026-11-12 close)
  REST : everything else, 63%
A cap-weighted fund simply owns both in proportion to their current value.

Three possible AI futures (we do not assign probabilities; each is run 10,000 times):
  boom  : AI sleeve beats the rest by ~6%/yr for 5 years, then normal
  fade  : AI sleeve trails the rest by ~3%/yr for 10 years
  pop   : starting in a random month in the first 3 years, AI sleeve loses 70% over 24 months while
          the rest loses 25% (contagion); afterwards AI trails by 2%/yr for 10 years (Cisco-style)

Investors (all start at age 25 with $10,000 and add $300/month for 40 years):
  holder  : cap-weighted S&P 500 fund, never sells
  panic   : same fund; if the account falls 30% below its peak, sells everything to cash (3%/yr),
            keeps saving into cash, buys back only when the fund regains its old peak
  spread  : a fund with only 3% in the AI giants (roughly equal-weight-like), rebalanced monthly
"""
import numpy as np

MONTHS = 40 * 12
START, MONTHLY = 10_000.0, 300.0
W_AI0 = 0.37
MU_REST = 0.095            # long-run nominal annual return for the rest of the market (approx.)
SIG_REST, SIG_AI, RHO = 0.15, 0.25, 0.75
CASH = 0.03


def market_paths(n, fate, rng):
    """Monthly log returns for (AI, REST): arrays shape (n, MONTHS)."""
    dt = 1 / 12
    z1 = rng.standard_normal((n, MONTHS)); z2 = rng.standard_normal((n, MONTHS))
    e_rest = z1
    e_ai = RHO * z1 + np.sqrt(1 - RHO ** 2) * z2
    mu_rest_log = np.log1p(MU_REST) * dt
    rest = mu_rest_log + SIG_REST * np.sqrt(dt) * e_rest
    ai = mu_rest_log + SIG_AI * np.sqrt(dt) * e_ai
    m = np.arange(MONTHS)[None, :]
    if fate == "boom":
        ai = ai + np.where(m < 60, np.log1p(0.06) * dt, 0)
    elif fate == "fade":
        ai = ai + np.where(m < 120, np.log(1 - 0.03) * dt, 0)
    elif fate == "pop":
        start = rng.integers(0, 36, n)[:, None]
        crash = (m >= start) & (m < start + 24)
        after = (m >= start + 24) & (m < start + 144)
        ai = np.where(crash, np.log(0.30) / 24 + SIG_AI * np.sqrt(dt) * e_ai * 0.5, ai)
        rest = np.where(crash, np.log(0.75) / 24 + SIG_REST * np.sqrt(dt) * e_rest * 0.5, rest)
        ai = ai + np.where(after, np.log(1 - 0.02) * dt, 0)
    return ai, rest


def run(n=10_000, fate="pop", seed=0):
    rng = np.random.default_rng(seed)
    ai, rest = market_paths(n, fate, rng)
    gai, grest = np.exp(ai), np.exp(rest)
    out = {}
    # index level of the cap-weighted fund (used by the panic seller's re-entry rule)
    a_val = np.full(n, W_AI0); r_val = np.full(n, 1 - W_AI0)
    idx_path = np.empty((n, MONTHS))
    for t in range(MONTHS):
        a_val = a_val * gai[:, t]; r_val = r_val * grest[:, t]
        idx_path[:, t] = a_val + r_val
    idx_ret = idx_path / np.concatenate([np.ones((n, 1)), idx_path[:, :-1]], axis=1)

    # holder
    v = np.full(n, START); low = np.full(n, START); contrib = START
    vmin_ratio = np.ones(n)
    for t in range(MONTHS):
        v = v * idx_ret[:, t] + MONTHLY
    out["holder"] = v

    # panic seller
    v = np.full(n, START); peak_acct = v.copy(); in_mkt = np.ones(n, bool)
    sold_idx_peak = np.zeros(n); idx_peak = np.ones(n); sold_ever = np.zeros(n, bool)
    months_out = np.zeros(n)
    for t in range(MONTHS):
        idx_now = idx_path[:, t]
        v = np.where(in_mkt, v * idx_ret[:, t], v * (1 + CASH) ** (1 / 12)) + MONTHLY
        idx_peak = np.maximum(idx_peak, idx_now)
        peak_acct = np.where(in_mkt, np.maximum(peak_acct, v), peak_acct)
        sell = in_mkt & (v < 0.70 * peak_acct)
        sold_idx_peak = np.where(sell, idx_peak, sold_idx_peak)
        in_mkt = in_mkt & ~sell
        sold_ever |= sell
        buy = (~in_mkt) & (idx_now >= sold_idx_peak) & ~sell
        in_mkt = in_mkt | buy
        peak_acct = np.where(buy, v, peak_acct)
        months_out += ~in_mkt
    out["panic"] = v
    out["panic_sold_share"] = sold_ever.mean()
    out["panic_months_out_median"] = np.median(months_out[sold_ever]) if sold_ever.any() else 0

    # spread (3% in AI giants, rebalanced monthly)
    w = 0.03
    sp_ret = w * gai + (1 - w) * grest
    v = np.full(n, START)
    for t in range(MONTHS):
        v = v * sp_ret[:, t] + MONTHLY
    out["spread"] = v

    # scary moment for the holder in the first 6 years: worst account value
    v = np.full(n, START); worst = np.full(n, np.inf)
    for t in range(72):
        v = v * idx_ret[:, t] + MONTHLY
        contributed = START + MONTHLY * (t + 1)
        worst = np.minimum(worst, v / contributed)
    out["worst_ratio_6y"] = worst
    return out


if __name__ == "__main__":
    contributed = START + MONTHLY * MONTHS
    print(f"total contributed: ${contributed:,.0f}")
    for fate in ("boom", "fade", "pop"):
        o = run(fate=fate, seed={"boom": 1, "fade": 2, "pop": 3}[fate])
        print(f"\n== {fate} ==")
        for k in ("holder", "panic", "spread"):
            x = o[k]
            print(f"  {k:7s} median ${np.median(x):>12,.0f}   10th pct ${np.percentile(x,10):>12,.0f}   90th ${np.percentile(x,90):>12,.0f}")
        print(f"  panic: share who ever sold {o['panic_sold_share']:.0%}, median months out {o['panic_months_out_median']:.0f}")
        print(f"  holder worst moment (first 6y), account/contributed: median {np.median(o['worst_ratio_6y']):.2f}")
        print(f"  panic vs holder (median of paired ratio): {np.median(o['panic']/o['holder']):.2f}")
        print(f"  spread vs holder (median of paired ratio): {np.median(o['spread']/o['holder']):.2f}")
