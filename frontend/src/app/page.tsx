"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import CoinCard from "@/components/CoinCard";
import CoinHeader from "@/components/CoinHeader";
import { useCoins } from "@/hooks/useCoins";
import { Coin } from "@/types/Coin";

export default function HomePage() {
  const { coins } = useCoins();
  const router = useRouter();

  // -------------------- Local State --------------------
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "name">("price");
  const [filterBy, setFilterBy] = useState<"all" | "gainers" | "losers">("all");
  const [currency, setCurrency] = useState<"usd" | "bhd">("usd");

  // -------------------- Filtering and Sorting --------------------
  const filteredAndSortedCoins = coins
    .filter((coin: Coin) => {
      const matchesSearch =
        coin.name.toLowerCase().includes(search.toLowerCase()) ||
        coin.symbol.toLowerCase().includes(search.toLowerCase());

      if (filterBy === "gainers") return matchesSearch && coin.price_change_percentage_24h > 0;
      if (filterBy === "losers") return matchesSearch && coin.price_change_percentage_24h < 0;
      return matchesSearch;
    })
    .sort((a: Coin, b: Coin) => {
      if (sortBy === "price") return b.current_price - a.current_price;
      if (sortBy === "change") return b.price_change_percentage_24h - a.price_change_percentage_24h;
      if (sortBy === "name") return a.name.localeCompare(b.name);
      return 0;
    });

  // -------------------- Navigation --------------------
  const goToDetails = (coin: Coin) => {
    // Pass both id and symbol in query parameters
    router.push(
      `/coin?id=${coin.id}&symbol=${coin.symbol}&currency=${currency}`
    );
  };

  // -------------------- Render --------------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Header with search, sort, filter, and currency */}
      <CoinHeader
        search={search}
        setSearch={setSearch}
        sortBy={sortBy}
        setSortBy={setSortBy}
        filterBy={filterBy}
        setFilterBy={setFilterBy}
        currency={currency}
        setCurrency={setCurrency}
        noResults={filteredAndSortedCoins.length === 0}
      />

      {/* Grid of coins */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {filteredAndSortedCoins.map((coin: Coin, index: number) => (
            <CoinCard
              key={coin.id}
              coin={coin}
              currency={currency}
              onViewDetails={() => goToDetails(coin)}
              isTopGainer={index === 0}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
