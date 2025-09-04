"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import CoinCard from "@/components/CoinCard";
import CoinHeader from "@/components/CoinHeader";
import { useCoins } from "@/hooks/useCoins";
import { Coin } from "@/types/Coin";

export default function HomePage() {
  // Fetch the list of coins from a custom hook
  const { coins } = useCoins();

  // Next.js router for navigating to other pages
  const router = useRouter();

  // -------------------- Local State --------------------
  // Text entered in the search box
  const [search, setSearch] = useState("");

  // Which property to sort coins by: price, 24h change, or name
  const [sortBy, setSortBy] = useState<"price" | "change" | "name">("price");

  // Filter coins: show all, only gainers, or only losers
  const [filterBy, setFilterBy] = useState<"all" | "gainers" | "losers">("all");

  // Currency to display prices in: USD or BHD
  const [currency, setCurrency] = useState<"usd" | "bhd">("usd");

  // -------------------- Filtering and Sorting --------------------
  // First filter coins based on search and filter criteria, then sort them
  const filteredAndSortedCoins = coins
    .filter((coin: Coin) => {
      // Check if the coin's name or symbol matches the search text
      const matchesSearch =
        coin.name.toLowerCase().includes(search.toLowerCase()) ||
        coin.symbol.toLowerCase().includes(search.toLowerCase());

      // Apply the filter: gainers, losers, or all
      if (filterBy === "gainers") return matchesSearch && coin.price_change_percentage_24h > 0;
      if (filterBy === "losers") return matchesSearch && coin.price_change_percentage_24h < 0;
      return matchesSearch;
    })
    .sort((a: Coin, b: Coin) => {
      // Sort coins based on the selected property
      if (sortBy === "price") return b.current_price - a.current_price; // highest price first
      if (sortBy === "change") return b.price_change_percentage_24h - a.price_change_percentage_24h; // biggest gain first
      if (sortBy === "name") return a.name.localeCompare(b.name); // alphabetical
      return 0;
    });

  // -------------------- Navigation --------------------
  // Function to go to a specific coin's detail page
  const goToDetails = (id: string) => router.push(`/coin/${id}`);

  // -------------------- Render --------------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      
      {/* Header section with search, sort, filter, and currency selection */}
      <CoinHeader
        search={search}
        setSearch={setSearch}
        sortBy={sortBy}
        setSortBy={setSortBy}
        filterBy={filterBy}
        setFilterBy={setFilterBy}
        currency={currency}
        setCurrency={setCurrency}
        noResults={filteredAndSortedCoins.length === 0} // Show "No coins found" if the search/filter yields nothing
      />

      {/* Main content: grid of coin cards */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {filteredAndSortedCoins.map((coin: Coin, index: number) => (
            <CoinCard
              key={coin.id} // Unique key required by React for each item in a list
              coin={coin} // Pass coin data to CoinCard
              currency={currency} // Current currency to display prices
              onViewDetails={() => goToDetails(coin.id)} // Go to coin detail page when clicked
              isTopGainer={index === 0} // Highlight the first coin in the list as top gainer
            />
          ))}
        </div>
      </main>
    </div>
  );
}
