# Course data

The Weekly Client Report runs on Monday 2 November 2026 for the week ending Sunday 1 November 2026
(business days 26–30 October). The client is PT Astra International Tbk (ASII).

| Path | Kind | What it is |
|---|---|---|
| `account/ASII.csv` | Internal, CSV | Daily account activity at our bank, 3 Aug–30 Oct 2026: `date, inflow, outflow, end_balance, facility_used, facility_limit` (IDR). Has one duplicate date (15 Sep) and one bad value (20 Aug) on purpose |
| `call_reports/ASII/` | Internal, PDF | Three call reports, one per meeting: 15 Jul (FX hedging), 10 Sep (payroll accounts), 21 Oct (EV battery plant, facility limit request). File names are `YYYY-MM-DD_call_report.pdf` |
| `news_site/astra.html` | Public, web page | The client's news page, scraped in Module 2. Serve it in class with `python -m http.server 8000` from this folder, or set `NEWS_URL` in `.env` to a hosted copy |
| `sample/` | Public, saved copies | Real Sectors responses for ASII (`report_`, `daily_`, `quarterly_`), and a saved copy of the news page (`news_ASII.html`). The code uses them when a source cannot be reached |

The account activity, the call reports and the news page are invented for training. They do not
describe Astra's real accounts, meetings or plans. The Sectors data in `sample/` is real.

Created while you work: `data/news/` (Module 2 saves one `.txt` per article), `output/`.
