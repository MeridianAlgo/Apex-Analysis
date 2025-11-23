# Apex Analysis REST API Documentation

Version: 1.0.0
Base URL: `http://localhost:5001`

## Overview

The Apex Analysis REST API provides programmatic access to stock market analysis, backtesting, risk management, and machine learning predictions. The API uses JWT and API key authentication, implements rate limiting, and follows versioning best practices.

## Features

- **JWT Authentication**: Secure token-based authentication
- **API Key Authentication**: Simple key-based access for automated systems
- **Rate Limiting**: Prevents abuse with configurable limits
- **API Versioning**: Clean version management (v1, v2, etc.)
- **Swagger Documentation**: Interactive API docs at `/apidocs`
- **CORS Support**: Cross-origin requests enabled
- **Role-Based Access**: Admin and user roles with different permissions

## Authentication

### Methods

The API supports two authentication methods:

#### 1. JWT Authentication (Recommended for web apps)

```bash
# Login to get tokens
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_id": "abc123",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin", "user"]
  }
}

# Use access token in subsequent requests
curl -X GET http://localhost:5001/api/v1/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### 2. API Key Authentication (Recommended for scripts/bots)

```bash
# Use API key in header
curl -X POST http://localhost:5001/api/v1/analyze \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "period": "1y"}'
```

### Default Credentials

For development and testing:

- **Admin User**
  - Username: `admin`
  - Password: `admin123`
  - Roles: `admin`, `user`

- **Demo User**
  - Username: `demo`
  - Password: `demo123`
  - Roles: `user`

## Rate Limits

Default rate limits per endpoint:

- **Global**: 200 requests per day, 50 per hour
- **Registration**: 5 per hour
- **Login**: 10 per minute
- **Analysis**: 30 per minute
- **Charts**: 20 per minute
- **Backtesting**: 10 per hour
- **Risk Metrics**: 30 per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1234567890
```

## API Versioning

The API uses URL versioning:

- **Current Version**: `v1` (`/api/v1/...`)
- **Future Versions**: `v2`, `v3` (when available)

Old versions remain available for backward compatibility.

### Legacy Dashboard Endpoints

The web dashboard still calls the original non-versioned routes (`/api/analyze`, `/api/chart/<ticker>`, `/api/backtest`, `/api/risk/<ticker>`).  
These endpoints now reuse the secured v1 handlers but do **not** enforce authentication so the UI can continue working while users migrate.  
They are rate limited identically to the v1 routes and will be removed in a future release—new integrations should target `/api/v1/...`.

---

## Endpoints

### Authentication

#### POST /api/v1/auth/register

Register a new user account.

**Rate Limit**: 5 per hour

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response** (201 Created):
```json
{
  "message": "User created successfully",
  "user": {
    "user_id": "abc123",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "api_key": "your-generated-api-key"
}
```

**Errors**:
- `400`: Missing required fields or username already exists
- `500`: Server error

---

#### POST /api/v1/auth/login

Login to get JWT tokens.

**Rate Limit**: 10 per minute

**Request Body**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_id": "abc123",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin", "user"]
  }
}
```

**Errors**:
- `400`: Missing username or password
- `401`: Invalid credentials

---

#### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Authentication**: Bearer (refresh token)

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### GET /api/v1/auth/me

Get current user information.

**Authentication**: Bearer (access token)

**Response** (200 OK):
```json
{
  "user_id": "abc123",
  "username": "admin",
  "email": "admin@example.com",
  "roles": ["admin", "user"],
  "api_key": "your-api-key",
  "created_at": "2025-01-01T00:00:00"
}
```

---

### Stock Analysis

#### POST /api/v1/analyze

Analyze a stock ticker with technical indicators.

**Authentication**: API Key (X-API-Key header)
**Rate Limit**: 30 per minute

**Request Body**:
```json
{
  "ticker": "AAPL",
  "period": "1y"
}
```

**Parameters**:
- `ticker` (required): Stock ticker symbol (e.g., "AAPL", "TSLA")
- `period` (optional): Time period - "1mo", "3mo", "6mo", "1y", "2y", "5y" (default: "1y")

**Response** (200 OK):
```json
{
  "ticker": "AAPL",
  "current_price": 271.49,
  "price_change": 5.24,
  "price_change_pct": 1.97,
  "volume": 58784100,
  "high_52w": 277.05,
  "low_52w": 255.18,
  "rsi": 55.14,
  "macd": 1.87,
  "macd_signal": 2.46
}
```

**Errors**:
- `401`: Missing or invalid API key
- `404`: No data available for ticker
- `500`: Server error

---

#### GET /api/v1/chart/{ticker}

Get chart data in Plotly format.

**Authentication**: API Key
**Rate Limit**: 20 per minute

**Parameters**:
- `ticker` (path, required): Stock ticker symbol
- `period` (query, optional): Time period (default: "1y")
- `type` (query, optional): Chart type - "candlestick", "line", "volume", "indicators" (default: "candlestick")

**Example**:
```bash
curl -X GET "http://localhost:5001/api/v1/chart/AAPL?period=1y&type=candlestick" \
  -H "X-API-Key: your-api-key"
