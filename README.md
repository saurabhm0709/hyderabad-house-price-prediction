# Hyderabad House Asking-Price Prediction

Predicting the **asking price** of residential property listings in Hyderabad from
listing attributes (area, bedrooms, bathrooms, property type, floor, furnishing, …)
and locality-level signals (average price per sqft, locality rank, ratings, coordinates).

Data was scraped from MagicBricks into a SQLite database (`listings_master.db`) in
price bands, then joined, cleaned, and modelled. **19,340 usable listings** after
cleaning, split 80/20 into train (15,472) and test (3,868).

---

## Results

Target is `log1p(price)`; errors are reported back in rupees (lakh).

| Model | Test MAE (lakh) | Test RMSE (lakh) | R² (log) | Median APE |
|---|---|---|---|---|
| Baseline (median) | 107.6 | 219.8 | 0.00 | 40.0% |
| Linear Regression | 77.0 | 215.0 | 0.615 | 24.5% |
| Ridge Regression | 77.0 | 215.3 | 0.616 | 24.5% |
| Random Forest | 54.3 | 143.0 | 0.767 | 15.8% |
| **Gradient Boosting** ⭐ | **53.4** | **140.1** | **0.776** | **16.3%** |

Gradient Boosting is the selected model.

- **33.8%** of test predictions land within ±10% of the actual asking price
- **66.4%** land within ±25%

### Error by price band

| Band | Listings | Median actual | MAE (lakh) | Median APE |
|---|---|---|---|---|
| under 50 L | 289 | 40 L | 17.0 | 26.2% |
| 50 L – 1 Cr | 783 | 70 L | 18.8 | 16.0% |
| 1 – 2 Cr | 1,738 | 1.50 Cr | 30.0 | 13.7% |
| 2 – 5 Cr | 848 | 2.95 Cr | 76.1 | 18.2% |
| above 5 Cr | 210 | 7.00 Cr | 333.3 | 32.7% |

The model is most reliable in the 50 L – 2 Cr range, where most of the market sits.
It degrades at the top end, where listings are few and prices are driven by factors
not present in the data.

### Top features (Gradient Boosting importance)

`covered_area` (0.585) dominates, followed by `bathrooms` (0.081), `bedrooms` (0.059),
and the locality's `avg_price_sqft` (0.047). Location also enters through `longitude`,
`latitude`, and `locality_rank`.

---

## Repository layout

```
.
├── notebooks/
│   ├── 01-database-audit.ipynb               # tables, row counts, keys, duplicates
│   ├── 02-data-exploration.ipynb             # join + clean → data/processed/
│   ├── 03-eda.ipynb                          # distributions, correlations, missingness
│   └── 04-feature-engineering-and-models.ipynb  # features, CV, tuning, final model
├── reports/
│   ├── figures/                              # EDA + model plots (PNG)
│   ├── model_results.json                    # all metrics, saved by notebook 04
│   ├── make_report.py                        # builds Modelling_Report.pdf
│   └── make_interview_pdf.py                 # builds Interview_Questions.pdf
├── data/                                     # not tracked — see data/README.md
├── models/                                   # not tracked — regenerate with notebook 04
├── Data_Cleaning_Report.pdf
├── Modelling_Report.pdf
├── Interview_Questions.pdf
└── requirements.txt
```

## Method

1. **Audit** — inspect the SQLite tables, confirm `listings.locality_id` → `locality_ratings`.
2. **Join** — `listings LEFT JOIN locality_ratings` on `locality_id`, so listings with
   no locality match are kept rather than dropped.
3. **Clean** — parse prices and areas out of free text, normalise units to a single
   area basis, split floor / total floors, standardise categoricals, drop duplicates
   and implausible rows.
4. **Features** — 23 input columns (14 numeric, 9 categorical) → 67 after one-hot
   encoding, median imputation with missing indicators, and scaling for the linear models.
5. **Target transform** — train on `log1p(price)` because asking prices are strongly
   right-skewed; score by inverting back to rupees so the errors are interpretable.
6. **Validation** — 5-fold cross-validation on train for model selection and
   hyperparameter search; the test split is touched once, at the end.

A side experiment compared three ways of encoding locality (numeric locality stats
only, numeric + one-hot, one-hot only). Numeric locality features carry nearly all
the signal — adding ~1,000 one-hot locality columns moved Random Forest R² by less
than 0.001.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Place `listings_master.db` in `data/raw/`, then run the notebooks in numeric order.
See `data/README.md` for the expected file layout.

## Caveats

- The target is the **asking price**, not the transacted price. Asking prices carry
  seller optimism that the model happily reproduces.
- Scraping was done in price bands, so the raw sample is not a random draw from the
  market; the band structure is visible in the price distribution.
- Locality features are aggregates. Two listings on the same street share them, so
  within-locality variation (floor plan, view, condition, builder) is largely invisible
  to the model — a floor of irreducible error.
- This is a snapshot, not a time series. Re-scrape before trusting it on current prices.
