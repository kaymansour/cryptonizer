"""
Strategy Comparison Module
Compares portfolio strategies against various benchmarks including equal weight,
buy-and-hold, and traditional indices.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from backtester import Backtester, backtest_portfolio
import warnings

warnings.filterwarnings("ignore")


class StrategyComparator:
    """
    Comprehensive strategy comparison engine
    """

    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_investment: float = 100000,
    ):
        """
        Initialize the strategy comparator

        Args:
            symbols: List of cryptocurrency symbols to analyze
            start_date: Start date for comparison (YYYY-MM-DD)
            end_date: End date for comparison (YYYY-MM-DD)
            initial_investment: Initial investment amount for all strategies
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_investment = initial_investment
        self.results = {}

    def compare_strategies(
        self,
        optimized_weights: Dict[str, float],
        rebalance_frequency: str = "monthly",
        include_benchmarks: List[str] = None,
    ) -> Dict:
        """
        Compare optimized portfolio against various benchmark strategies

        Args:
            optimized_weights: Weights from portfolio optimization
            rebalance_frequency: How often to rebalance portfolios
            include_benchmarks: List of benchmarks to include
                               ['equal_weight', 'btc_only', 'eth_only', 'btc_eth_60_40', 'market_cap_weighted']

        Returns:
            Dictionary containing comparison results for all strategies
        """
        if include_benchmarks is None:
            include_benchmarks = [
                "equal_weight",
                "btc_only",
                "eth_only",
                "btc_eth_60_40",
            ]

        print(
            f"Comparing {len(include_benchmarks) + 1} strategies over period {self.start_date} to {self.end_date}"
        )

        strategies = {}

        # 1. Optimized Portfolio
        print("Running optimized portfolio backtest...")
        strategies["optimized"] = self._backtest_strategy(
            optimized_weights, "Optimized Portfolio", rebalance_frequency
        )

        # 2. Equal Weight Portfolio
        if "equal_weight" in include_benchmarks:
            print("Running equal weight backtest...")
            equal_weights = {symbol: 1 / len(self.symbols) for symbol in self.symbols}
            strategies["equal_weight"] = self._backtest_strategy(
                equal_weights, "Equal Weight Portfolio", rebalance_frequency
            )

        # 3. Bitcoin Only (Buy and Hold)
        if "btc_only" in include_benchmarks and "BTC-USD" in self.symbols:
            print("Running Bitcoin-only backtest...")
            btc_weights = {
                symbol: 1.0 if symbol == "BTC-USD" else 0.0 for symbol in self.symbols
            }
            strategies["btc_only"] = self._backtest_strategy(
                btc_weights, "Bitcoin Only (Buy & Hold)", "never"  # Buy and hold
            )

        # 4. Ethereum Only (Buy and Hold)
        if "eth_only" in include_benchmarks and "ETH-USD" in self.symbols:
            print("Running Ethereum-only backtest...")
            eth_weights = {
                symbol: 1.0 if symbol == "ETH-USD" else 0.0 for symbol in self.symbols
            }
            strategies["eth_only"] = self._backtest_strategy(
                eth_weights, "Ethereum Only (Buy & Hold)", "never"  # Buy and hold
            )

        # 5. 60/40 BTC/ETH Portfolio
        if (
            "btc_eth_60_40" in include_benchmarks
            and "BTC-USD" in self.symbols
            and "ETH-USD" in self.symbols
        ):
            print("Running 60/40 BTC/ETH backtest...")
            btc_eth_weights = {
                symbol: (
                    0.6 if symbol == "BTC-USD" else 0.4 if symbol == "ETH-USD" else 0.0
                )
                for symbol in self.symbols
            }
            strategies["btc_eth_60_40"] = self._backtest_strategy(
                btc_eth_weights, "60% BTC / 40% ETH", rebalance_frequency
            )

        # 6. Market Cap Weighted Portfolio
        if "market_cap_weighted" in include_benchmarks:
            print("Running market cap weighted backtest...")
            market_cap_weights = self._calculate_market_cap_weights()
            if market_cap_weights:
                strategies["market_cap_weighted"] = self._backtest_strategy(
                    market_cap_weights, "Market Cap Weighted", rebalance_frequency
                )

        # 7. Dynamic 60/40 strategies (e.g., bnb_sol_60_40, ada_dot_60_40)
        # Parse any benchmark that matches the pattern: {symbol1}_{symbol2}_60_40
        for benchmark in include_benchmarks:
            if benchmark.endswith("_60_40") and benchmark != "btc_eth_60_40":
                # Extract symbol names (remove _60_40 suffix)
                symbol_part = benchmark[:-6]  # Remove _60_40

                # Try to split into two symbols
                # We'll check all possible splits
                parts = symbol_part.split("_")

                for split_idx in range(1, len(parts)):
                    symbol1_name = "_".join(parts[:split_idx]).upper()
                    symbol2_name = "_".join(parts[split_idx:]).upper()

                    symbol1 = f"{symbol1_name}-USD"
                    symbol2 = f"{symbol2_name}-USD"

                    if symbol1 in self.symbols and symbol2 in self.symbols:
                        print(f"Running dynamic 60/40 {symbol1}/{symbol2} backtest...")
                        dynamic_weights = {
                            symbol: (
                                0.6
                                if symbol == symbol1
                                else 0.4 if symbol == symbol2 else 0.0
                            )
                            for symbol in self.symbols
                        }
                        strategies[benchmark] = self._backtest_strategy(
                            dynamic_weights,
                            f"60% {symbol1_name} / 40% {symbol2_name}",
                            rebalance_frequency,
                        )
                        break  # Found valid split, stop trying other splits

        self.results = strategies
        return self._generate_comparison_report()

    def _backtest_strategy(
        self, weights: Dict[str, float], strategy_name: str, rebalance_freq: str
    ) -> Dict:
        """
        Run backtest for a specific strategy

        Args:
            weights: Portfolio weights
            strategy_name: Name of the strategy
            rebalance_freq: Rebalancing frequency

        Returns:
            Backtest results for the strategy
        """
        try:
            # Filter weights to only include symbols with non-zero weights
            filtered_weights = {k: v for k, v in weights.items() if v > 0.0001}
            filtered_symbols = list(filtered_weights.keys())

            if not filtered_symbols:
                raise ValueError(f"No valid symbols for strategy {strategy_name}")

            backtester = Backtester(
                symbols=filtered_symbols,
                weights=filtered_weights,
                initial_investment=self.initial_investment,
                start_date=self.start_date,
                end_date=self.end_date,
                rebalance_frequency=rebalance_freq,
            )

            report = backtester.generate_report(include_detailed_data=True)
            report["strategy_name"] = strategy_name
            report["rebalance_frequency"] = rebalance_freq

            return report

        except Exception as e:
            print(f"Error backtesting {strategy_name}: {str(e)}")
            return None

    def _calculate_market_cap_weights(self) -> Optional[Dict[str, float]]:
        """
        Calculate market cap weighted portfolio (simplified)
        Note: This is a simplified version. In practice, you'd want real-time market cap data.

        Returns:
            Market cap weighted portfolio or None if calculation fails
        """
        try:
            import yfinance as yf

            # Approximate market caps (these would normally come from an API)
            # Using rough estimates as of 2024
            approximate_market_caps = {
                "BTC-USD": 800_000_000_000,  # ~$800B
                "ETH-USD": 300_000_000_000,  # ~$300B
                "ADA-USD": 15_000_000_000,  # ~$15B
                "SOL-USD": 45_000_000_000,  # ~$45B
                "DOT-USD": 8_000_000_000,  # ~$8B
                "MATIC-USD": 7_000_000_000,  # ~$7B
                "AVAX-USD": 12_000_000_000,  # ~$12B
                "LINK-USD": 8_000_000_000,  # ~$8B
                "ATOM-USD": 3_000_000_000,  # ~$3B
                "XRP-USD": 30_000_000_000,  # ~$30B
            }

            # Calculate weights based on available symbols
            available_caps = {
                symbol: approximate_market_caps.get(symbol, 1_000_000_000)
                for symbol in self.symbols
            }
            total_cap = sum(available_caps.values())

            weights = {
                symbol: cap / total_cap for symbol, cap in available_caps.items()
            }

            print(f"Calculated market cap weights: {weights}")
            return weights

        except Exception as e:
            print(f"Error calculating market cap weights: {str(e)}")
            return None

    def _generate_comparison_report(self) -> Dict:
        """
        Generate comprehensive comparison report

        Returns:
            Detailed comparison report
        """
        if not self.results:
            raise ValueError("No strategy results to compare")

        # Extract key metrics for comparison
        comparison_data = {}

        for strategy_key, result in self.results.items():
            if result is None:
                continue

            summary = result.get("summary", {})
            performance = result.get("performance_metrics", {})

            comparison_data[strategy_key] = {
                "strategy_name": result.get("strategy_name", strategy_key),
                "final_value": float(summary.get("final_value", 0)),
                "total_return": float(summary.get("total_return", 0)),
                "annualized_return": float(summary.get("annualized_return", 0)),
                "volatility": float(summary.get("volatility", 0)),
                "sharpe_ratio": float(summary.get("sharpe_ratio", 0)),
                "max_drawdown": float(summary.get("max_drawdown", 0)),
                "win_rate": float(performance.get("risk", {}).get("win_rate", 0)),
                "rebalance_frequency": result.get("rebalance_frequency", "unknown"),
            }

        # Create rankings
        rankings = self._create_rankings(comparison_data)

        # Generate comparison charts data
        chart_data = self._prepare_chart_data()

        return {
            "comparison_summary": comparison_data,
            "rankings": rankings,
            "chart_data": chart_data,
            "period": f"{self.start_date} to {self.end_date}",
            "initial_investment": self.initial_investment,
            "symbols_analyzed": self.symbols,
        }

    def _create_rankings(self, comparison_data: Dict) -> Dict:
        """
        Create rankings for different metrics

        Args:
            comparison_data: Strategy comparison data

        Returns:
            Rankings dictionary
        """
        rankings = {}

        metrics_to_rank = [
            ("total_return", False),  # Higher is better
            ("annualized_return", False),
            ("sharpe_ratio", False),
            ("volatility", True),  # Lower is better
            ("max_drawdown", True),  # Lower is better (less negative)
        ]

        for metric, ascending in metrics_to_rank:
            # Sort strategies by metric
            sorted_strategies = sorted(
                comparison_data.items(),
                key=lambda x: x[1].get(metric, 0),
                reverse=not ascending,
            )

            rankings[metric] = [
                {
                    "strategy": strategy_key,
                    "value": float(data.get(metric, 0)),
                }
                for i, (strategy_key, data) in enumerate(sorted_strategies)
            ]

        return rankings

    def _prepare_chart_data(self) -> Dict:
        """
        Prepare data for charting portfolio values over time

        Returns:
            Chart data dictionary
        """
        chart_data = {"dates": [], "strategies": {}}

        # Get dates from the first strategy with daily data
        for strategy_key, result in self.results.items():
            if result and "daily_data" in result:
                chart_data["dates"] = result["daily_data"]["dates"]
                break

        # Collect portfolio values for each strategy
        for strategy_key, result in self.results.items():
            if result and "daily_data" in result:
                chart_data["strategies"][strategy_key] = {
                    "name": result.get("strategy_name", strategy_key),
                    "values": result["daily_data"]["portfolio_values"],
                    "returns": result["daily_data"]["cumulative_returns"],
                }

        return chart_data

    def get_comparison_summary(self) -> str:
        """
        Get formatted text summary of strategy comparison

        Returns:
            Formatted comparison summary
        """
        if not self.results:
            return "No strategy comparison results available"

        report = self._generate_comparison_report()
        comparison_data = report["comparison_summary"]

        summary = f"""
Strategy Comparison Results
{'='*60}
Period: {report['period']}
Initial Investment: ${report['initial_investment']:,.2f}

Performance Summary:
{'-'*60}
"""

        # Sort by total return for display
        sorted_strategies = sorted(
            comparison_data.items(), key=lambda x: x[1]["total_return"], reverse=True
        )

        for i, (strategy_key, data) in enumerate(sorted_strategies):
            rank = i + 1
            summary += f"""
{rank}. {data['strategy_name']}
   Final Value: ${data['final_value']:,.2f}
   Total Return: {data['total_return']:.2f}%
   Annualized Return: {data['annualized_return']:.2f}%
   Volatility: {data['volatility']:.2f}%
   Sharpe Ratio: {data['sharpe_ratio']:.3f}
   Max Drawdown: {data['max_drawdown']:.2f}%
   Rebalancing: {data['rebalance_frequency']}
"""

        # Add best performer analysis
        best_strategy = sorted_strategies[0]
        summary += f"""
{'-'*60}
Best Performing Strategy: {best_strategy[1]['strategy_name']}
  - Outperformed initial investment by {best_strategy[1]['total_return']:.2f}%
  - Risk-adjusted performance (Sharpe): {best_strategy[1]['sharpe_ratio']:.3f}
"""

        return summary

    def export_results(self, filename: str = None) -> str:
        """
        Export comparison results to CSV format

        Args:
            filename: Output filename (optional)

        Returns:
            Filename where results were saved
        """
        if not self.results:
            raise ValueError("No results to export")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_comparison_{timestamp}.csv"

        # Prepare data for CSV
        rows = []
        for strategy_key, result in self.results.items():
            if result is None:
                continue

            summary = result.get("summary", {})
            performance = result.get("performance_metrics", {})

            row = {
                "Strategy": result.get("strategy_name", strategy_key),
                "Final_Value": summary.get("final_value", 0),
                "Total_Return_Pct": summary.get("total_return", 0),
                "Annualized_Return_Pct": summary.get("annualized_return", 0),
                "Volatility_Pct": summary.get("volatility", 0),
                "Sharpe_Ratio": summary.get("sharpe_ratio", 0),
                "Max_Drawdown_Pct": summary.get("max_drawdown", 0),
                "Win_Rate_Pct": performance.get("risk", {}).get("win_rate", 0),
                "Rebalance_Frequency": result.get("rebalance_frequency", "unknown"),
            }
            rows.append(row)

        # Save to CSV
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)

        print(f"Results exported to {filename}")
        return filename


