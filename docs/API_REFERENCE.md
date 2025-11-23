# API Reference

For full schemas and Swagger examples see `API_DOCUMENTATION.md`. This companion file highlights the structure, versioning, and authentication flow.

## Versioning
- **Base URL**: `http://localhost:5001`
- **Versioned endpoints**: `/api/v1/...` (current)
- **Legacy shortcuts**: `/api/...` retained for the dashboard; they proxy to v1 handlers but omit auth.

## Authentication
| Endpoint | Method | Auth | Rate Limit | Notes |
| --- | --- | --- | --- | --- |
| `/api/v1/auth/register` | POST | none | 5/hour | Creates user + API key |
| `/api/v1/auth/login` | POST | none | 10/min | Returns access/refresh tokens |
| `/api/v1/auth/refresh` | POST | Bearer (refresh) | default | Issue new access token |
| `/api/v1/auth/me` | GET | Bearer (access) | default | Inspect profile + API key |

API keys (`X-API-Key`) secure analysis/risk/chart routes; JWT protects backtesting/admin surfaces.

## Core Endpoints
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| `/api/v1/analyze` | POST | API Key | Fetches latest OHLCV/indicator summary for a ticker & period |
| `/api/v1/chart/<ticker>` | GET | API Key | Returns Plotly JSON for candlestick/line/indicator views |
| `/api/v1/backtest` | POST | JWT | Runs moving-average strategy backtest and returns metrics + equity curve |
| `/api/v1/risk/<ticker>` | GET | API Key | Computes VaR/CVaR/drawdowns/volatility |
| `/api/v1/admin/users` | GET | JWT + admin role | Lists registered users |
| `/api/v1/admin/users/<id>/regenerate-key` | POST | JWT + admin | Issues new API key |

## Rate Limiting
- Global default: `200/day` and `50/hour` per IP
- Custom decorators on each auth-critical endpoint enforce tighter caps (e.g., analysis `30/min`)

## Documentation & Tooling
- Swagger UI: `http://localhost:5001/apidocs`
- OpenAPI spec: `/apispec_1.json`
- Example client flows: `demo_api_v2.py`

Use this guide to quickly understand which authentication method to apply and where to find sample payloads.
