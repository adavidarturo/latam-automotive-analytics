<<<<<<< HEAD
# latam-automotive-analytics
=======
# LatAm Automotive Analytics

Analysis of the shift from combustion to electric vehicles across Latin America's largest
automotive markets (Brazil, Mexico, Chile, Colombia, Peru, Argentina, Ecuador, Bolivia),
focused on three questions:

- **Adoption trend** — which countries are moving fastest toward EVs, and how consistently.
- **Country of origin** — how much ground Chinese brands (BYD, Changan, JAC, Foton, and
  others) are gaining against established Japanese, Korean, US, and European players.
- **Aftermarket opportunity** — whether spare parts, battery servicing, and specialized
  technical capacity are keeping pace with EV fleet growth, or lagging behind it.

This is a personal data analytics portfolio project: real public sources, a reproducible
pipeline, and an explicit account of each source's limitations — including where and why
certain countries or years are not covered.

## Project structure

```
latam-automotive-analytics/
├── data/
│   ├── raw/                 Unmodified downloads (not tracked in git)
│   └── processed/           Cleaned, analysis-ready datasets
├── notebooks/
│   ├── 01_ingestion_iea.ipynb              EV sales and market share (IEA / Our World in Data)
│   ├── 02_ingestion_comtrade.ipynb         Imports by HS code and country of origin (UN Comtrade)
│   ├── 03_ingestion_central_banks.ipynb    Peru (BCRP) and Brazil (ComexStat) import series
│   ├── 04_eda.ipynb                        Descriptive exploration of all three questions above
│   ├── 05_statistical_analysis.ipynb       Outlier detection, correlations, hypothesis testing
│   ├── 06_forecasting.ipynb                Trend projections (Prophet)
│   └── 07_executive_summary.ipynb          Non-technical summary of findings, limitations,
│                                             and business opportunities for stakeholders
├── src/
│   └── utils.py              Shared download, retry, deduplication, and logging functions
├── docs/
│   └── data_sources.md       What was verified for each source, and why some countries
│                              are documented as qualitative context instead of pipeline data
├── requirements.txt
└── README.md
```

## How to run

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/01_ingestion_iea.ipynb
```

Run the notebooks **in order** (01 through 07) — each one reads the processed CSVs the
previous notebook saved to `data/processed/`. Notebook 07 is a text-only summary and does not
need to be re-run; it reads no data itself.

**Note on included data:** `data/processed/` ships with the IEA and ComexStat outputs already
generated. The Comtrade output is **not** included — a real bug was found in the version you
previously ran (the "World" aggregate row was being counted as an extra country of origin,
roughly doubling totals — see `docs/data_sources.md`). Re-run the corrected notebook 02 to
regenerate `comtrade_imports_latam.csv` before continuing to notebooks 04 and 05, since both
consume that file directly.

## Data sources at a glance

| Source | Provides | Coverage | Access |
|---|---|---|---|
| IEA / Our World in Data | EV sales and market share by year | Brazil, Mexico, Chile, Colombia | Free, no key |
| UN Comtrade | Imports by HS code and country of origin | All 8 target countries | Free, no key |
| BCRP (Peru) | Monthly imports through Callao | Peru | Free, no key |
| ComexStat (Brazil) | Imports by NCM code and origin | Brazil | Free, no key |

Peru, Argentina, Ecuador, and Bolivia are not individually reported by the IEA source, and
their national trade associations (AAP, ADEFA, AEADE) do not publish machine-readable data.
This was verified directly rather than assumed. Sourced figures for these countries — Ecuador
in particular has a strong brand-level breakdown showing BYD's rise — are documented in
`docs/data_sources.md` and used as cited qualitative context in the final report, not as rows
in the automated dataset. See that file for the full reasoning.

## Design notes

**Why CSV files instead of a database.** Data is pulled via HTTP and stored as CSV under
`data/raw/` and `data/processed/`, using paths anchored to the repo root (see `src/utils.py`),
not to any local machine. This means the same code runs unchanged on a laptop, in Google
Colab, or in a CI pipeline. A traditional database was not necessary at this data volume; if
the project grows, a natural next step would be a small SQLite file (versioned) or a free-tier
managed Postgres instance (e.g. Supabase, Neon) for SQL-based querying.

**Why some data quality issues are documented instead of hidden.** Two real bugs were found
and fixed during development: UN Comtrade's country-of-origin field was returning empty
values, and one Peruvian customs series pointed at a minor secondary port instead of the
country's main import gateway. Both are described in detail in the relevant notebooks and in
`docs/data_sources.md`, alongside the fix. Leaving that trail visible is intentional — it is
part of what makes the pipeline auditable.

## Suggested next steps

- Confirm Brazil's exact NCM code for BEVs and hybrids in ComexStat (can differ from the
  standard HS code in the last digits).
- Bring in the OWID lithium-ion battery price dataset to extend the correlation analysis in
  notebook 05.
- Re-run the central bank ingestion once BCRP/ComexStat publish more recent months.
- Export final tables in wide format (country × year) for a clean Power BI import, with one
  fact table per theme (adoption, imports by origin, forecast) rather than a single merged
  table.
>>>>>>> 63bd3b1 (Vehicle sales performance project in LATAM)
