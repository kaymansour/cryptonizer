/**
 * API utility functions for portfolio management
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SavePortfolioData {
  name: string;
  symbols: string[];
  weights: Record<string, number>;
  total_value: number;
  expected_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  objective?: string;
  period?: string;
  allocation?: Record<string, any>;
  // Investment preferences
  trading_frequency?: string;
  loss_tolerance?: string;
  profit_taking?: string;
  investment_horizon?: string;
  ml_config?: {
    signal_threshold?: number;
    max_position_size?: number;
    rsi_oversold?: number;
    rsi_overbought?: number;
    stop_loss_pct?: number;
    trailing_stop_pct?: number;
    trade_cooldown_periods?: number;
    take_profit_levels?: number[];
    interval?: string;
    use_trend_filter?: boolean;
    use_rsi_filter?: boolean;
    use_volume_filter?: boolean;
  };
}

export interface SavePortfolioResponse {
  success: boolean;
  portfolio_id: number;
  message: string;
}

/**
 * Save a portfolio to the database
 * @param data Portfolio data to save
 * @param clerkUserId Clerk user ID from authentication
 * @returns Response with portfolio ID
 */
export async function savePortfolio(
  data: SavePortfolioData,
  clerkUserId: string
): Promise<SavePortfolioResponse> {
  const response = await fetch(`${API_BASE_URL}/api/saved-portfolios`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Clerk-User-Id": clerkUserId,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to save portfolio");
  }

  return response.json();
}

/**
 * Get all portfolios for the current user
 * @param clerkUserId Clerk user ID from authentication
 * @param limit Maximum number of portfolios to fetch
 * @param offset Offset for pagination
 * @returns List of user portfolios
 */
export async function getUserPortfolios(
  clerkUserId: string,
  limit: number = 50,
  offset: number = 0
) {
  const response = await fetch(
    `${API_BASE_URL}/api/saved-portfolios?limit=${limit}&offset=${offset}`,
    {
      method: "GET",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch portfolios");
  }

  return response.json();
}

/**
 * Get a specific portfolio by ID
 * @param portfolioId Portfolio ID
 * @param clerkUserId Clerk user ID from authentication
 * @returns Portfolio data
 */
export async function getPortfolio(portfolioId: number, clerkUserId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/saved-portfolios/${portfolioId}`,
    {
      method: "GET",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch portfolio");
  }

  return response.json();
}

/**
 * Delete a portfolio
 * @param portfolioId Portfolio ID to delete
 * @param clerkUserId Clerk user ID from authentication
 */
export async function deletePortfolio(portfolioId: number, clerkUserId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/saved-portfolios/${portfolioId}`,
    {
      method: "DELETE",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete portfolio");
  }

  return response.json();
}

export interface SaveMLBacktestResultData {
  name: string;
  symbols: string[];
  weights: Record<string, number>;
  initial_investment: number;

  // Backtest Results
  final_value?: number;
  total_return?: number;
  annualized_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_trades?: number;
  buy_trades?: number;
  sell_trades?: number;
  win_rate?: number;
  total_realized_pnl?: number;
  avg_win?: number;
  avg_loss?: number;
  take_profit_trades?: number;
  stop_loss_trades?: number;
  trailing_stop_trades?: number;

  // Per-Symbol Results
  symbol_results?: Record<string, any>;

  // Trade History
  trade_history?: Array<Record<string, any>>;

  // ML Configuration
  interval?: string;
  signal_threshold?: number;
  max_position_size?: number;
  min_confidence?: number;
  rsi_oversold?: number;
  rsi_overbought?: number;
  stop_loss_pct?: number;
  trailing_stop_pct?: number;
  trade_cooldown_periods?: number;
  required_confirmations?: number;
  use_trend_filter?: boolean;
  use_rsi_filter?: boolean;
  use_volume_filter?: boolean;

  // Time Period
  start_date?: string;
  end_date?: string;
  backtest_period?: string;

  // Optional link to portfolio
  portfolio_id?: number;
}

export interface SaveMLBacktestResultResponse {
  success: boolean;
  result_id: number;
  message: string;
}

/**
 * Save an ML backtest result to the database
 * @param data ML backtest result data to save
 * @param clerkUserId Clerk user ID from authentication
 * @returns Response with result ID
 */
export async function saveMLBacktestResult(
  data: SaveMLBacktestResultData,
  clerkUserId: string
): Promise<SaveMLBacktestResultResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ml-backtest-results`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Clerk-User-Id": clerkUserId,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to save ML backtest result");
  }

  return response.json();
}

/**
 * Get all ML backtest results for the current user
 * @param clerkUserId Clerk user ID from authentication
 * @param limit Maximum number of results to fetch
 * @param offset Offset for pagination
 * @returns List of ML backtest results
 */
export async function getUserMLBacktestResults(
  clerkUserId: string,
  limit: number = 50,
  offset: number = 0
) {
  const response = await fetch(
    `${API_BASE_URL}/api/ml-backtest-results?limit=${limit}&offset=${offset}`,
    {
      method: "GET",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch ML backtest results");
  }

  return response.json();
}

/**
 * Get a specific ML backtest result by ID
 * @param resultId Result ID
 * @param clerkUserId Clerk user ID from authentication
 * @returns ML backtest result data
 */
export async function getMLBacktestResult(resultId: number, clerkUserId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/ml-backtest-results/${resultId}`,
    {
      method: "GET",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch ML backtest result");
  }

  return response.json();
}

/**
 * Delete an ML backtest result
 * @param resultId Result ID to delete
 * @param clerkUserId Clerk user ID from authentication
 */
export async function deleteMLBacktestResult(resultId: number, clerkUserId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/ml-backtest-results/${resultId}`,
    {
      method: "DELETE",
      headers: {
        "X-Clerk-User-Id": clerkUserId,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete ML backtest result");
  }

  return response.json();
}
