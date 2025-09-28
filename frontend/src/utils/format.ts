/**
 * Utility functions for formatting numbers and currency conversions
 * Provides consistent number formatting and currency conversion across the application
 */

/**
 * Formats large numbers into human-readable strings with appropriate suffixes
 * Converts numbers to compact notation (K for thousands, M for millions, B for billions)
 * 
 * @param num - The number to format (e.g., 1500, 2500000, 1800000000)
 * @returns Formatted string with appropriate suffix (K, M, B) and 1 decimal place
 * 
 * @example
 * formatNumber(1500)     // Returns "1.5K"
 * formatNumber(2500000)  // Returns "2.5M"
 * formatNumber(1800000000) // Returns "1.8B"
 * formatNumber(500)      // Returns "500.00"
 */
export const formatNumber = (num: number) => {
  // Check for billions (1,000,000,000+)
  if (num >= 1e9) return (num / 1e9).toFixed(1) + "B";
  
  // Check for millions (1,000,000+)
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  
  // Check for thousands (1,000+)
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  
  // For numbers less than 1000, return with 2 decimal places
  return num.toFixed(2);
};

/**
 * Converts USD prices to selected currency (supports USD and Bahraini Dinar)
 * Uses fixed conversion rate for USD to BHD
 * 
 * @param priceUsd - The price in US Dollars to convert
 * @param currency - The target currency ("usd" or "bhd")
 * @returns The converted price in the target currency
 * 
 * @example
 * convertPrice(100, "usd") // Returns 100 (no conversion)
 * convertPrice(100, "bhd") // Returns 37.6 (100 * 0.376)
 */
export const convertPrice = (priceUsd: number, currency: "usd" | "bhd") => {
  // Convert to Bahraini Dinar using fixed exchange rate
  if (currency === "bhd") return priceUsd * 0.376; // 1 USD = 0.376 BHD
  
  // Return original USD price if no conversion needed
  return priceUsd; // default USD
};