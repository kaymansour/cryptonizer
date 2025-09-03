"""
Comprehensive Portfolio Optimization Test
Demonstrates all features of the crypto portfolio optimizer
"""

import numpy as np
from portfolio_optimizer import optimize_crypto_portfolio, CryptoPortfolioOptimizer

print("=" * 80)
print("CRYPTOCURRENCY PORTFOLIO OPTIMIZATION - COMPREHENSIVE TEST")
print("=" * 80)

# Test 1: Max Sharpe Portfolio
print("\n1. MAXIMUM SHARPE RATIO PORTFOLIO")
print("-" * 50)

symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'MATIC-USD']
portfolio_value = 150000

result_sharpe = optimize_crypto_portfolio(
    symbols=symbols,
    total_value=portfolio_value,
    objective="max_sharpe",
    period="1y"
)

print(f"Expected Annual Return: {result_sharpe['optimization']['expected_return']:.2%}")
print(f"Annual Volatility: {result_sharpe['optimization']['volatility']:.2%}")
print(f"Sharpe Ratio: {result_sharpe['optimization']['sharpe_ratio']:.3f}")
print("\nOptimal Weights:")
for symbol, weight in result_sharpe['optimization']['weights'].items():
    if weight > 0.001:
        print(f"  {symbol}: {weight:.2%}")

# Test 2: Minimum Volatility Portfolio
print("\n\n2. MINIMUM VOLATILITY PORTFOLIO")
print("-" * 50)

result_minvol = optimize_crypto_portfolio(
    symbols=symbols,
    total_value=portfolio_value,
    objective="min_volatility",
    period="1y"
)

print(f"Expected Annual Return: {result_minvol['optimization']['expected_return']:.2%}")
print(f"Annual Volatility: {result_minvol['optimization']['volatility']:.2%}")
print(f"Sharpe Ratio: {result_minvol['optimization']['sharpe_ratio']:.3f}")
print("\nOptimal Weights:")
for symbol, weight in result_minvol['optimization']['weights'].items():
    if weight > 0.001:
        print(f"  {symbol}: {weight:.2%}")

# Test 3: Efficient Frontier Calculation
print("\n\n3. EFFICIENT FRONTIER ANALYSIS")
print("-" * 50)

optimizer = CryptoPortfolioOptimizer(symbols, period="1y")
optimizer.fetch_price_data()
optimizer.calculate_expected_returns()
optimizer.calculate_risk_matrix()

volatilities, returns = optimizer.calculate_efficient_frontier(num_portfolios=20)

print("Sample Efficient Frontier Points (Risk vs Return):")
print("Volatility\tReturn")
for i in range(0, len(volatilities), max(1, len(volatilities)//5)):
    print(f"{volatilities[i]:.2%}\t\t{returns[i]:.2%}")

# Test 4: Portfolio Metrics Comparison
print("\n\n4. PORTFOLIO METRICS COMPARISON")
print("-" * 50)

portfolios = [
    ("Max Sharpe", result_sharpe),
    ("Min Volatility", result_minvol)
]

print(f"{'Portfolio':<15} {'Return':<10} {'Risk':<10} {'Sharpe':<8} {'VaR 95%':<10} {'Max DD':<10}")
print("-" * 70)

for name, result in portfolios:
    metrics = result['metrics']
    print(f"{name:<15} {metrics['expected_return']:<10.2%} {metrics['volatility']:<10.2%} "
          f"{metrics['sharpe_ratio']:<8.3f} {metrics['var_95']:<10.2%} {metrics['max_drawdown']:<10.2%}")

# Test 5: Discrete Allocation Details
print(f"\n\n5. DISCRETE ALLOCATION DETAILS (${portfolio_value:,})")
print("-" * 50)

for name, result in portfolios:
    print(f"\n{name} Portfolio:")
    allocation = result['allocation']
    if allocation['allocation']:
        total_allocated = 0
        for symbol, shares in allocation['allocation'].items():
            price = allocation['latest_prices'][symbol]
            value = shares * price
            total_allocated += value
            print(f"  {symbol}: {shares} shares @ ${price:.2f} = ${value:,.2f}")
        print(f"  Total Allocated: ${total_allocated:,.2f}")
        print(f"  Cash Remaining: ${allocation['leftover']:,.2f}")
        print(f"  Allocation Rate: {(total_allocated/portfolio_value)*100:.1f}%")
    else:
        print(f"  No allocations possible (prices too high)")
        print(f"  Cash Remaining: ${allocation['leftover']:,.2f}")

# Test 6: Risk Analysis
print("\n\n6. DETAILED RISK ANALYSIS")
print("-" * 50)

print("Expected Returns by Asset (Annualized):")
mu = optimizer.mu
for symbol in symbols:
    if symbol in mu.index:
        print(f"  {symbol}: {mu[symbol]:.2%}")

print(f"\nCovariance Matrix Diagonal (Variances):")
S = optimizer.S
for symbol in symbols:
    if symbol in S.index:
        print(f"  {symbol}: {S.loc[symbol, symbol]:.6f} (Volatility: {np.sqrt(S.loc[symbol, symbol]):.2%})")

print("\n" + "=" * 80)
print("OPTIMIZATION COMPLETE")
print("=" * 80)
