"use client";

interface CoinHeaderProps {
  search: string;
  setSearch: (val: string) => void;
  sortBy: "price" | "change" | "name";
  setSortBy: (val: "price" | "change" | "name") => void;
  filterBy: "all" | "gainers" | "losers";
  setFilterBy: (val: "all" | "gainers" | "losers") => void;
  currency: "usd" | "bhd";
  setCurrency: (val: "usd" | "bhd") => void;
  noResults?: boolean;
}

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
    <header className="sticky top-0 z-20 backdrop-blur-xl bg-background/80 border-b border-border px-4 py-3 mb-6">
      <div className="container mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">

        {/* Search Input */}
        <div className="w-full sm:w-auto flex flex-col">
          <input
            type="text"
            placeholder="Search coins..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-72 px-4 py-2.5 rounded-xl bg-muted/30 border border-border text-foreground
            placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          />

          {noResults && search.trim() !== "" && (
            <p className="text-destructive text-sm mt-1">
              No results for “{search}”
            </p>
          )}
        </div>

        {/* Controls */}
        <div className="flex gap-3 items-center w-full sm:w-auto justify-center sm:justify-end">

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2.5 rounded-xl bg-muted/30 border border-border text-foreground 
            focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            <option value="price">Price</option>
            <option value="change">24h Change</option>
            <option value="name">Name</option>
          </select>

          {/* Filter */}
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as any)}
            className="px-3 py-2.5 rounded-xl bg-muted/30 border border-border text-foreground 
            focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            <option value="all">All</option>
            <option value="gainers">Top Gainers</option>
            <option value="losers">Top Losers</option>
          </select>

          {/* Currency */}
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value as "usd" | "bhd")}
            className="px-3 py-2.5 rounded-xl bg-muted/30 border border-border text-foreground 
            focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            <option value="usd">USD ($)</option>
            <option value="bhd">BHD (BD)</option>
          </select>

        </div>
      </div>
    </header>
  );
}
