"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import CoinCard from "@/components/CoinCard";
import CoinHeader from "@/components/CoinHeader";
import { Coin } from "../types/coin";

export default function HomePage() {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "name">("price");
  const [filterBy, setFilterBy] = useState<"all" | "gainers" | "losers">("all");
  const [currency, setCurrency] = useState<"usd" | "bhd">("usd");
  const router = useRouter();
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

  const filteredAndSortedCoins = coins
    .filter((coin) => {
      const matchesSearch = coin.name.toLowerCase().includes(search.toLowerCase()) || coin.symbol.toLowerCase().includes(search.toLowerCase());
      if (filterBy === "gainers") return matchesSearch && coin.price_change_percentage_24h > 0;
      if (filterBy === "losers") return matchesSearch && coin.price_change_percentage_24h < 0;
      return matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === "price") return b.current_price - a.current_price;
      if (sortBy === "change") return b.price_change_percentage_24h - a.price_change_percentage_24h;
      if (sortBy === "name") return a.name.localeCompare(b.name);
      return 0;
    });

  const goToDetails = (id: string) => router.push(`/coin/${id}`);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* CoinHeader */}
      <CoinHeader
        search={search}
        setSearch={setSearch}
        sortBy={sortBy}
        setSortBy={setSortBy}
        filterBy={filterBy}
        setFilterBy={setFilterBy}
        currency={currency}
        setCurrency={setCurrency}
      />

      {/* Main Grid */}
      <main className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white/10 p-6 rounded-2xl animate-pulse h-64"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {filteredAndSortedCoins.map((coin, index) => (
              <CoinCard
                key={coin.id}
                coin={coin}
                currency={currency}
                onViewDetails={() => goToDetails(coin.id)}
                isTopGainer={index === 0} // Top coin after sorting
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
