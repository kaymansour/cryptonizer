/**
 * Interface representing a cryptocurrency coin in the application
 * Defines the structure for cryptocurrency data used throughout the frontend
 * Maps to the data structure returned by the backend API and CoinGecko API
 */
export interface Coin {
  /**
   * Unique identifier for the cryptocurrency
   * Used as the primary key for API calls and caching
   * Example: "bitcoin", "ethereum", "cardano"
   */
  id: string;

  /**
   * Ticker symbol for the cryptocurrency (short code)
   * Typically 3-5 characters, uppercase in display
   * Example: "btc", "eth", "ada"
   */
  symbol: string;

  /**
   * Full name of the cryptocurrency
   * Example: "Bitcoin", "Ethereum", "Cardano"
   */
  name: string;

  /**
   * URL to the cryptocurrency's logo/image
   * Used for display in UI components
   * Example: "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
   */
  image: string;

  /**
   * Current trading price in the selected currency
   * Real-time value that updates frequently
   * Example: 45000.50 (for USD), 16950.25 (for BHD)
   */
  current_price: number;

  /**
   * Percentage price change over the last 24 hours
   * Positive values indicate price increase, negative values indicate decrease
   * Example: 2.5 (for 2.5% increase), -1.8 (for 1.8% decrease)
   */
  price_change_percentage_24h: number;

  /**
   * Optional: Array of price points for the sparkline chart (24-hour period)
   * Used for displaying mini-charts in lists and tables
   * Each number represents a price point at a specific time
   * Example: [45000, 45100, 44900, 45200, ...]
   */
  sparkline_in_24h?: number[];

  /**
   * Optional: Total market capitalization in the selected currency
   * Represents the total value of all circulating coins
   * Calculated as: current_price * circulating_supply
   * Example: 850000000000 (for $850B market cap)
   */
  market_cap?: number;

  /**
   * Optional: Total trading volume over the last 24 hours
   * Represents the total value of all trades in the past 24 hours
   * Indicator of trading activity and liquidity
   * Example: 25000000000 (for $25B volume)
   */
  total_volume?: number;

  /**
   * Optional: Global ranking by market capitalization
   * Lower numbers indicate higher market cap (1 = highest)
   * Used to show the coin's position relative to other cryptocurrencies
   * Example: 1 (Bitcoin), 2 (Ethereum), 7 (Cardano)
   */
  market_cap_rank?: number;   
}