```

**Response** (200 OK):
```json
{
  "data": [...],
  "layout": {...}
}
```

---

### Backtesting

#### POST /api/v1/backtest

Run a backtest with moving average crossover strategy.

**Authentication**: Bearer (access token)
**Rate Limit**: 10 per hour

**Request Body**:
```json
{
  "ticker": "AAPL",
  "period": "1y",
  "initial_capital": 100000
}
```

**Response** (200 OK):
```json
{
  "metrics": {
    "total_return": 0.4466,
    "annualized_return": 0.4466,
    "sharpe_ratio": 1.14,
    "sortino_ratio": 1.21,
    "max_drawdown": -0.1523,
    "total_trades": 12,
    "win_rate": 0.583
  },
  "equity_curve": {
    "dates": ["2024-01-01", "2024-01-02", ...],
    "values": [100000, 100500, ...]
  }
}
```

---

### Risk Management

#### GET /api/v1/risk/{ticker}

Calculate risk metrics for a ticker.

**Authentication**: API Key
**Rate Limit**: 30 per minute

**Parameters**:
- `ticker` (path, required): Stock ticker symbol
- `period` (query, optional): Time period (default: "1y")

**Example**:
```bash
curl -X GET "http://localhost:5001/api/v1/risk/AAPL?period=1y" \
  -H "X-API-Key: your-api-key"
```

**Response** (200 OK):
```json
{
  "var_95": -0.0234,
  "var_99": -0.0345,
  "cvar_95": -0.0289,
  "max_drawdown": -0.1523,
  "current_drawdown": -0.0234,
  "sharpe_ratio": 1.14,
  "sortino_ratio": 1.21,
  "volatility": 0.2345
}
```

**Metrics**:
- `var_95`: Value at Risk at 95% confidence
- `var_99`: Value at Risk at 99% confidence
- `cvar_95`: Conditional VaR (Expected Shortfall)
- `max_drawdown`: Maximum drawdown from peak
- `current_drawdown`: Current drawdown from recent peak
- `sharpe_ratio`: Risk-adjusted return (Sharpe ratio)
- `sortino_ratio`: Downside risk-adjusted return
- `volatility`: Annualized volatility

---

### Admin Endpoints

Admin endpoints require JWT authentication with the `admin` role.

#### GET /api/v1/admin/users

List all users (admin only).

**Authentication**: Bearer (access token) with admin role

**Response** (200 OK):
```json
[
  {
    "user_id": "abc123",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin", "user"],
    "is_active": true,
    "created_at": "2025-01-01T00:00:00"
  },
  ...
]
```

**Errors**:
- `401`: Not authenticated
- `403`: Insufficient permissions (requires admin role)

---

#### POST /api/v1/admin/users/{user_id}/regenerate-key

Regenerate API key for a user (admin only).

**Authentication**: Bearer (access token) with admin role

**Response** (200 OK):
```json
{
  "api_key": "new-generated-api-key"
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Error message description"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5001"

# 1. Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
tokens = response.json()
access_token = tokens['access_token']

# 2. Get user info
response = requests.get(
    f"{BASE_URL}/api/v1/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
user = response.json()
api_key = user['api_key']

# 3. Analyze stock
response = requests.post(
    f"{BASE_URL}/api/v1/analyze",
    headers={"X-API-Key": api_key},
    json={"ticker": "AAPL", "period": "1y"}
)
analysis = response.json()
print(f"Current price: ${analysis['current_price']:.2f}")
print(f"RSI: {analysis['rsi']:.2f}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5001';

// 1. Login
const loginResponse = await axios.post(`${BASE_URL}/api/v1/auth/login`, {
  username: 'admin',
  password: 'admin123'
});
const { access_token, user } = loginResponse.data;

// 2. Analyze stock
const analysisResponse = await axios.post(
  `${BASE_URL}/api/v1/analyze`,
  { ticker: 'AAPL', period: '1y' },
  { headers: { 'X-API-Key': user.api_key } }
);
console.log(analysisResponse.data);
```

### cURL

```bash
# Login
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Analyze stock (with API key)
curl -X POST http://localhost:5001/api/v1/analyze \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "period": "1y"}'

# Get risk metrics
curl -X GET "http://localhost:5001/api/v1/risk/AAPL?period=1y" \
  -H "X-API-Key: your-api-key"
```

---

## Interactive Documentation

Visit the Swagger UI for interactive API documentation:

**URL**: http://localhost:5001/apidocs

The Swagger UI allows you to:
- Browse all endpoints
- Try out requests directly in the browser
- View request/response schemas
- Test authentication

---

## Best Practices

1. **Use API Keys for automation**: API keys are simpler for scripts and bots
2. **Use JWT for web applications**: JWTs are more secure for browser-based apps
3. **Refresh tokens before expiry**: Access tokens expire after 1 hour
4. **Handle rate limits gracefully**: Implement exponential backoff
5. **Store credentials securely**: Never hardcode credentials in source code
6. **Use HTTPS in production**: Always use encrypted connections
7. **Monitor rate limit headers**: Check remaining requests before hitting limits

---

## Changelog

### Version 1.0.0 (2025-01-23)
- Initial release
- JWT authentication
- API key authentication
- Rate limiting
- Stock analysis endpoints
- Backtesting endpoints
- Risk management endpoints
- Admin endpoints
- Swagger documentation

---

## Support

For issues, questions, or feature requests, please contact:
- Email: support@apexanalysis.com
- GitHub: https://github.com/yourusername/apex-analysis
