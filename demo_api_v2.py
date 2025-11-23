"""
Demo: Apex Analysis API v2 with Authentication

Demonstrates:
- User registration
- JWT authentication
- API key authentication
- Rate limiting
- Protected endpoints
- Admin operations
"""
import requests
import time
import json

BASE_URL = "http://localhost:5001"


def print_section(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_response(response, show_body=True):
    """Print response details"""
    status_icon = "✓" if response.status_code < 400 else "✗"
    print(f"{status_icon} Status: {response.status_code}")

    if show_body:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text[:200]}")


def demo_registration():
    """Demo: User registration"""
    print_section("1. User Registration")

    # Register a new user
    print("\nRegistering new user...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    print_response(response)

    if response.status_code == 201:
        data = response.json()
        return data.get('api_key')

    return None


def demo_login():
    """Demo: JWT authentication"""
    print_section("2. JWT Authentication")

    # Login with admin user
    print("\nLogging in as admin...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    print_response(response)

    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        print(f"\n✓ Access token obtained: {access_token[:50]}...")
        return access_token

    return None


def demo_jwt_protected_endpoint(access_token):
    """Demo: JWT-protected endpoint"""
    print_section("3. JWT-Protected Endpoint")

    # Get current user info
    print("\nGetting current user info...")
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print_response(response)

    if response.status_code == 200:
        data = response.json()
        return data.get('api_key')

    return None


def demo_api_key_authentication(api_key):
    """Demo: API key authentication"""
    print_section("4. API Key Authentication")

    # Analyze stock with API key
    print("\nAnalyzing AAPL with API key...")
    response = requests.post(
        f"{BASE_URL}/api/v1/analyze",
        headers={"X-API-Key": api_key},
        json={
            "ticker": "AAPL",
            "period": "1mo"
        }
    )
    print_response(response)


def demo_rate_limiting(api_key):
    """Demo: Rate limiting"""
    print_section("5. Rate Limiting")

    print("\nMaking rapid requests to test rate limiting...")
    print("(Rate limit: 30 per minute for analyze endpoint)")

    success_count = 0
    rate_limited_count = 0

    # Make 35 requests rapidly
    for i in range(35):
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze",
            headers={"X-API-Key": api_key},
            json={"ticker": "AAPL", "period": "1mo"}
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Request {i+1}: ✓ Success")
        elif response.status_code == 429:
            rate_limited_count += 1
            print(f"  Request {i+1}: ✗ Rate limited")
        else:
            print(f"  Request {i+1}: ✗ Error ({response.status_code})")

        # Small delay to avoid overwhelming the server
        time.sleep(0.1)

    print(f"\nResults:")
    print(f"  Successful: {success_count}")
    print(f"  Rate limited: {rate_limited_count}")


def demo_chart_endpoint(api_key):
    """Demo: Chart data endpoint"""
    print_section("6. Chart Data Endpoint")

    print("\nFetching candlestick chart for TSLA...")
    response = requests.get(
        f"{BASE_URL}/api/v1/chart/TSLA",
        headers={"X-API-Key": api_key},
        params={"period": "1mo", "type": "candlestick"}
    )
    print_response(response, show_body=False)

    if response.status_code == 200:
        data = response.json()
        print(f"  Chart data keys: {list(data.keys())}")
        print(f"  Number of data points: {len(data.get('data', []))}")


def demo_backtest_endpoint(access_token):
    """Demo: Backtesting endpoint (JWT required)"""
    print_section("7. Backtesting Endpoint (JWT Required)")

    print("\nRunning backtest for MSFT...")
    response = requests.post(
        f"{BASE_URL}/api/v1/backtest",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "ticker": "MSFT",
            "period": "1y",
            "initial_capital": 100000
        }
    )
    print_response(response, show_body=False)

    if response.status_code == 200:
        data = response.json()
        metrics = data.get('metrics', {})
        print(f"\nBacktest Results:")
        print(f"  Total Return: {metrics.get('total_return', 0)*100:.2f}%")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 0)*100:.2f}%")
        print(f"  Win Rate: {metrics.get('win_rate', 0)*100:.2f}%")


