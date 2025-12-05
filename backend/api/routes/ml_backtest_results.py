"""
ML Backtest Results API Routes
Handle saving, retrieving, and managing ML backtest results
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict
from database.models.ml_backtest_results import (
    insert_ml_backtest_result,
    get_ml_backtest_result_by_id,
    get_ml_backtest_results_by_user,
    get_ml_backtest_results_by_portfolio,
    update_ml_backtest_result_name,
    delete_ml_backtest_result,
    count_user_ml_backtest_results,
)

router = APIRouter(prefix="/api/ml-backtest-results")


class SaveMLBacktestResultRequest(BaseModel):
    """Request to save an ML backtest result"""

    name: str
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float

    # Backtest Results
    final_value: Optional[float] = None
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    buy_trades: Optional[int] = None
    sell_trades: Optional[int] = None
    win_rate: Optional[float] = None
    total_realized_pnl: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    take_profit_trades: Optional[int] = None
    stop_loss_trades: Optional[int] = None
    trailing_stop_trades: Optional[int] = None

    # Per-Symbol Results (predictions, trades per symbol, etc.)
    symbol_results: Optional[Dict] = None

    # Trade History
    trade_history: Optional[List[Dict]] = None

    # ML Configuration
    interval: Optional[str] = "1d"
    signal_threshold: Optional[float] = 1.5
    max_position_size: Optional[float] = 0.6
    min_confidence: Optional[float] = 0.35
    rsi_oversold: Optional[float] = 25
    rsi_overbought: Optional[float] = 60
    stop_loss_pct: Optional[float] = 0.03
    trailing_stop_pct: Optional[float] = 0.05
    trade_cooldown_periods: Optional[int] = 6
    required_confirmations: Optional[int] = 2
    use_trend_filter: Optional[bool] = True
    use_rsi_filter: Optional[bool] = True
    use_volume_filter: Optional[bool] = True

    # Time Period
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    backtest_period: Optional[str] = None

    # Optional link to portfolio
    portfolio_id: Optional[int] = None


class UpdateNameRequest(BaseModel):
    """Request to update backtest result name"""

    name: str


@router.post("")
async def save_ml_backtest_result(
    request: SaveMLBacktestResultRequest,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Save an ML backtest result for a user

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please sign in to save backtest results.",
            )

        # Check user's backtest result count (limit to 100 per user)
        result_count = count_user_ml_backtest_results(x_clerk_user_id)
        if result_count >= 100:
            raise HTTPException(
                status_code=400,
                detail="Maximum number of saved backtest results reached (100). Please delete some old results.",
            )

        # Insert the backtest result
        result_id = insert_ml_backtest_result(
            clerk_id=x_clerk_user_id,
            name=request.name,
            symbols=request.symbols,
            weights=request.weights,
            initial_investment=request.initial_investment,
            final_value=request.final_value,
            total_return=request.total_return,
            annualized_return=request.annualized_return,
            volatility=request.volatility,
            sharpe_ratio=request.sharpe_ratio,
            max_drawdown=request.max_drawdown,
            total_trades=request.total_trades,
            buy_trades=request.buy_trades,
            sell_trades=request.sell_trades,
            win_rate=request.win_rate,
            total_realized_pnl=request.total_realized_pnl,
            avg_win=request.avg_win,
            avg_loss=request.avg_loss,
            take_profit_trades=request.take_profit_trades,
            stop_loss_trades=request.stop_loss_trades,
            trailing_stop_trades=request.trailing_stop_trades,
            symbol_results=request.symbol_results,
            trade_history=request.trade_history,
            interval=request.interval or "1d",
            signal_threshold=request.signal_threshold or 1.5,
            max_position_size=request.max_position_size or 0.6,
            min_confidence=request.min_confidence or 0.35,
            rsi_oversold=request.rsi_oversold or 25,
            rsi_overbought=request.rsi_overbought or 60,
            stop_loss_pct=request.stop_loss_pct or 0.03,
            trailing_stop_pct=request.trailing_stop_pct or 0.05,
            trade_cooldown_periods=request.trade_cooldown_periods or 6,
            required_confirmations=request.required_confirmations or 2,
            use_trend_filter=(
                request.use_trend_filter
                if request.use_trend_filter is not None
                else True
            ),
            use_rsi_filter=(
                request.use_rsi_filter if request.use_rsi_filter is not None else True
            ),
            use_volume_filter=(
                request.use_volume_filter
                if request.use_volume_filter is not None
                else True
            ),
            start_date=request.start_date,
            end_date=request.end_date,
            backtest_period=request.backtest_period,
            portfolio_id=request.portfolio_id,
        )

        return {
            "success": True,
            "result_id": result_id,
            "message": f"ML backtest result '{request.name}' saved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving ML backtest result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save backtest result: {str(e)}",
        )


@router.get("")
async def get_user_ml_backtest_results(
    x_clerk_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """
    Get all ML backtest results for a user

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please sign in to view backtest results.",
            )

        results = get_ml_backtest_results_by_user(x_clerk_user_id, limit, offset)
        total_count = count_user_ml_backtest_results(x_clerk_user_id)

        return {
            "success": True,
            "results": results,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching ML backtest results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch backtest results: {str(e)}",
        )


@router.get("/by-portfolio/{portfolio_id}")
async def get_portfolio_ml_backtest_results(
    portfolio_id: int,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Get all ML backtest results linked to a specific portfolio

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
            )

        results = get_ml_backtest_results_by_portfolio(portfolio_id)

        return {
            "success": True,
            "results": results,
            "portfolio_id": portfolio_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching portfolio backtest results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch backtest results: {str(e)}",
        )


@router.get("/{result_id}")
async def get_ml_backtest_result(
    result_id: int,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Get a specific ML backtest result by ID

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
            )

        result = get_ml_backtest_result_by_id(result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Backtest result not found",
            )

        # Verify ownership
        if result["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this backtest result",
            )

        return {
            "success": True,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching ML backtest result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch backtest result: {str(e)}",
        )


@router.patch("/{result_id}/name")
async def update_backtest_result_name(
    result_id: int,
    request: UpdateNameRequest,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Update an ML backtest result's name

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
            )

        # Get the result to verify ownership
        result = get_ml_backtest_result_by_id(result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Backtest result not found",
            )

        if result["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to modify this backtest result",
            )

        # Update the name
        success = update_ml_backtest_result_name(result_id, request.name)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update backtest result name",
            )

        return {
            "success": True,
            "message": f"Backtest result renamed to '{request.name}'",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating backtest result name: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update backtest result: {str(e)}",
        )


@router.delete("/{result_id}")
async def delete_saved_ml_backtest_result(
    result_id: int,
    x_clerk_user_id: Optional[str] = Header(None),
):
    """
    Delete an ML backtest result

    Requires Clerk user ID in X-Clerk-User-Id header
    """
    try:
        if not x_clerk_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
            )

        # Get the result to verify ownership
        result = get_ml_backtest_result_by_id(result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Backtest result not found",
            )

        if result["clerk_id"] != x_clerk_user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this backtest result",
            )

        # Delete the result
        success = delete_ml_backtest_result(result_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete backtest result",
            )

        return {
            "success": True,
            "message": "Backtest result deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting backtest result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete backtest result: {str(e)}",
        )
