# outputs/reports/

This folder contains the written reports produced by the Reporting role (Ivan Kubskyi).

## Files

| File | Description |
|------|-------------|
| report.md | Full analysis report covering all findings from the data engineering and analysis pipeline |
| executive_summary.md | One-page summary of key findings for quick reference |

## How to regenerate the report

The full report is generated automatically from the processed data by running:

```
python src/reporting.py
```

This reads the CSV files from `data/processed/` and overwrites `outputs/reports/report.md` with up-to-date figures.
