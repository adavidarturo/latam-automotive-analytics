# Data Sources

This document records exactly what was verified for each data source used in this project,
including the sources that were investigated and deliberately excluded from the automated
pipeline. The goal is traceability: every number in the final report should be attributable to
a real, checkable source.

## Automated pipeline sources

### Comtrade "World" aggregate counted as a country of origin (fixed)

Even after resolving country-of-origin codes, the preview endpoint returns an aggregate
`"World"` row (`Origin_Code == '0'`) mixed in with the real per-country breakdown — this
happens regardless of whether `partnerCode=0` is passed. Left uncorrected, this row gets
treated as an extra "country," roughly doubling category totals and distorting any
China-vs-rest comparison (confirmed on Brazil 2023 EV imports, where the "World" row was
worth almost exactly the sum of the real countries of origin for that same row).

Fixed in notebook 02 (v4): the "World" rows are split into their own file,
`comtrade_world_totals_latam.csv`, and used as a cross-check to flag country/category/year
combinations that look truncated by the 500-row free-tier cap. `comtrade_imports_latam.csv`
now contains only real countries of origin.

| Source | What it provides | Countries covered | Access |
|---|---|---|---|
| IEA / Our World in Data | EV sales (units) and EV share of new car sales (%) | Brazil, Mexico, Chile, Colombia | Free, no key, stable CSV endpoint |
| UN Comtrade (preview) | Imports by HS code and country of origin | All 8 target countries | Free, no key, 500 rows/query cap |
| BCRP (Peru) | Monthly imports through the Callao seaport | Peru | Free, no key. Data currently ends December 2023 |
| ComexStat (Brazil) | Imports by NCM code and country of origin | Brazil | Free, no key |

## Countries without a machine-readable source

Peru, Argentina, Ecuador, and Bolivia are **not** individually reported in the IEA/OWID EV
adoption series. Separately, Argentina, Ecuador, and Bolivia's national auto trade
associations do not publish an API or downloadable dataset. This was investigated directly —
not assumed — before deciding to exclude them from the automated pipeline.

### Peru — Asociación Automotriz del Perú (AAP)

- Source type: press bulletins, citing SUNARP (vehicle registry) data.
- 2024: electrified vehicle (hybrid + electric) sales grew 51% year-over-year to 5,537 units
  (January–October), reaching roughly 4% of the total market.
- AAP's 2025 projection: approximately 10,000 electrified units, raising penetration to
  roughly 7% of the total market.
- Electrified vehicles in Peru currently skew toward Japanese, Korean, and US brands rather
  than Chinese ones — a notable contrast with the pattern seen in other countries in this
  project, suggesting the Chinese-brand wave may be arriving later or more slowly in Peru.
- Consulted: September 2026, via gestion.pe and forbes.pe (multiple articles, 2024–2026),
  citing AAP/SUNARP.

### Ecuador — Asociación de Empresas Automotrices del Ecuador (AEADE)

The richest of the three qualitative sources — includes a brand-level breakdown, which is
directly useful for the "rise of Chinese brands" question.

Annual BEV sales (January–May, year-over-year comparable window):

| Year | BEV units (Jan–May) |
|---|---|
| 2021 | 108 |
| 2022 | 128 |
| 2023 | 277 |
| 2024 | 492 (one source cites 1,158 for a different period — reconcile exact window before final use) |
| 2025 | 1,192 |
| 2026 | 4,019 |

Brand breakdown, January–May 2026: BYD leads with 1,565 units (38.9% of the EV market,
+152.4% year-over-year), followed by Chevrolet (644 units, +675.9%) and Dongfeng (471 units).
For the same window in 2025, BYD already led with 623 units out of 1,192 total EV sales.

- Source type: press bulletins and news coverage, citing AEADE/SRI data.
- Consulted: September 2026, via expreso.ec, eluniverso.com, elmercurio.com.ec.

### Argentina — Asociación de Fábricas de Automotores (ADEFA)

- Source type: PDF annual reports and press bulletins.
- No consistent EV-specific breakdown was found in the sources reviewed. If this country is
  revisited, check ADEFA's monthly bulletins directly (adefa.org.ar) or ACARA for
  motorization-type detail.

### Bolivia

- No trade association with public, citable bulletins was identified.
- Comtrade (notebook 02) does show small but growing EV import volumes for Bolivia,
  consistent with an early-stage market.

## How to use this in the final report

These figures belong in the report as **cited qualitative context** (e.g., a callout box or
footnote), not as rows in the automated data tables — mixing API-verifiable numbers with
manually transcribed press figures inside the same table would blur the trust level of the
data. If this project later justifies the effort of tracking these countries over time,
this document is the starting point — but re-verify each figure against the original
bulletin before treating it as final for a formal report.
