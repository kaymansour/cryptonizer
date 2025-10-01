"""
Debug BTC allocation issue
"""

from portfolio_optimizer import CryptoPortfolioOptimizer
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

symbols = ['BTC-USD']
optimizer = CryptoPortfolioOptimizer(symbols, period="3mo")

# Fetch data
data = optimizer.fetch_price_data()
latest_prices = get_latest_prices(data)
print(f"BTC latest price: ${latest_prices['BTC-USD']:,.2f}")

# Calculate optimization
optimizer.calculate_expected_returns()
optimizer.calculate_risk_matrix()
result = optimizer.optimize_portfolio(objective="min_volatility")
print(f"BTC weight: {result['weights']['BTC-USD']:.6f}")

# Test different portfolio values
portfolio_values = [50000, 100000, 150000, 200000]

for pv in portfolio_values:
    print(f"\nPortfolio value: ${pv:,}")
    btc_shares = pv / latest_prices['BTC-USD']
    print(f"Could buy {btc_shares:.6f} BTC shares")
    
    if btc_shares >= 1:
        print(f"Can buy at least 1 full share")
        weights = {'BTC-USD': 1.0}
        da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=pv)
        allocation, leftover = da.greedy_portfolio()
        print(f"Allocation: {allocation}")
        print(f"Leftover: ${leftover:.2f}")
    else:
        print(f"Cannot buy 1 full share")
