"""
Portfolio optimization routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from api.models.requests import PortfolioOptimizationRequest, EfficientFrontierRequest
from portfolio_optimizer import (
    optimize_crypto_portfolio,
    CryptoPortfolioOptimizer,
    optimize_crypto_portfolio_with_lstm,
)
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
from hybrid_predictor import HybridPredictor

router = APIRouter(prefix="/api")


class PredictionRequest(BaseModel):
    symbols: List[str]
    interval: str = "4h"
    steps: int = 7


@router.post("/optimize-portfolio")
async def optimize_portfolio(request: PortfolioOptimizationRequest):
    """
    Optimize a cryptocurrency portfolio using Modern Portfolio Theory
    """
    try:
        # Convert symbols to Yahoo Finance format (add -USD suffix if not present)
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Perform portfolio optimization
        result = optimize_crypto_portfolio(
            symbols=yf_symbols,
            total_value=request.total_value,
            objective=request.objective,
            period=request.period,
        )

        # Format response for frontend
        return {
            "success": True,
            "portfolio": {
                "expected_return": result["optimization"]["expected_return"],
                "volatility": result["optimization"]["volatility"],
                "sharpe_ratio": result["optimization"]["sharpe_ratio"],
                "weights": dict(result["optimization"]["weights"]),
                "objective": result["optimization"]["objective"],
            },
            "allocation": {
                "total_value": result["allocation"]["total_value"],
                "allocation": result["allocation"]["allocation"],
                "leftover": result["allocation"]["leftover"],
                "latest_prices": result["allocation"]["latest_prices"],
            },
            "metrics": {
                "var_95": result["metrics"]["var_95"],
                "max_drawdown": result["metrics"]["max_drawdown"],
            },
            "symbols": result["symbols"],
            "period": request.period,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio optimization failed: {str(e)}"
        )


@router.post("/optimize-portfolio-lstm")
async def optimize_portfolio_lstm(request: PortfolioOptimizationRequest):
    """
    Optimize portfolio with LSTM predictions and weight constraints
    """
    try:
        # Convert symbols to Yahoo Finance format
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        result = optimize_crypto_portfolio_with_lstm(
            symbols=yf_symbols,
            total_value=request.total_value,
            objective=request.objective,
            period=request.period,
            use_lstm=True,
            lstm_weight=0.6,  # 60% LSTM, 40% historical
            min_weight=0.05,  # 5% minimum
            max_weight=0.50,  # 50% maximum
        )

        return {"success": True, **result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/efficient-frontier")
async def get_efficient_frontier(request: EfficientFrontierRequest):
    """
    Calculate the efficient frontier for given cryptocurrencies
    """
    try:
        # Convert symbols to Yahoo Finance format
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Create optimizer and calculate efficient frontier
        optimizer = CryptoPortfolioOptimizer(yf_symbols, period=request.period)
        optimizer.fetch_price_data()
        optimizer.calculate_expected_returns()
        optimizer.calculate_risk_matrix()

        volatilities, returns = optimizer.calculate_efficient_frontier(
            request.num_portfolios
        )

        # Also get some reference portfolios
        max_sharpe = optimizer.optimize_portfolio("max_sharpe")
        min_vol = optimizer.optimize_portfolio("min_volatility")

        return {
            "success": True,
            "efficient_frontier": {"volatilities": volatilities, "returns": returns},
            "reference_portfolios": {
                "max_sharpe": {
                    "return": max_sharpe["expected_return"],
                    "volatility": max_sharpe["volatility"],
                    "sharpe_ratio": max_sharpe["sharpe_ratio"],
                },
                "min_volatility": {
                    "return": min_vol["expected_return"],
                    "volatility": min_vol["volatility"],
                    "sharpe_ratio": min_vol["sharpe_ratio"],
                },
            },
            "symbols": optimizer.symbols,
            "period": request.period,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Efficient frontier calculation failed: {str(e)}"
        )


@router.get("/portfolio/objectives")
async def get_optimization_objectives():
    """
    Get available portfolio optimization objectives
    """
    return {
        "objectives": [
            {
                "id": "max_sharpe",
                "name": "Maximum Sharpe Ratio",
                "description": "Maximize risk-adjusted returns",
            },
            {
                "id": "min_volatility",
                "name": "Minimum Volatility",
                "description": "Minimize portfolio risk",
            },
            {
                "id": "efficient_return",
                "name": "Efficient Return",
                "description": "Optimize for target return level",
            },
            {
                "id": "efficient_risk",
                "name": "Efficient Risk",
                "description": "Optimize for target risk level",
            },
        ]
    }


@router.post("/predict-next-candles")
async def predict_next_candles(request: PredictionRequest):
    """
    Get LSTM predictions for the next N candles for portfolio symbols
    """
    try:
        predictions = {}

        for symbol in request.symbols:
            # Ensure proper format
            if not symbol.endswith("-USD"):
                symbol = f"{symbol.upper()}-USD"
            else:
                symbol = symbol.upper()

            print(f"\n🔮 Predicting for {symbol}")

            try:
                # Use hybrid predictor (automatically selects best model)
                predictor = HybridPredictor(
                    symbol=symbol,
                    interval=request.interval,
                    lookback_periods=168,
                    auto_select=False,  # Use pre-configured optimal models
                )

                print(f"   Selected model: {predictor.selected_model}")
                print(f"   Loading model from: {predictor.predictor.model_path}")

                # Load model
                predictor.load_model()

                print(f"   Model loaded successfully")

                # Fetch MORE data to account for feature engineering dropna
                # Feature engineering drops ~60 rows, so we need 168 + 60 = ~230+ days
                days_to_fetch = (
                    365 if request.interval == "4h" else 730
                )  # Fetch more data
                print(f"   Fetching {days_to_fetch} days of data...")

                recent_data = predictor.predictor.fetch_intraday_data(days_back=days_to_fetch)
                print(f"   Fetched {len(recent_data)} candles (RAW data)")

                # Don't pre-process! predict_next() will call _add_features() internally
                # Validate we have enough RAW data
                if len(recent_data) < predictor.predictor.lookback_periods + 60:
                    raise ValueError(
                        f"Insufficient raw data. "
                        f"Need at least {predictor.predictor.lookback_periods + 60}, got {len(recent_data)}."
                    )

                # Multi-step prediction
                candle_predictions = []
                current_data = recent_data.copy()  # Keep RAW data

                for step in range(request.steps):
                    print(
                        f"   Predicting step {step + 1}/{request.steps} (input: {len(current_data)} candles)"
                    )

                    # Get prediction for next candle (predict_next will handle feature engineering)
                    pred = predictor.predict_next(current_data)

                    candle_predictions.append(
                        {
                            "step": step + 1,
                            "current_price": (
                                pred["current_price"]
                                if step == 0
                                else candle_predictions[step - 1]["predicted_price"]
                            ),
                            "predicted_price": pred["predicted_price"],
                            "predicted_change_percent": pred[
                                "predicted_change_percent"
                            ],
                            "signal": pred["signal"],
                            "candle_time": f"+{(step + 1) * (4 if request.interval == '4h' else 1)}h",
                        }
                    )

                    # For next iteration, append predicted price as if it happened
                    if step < request.steps - 1:
                        import pandas as pd

                        # Create new candle with predicted values (RAW format, no features)
                        last_row = current_data.iloc[-1].copy()
                        last_row["Close"] = pred["predicted_price"]
                        last_row["Open"] = pred["current_price"]
                        last_row["High"] = max(
                            pred["current_price"], pred["predicted_price"]
                        )
                        last_row["Low"] = min(
                            pred["current_price"], pred["predicted_price"]
                        )

                        # Append RAW candle (predict_next will re-calculate features)
                        new_row_df = pd.DataFrame([last_row])
                        current_data = pd.concat(
                            [current_data, new_row_df], ignore_index=True
                        )
                        print(
                            f"      Added simulated candle. New dataset size: {len(current_data)} candles"
                        )

                print(f"   ✅ Completed predictions for {symbol}")

                predictions[symbol] = {
                    "symbol": symbol.replace("-USD", ""),
                    "model_used": predictor.selected_model,
                    "current_price": candle_predictions[0]["current_price"],
                    "predictions": candle_predictions,
                    "overall_trend": (
                        "BULLISH"
                        if sum(
                            p["predicted_change_percent"] for p in candle_predictions
                        )
                        > 0
                        else "BEARISH"
                    ),
                    "confidence": (
                        "Medium"
                        if abs(
                            sum(
                                p["predicted_change_percent"]
                                for p in candle_predictions
                            )
                        )
                        > 2
                        else "Low"
                    ),
                }

            except FileNotFoundError as e:
                print(f"   ❌ Model file not found for {symbol}: {str(e)}")
                predictions[symbol] = {
                    "symbol": symbol.replace("-USD", ""),
                    "error": f"Model not trained yet. Please train LSTM model for {symbol}.",
                    "predictions": [],
                }
            except Exception as e:
                print(f"   ❌ Error predicting for {symbol}: {str(e)}")
                import traceback

                traceback.print_exc()
                predictions[symbol] = {
                    "symbol": symbol.replace("-USD", ""),
                    "error": str(e),
                    "predictions": [],
                }

        return {
            "success": True,
            "interval": request.interval,
            "steps": request.steps,
            "predictions": predictions,
            "note": "Multi-step predictions become less accurate over time. Use for short-term guidance only.",
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
