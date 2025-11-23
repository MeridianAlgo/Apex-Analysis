# Apex Analysis User Guide

The dashboard now includes personal productivity tools so you can keep tabs on the tickers you care about, get alerted when price levels hit, save preferences, and download results for post-processing. Everything in this guide runs entirely in your browser—no credentials or servers are required.

## Quick Start
1. Launch the app: `python web_app.py` and visit `http://localhost:5001`.
2. Run a quick analysis by entering a ticker/period on the Dashboard card.
3. Review the summary cards and switch chart types (candlestick, line, indicators).
4. Save interesting symbols via **Save ticker to watchlist** or the Watchlist form.
5. Configure alerts/preferences/export defaults to personalize the experience.

## 1. Watchlists

1. Open the **Watchlists** card on the main dashboard.
2. Enter a ticker (1–5 letters) and an optional note, then click **Add to watchlist**.
3. Saved tickers appear immediately below the form with quick **Analyze** and **Remove** buttons.
4. Click **Analyze** to rerun the analysis form with that ticker prefilled.
5. The **Save ticker to watchlist** shortcut above the summary cards adds the most recent symbol in one click.

> **Persistence:** Watchlists are stored in `localStorage` under the key `apex-watchlist`. Clearing browser data resets the list.

## 2. Price Alerts

1. Use the **Price Alerts** card to define alerts per ticker.
2. Choose the direction (≥ target or ≤ target) and a price threshold, then click **Create alert**.
3. Alerts are evaluated automatically whenever you run a new analysis for that ticker.
4. Triggered alerts surface in the yellow notification panel and record a "last triggered" timestamp.
5. You can **Pause/Resume** or **Delete** any alert from the list.

Alerts also live in `localStorage` (`apex-alerts`). Toggle the "Enable in-app alerts" preference to mute alert notifications without deleting them.

## 3. User Preferences

Use the **User Preferences** card to control defaults:

- **Default ticker & period** populate the quick analysis form on load.
- **Preferred theme** stays in sync with the existing dark/light toggle.
- **Default export format** highlights the preferred summary download button so you can spot it instantly.
- **In-app alerts** lets you silence notifications while keeping alert definitions intact.

Click **Save preferences** to persist them (`apex-preferences`). The dashboard immediately applies the new values and confirms the update.

## 4. Data Export

The **Data Export** card provides one-click downloads:

| Button | Contents | Notes |
| --- | --- | --- |
| Summary (JSON/CSV) | Latest analysis snapshot (ticker, period, generated time, pricing stats, indicators) | Enabled after any successful analysis run |
| Watchlist (JSON) | Entire watchlist array with notes and timestamps | Always available |
| Alerts (JSON) | Alert definitions with last-triggered metadata | Always available |

Exports are generated on the client using the `ApexUtils.downloadJSON/CSV` helpers, so no data leaves your machine.

## 5. Tips & Troubleshooting

- **Resetting data:** Clear browser storage (or use your dev tools) to remove watchlists, alerts, and preferences.
- **Cross-browser usage:** Local storage does not sync across browsers or devices; export/import JSON files to move data.
- **Alert sensitivity:** Alerts fire when the most recent closing price meets the condition. Re-run the analysis periodically for intra-day monitoring.
- **Accessibility:** All new controls use standard form elements and keyboard-accessible buttons.

Need more help? Open an issue in the repo with screenshots of any problems, and mention which browser/OS you are using.
