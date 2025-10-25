#!/usr/bin/env python3
"""
Backtesting Demo Script
Demonstrates the portfolio backtesting and strategy comparison capabilities.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append("/home/ayoub/senior/backend")

from backtester import Backtester, backtest_portfolio
from strategy_comparator import StrategyComparator, compare_with_benchmarks


def demo_basic_backtest():
    """Demo basic backtesting functionality"""
    print("🚀 DEMO 1: Basic Portfolio Backtesting")
    print("=" * 60)

    # Demo portfolio
    symbols = ["BTC-USD", "ETH-USD", "ADA-USD"]
    weights = {"BTC-USD": 0.4, "ETH-USD": 0.35, "ADA-USD": 0.25}

    print(f"📊 Portfolio Configuration:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Weights: {weights}")
    print(f"   Investment: $100,000")
    print(f"   Period: 1 year backtest (2023)")

    try:
        # Run backtest
        print(f"\n🔄 Running backtest...")

        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=100000,
            start_date="2023-01-01",
            end_date="2023-12-31",
            rebalance_frequency="monthly",
        )

        report = backtester.generate_report()

        # Display results
        print(f"\n✅ Backtest Results:")
        print(f"   Initial Investment: ${report['summary']['initial_investment']:,.2f}")
        print(f"   Final Value: ${report['summary']['final_value']:,.2f}")
        print(f"   Total Return: {report['summary']['total_return']:.2f}%")
        print(f"   Annualized Return: {report['summary']['annualized_return']:.2f}%")
        print(f"   Sharpe Ratio: {report['summary']['sharpe_ratio']:.3f}")
        print(f"   Max Drawdown: {report['summary']['max_drawdown']:.2f}%")

        return True

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False


def demo_strategy_comparison():
    """Demo strategy comparison functionality"""
    print("\n🚀 DEMO 2: Strategy Comparison")
    print("=" * 60)

    # Demo portfolio vs benchmarks
    symbols = ["BTC-USD", "ETH-USD"]
    optimized_weights = {"BTC-USD": 0.65, "ETH-USD": 0.35}

    print(f"📊 Strategy Comparison Setup:")
    print(f"   Optimized Portfolio: {optimized_weights}")
    print(f"   Benchmarks: Equal Weight, Bitcoin Only, Ethereum Only")
    print(f"   Period: Last 6 months")

    try:
        # Set up date range
        end_date = "2023-12-31"
        start_date = "2023-07-01"

        print(f"\n🔄 Running strategy comparison...")

        comparator = StrategyComparator(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_investment=100000,
        )

        results = comparator.compare_strategies(
            optimized_weights=optimized_weights,
            rebalance_frequency="monthly",
            include_benchmarks=["equal_weight", "btc_only", "eth_only"],
        )

        # Display results
        print(f"\n✅ Strategy Comparison Results:")
        comparison_data = results["comparison_summary"]

        # Sort by total return
        sorted_strategies = sorted(
            comparison_data.items(), key=lambda x: x[1]["total_return"], reverse=True
        )

        for i, (strategy_key, data) in enumerate(sorted_strategies):
            rank = i + 1
            print(f"   {rank}. {data['strategy_name']}")
            print(f"      Return: {data['total_return']:.2f}%")
            print(f"      Sharpe: {data['sharpe_ratio']:.3f}")
            print(f"      Max DD: {data['max_drawdown']:.2f}%")

        return True

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False


def demo_rebalancing_comparison():
    """Demo different rebalancing frequencies"""
    print("\n🚀 DEMO 3: Rebalancing Frequency Impact")
    print("=" * 60)

    symbols = ["BTC-USD", "ETH-USD"]
    weights = {"BTC-USD": 0.6, "ETH-USD": 0.4}

    print(f"📊 Testing Portfolio:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Weights: {weights}")
    print(f"   Frequencies: Never, Monthly, Weekly")

    frequencies = ["never", "monthly", "weekly"]
    results = {}

    for freq in frequencies:
        try:
            print(f"\n🔄 Testing {freq} rebalancing...")

            backtester = Backtester(
                symbols=symbols,
                weights=weights,
                initial_investment=100000,
                start_date="2023-06-01",
                end_date="2023-12-01",
                rebalance_frequency=freq,
            )

            report = backtester.generate_report()
            results[freq] = {
                "final_value": report["summary"]["final_value"],
                "total_return": report["summary"]["total_return"],
                "sharpe_ratio": report["summary"]["sharpe_ratio"],
            }

        except Exception as e:
            print(f"   ❌ {freq} failed: {str(e)}")

    if results:
        print(f"\n✅ Rebalancing Comparison Results:")
        print(f"{'Frequency':<10} {'Final Value':<12} {'Return':<8} {'Sharpe':<8}")
        print("-" * 40)

        for freq, data in results.items():
            print(
                f"{freq:<10} ${data['final_value']:<11,.0f} {data['total_return']:<7.2f}% {data['sharpe_ratio']:<7.3f}"
            )

    return len(results) > 0


def demo_api_usage():
    """Demo API usage examples"""
    print("\n🚀 DEMO 4: API Usage Examples")
    print("=" * 60)

    print("📝 Example API Calls:")
    print("\n1. Backtest Portfolio:")
    print(
        """
