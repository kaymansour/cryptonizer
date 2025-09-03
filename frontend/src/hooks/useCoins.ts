import { useState, useEffect, useRef } from "react";
import { Coin } from "../types/coin";

export const useCoins = () => {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [loading, setLoading] = useState(true);
  const prevPrices = useRef<Map<string, number>>(new Map());

  const fetchCoins = async () => {
    try {
      const res = await fetch("http://localhost:8000/coins");
      const data: Coin[] = await res.json();
      data.forEach((coin) => prevPrices.current.set(coin.id, coin.current_price));
      setCoins(data);
    } catch (err) {
      console.error("Error fetching coins:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoins();
    const interval = setInterval(fetchCoins, 30000);
    return () => clearInterval(interval);
  }, []);

  return { coins, loading, prevPrices };
};
