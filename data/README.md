# Data

The data files are **not tracked in git** — the SQLite database is ~253 MB and the
extracted/merged CSVs are 250-260 MB each, well past GitHub's 100 MB per-file limit.

## Expected layout

```
data/
├── raw/
│   └── listings_master.db        # scraped MagicBricks data (SQLite)
├── extracted/
│   ├── listings.csv              # listings table, dumped from the DB
│   ├── locality.csv              # locality_ratings table
│   └── merged_listings.csv       # listings LEFT JOIN locality_ratings on locality_id
└── processed/
    ├── listings_clean.csv        # after cleaning (notebook 02)
    ├── train.csv                 # 15,472 rows
    └── test.csv                  # 3,868 rows
```

## How to rebuild it

1. Put `listings_master.db` in `data/raw/`.
2. Run the notebooks in order:
   - `01-database-audit.ipynb` — inspect tables, row counts, keys
   - `02-data-exploration.ipynb` — join + clean, writes `data/extracted/` and `data/processed/`
   - `03-eda.ipynb` — figures in `reports/figures/`
   - `04-feature-engineering-and-models.ipynb` — trains models, writes `models/` and `reports/model_results.json`

The database itself is not redistributed here. It was scraped from MagicBricks in
price bands (1-50 L, 50-80 L, 80 L-1 Cr, and upward), which is why price is not
uniformly distributed across the raw sample.
