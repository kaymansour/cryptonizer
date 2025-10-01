import { useState, useEffect, useRef } from "react";
import { Coin } from "../types/Coin";

/**
 * Custom React hook for fetching and managing cryptocurrency data
 * Provides real-time coin data with caching, auto-refresh, and price tracking
 * 
 * @param currency - The currency to display prices in ("usd" or "bhd")
 * @returns Object containing coins data, loading state, error state, and price tracking references
 */
export const useCoins = (currency: "usd" | "bhd" = "usd") => {
  // State for storing the list of coins
  const [coins, setCoins] = useState<Coin[]>([]);
  // State to track loading status
  const [loading, setLoading] = useState(true);
  // State to track any errors during data fetching
  const [error, setError] = useState('');

  // useRef for persistent cache that doesn't trigger re-renders
  const cache = useRef<Coin[]>([]);
  
  // useRef to track previous prices for detecting price changes
  // Uses Map for O(1) lookups by coin ID
  const prevPrices = useRef<Map<string, number>>(new Map());

  /**
   * Fetches coins data from the backend API
   * Updates cache, sessionStorage, and tracks price changes
   */
  const fetchCoins = async () => {
    try {
      // Fetch coins data from backend API with specified currency
      const res = await fetch(`http://localhost:8000/coins?currency=${currency}`);
      const data: Coin[] = await res.json();

      // Validate response format
      if (!Array.isArray(data)) throw new Error("API did not return an array");

      // Update cache with new data
      cache.current = data;
      
      // Store current prices as previous prices for next comparison
      // This enables tracking price changes between updates
      data.forEach((coin) => prevPrices.current.set(coin.id, coin.current_price));

      // Update state with new coins data
      setCoins([...cache.current]);

      // Persist data in sessionStorage for faster initial load
      // Key includes currency to support multiple currency caching
      sessionStorage.setItem(`coins_${currency}`, JSON.stringify(cache.current));

      // Clear any previous errors on successful fetch
      setError('');
    } catch (err) {
      console.error("Error fetching coins:", err);
      setError('Failed to fetch coins');
    } finally {
      // Always set loading to false when fetch completes (success or error)
      setLoading(false);
    }
  };

  /**
   * useEffect hook for data fetching lifecycle
   * - Loads cached data on initial render
   * - Sets up automatic refresh interval
   * - Cleans up interval on unmount or currency change
   */
  useEffect(() => {
    // Check sessionStorage for cached data to provide instant initial load
    const cachedData = sessionStorage.getItem(`coins_${currency}`);
    
    if (cachedData) {
      // If cached data exists, parse and use it
      const parsed: Coin[] = JSON.parse(cachedData);
      cache.current = parsed;
      setCoins(parsed);
      setLoading(false); // Data is ready immediately from cache
    } else {
      // No cached data, fetch fresh data from API
      fetchCoins();
    }

    // Set up automatic refresh every 30 seconds (30000ms)
    // This keeps the price data current without manual refresh
    const interval = setInterval(fetchCoins, 30000);
    
    // Cleanup function: clear interval when component unmounts or currency changes
    // Prevents memory leaks and unnecessary API calls
    return () => clearInterval(interval);
  }, [currency ?? "usd"]); // Dependency array: re-run effect when currency changes

  /**
   * Return the hook's public interface
   * - coins: Current list of coins with latest data
   * - loading: Boolean indicating if initial data is being loaded
   * - error: Any error message from failed API calls
   * - prevPrices: Reference to previous prices for change detection
   * - cache: Reference to current cached data
   */
  return { coins, loading, error, prevPrices, cache };
};