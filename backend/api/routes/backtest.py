"""
Backtesting routes for portfolio performance analysis
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from api.models.requests import (
    BacktestRequest, 
    StrategyComparisonRequest, 
    MLBacktestRequest
)
from backtester import Backtester
from strategy_comparator import StrategyComparator
from ml_backtester import MLTradingBacktester
from datetime import datetime, timedelta

router = APIRouter(prefix="/api")


@router.post("/backtest-portfolio")
async def backtest_portfolio_endpoint(request: BacktestRequest):
    """
    Backtest a portfolio with given weights over a historical period
    """
    try:
        print(f"Backtesting portfolio with {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Weights: {request.weights}")

        # Validate weights
        total_weight = sum(request.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Create backtester
        backtester = Backtester(
            symbols=request.symbols,
            weights=request.weights,
            initial_investment=request.initial_investment,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_frequency=request.rebalance_frequency,
        )

        # Generate comprehensive report
        report = backtester.generate_report(include_detailed_data=True)

        print(f"Backtest completed successfully")
        print(f"Final value: ${report['summary']['final_value']:,.2f}")
        print(f"Total return: {report['summary']['total_return']:.2f}%")

        return {
            "success": True,
            "backtest_results": report,
            "summary": {
                "initial_investment": request.initial_investment,
                "final_value": report["summary"]["final_value"],
                "total_return": report["summary"]["total_return"],
                "annualized_return": report["summary"]["annualized_return"],
                "sharpe_ratio": report["summary"]["sharpe_ratio"],
                "max_drawdown": report["summary"]["max_drawdown"],
                "period": f"{request.start_date} to {request.end_date}",
            },
        }

    except ValueError as ve:
        print(f"Validation error in backtest: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in backtest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtesting failed: {str(e)}")


@router.post("/compare-strategies")
async def compare_strategies_endpoint(request: StrategyComparisonRequest):
    """
    Compare optimized portfolio against benchmark strategies
    """
    try:
        print(f"Comparing strategies for {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Optimized weights: {request.optimized_weights}")

        # Validate optimized weights
        total_weight = sum(request.optimized_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Optimized weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Set default benchmarks if not provided
        if request.include_benchmarks is None:
            request.include_benchmarks = [
                "equal_weight",
                "btc_only",
                "eth_only",
                "btc_eth_60_40",
            ]

        # Create strategy comparator
        comparator = StrategyComparator(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_investment=request.initial_investment,
        )

        # Run comparison
        comparison_results = comparator.compare_strategies(
            optimized_weights=request.optimized_weights,
            rebalance_frequency=request.rebalance_frequency,
            include_benchmarks=request.include_benchmarks,
        )

        print(f"Strategy comparison completed successfully")
        print(f"Compared {len(comparison_results['comparison_summary'])} strategies")

        # Find best performing strategy
        best_strategy = max(
            comparison_results["comparison_summary"].items(),
            key=lambda x: x[1]["total_return"],
        )

        return {
            "success": True,
            "comparison_results": comparison_results,
            "summary": {
                "period": comparison_results["period"],
                "initial_investment": comparison_results["initial_investment"],
                "strategies_compared": len(comparison_results["comparison_summary"]),
                "best_strategy": {
                    "name": best_strategy[1]["strategy_name"],
                    "total_return": best_strategy[1]["total_return"],
                    "sharpe_ratio": best_strategy[1]["sharpe_ratio"],
                },
            },
        }

    except ValueError as ve:
        print(f"Validation error in strategy comparison: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in strategy comparison endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Strategy comparison failed: {str(e)}"
        )


@router.post("/ml-backtest")
async def ml_backtest_endpoint(request: MLBacktestRequest):
    """
    Run ML-driven backtesting using LSTM predictions for trading signals
    Returns predicted vs actual prices for visualization
    """
    try:
        print(f"ML Backtesting portfolio with {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Interval: {request.interval}")
        print(f"Signal threshold: {request.signal_threshold}")

        # Validate weights
        total_weight = sum(request.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Convert symbols to Yahoo Finance format if needed
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Create ML backtester
        backtester = MLTradingBacktester(
            symbols=yf_symbols,
            initial_capital=request.initial_investment,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval,
            signal_threshold=request.signal_threshold,
        )

        # Run backtest
        results = backtester.run_backtest()

        if not results.get("success"):
            raise HTTPException(
                status_code=500, detail="ML backtesting failed to complete successfully"
            )

        # Format portfolio history for frontend charting
        portfolio_history = results.get("portfolio_history", {})
        daily_values = [
            {
                "date": str(timestamp) if not isinstance(timestamp, str) else timestamp,
                "portfolio_value": value,
            }
            for timestamp, value in portfolio_history.items()
        ]

        # Get predictions log for comparison chart
        predictions_log = backtester.predictions_log

        # Group predictions by symbol for easier frontend processing
        predictions_by_symbol = {}
        for pred in predictions_log:
            symbol = pred["symbol"]
            if symbol not in predictions_by_symbol:
                predictions_by_symbol[symbol] = []

            # Convert timestamp to ISO format string
            timestamp = pred["timestamp"]
            if hasattr(timestamp, "isoformat"):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)

            predictions_by_symbol[symbol].append(
                {
                    "timestamp": timestamp_str,
                    "actual_price": pred.get(
                        "actual_next_price", pred.get("current_price", 0)
                    ),
                    "predicted_price": pred.get("predicted_price", 0),
                    "predicted_change": pred.get("predicted_change", 0),
                    "confidence": pred.get("confidence", 0),
                }
            )

        print(f"ML Backtest completed successfully")
        print(f"Final value: ${results['summary']['final_value']:,.2f}")
        print(f"Total return: {results['summary']['total_return']:.2f}%")
        print(f"Total trades: {results['trading_stats']['total_trades']}")

        # Format trade history timestamps for JSON serialization
        formatted_trade_history = []
        for trade in results.get("trade_history", []):
            timestamp = trade["timestamp"]
            if hasattr(timestamp, "isoformat"):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)

            formatted_trade_history.append(
                {
                    "timestamp": timestamp_str,
                    "symbol": trade["symbol"],
                    "action": trade["action"],
                    "coins": trade["coins"],
                    "price": trade["price"],
                    "value": trade["value"],
                    "predicted_change": trade.get("predicted_change", 0),
                    "confidence": trade.get("confidence", 0),
                }
            )

        return {
            "success": True,
            "backtest_results": {
                "summary": results["summary"],
                "trading_stats": results["trading_stats"],
                "daily_values": daily_values,
                "predictions_by_symbol": predictions_by_symbol,
                "trade_history": formatted_trade_history,
                "config": results.get("config", {}),
            },
            "summary": {
                "initial_investment": request.initial_investment,
                "final_value": results["summary"]["final_value"],
                "total_return": results["summary"]["total_return"],
                "annualized_return": results["summary"]["annualized_return"],
                "sharpe_ratio": results["summary"]["sharpe_ratio"],
                "max_drawdown": results["summary"]["max_drawdown"],
                "period": f"{request.start_date} to {request.end_date}",
                "total_trades": results["trading_stats"]["total_trades"],
                "win_rate": results["trading_stats"]["win_rate"],
            },
        }

    except ValueError as ve:
        print(f"Validation error in ML backtest: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in ML backtest endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ML backtesting failed: {str(e)}")


@router.post("/quick-backtest")
async def quick_backtest_endpoint(
    symbols: List[str], weights: Dict[str, float], days_back: int = 365
):
    """
    Quick backtest for the last N days (convenience endpoint)
    """
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Create backtester
        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=100000,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly",
        )

        result = backtester.generate_report(include_detailed_data=True)

        return {"success": True, "backtest_results": result, "period_days": days_back}

    except Exception as e:
        print(f"Error in quick backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")
