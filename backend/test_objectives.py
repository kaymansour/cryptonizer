"""
Test different optimization objectives
"""

from portfolio_optimizer import optimize_crypto_portfolio

symbols = ["BTC-USD", "ETH-USD", "ADA-USD", "SOL-USD"]
portfolio_value = 50000

objectives = ["max_sharpe", "min_volatility"]

for objective in objectives:
    print(f"\n{'='*60}")
    print(f"OPTIMIZATION OBJECTIVE: {objective.upper()}")
    print(f"{'='*60}")

    try:
        result = optimize_crypto_portfolio(
            symbols=symbols,
            total_value=portfolio_value,
            objective=objective,
            period="6mo",
        )

        print(
            f"Expected Annual Return: {result['optimization']['expected_return']:.2%}"
        )
        print(f"Annual Volatility: {result['optimization']['volatility']:.2%}")
        print(f"Sharpe Ratio: {result['optimization']['sharpe_ratio']:.3f}")

        print("\nOptimal Weights:")
        for symbol, weight in result["optimization"]["weights"].items():
            if weight > 0.001:
                print(f"  {symbol}: {weight:.2%}")

        print(f"\nDiscrete Allocation (${portfolio_value:,}):")
        if result["allocation"]["allocation"]:
            total_allocated = 0
            for symbol, shares in result["allocation"]["allocation"].items():
                price = result["allocation"]["latest_prices"][symbol]
                value = shares * price
                total_allocated += value
                print(f"  {symbol}: {shares} shares @ ${price:.2f} = ${value:.2f}")
            print(f"  Total allocated: ${total_allocated:.2f}")
            print(f"  Cash remaining: ${result['allocation']['leftover']:.2f}")
        else:
            print("  No allocations made")

    except Exception as e:
        print(f"Error with {objective}: {e}")
