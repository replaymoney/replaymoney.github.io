# Episode 1 simulation: model specification

"If the AI Bubble Pops, What Happens to YOUR 401(k)?" Illustrative Monte Carlo, **not a forecast**.

Files:
- `ai401k_model.py` — the model
- `run_all.py` — reproduces every number used in the video and every stress test
- `results.md` / `results.json` — output of `run_all.py`

## How to reproduce

```
pip install numpy
python3 run_all.py        # about 10 seconds; writes results.json and results.md
```

- Random seeds are fixed: boom = 1, cool-off = 2, pop = 3. The same seed is used for every investor within a future, so their results are compared on the same random market path ("paired").
- Results were generated with numpy 2.x. Different numpy major versions may change the random stream slightly; medians move by well under 1%.

## 1. Market

The S&P 500 fund is modeled as two "sleeves" held in proportion to their market value (cap-weighted, no rebalancing):

| Sleeve | Starting weight | Meaning |
|---|---|---|
| AI giants | 37% | The 10 largest holdings (SPY holdings, Nov 12, 2026 close) |
| Rest | 63% | The other ~490 companies |

Monthly log returns, 480 months (40 years):

| Parameter | Value | Note |
|---|---|---|
| Long-run return, "rest" sleeve | 9.5% / yr nominal | Close to the S&P 500's long-run total return. Used as the baseline drift for both sleeves. |
| Volatility, "rest" sleeve | 15% / yr | Close to the S&P 500's long-run annualized volatility |
| Volatility, AI giants | 25% / yr | **Model assumption** (a concentrated basket of large tech stocks is more volatile than the whole index). Not a historical measurement. |
| Correlation between sleeves | 0.75 | Model assumption |
| Distribution | Normal monthly log returns | Understates extreme crashes (fat tails) |
| Dividends | Included in the return assumption | Returns are total returns |
| Fees, taxes | Not modeled | Same for every investor, so they do not change the comparison |

## 2. The three futures (each run 10,000 times)

We do **not** assign probabilities to these futures.

| Future | Definition |
|---|---|
| Boom | AI giants beat the rest by ~6% / yr for the first 5 years, then normal |
| Cool-off | AI giants trail the rest by ~3% / yr for the first 10 years |
| Pop | Starting in a random month within the first 3 years, AI giants lose 70% over 24 months while the rest loses 25% (contagion). Afterwards AI giants trail by 2% / yr for 10 years. Loosely based on 2000–02 (Nasdaq ≈ −78%, S&P 500 ≈ −49%) and the slow recovery of bubble-era leaders. |

## 3. The investors

All start at age 25 with $10,000 and add **$300 every month for 40 years**. The $300 is a fixed nominal amount (it does not rise with inflation), added at the end of each month. Total put in: $154,000.

| Investor | Rule |
|---|---|
| Holder | Owns the cap-weighted fund, never sells |
| Panic-seller | If the account falls 30% below its own previous peak, sells everything to cash (3% / yr). Keeps adding $300 a month into cash. Buys back in (all of it) only when the fund regains the index peak it had when they sold. The rule repeats every time it is triggered. |
| Capped 3% portfolio | Only 3% in the AI giants and 97% in the "rest" sleeve, rebalanced monthly. This is a **capped-concentration** portfolio, not an equal-weight fund (an equal-weight S&P 500 fund is the closest real-world idea). |

## 4. Outputs

- "Today's money" = nominal ÷ 1.03^40 (≈ 3.26), i.e. 3% / yr inflation.
- "Typical result" in the video = **median** across runs.
- Panic vs holder and capped vs holder = median of the paired ratio (same market path).
- "Scary moment" = holder's lowest account value in the first 6 years divided by the money put in up to that point (median).

## 5. Limitations

- Scenario sizes (boom +6%, cool-off −3%, pop −70%) are illustrative assumptions.
- Normal returns understate extreme events.
- No fees, taxes, or employer match.
- The panic rule is one simple behavior; real investors vary (see the buy-back tests in `results.md`).
- The $300 contribution does not grow with inflation or salary.

## 6. Stress tests (in `results.md`)

1. Return for the rest of the market: 7.5%, 9.5%, 11%, crossed with AI-giant volatility 20%, 25%, 30% (9 combinations).
2. Cash yield 1% instead of 3%.
3. Correlation 0.9 instead of 0.75.
4. Four buy-back rules for the panic-seller: back at the old peak (main), 20% above the low, after 12 months, after 6 months.

## 7. What held up

- The typical panic-seller ends up behind the holder in 8 of 9 grid settings in all three futures, and under 1% cash, 0.9 correlation, and −50% / −85% crash depths. Panic beats holding in a minority of runs (3%–12%).
- Buying back sooner shrinks the gap a lot (6-month rule: about 0%). The cost of panic depends mostly on how long you stay out.
- "Best-future panic-seller < worst-future holder" holds when AI-giant volatility is 25% or 30% and fails at 20%. The video says "in our main run".
- Dollar amounts depend heavily on the return assumption ($274K–$1.09M across the grid). The video presents them as typical results of one illustrative setup, not forecasts.
