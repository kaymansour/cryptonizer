"""
Portfolio optimization routes
"""
from fastapi import APIRouter, HTTPException
from api.models.requests import PortfolioOptimizationRequest, EfficientFrontierRequest
from portfolio_optimizer import (
    optimize_crypto_portfolio,
    CryptoPortfolioOptimizer,
    optimize_crypto_portfolio_with_lstm,
)

router = APIRouter(prefix="/api")


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
