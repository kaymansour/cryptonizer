"""
Simple test script for portfolio optimization
"""

from portfolio_optimizer import CryptoPortfolioOptimizer
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

# Test with a smaller set of cryptos
symbols = ['BTC-USD', 'ETH-USD']

try:
    optimizer = CryptoPortfolioOptimizer(symbols, period="6mo")
    
    # Fetch data
    print("Fetching price data...")
    data = optimizer.fetch_price_data()
    print(f"Data shape: {data.shape}")
    
    # Get latest prices
    latest_prices = get_latest_prices(data)
    print(f"Latest prices: {latest_prices}")
    
    # Calculate expected returns and optimize
    optimizer.calculate_expected_returns()
    optimizer.calculate_risk_matrix()
    result = optimizer.optimize_portfolio(objective="max_sharpe")
    print(f"Optimization weights: {result['weights']}")
    
    # Test discrete allocation manually
    print("\nTesting discrete allocation manually...")
    weights = result['weights']
    portfolio_value = 100000
    
    # Filter out zero weights
    filtered_weights = {k: v for k, v in weights.items() if v > 0.001}
    print(f"Filtered weights: {filtered_weights}")
    
    if filtered_weights:
        da = DiscreteAllocation(filtered_weights, latest_prices, total_portfolio_value=portfolio_value)
        allocation, leftover = da.greedy_portfolio()
        print(f"Allocation: {allocation}")
        print(f"Leftover: {leftover}")
    else:
        print("No meaningful weights to allocate")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
