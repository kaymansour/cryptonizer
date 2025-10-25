"""
Comprehensive Test Suite for Backtesting and Strategy Comparison
Tests the backtesting engine and strategy comparison functionality.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append("/home/ayoub/senior/backend")

from backtester import Backtester, backtest_portfolio
from strategy_comparator import StrategyComparator, compare_with_benchmarks
import requests


def test_backtester_basic():
    """Test basic backtesting functionality"""
    print("\n" + "=" * 60)
    print("Testing Basic Backtesting Functionality")
    print("=" * 60)

    try:
        # Test data
        symbols = ["BTC-USD", "ETH-USD"]
        weights = {"BTC-USD": 0.6, "ETH-USD": 0.4}
        initial_investment = 50000
        start_date = "2023-06-01"
        end_date = "2023-12-01"

        print(f"Testing backtest with:")
        print(f"  Symbols: {symbols}")
        print(f"  Weights: {weights}")
        print(f"  Period: {start_date} to {end_date}")
        print(f"  Initial Investment: ${initial_investment:,}")

        # Create backtester
        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=initial_investment,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly",
        )

        # Run backtest
        print("\n📊 Running backtest...")
        report = backtester.generate_report(include_detailed_data=True)

        # Validate results
        assert report is not None, "Report should not be None"
        assert "summary" in report, "Report should contain summary"
        assert (
            "performance_metrics" in report
        ), "Report should contain performance metrics"
        assert "portfolio_info" in report, "Report should contain portfolio info"

        summary = report["summary"]
        print(f"\n✅ Backtest Results:")
        print(f"  Final Value: ${summary['final_value']:,.2f}")
        print(f"  Total Return: {summary['total_return']:.2f}%")
        print(f"  Annualized Return: {summary['annualized_return']:.2f}%")
        print(f"  Sharpe Ratio: {summary['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {summary['max_drawdown']:.2f}%")

        # Print formatted summary
        print(backtester.get_performance_summary())

        print("✅ Basic backtesting test PASSED")
        return True

    except Exception as e:
        print(f"❌ Basic backtesting test FAILED: {str(e)}")
        return False


def test_strategy_comparison():
    """Test strategy comparison functionality"""
    print("\n" + "=" * 60)
    print("Testing Strategy Comparison Functionality")
    print("=" * 60)

    try:
        # Test data
        symbols = ["BTC-USD", "ETH-USD", "ADA-USD"]
        optimized_weights = {"BTC-USD": 0.5, "ETH-USD": 0.3, "ADA-USD": 0.2}
        start_date = "2023-06-01"
        end_date = "2023-12-01"
        initial_investment = 100000

        print(f"Testing strategy comparison with:")
        print(f"  Symbols: {symbols}")
        print(f"  Optimized Weights: {optimized_weights}")
        print(f"  Period: {start_date} to {end_date}")

        # Create strategy comparator
        comparator = StrategyComparator(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_investment=initial_investment,
        )

        # Run comparison
        print("\n📊 Running strategy comparison...")
        results = comparator.compare_strategies(
            optimized_weights=optimized_weights,
            rebalance_frequency="monthly",
            include_benchmarks=["equal_weight", "btc_only", "eth_only"],
        )

        # Validate results
        assert results is not None, "Results should not be None"
        assert (
            "comparison_summary" in results
        ), "Results should contain comparison summary"
        assert "rankings" in results, "Results should contain rankings"

        print(f"\n✅ Comparison Results:")
        print(f"  Strategies compared: {len(results['comparison_summary'])}")

        # Print summary
        print(comparator.get_comparison_summary())

        # Show top 3 strategies by total return
        if "total_return" in results["rankings"]:
            print(f"\nTop 3 Strategies by Total Return:")
            for i, strategy in enumerate(results["rankings"]["total_return"][:3]):
                print(f"  {i+1}. {strategy['strategy_name']}: {strategy['value']:.2f}%")

        print("✅ Strategy comparison test PASSED")
        return True

    except Exception as e:
        print(f"❌ Strategy comparison test FAILED: {str(e)}")
        return False


def test_convenience_functions():
    """Test convenience functions"""
    print("\n" + "=" * 60)
    print("Testing Convenience Functions")
    print("=" * 60)

    try:
        symbols = ["BTC-USD", "ETH-USD"]
        weights = {"BTC-USD": 0.7, "ETH-USD": 0.3}

        print(f"Testing convenience functions with:")
        print(f"  Symbols: {symbols}")
        print(f"  Weights: {weights}")

        # Test backtest_portfolio function
        print("\n📊 Testing backtest_portfolio convenience function...")
        result = backtest_portfolio(
            symbols=symbols,
            weights=weights,
            initial_investment=50000,
            start_date="2023-08-01",
            end_date="2023-11-01",
        )

        assert result is not None, "Backtest result should not be None"
        print(f"✅ Final Value: ${result['summary']['final_value']:,.2f}")

        # Test compare_with_benchmarks function
        print("\n📊 Testing compare_with_benchmarks convenience function...")
        comparison = compare_with_benchmarks(
            symbols=symbols,
            optimized_weights=weights,
            start_date="2023-08-01",
            end_date="2023-11-01",
            initial_investment=50000,
        )

        assert comparison is not None, "Comparison result should not be None"
        print(f"✅ Strategies compared: {len(comparison['comparison_summary'])}")

        print("✅ Convenience functions test PASSED")
        return True

    except Exception as e:
        print(f"❌ Convenience functions test FAILED: {str(e)}")
        return False


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("Testing Edge Cases and Error Handling")
    print("=" * 60)

    passed_tests = 0
    total_tests = 0

    # Test 1: Invalid weights (don't sum to 1)
    total_tests += 1
    try:
        print("\n🧪 Test 1: Invalid weights (don't sum to 1)")
        symbols = ["BTC-USD", "ETH-USD"]
        invalid_weights = {"BTC-USD": 0.3, "ETH-USD": 0.3}  # Sum = 0.6

        backtester = Backtester(
            symbols=symbols,
            weights=invalid_weights,
            initial_investment=10000,
            start_date="2023-01-01",
            end_date="2023-02-01",
        )
        print("❌ Should have raised ValueError for invalid weights")

    except ValueError as e:
        print(f"✅ Correctly caught invalid weights: {str(e)}")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    # Test 2: Empty symbols list
    total_tests += 1
    try:
        print("\n🧪 Test 2: Empty symbols list")
        backtester = Backtester(
            symbols=[],
            weights={},
            initial_investment=10000,
            start_date="2023-01-01",
            end_date="2023-02-01",
        )
        print("❌ Should have raised ValueError for empty symbols")

    except ValueError as e:
        print(f"✅ Correctly caught empty symbols: {str(e)}")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    # Test 3: Invalid date range
    total_tests += 1
    try:
        print("\n🧪 Test 3: Invalid date range (start > end)")
        symbols = ["BTC-USD"]
        weights = {"BTC-USD": 1.0}

        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=10000,
            start_date="2023-06-01",
            end_date="2023-01-01",  # End before start
        )
        print("❌ Should have raised ValueError for invalid date range")

    except ValueError as e:
        print(f"✅ Correctly caught invalid date range: {str(e)}")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    # Test 4: Single symbol portfolio
    total_tests += 1
    try:
        print("\n🧪 Test 4: Single symbol portfolio")
        symbols = ["BTC-USD"]
        weights = {"BTC-USD": 1.0}

        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=25000,
            start_date="2023-09-01",
            end_date="2023-10-01",
        )

        report = backtester.generate_report()
        assert report is not None, "Single symbol backtest should work"
        print(
            f"✅ Single symbol backtest worked: Final value ${report['summary']['final_value']:,.2f}"
        )
        passed_tests += 1

    except Exception as e:
        print(f"❌ Single symbol test failed: {str(e)}")

    print(f"\n📊 Edge Cases Summary: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests


def test_api_endpoints():
    """Test the FastAPI endpoints (requires running server)"""
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code != 200:
            print("⚠️  Backend server not running. Skipping API tests.")
            return True
    except requests.exceptions.RequestException:
        print("⚠️  Backend server not accessible. Skipping API tests.")
        return True

    passed_tests = 0
    total_tests = 0

    # Test 1: Backtest endpoint
    total_tests += 1
    try:
        print("\n🧪 Testing /api/backtest-portfolio endpoint")

        backtest_request = {
            "symbols": ["BTC-USD", "ETH-USD"],
            "weights": {"BTC-USD": 0.6, "ETH-USD": 0.4},
            "initial_investment": 50000,
            "start_date": "2023-08-01",
            "end_date": "2023-10-01",
            "rebalance_frequency": "monthly",
        }

        response = requests.post(
            f"{base_url}/api/backtest-portfolio", json=backtest_request, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True, "API should return success=True"
            assert "backtest_results" in data, "API should return backtest results"
            print(
                f"✅ Backtest API: Final value ${data['summary']['final_value']:,.2f}"
            )
            passed_tests += 1
        else:
            print(f"❌ Backtest API failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Backtest API error: {str(e)}")

    # Test 2: Strategy comparison endpoint
    total_tests += 1
    try:
        print("\n🧪 Testing /api/compare-strategies endpoint")

        comparison_request = {
            "symbols": ["BTC-USD", "ETH-USD"],
            "optimized_weights": {"BTC-USD": 0.6, "ETH-USD": 0.4},
            "initial_investment": 50000,
            "start_date": "2023-08-01",
            "end_date": "2023-10-01",
            "rebalance_frequency": "monthly",
            "include_benchmarks": ["equal_weight", "btc_only"],
        }

        response = requests.post(
            f"{base_url}/api/compare-strategies",
            json=comparison_request,
            timeout=60,  # Longer timeout for comparison
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True, "API should return success=True"
            assert "comparison_results" in data, "API should return comparison results"
            print(
                f"✅ Strategy Comparison API: {data['summary']['strategies_compared']} strategies compared"
            )
            passed_tests += 1
        else:
            print(
                f"❌ Strategy Comparison API failed: {response.status_code} - {response.text}"
            )

    except Exception as e:
        print(f"❌ Strategy Comparison API error: {str(e)}")

    print(f"\n📊 API Tests Summary: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests


def test_rebalancing_frequencies():
    """Test different rebalancing frequencies"""
    print("\n" + "=" * 60)
    print("Testing Different Rebalancing Frequencies")
    print("=" * 60)

    symbols = ["BTC-USD", "ETH-USD"]
    weights = {"BTC-USD": 0.6, "ETH-USD": 0.4}
    initial_investment = 50000
    start_date = "2023-08-01"
    end_date = "2023-11-01"

    frequencies = ["never", "monthly", "weekly"]
    results = {}

    for freq in frequencies:
        try:
            print(f"\n🧪 Testing {freq} rebalancing...")

            backtester = Backtester(
                symbols=symbols,
                weights=weights,
                initial_investment=initial_investment,
                start_date=start_date,
                end_date=end_date,
                rebalance_frequency=freq,
            )

            report = backtester.generate_report()
            final_value = report["summary"]["final_value"]
            total_return = report["summary"]["total_return"]

            results[freq] = {"final_value": final_value, "total_return": total_return}

            print(
                f"  ✅ {freq}: Final value ${final_value:,.2f}, Return {total_return:.2f}%"
            )

        except Exception as e:
            print(f"  ❌ {freq} failed: {str(e)}")

    print(f"\n📊 Rebalancing Comparison:")
    for freq, data in results.items():
        print(
            f"  {freq:8}: ${data['final_value']:8,.0f} ({data['total_return']:6.2f}%)"
        )

    print("✅ Rebalancing frequencies test completed")
    return len(results) == len(frequencies)


def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Starting Comprehensive Backtesting Test Suite")
    print("=" * 80)

    start_time = datetime.now()
    test_results = []

    # Run all tests
    tests = [
        ("Basic Backtesting", test_backtester_basic),
        ("Strategy Comparison", test_strategy_comparison),
        ("Convenience Functions", test_convenience_functions),
        ("Edge Cases", test_edge_cases),
        ("Rebalancing Frequencies", test_rebalancing_frequencies),
        ("API Endpoints", test_api_endpoints),
    ]

    for test_name, test_function in tests:
        try:
            print(f"\n🧪 Running {test_name} tests...")
            result = test_function()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test suite failed with error: {str(e)}")
            test_results.append((test_name, False))

    # Print final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:25}: {status}")

    print(f"\n📊 Overall Results: {passed}/{total} test suites passed")
    print(f"⏱️  Total time: {duration:.1f} seconds")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Backtesting system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
