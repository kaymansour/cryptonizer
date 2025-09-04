import { useState, useEffect, useRef } from "react";
import { Coin } from "../types/Coin";

/**
 * Custom hook to get cryptocurrency data from the backend
 * - Keeps track of coins and their prices
 * - Remembers old prices to compare later (up/down)
 * - Updates automatically every 10 seconds
 */
export const useCoins = () => {
  // List of coins from backend
  const [coins, setCoins] = useState<Coin[]>([]);
  
  // True if data is still loading, false when finished
  const [loading, setLoading] = useState(true);
  
  // Remember previous prices so we can compare with new prices
  // Format: prevPrices.current.get("bitcoin") → 57000
  const prevPrices = useRef<Map<string, number>>(new Map());

  /**
   * Fetch coin data from the backend
   */
  const fetchCoins = async () => {
    try {
      // Call the backend API to get coins
      const res = await fetch("http://localhost:8000/coins");
      
      // Convert the response into JavaScript object
      const data: Coin[] = await res.json();
      
      // Save current prices into prevPrices
      // Example: prevPrices.current.set("bitcoin", 57000)
      data.forEach((coin) => prevPrices.current.set(coin.id, coin.current_price));
      
      // Update the coins state so UI shows the latest coins
      setCoins(data);
    } catch (err) {
      // Show an error if API fails
      console.error("Error fetching coins:", err);
    } finally {
      // Loading is finished, set to false
      setLoading(false);
    }
  };

  /**
   * useEffect runs when the component loads
   * - Fetches coins initially
   * - Repeats fetch every 10 seconds
   * - Stops interval when component is removed
   */
  useEffect(() => {
    fetchCoins(); // fetch coins immediately

    // Repeat fetch every 10 seconds
    const interval = setInterval(fetchCoins, 30000);

    // Cleanup: stop the interval if component is unmounted
    return () => clearInterval(interval);
  }, []);

  // Return coins, loading state, and previous prices map
  return { coins, loading, prevPrices };
};
