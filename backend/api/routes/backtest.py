"""
Backtesting routes for portfolio performance analysis
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from api.models.requests import (
    BacktestRequest,
    StrategyComparisonRequest,
    MLBacktestRequest,
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
        print(f"Max position size: {request.max_position_size}")
        print(f"RSI oversold: {request.rsi_oversold}")
        print(f"RSI overbought: {request.rsi_overbought}")
        print(f"Stop loss: {request.stop_loss_pct}")
        print(f"Trailing stop: {request.trailing_stop_pct}")

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

        # Create ML backtester with user preferences if provided
        ml_config = request.ml_config
        if ml_config:
            print(f"Using custom ML config from user preferences")
            backtester = MLTradingBacktester(
                symbols=yf_symbols,
                initial_capital=request.initial_investment,
                start_date=request.start_date,
                end_date=request.end_date,
                interval=ml_config.interval,
                signal_threshold=ml_config.signal_threshold,
                max_position_size=ml_config.max_position_size,
                rsi_oversold=ml_config.rsi_oversold,
                rsi_overbought=ml_config.rsi_overbought,
                stop_loss_pct=ml_config.stop_loss_pct,
                trailing_stop_pct=ml_config.trailing_stop_pct,
                use_trend_filter=ml_config.use_trend_filter,
                use_rsi_filter=ml_config.use_rsi_filter,
                use_volume_filter=ml_config.use_volume_filter,
                min_confidence=ml_config.min_confidence,
                trade_cooldown_periods=ml_config.trade_cooldown_periods,
                required_confirmations=ml_config.required_confirmations,
            )
            # Set take profit levels if backtester supports these attributes
            if hasattr(backtester, "take_profit_levels"):
                backtester.take_profit_levels = ml_config.take_profit_levels
            if hasattr(backtester, "take_profit_portions"):
                backtester.take_profit_portions = ml_config.take_profit_portions
        else:
            backtester = MLTradingBacktester(
                symbols=yf_symbols,
                initial_capital=request.initial_investment,
                start_date=request.start_date,
                end_date=request.end_date,
                interval=request.interval,
                signal_threshold=request.signal_threshold,
                max_position_size=request.max_position_size,
                rsi_oversold=request.rsi_oversold,
                rsi_overbought=request.rsi_overbought,
                stop_loss_pct=request.stop_loss_pct,
                trailing_stop_pct=request.trailing_stop_pct,
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


@router.post("/predict-next-candle")
async def predict_next_candle_endpoint(request: dict):
    """
    Enhanced prediction endpoint with intelligent trading recommendations
    """
    try:
        symbols = request.get("symbols", [])
        interval = request.get("interval", "1d")  # Daily candles for better accuracy
        signal_threshold = request.get("signal_threshold", 2.0)
        max_position_size = request.get("max_position_size", 0.6)
        rsi_oversold = request.get("rsi_oversold", 25)
        rsi_overbought = request.get("rsi_overbought", 60)
        stop_loss_pct = request.get("stop_loss_pct", 0.03)
        trailing_stop_pct = request.get("trailing_stop_pct", 0.05)

        print(
            f"Predicting next candle for {len(symbols)} symbols with intelligent analysis"
        )

        # Convert symbols to Yahoo Finance format
        yf_symbols = []
        for symbol in symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        predictions = {}

        for symbol in yf_symbols:
            try:
                # Import predictor
                import sys
                import os
                import yfinance as yf
                import pandas as pd
                import numpy as np
                from datetime import datetime, timedelta

                sys.path.append(
                    os.path.join(os.path.dirname(__file__), "..", "..", "models")
                )
                from intraday_predictor import IntradayPredictor

                # Initialize predictor
                predictor = IntradayPredictor(
                    symbol=symbol,
                    interval=interval,
                    lookback_periods=60 if interval == "1d" else 168,
                )

                # Load trained model
                predictor.load_model()

                # Get recent data - need enough for lookback + feature engineering
                # For daily candles: 60 periods + 60 for features = 120 days needed
                end_date = datetime.now()
                days_needed = (
                    180 if interval == "1d" else (60 if interval == "4h" else 30)
                )
                start_date = end_date - timedelta(days=days_needed)

                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False,
                )

                if data.empty:
                    print(f"No data returned for {symbol}")
                    continue

                # Handle different column formats from yfinance
                if isinstance(data.columns, pd.MultiIndex):
                    # For MultiIndex like [('Close', 'BTC-USD'), ('High', 'BTC-USD'), ...]
                    # Get the first level (price type) not the symbol name
                    data.columns = data.columns.get_level_values(0)

                # Ensure we have the required columns
                required_cols = ["Close", "High", "Low", "Open", "Volume"]
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    print(
                        f"Error: Missing columns for {symbol}: {missing_cols}. Available: {data.columns.tolist()}"
                    )
                    continue

                # Calculate technical indicators
                # RSI
                delta = data["Close"].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                data["RSI"] = 100 - (100 / (1 + rs))
                current_rsi = (
                    float(data["RSI"].iloc[-1])
                    if not pd.isna(data["RSI"].iloc[-1])
                    else 50
                )

                # SMA
                data["SMA_20"] = data["Close"].rolling(window=20).mean()
                data["SMA_50"] = data["Close"].rolling(window=50).mean()
                sma_20 = (
                    float(data["SMA_20"].iloc[-1])
                    if not pd.isna(data["SMA_20"].iloc[-1])
                    else data["Close"].iloc[-1]
                )
                sma_50 = (
                    float(data["SMA_50"].iloc[-1])
                    if not pd.isna(data["SMA_50"].iloc[-1])
                    else data["Close"].iloc[-1]
                )

                # Trend detection
                if sma_20 > sma_50 and data["Close"].iloc[-1] > sma_20:
                    trend = "UPTREND"
                    trend_strength = ((sma_20 - sma_50) / sma_50) * 100
                elif sma_20 < sma_50 and data["Close"].iloc[-1] < sma_20:
                    trend = "DOWNTREND"
                    trend_strength = ((sma_50 - sma_20) / sma_50) * 100
                else:
                    trend = "SIDEWAYS"
                    trend_strength = 0

                # Make prediction
                prediction = predictor.predict_next(data)
                current_price = prediction.get("current_price")
                predicted_price = prediction.get("predicted_price")
                predicted_change = prediction.get("predicted_change_percent", 0)

                # Intelligent signal classification
                signal = "HOLD"
                position_recommendation = 0.0
                action_reason = ""

                if predicted_change >= signal_threshold and current_rsi < rsi_oversold:
                    signal = "STRONG BUY"
                    position_recommendation = max_position_size
                    action_reason = f"Strong bullish signal: {predicted_change:+.2f}% prediction + oversold RSI ({current_rsi:.0f})"
                elif predicted_change >= signal_threshold * 0.5 and trend == "UPTREND":
                    signal = "BUY"
                    position_recommendation = max_position_size * 0.7
                    action_reason = f"Moderate buy: {predicted_change:+.2f}% prediction + uptrend confirmed"
                elif (
                    predicted_change <= -signal_threshold
                    and current_rsi > rsi_overbought
                ):
                    signal = "STRONG SELL"
                    position_recommendation = 1.0  # Close full position
                    action_reason = f"Strong bearish signal: {predicted_change:+.2f}% prediction + overbought RSI ({current_rsi:.0f})"
                elif (
                    predicted_change <= -signal_threshold * 0.5 and trend == "DOWNTREND"
                ):
                    signal = "SELL"
                    position_recommendation = 1.0
                    action_reason = f"Moderate sell: {predicted_change:+.2f}% prediction + downtrend confirmed"
                elif current_rsi < rsi_oversold and predicted_change > 0:
                    signal = "WATCH"
                    position_recommendation = max_position_size * 0.5
                    action_reason = f"Oversold opportunity: RSI {current_rsi:.0f}, predicted {predicted_change:+.2f}%"
                elif current_rsi > rsi_overbought and predicted_change < 0:
                    signal = "WATCH"
                    position_recommendation = 0.7
                    action_reason = f"Overbought risk: RSI {current_rsi:.0f}, predicted {predicted_change:+.2f}%"
                else:
                    signal = "HOLD"
                    position_recommendation = 0.0
                    action_reason = f"Neutral: {predicted_change:+.2f}% prediction, RSI {current_rsi:.0f}, {trend.lower()}"

                # Calculate risk metrics
                stop_loss_price = (
                    current_price * (1 - stop_loss_pct)
                    if signal in ["BUY", "STRONG BUY"]
                    else None
                )
                take_profit_price = (
                    current_price * (1 + (stop_loss_pct * 2))
                    if signal in ["BUY", "STRONG BUY"]
                    else None
                )

                predictions[symbol] = {
                    "current_price": current_price,
                    "predicted_price": predicted_price,
                    "predicted_change": predicted_change,
                    "signal": signal,
                    "rsi": current_rsi,
                    "trend": trend,
                    "trend_strength": round(trend_strength, 2),
                    "position_recommendation": position_recommendation,
                    "action_reason": action_reason,
                    "risk_metrics": {
                        "stop_loss_price": stop_loss_price,
                        "take_profit_price": take_profit_price,
                        "risk_reward_ratio": (
                            2.0 if signal in ["BUY", "STRONG BUY"] else None
                        ),
                    },
                }

                print(f"✓ {symbol}: {signal} - {action_reason}")

            except Exception as e:
                print(f"Failed to predict {symbol}: {str(e)}")
                import traceback

                traceback.print_exc()
                continue

        return {
            "success": True,
            "predictions": predictions,
            "interval": interval,
            "signal_threshold": signal_threshold,
        }

    except Exception as e:
        print(f"Error in predict next candle: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
