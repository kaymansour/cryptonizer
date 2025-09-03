"""
Test the portfolio optimization API endpoints
"""

import requests
import json

base_url = "http://localhost:8000"

# Test 1: Portfolio optimization
print("Testing Portfolio Optimization API...")
portfolio_request = {
    "symbols": ["BTC", "ETH", "ADA"],
    "total_value": 50000,
    "objective": "max_sharpe",
    "period": "6mo"
}

try:
    response = requests.post(f"{base_url}/api/optimize-portfolio", json=portfolio_request)
    if response.status_code == 200:
        result = response.json()
        print("✅ Portfolio optimization successful!")
        print(f"Expected Return: {result['portfolio']['expected_return']:.2%}")
        print(f"Volatility: {result['portfolio']['volatility']:.2%}")
        print(f"Sharpe Ratio: {result['portfolio']['sharpe_ratio']:.3f}")
        print("Weights:")
        for symbol, weight in result['portfolio']['weights'].items():
            if weight > 0.001:
                print(f"  {symbol}: {weight:.2%}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to API server. Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Get optimization objectives
print("Testing Optimization Objectives API...")
try:
    response = requests.get(f"{base_url}/api/portfolio/objectives")
    if response.status_code == 200:
        objectives = response.json()
        print("✅ Available optimization objectives:")
        for obj in objectives['objectives']:
            print(f"  - {obj['name']}: {obj['description']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Efficient frontier
print("Testing Efficient Frontier API...")
frontier_request = {
    "symbols": ["BTC", "ETH"],
    "period": "3mo",
    "num_portfolios": 10
}

try:
    response = requests.post(f"{base_url}/api/efficient-frontier", json=frontier_request)
    if response.status_code == 200:
        result = response.json()
        print("✅ Efficient frontier calculation successful!")
        print(f"Number of frontier points: {len(result['efficient_frontier']['returns'])}")
        print("Reference portfolios:")
        for name, portfolio in result['reference_portfolios'].items():
            print(f"  {name}: Return={portfolio['return']:.2%}, Risk={portfolio['volatility']:.2%}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nAPI testing complete!")