def demo_risk_endpoint(api_key):
    """Demo: Risk metrics endpoint"""
    print_section("8. Risk Metrics Endpoint")

    print("\nCalculating risk metrics for GOOGL...")
    response = requests.get(
        f"{BASE_URL}/api/v1/risk/GOOGL",
        headers={"X-API-Key": api_key},
        params={"period": "1y"}
    )
    print_response(response, show_body=False)

    if response.status_code == 200:
        data = response.json()
        print(f"\nRisk Metrics:")
        print(f"  VaR (95%): {data.get('var_95', 0)*100:.2f}%")
        print(f"  VaR (99%): {data.get('var_99', 0)*100:.2f}%")
        print(f"  Sharpe Ratio: {data.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {data.get('max_drawdown', 0)*100:.2f}%")


def demo_admin_endpoints(access_token):
    """Demo: Admin-only endpoints"""
    print_section("9. Admin Endpoints (Admin Role Required)")

    print("\nListing all users (admin only)...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print_response(response, show_body=False)

    if response.status_code == 200:
        users = response.json()
        print(f"\nTotal users: {len(users)}")
        for user in users[:3]:  # Show first 3 users
            print(f"  - {user.get('username')} ({user.get('email')}) - Roles: {user.get('roles')}")


def demo_unauthorized_access():
    """Demo: Unauthorized access attempts"""
    print_section("10. Unauthorized Access")

    print("\n1. Accessing protected endpoint without auth...")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me")
    print_response(response)

    print("\n2. Using invalid API key...")
    response = requests.post(
        f"{BASE_URL}/api/v1/analyze",
        headers={"X-API-Key": "invalid-key-12345"},
        json={"ticker": "AAPL", "period": "1mo"}
    )
    print_response(response)

    print("\n3. Accessing admin endpoint as regular user...")
    # Login as demo user (non-admin)
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "demo", "password": "demo123"}
    )
    if login_response.status_code == 200:
        demo_token = login_response.json().get('access_token')
        response = requests.get(
            f"{BASE_URL}/api/v1/admin/users",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        print_response(response)


def demo_api_versioning():
    """Demo: API versioning"""
    print_section("11. API Versioning")

    print("\nAPI v1 endpoints are at /api/v1/...")
    print("Future versions (v2, v3) can coexist:")
    print("  - /api/v1/analyze  (current)")
    print("  - /api/v2/analyze  (future)")
    print("\nThis allows for backwards compatibility while introducing new features.")


def main():
    """Run all demos"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " "*15 + "Apex Analysis API v2 Demo" + " "*19 + "║")
    print("╚" + "═"*58 + "╝")

    print("\nMake sure the API server is running on http://localhost:5001")
    input("Press Enter to start demo...")

    # Test server availability
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n✗ Error: API server not responding")
            return
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to API server")
        print("Please start the server with: python web_app_v2.py")
        return

    # Run demos
    api_key = None
    access_token = None

    # 1. Registration
    new_api_key = demo_registration()

    # 2. Login
    access_token = demo_login()

    # 3. JWT protected endpoint
    if access_token:
        api_key = demo_jwt_protected_endpoint(access_token)

    # 4. API key authentication
    if api_key:
        demo_api_key_authentication(api_key)

        # 5. Rate limiting
        # demo_rate_limiting(api_key)  # Commented out to avoid hitting rate limits

        # 6. Chart endpoint
        demo_chart_endpoint(api_key)

    # 7. Backtest endpoint
    if access_token:
        demo_backtest_endpoint(access_token)

    # 8. Risk endpoint
    if api_key:
        demo_risk_endpoint(api_key)

    # 9. Admin endpoints
    if access_token:
        demo_admin_endpoints(access_token)

    # 10. Unauthorized access
    demo_unauthorized_access()

    # 11. API versioning
    demo_api_versioning()

    print_section("Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✓ User registration and JWT authentication")
    print("  ✓ API key authentication")
    print("  ✓ Rate limiting (commented out in demo)")
    print("  ✓ Role-based access control (admin vs user)")
    print("  ✓ API versioning (v1)")
    print("  ✓ Swagger documentation at /apidocs")
    print("\nNext Steps:")
    print("  1. Visit http://localhost:5001/apidocs for interactive API docs")
    print("  2. Try the endpoints with Postman or curl")
    print("  3. Explore the dashboard at http://localhost:5001")


if __name__ == '__main__':
    main()
