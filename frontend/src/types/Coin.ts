
// Info about a cryptocurrency coin
export interface Coin {
  id: string;                         // coin id (example: "bitcoin")
  symbol: string;                     // short name (example: "btc")
  name: string;                       // full name (example: "Bitcoin")
  image: string;                      // coin logo image
  current_price: number;              // current price in USD
  price_change_percentage_24h: number;// price change in last 24h (percent)
  sparkline_in_24h?: number[];        // small chart data for 24h
  market_cap?: number;                // total market value
  total_volume?: number;              // trading volume in 24h
}