# Convenience functions
def compare_with_benchmarks(
    symbols: List[str],
    optimized_weights: Dict[str, float],
    start_date: str = None,
    end_date: str = None,
    initial_investment: float = 100000,
    rebalance_frequency: str = "monthly",
) -> Dict:
    """
    Convenience function to compare optimized portfolio with standard benchmarks

    Args:
        symbols: List of cryptocurrency symbols
        optimized_weights: Optimized portfolio weights
        start_date: Start date (defaults to 1 year ago)
        end_date: End date (defaults to today)
        initial_investment: Initial investment amount
        rebalance_frequency: Rebalancing frequency

    Returns:
        Complete comparison results
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    comparator = StrategyComparator(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_investment=initial_investment,
    )

    return comparator.compare_strategies(
        optimized_weights=optimized_weights,
        rebalance_frequency=rebalance_frequency,
        include_benchmarks=["equal_weight", "btc_only", "eth_only", "btc_eth_60_40"],
    )


def quick_comparison(
    symbols: List[str], optimized_weights: Dict[str, float], days_back: int = 365
) -> str:
    """
    Quick comparison with text output

    Args:
        symbols: List of cryptocurrency symbols
        optimized_weights: Optimized portfolio weights
        days_back: Number of days to look back

    Returns:
        Formatted comparison summary
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    comparator = StrategyComparator(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_investment=100000,
    )

    comparator.compare_strategies(
        optimized_weights=optimized_weights,
        include_benchmarks=["equal_weight", "btc_only", "eth_only"],
    )

    return comparator.get_comparison_summary()


# Example usage and testing
if __name__ == "__main__":
    # Example strategy comparison
    symbols = ["BTC-USD", "ETH-USD", "ADA-USD"]
    optimized_weights = {"BTC-USD": 0.4, "ETH-USD": 0.35, "ADA-USD": 0.25}

    try:
        print("Running strategy comparison example...")

        # Create comparator
        comparator = StrategyComparator(
            symbols=symbols,
            start_date="2023-01-01",
            end_date="2024-01-01",
            initial_investment=100000,
        )

        # Run comparison
        results = comparator.compare_strategies(
            optimized_weights=optimized_weights,
            rebalance_frequency="monthly",
            include_benchmarks=[
                "equal_weight",
                "btc_only",
                "eth_only",
                "btc_eth_60_40",
            ],
        )

        # Print summary
        print(comparator.get_comparison_summary())

        # Show rankings
        print("\nTop Strategies by Total Return:")
        for rank_data in results["rankings"]["total_return"][:3]:
            print(
                f"  {rank_data['rank']}. {rank_data['strategy_name']}: {rank_data['value']:.2f}%"
            )

    except Exception as e:
        print(f"Error: {e}")
