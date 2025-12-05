"""
Saved Portfolios API Routes
Handle saving, retrieving, and managing user portfolios
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict
from database.models.portfolios import (
    insert_portfolio,
    get_portfolio_by_id,
    get_portfolios_by_user,
    update_portfolio,
    delete_portfolio,
    count_user_portfolios,
)
from database.models.investment_preferences import (
    insert_investment_preferences,
    get_preferences_by_portfolio_id,
    update_investment_preferences,
    delete_preferences,
)

router = APIRouter(prefix="/api/saved-portfolios")


class SavePortfolioRequest(BaseModel):
    """Request to save a portfolio"""

    name: str
    symbols: List[str]
    weights: Dict[str, float]
    total_value: float
    expected_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    objective: Optional[str] = None
    period: Optional[str] = None
    allocation: Optional[Dict] = None
    # Investment preferences
    trading_frequency: Optional[str] = None
    loss_tolerance: Optional[str] = None
    profit_taking: Optional[str] = None
    investment_horizon: Optional[str] = None
    ml_config: Optional[Dict] = None


class UpdatePortfolioNameRequest(BaseModel):
    """Request to update portfolio name"""

    name: str


@router.post("")
async def save_portfolio(
    request: SavePortfolioRequest, x_clerk_user_id: Optional[str] = Header(None)
):
    """
    Save a portfolio for a user

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        # Verify user authentication
        if not x_clerk_user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Insert portfolio
        portfolio_id = insert_portfolio(
            clerk_id=x_clerk_user_id,
            name=request.name,
            symbols=request.symbols,
            weights=request.weights,
            total_value=request.total_value,
            expected_return=request.expected_return,
            volatility=request.volatility,
            sharpe_ratio=request.sharpe_ratio,
            objective=request.objective,
            period=request.period,
            allocation=request.allocation,
        )

        # Insert investment preferences if provided
        if any(
            [
                request.trading_frequency,
                request.loss_tolerance,
                request.profit_taking,
                request.investment_horizon,
                request.ml_config,
            ]
        ):
            ml_config = request.ml_config or {}
            insert_investment_preferences(
                portfolio_id=portfolio_id,
                trading_frequency=request.trading_frequency,
                loss_tolerance=request.loss_tolerance,
                profit_taking=request.profit_taking,
                investment_horizon=request.investment_horizon,
                signal_threshold=ml_config.get("signal_threshold", 2.0),
                max_position_size=ml_config.get("max_position_size", 0.6),
                rsi_oversold=ml_config.get("rsi_oversold", 25),
                rsi_overbought=ml_config.get("rsi_overbought", 60),
                stop_loss_pct=ml_config.get("stop_loss_pct", 0.03),
                trailing_stop_pct=ml_config.get("trailing_stop_pct", 0.05),
                trade_cooldown_periods=ml_config.get("trade_cooldown_periods", 6),
                take_profit_levels=ml_config.get(
                    "take_profit_levels", [0.03, 0.05, 0.08]
                ),
                interval=ml_config.get("interval", "1d"),  # Daily candles by default
                use_trend_filter=ml_config.get("use_trend_filter", True),
                use_rsi_filter=ml_config.get("use_rsi_filter", True),
                use_volume_filter=ml_config.get("use_volume_filter", True),
            )

        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "message": f"Portfolio '{request.name}' saved successfully",
        }

    except Exception as e:
        print(f"Error saving portfolio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save portfolio: {str(e)}"
        )


@router.get("")
async def get_user_portfolios(
    x_clerk_user_id: Optional[str] = Header(None), limit: int = 50, offset: int = 0
):
    """
    Get all portfolios for a user

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        # Verify user authentication
        if not x_clerk_user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get portfolios
        portfolios = get_portfolios_by_user(x_clerk_user_id, limit, offset)
        total_count = count_user_portfolios(x_clerk_user_id)

        # Enrich with preferences
        enriched_portfolios = []
        for portfolio in portfolios:
            preferences = get_preferences_by_portfolio_id(portfolio["id"])
            portfolio["preferences"] = preferences
            enriched_portfolios.append(portfolio)

        return {
            "success": True,
            "portfolios": enriched_portfolios,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        print(f"Error retrieving portfolios: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve portfolios: {str(e)}"
        )


@router.get("/{portfolio_id}")
async def get_portfolio(
    portfolio_id: int, x_clerk_user_id: Optional[str] = Header(None)
):
    """
    Get a specific portfolio by ID

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        # Verify user authentication
        if not x_clerk_user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get portfolio
        portfolio = get_portfolio_by_id(portfolio_id)

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Verify ownership
        if portfolio["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this portfolio"
            )

        # Get preferences
        preferences = get_preferences_by_portfolio_id(portfolio_id)
        portfolio["preferences"] = preferences

        return {"success": True, "portfolio": portfolio}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving portfolio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve portfolio: {str(e)}"
        )


@router.patch("/{portfolio_id}/name")
async def update_portfolio_name(
    portfolio_id: int,
    request: UpdatePortfolioNameRequest,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Update a portfolio's name

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        # Verify user authentication
        if not x_clerk_user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get portfolio to verify ownership
        portfolio = get_portfolio_by_id(portfolio_id)

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        if portfolio["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to modify this portfolio"
            )

        # Update name
        update_portfolio(portfolio_id, name=request.name)

        return {"success": True, "message": "Portfolio name updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating portfolio name: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update portfolio name: {str(e)}"
        )


@router.delete("/{portfolio_id}")
async def delete_saved_portfolio(
    portfolio_id: int, x_clerk_user_id: Optional[str] = Header(None)
):
    """
    Delete a portfolio

    Requires Clerk user ID in X-Clerk-User-Id header
    Cascade deletes associated investment preferences
    """
    try:
        # Verify user authentication
        if not x_clerk_user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get portfolio to verify ownership
        portfolio = get_portfolio_by_id(portfolio_id)

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        if portfolio["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this portfolio"
            )

        # Delete portfolio (preferences will be cascade deleted)
        delete_portfolio(portfolio_id)

        return {"success": True, "message": "Portfolio deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting portfolio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete portfolio: {str(e)}"
        )
