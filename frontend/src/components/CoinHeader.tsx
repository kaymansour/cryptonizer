"use client";

interface CoinHeaderProps {
  search: string; // Current search text
  setSearch: (val: string) => void; // Function to update search
  sortBy: "price" | "change" | "name"; // Current sort type
  setSortBy: (val: "price" | "change" | "name") => void; // Function to update sort type
  filterBy: "all" | "gainers" | "losers"; // Current filter type
  setFilterBy: (val: "all" | "gainers" | "losers") => void; // Function to update filter type
  currency: "usd" | "bhd"; // Current currency
  setCurrency: (val: "usd" | "bhd") => void; // Function to update currency
  noResults?: boolean; // Optional prop to show "no coins found" message
}

/**
 * Header component for the coin dashboard
 * - Contains search input
 * - Contains sorting, filtering, and currency selection controls
 * - Sticky on top of the page with blurred background
 */
export default function CoinHeader({
  search,
  setSearch,
  sortBy,
  setSortBy,
  filterBy,
  setFilterBy,
  currency,
  setCurrency,
  noResults = false,
}: CoinHeaderProps) {
  return (
    <header className="sticky top-0 z-20 backdrop-blur-md bg-slate-900/80 border-b border-white/10 p-4 mb-6">
      <div className="container mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Search input */}
        <div className="w-full sm:w-auto flex flex-col">
          <input
            type="text"
            placeholder="🔍 Search coins..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-64 px-4 py-2 rounded-xl bg-slate-800/70 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          />
          {noResults && search.trim() !== "" && (
            <p className="text-red-400 text-sm mt-1">
              ❌ No coins found with the name "{search}"
            </p>
          )}
        </div>

        {/* Controls: Sort, Filter, Currency */}
        <div className="flex gap-3 items-center w-full sm:w-auto justify-center sm:justify-end">
          {/* Sort by dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-slate-800/70 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="price">Price</option>
            <option value="change">24h Change</option>
            <option value="name">Name</option>
          </select>

          {/* Filter dropdown */}
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-slate-800/70 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="all">All</option>
            <option value="gainers">Gainers</option>
            <option value="losers">Losers</option>
          </select>

          {/* Currency dropdown */}
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value as "usd" | "bhd")}
            className="px-3 py-2 rounded-lg bg-slate-800/70 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="usd">USD ($)</option>
            <option value="bhd">BHD (BD)</option>
          </select>
        </div>
      </div>
    </header>
  );
}
