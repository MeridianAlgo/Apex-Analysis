# Frontend Architecture

The dashboard is a lightweight Flask + Tailwind SPA hybrid focused on data visualization and user productivity.

## Layout
- **Templates**: `templates/base.html` defines navigation, theme toggling, and shared assets. Feature pages extend it with page-specific blocks.
- **Components**: `templates/index.html` now hosts reusable cards (analysis form, summary, watchlist, alerts, preferences, export hub).
- **Styling**: Tailwind via CDN plus a small `static/css/style.css` file for overrides.

## State Management
- `static/js/app.js` contains shared utilities (formatting, downloads, API helper).
- Page-specific scripts (embedded in templates) maintain local state objects, combining:
  - `watchlist`, `alerts`, and `preferences` stored in `localStorage`.
  - Derived UI state (last summary, current ticker) to drive buttons/exports.

## API Integration
- Fetch requests hit legacy `/api/*` endpoints for dashboard compatibility; the same logic is shared with secured `/api/v1/*` routes.
- Loading states, error handling, and Plotly chart rendering use standard JS without frameworks to keep bundle size minimal.

## Theming
- Theme preference lives on the `<html>` `data-theme` attribute.
- Preferences UI syncs the theme with `localStorage` and ensures components respect light/dark palettes.

## Extensibility
- Add new cards by following the existing pattern (card container + script functions managing state and persistence).
- Shared helpers in `ApexUtils` simplify currency formatting, download exports, and clipboard interactions.
- When introducing heavier interactivity, consider migrating to a micro front-end (React/Vue) fed by the same REST API.

This architecture keeps the UI simple enough for fast iteration while supporting persistent personalization features.