curl -X POST "http://localhost:8000/api/backtest-portfolio" \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbols": ["BTC-USD", "ETH-USD"],
    "weights": {"BTC-USD": 0.6, "ETH-USD": 0.4},
    "initial_investment": 100000,
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "rebalance_frequency": "monthly"
  }'
"""
    )

    print("\n2. Compare Strategies:")
    print(
        """
curl -X POST "http://localhost:8000/api/compare-strategies" \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbols": ["BTC-USD", "ETH-USD"],
    "optimized_weights": {"BTC-USD": 0.6, "ETH-USD": 0.4},
    "initial_investment": 100000,
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "include_benchmarks": ["equal_weight", "btc_only", "eth_only"]
  }'
"""
    )

    print("\n3. Quick Backtest (last 365 days):")
    print(
        """
curl -X POST "http://localhost:8000/api/quick-backtest?days_back=365" \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbols": ["BTC-USD", "ETH-USD"],
    "weights": {"BTC-USD": 0.6, "ETH-USD": 0.4}
  }'
"""
    )


def main():
    """Run all demos"""
    print("🎯 Portfolio Backtesting & Strategy Comparison Demo")
    print("=" * 70)
    print("This demo showcases the comprehensive backtesting capabilities")
    print("that allow users to see how their optimized portfolios would")
    print("have performed historically against various benchmarks.")
    print("=" * 70)

    demos = [
        ("Basic Backtesting", demo_basic_backtest),
        ("Strategy Comparison", demo_strategy_comparison),
        ("Rebalancing Impact", demo_rebalancing_comparison),
        ("API Usage Examples", demo_api_usage),
    ]

    results = []

    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"❌ {demo_name} demo failed: {str(e)}")
            results.append((demo_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 DEMO SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(
        [r for r in results if r[0] != "API Usage Examples"]
    )  # API demo always "passes"

    for demo_name, result in results:
        if demo_name == "API Usage Examples":
            status = "📋 SHOWN"
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {demo_name:<25}: {status}")

    print(f"\n🎯 Results: {passed}/{total} functional demos passed")

    if passed == total:
        print("\n🎉 All demos completed successfully!")
        print("🚀 Your backtesting system is ready for production use!")
    else:
        print("\n⚠️  Some demos failed. Please check the output above.")

    print("\n📖 Key Features Demonstrated:")
    print("   ✓ Historical portfolio performance analysis")
    print("   ✓ Strategy comparison vs benchmarks")
    print("   ✓ Rebalancing frequency optimization")
    print("   ✓ Comprehensive risk metrics calculation")
    print("   ✓ REST API endpoints for integration")

    print("\n🔗 Next Steps:")
    print("   1. Integrate with your frontend for user-friendly backtesting")
    print("   2. Add more sophisticated benchmarks (market indices, etc.)")
    print("   3. Implement real-time portfolio tracking")
    print("   4. Add machine learning for forward-looking analysis")


if __name__ == "__main__":
    main()
