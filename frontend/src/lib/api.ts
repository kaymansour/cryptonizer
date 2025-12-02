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
