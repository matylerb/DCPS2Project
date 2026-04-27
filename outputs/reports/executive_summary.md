# Dublin Bus Cancellation Analysis — Executive Summary

**Module:** DATA 2005 Data Centric Programming  
**Team:** Cillian Chatham, Tyler Brady, Ilya Mikava, Ivan Kubskyi  
**Data source:** GTFS Static Data, Transport for Ireland / NTA  
**Data period:** 17 March 2026 – 28 August 2026

---

## What we investigated

This project analysed GTFS (General Transit Feed Specification) data from Ireland's National Transport Authority to identify patterns in Dublin Bus service cancellations — routes that are scheduled to run but never actually show up ("ghost buses").

---

## Key numbers

| Metric | Value |
|--------|-------|
| Total cancelled trips | 25,632 |
| Routes affected | 160 |
| Most cancelled route | S4 — Liffey Valley to UCD (856 trips) |
| Worst day | Tuesday (10,456 cancelled trips) |
| Weekend cancellations | 0 |

---

## Key findings

**1. All cancellations are weekday-only.**  
Not a single cancellation was recorded on a Saturday or Sunday. This rules out random or weather-driven causes and points directly to weekday operational pressures.

**2. Strike days drive the majority of cancellations.**  
Monday and Tuesday together account for over 72% of all cancelled trips. These dates correspond to known industrial action days. Wednesday through Friday each show a much lower and consistent level of around 2,359 cancelled trips.

**3. Route S4 is the worst affected single route.**  
The Liffey Valley–UCD corridor had 856 cancelled trips across 45 affected dates — the highest of any route in the dataset.

**4. Newer orbital route families are disproportionately affected.**  
Routes in the S, N, W, and L series (suburban orbital and orbital routes) appear heavily in the top cancellation rankings, suggesting these services may have less resilient scheduling or staffing compared to legacy core routes.

---

## Conclusion

Dublin Bus cancellations are not random — they follow clear, predictable patterns tied to industrial action and specific route families. For commuters, the highest risk is on Monday and Tuesday, particularly on suburban orbital routes. For the NTA, addressing staffing and contingency planning on strike days would have the greatest impact on reducing cancellations.

---

*Full report: `outputs/reports/report.md`*  
*Visualisations: `outputs/figures/`*
