# Malaysia household income explorer

An interactive, static dashboard for comparing **gross monthly household income** with 2024 DOSM survey medians and Selangor percentile groups. [Open the hosted dashboard](https://syamim5499.github.io/household-income-bi-pages/).

## Data pipeline

```text
OpenDOSM CSVs → Python extract + schema checks → common survey year → area medians + percentile bands → data/income.json → GitHub Pages
```

Run `python3 scripts/build_data.py` (Python 3.10+, standard library only). The script downloads these official datasets:

- `hh_income.csv`: national median and mean
- `hh_income_state.csv`: Selangor median and mean
- `hh_income_district.csv`: Kuala Langat median and mean
- `hies_state_percentile.csv`: Selangor percentile minimum, median and maximum values

It requires a common survey year across all four datasets, validates the expected columns and 100 percentile rows, then writes `data/income.json`. A monthly GitHub Action reruns the script and commits changes if DOSM publishes updates. The page loads the generated JSON; it does **not** fetch DOSM from each visitor's browser. Personal income is only handled client-side and is never written to GitHub, a URL or the pipeline output.

National B40/M40/T20 thresholds (RM5,860 and RM12,680) are rounded values from the **2024 Household Income Survey report**. They are not derived from the Selangor percentile file; review them when a newer survey arrives. The pipeline uses latest common-year medians but retains these thresholds, so the page should be reviewed when the survey year changes.

## How the analysis works

- `difference = entered_income - median`; percentage difference = `difference / median × 100`.
- Selangor percentile group uses the published minimum/maximum band containing the income. Since survey bands may touch or have small rounding gaps, the nearest group median is a fallback estimate. P70 means the 70th 1% group, **not** an exact 70.0th percentile.
- The district dataset provides median and mean but no district percentile breakdown. The page does not claim a Kuala Langat percentile.
- Survey values are nominal gross household income for the stated survey year; this is not real-time 2026 data.

Sources: [national](https://open.dosm.gov.my/data-catalogue/hh_income), [state](https://open.dosm.gov.my/data-catalogue/hh_income_state), [district](https://open.dosm.gov.my/data-catalogue/hh_income_district), [state percentile](https://open.dosm.gov.my/data-catalogue/hies_state_percentile), [DOSM 2024 report](https://www.dosm.gov.my/portal-main/release-content/household-income-survey-report--malaysia--states-2024). DOSM data is made available under CC BY 4.0.
