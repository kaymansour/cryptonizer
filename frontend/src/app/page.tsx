"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Select from 'react-select';
import CoinCard from "@/components/CoinCard";
import { useCoins } from "@/hooks/useCoins";
import { Coin } from "@/types/Coin";

// Options for react-select dropdowns
const sortOptions = [
  { value: "price", label: "Price" },
  { value: "change", label: "24h Change" },
  { value: "name", label: "Name" },
];

const filterOptions = [
  { value: "all", label: "All" },
  { value: "gainers", label: "Gainers" },
  { value: "losers", label: "Losers" },
];

const currencyOptions = [
  { value: "usd", label: "USD ($)" },
  { value: "bhd", label: "BHD (BD)" },
];

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
    <div className="min-h-screen bg-background text-foreground">
      {/* Search controls bar - appears below the header from layout */}
      <div className="sticky top-[65px] z-40 backdrop-blur-md bg-card/95 border-b border-border">
        <div className="container mx-auto px-6 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            {/* Search input */}
            <div className="w-full sm:w-auto flex flex-col">
              <input
                type="text"
                placeholder="Search coins..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full sm:w-64 px-4 py-2 rounded-xl bg-muted border border-input text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-sans"
              />
              {filteredAndSortedCoins.length === 0 && search.trim() !== "" && (
                <p className="text-destructive text-sm mt-1 font-sans">
                  ❌ No coins found with the name &ldquo;{search}&rdquo;
                </p>
              )}
            </div>

            {/* Controls: Sort, Filter, Currency */}
            <div className="flex gap-3 items-center w-full sm:w-auto justify-center sm:justify-end">
              {/* Sort by dropdown */}
              <Select
                instanceId="sort-select"
                className="react-select-container w-40"
                classNamePrefix="react-select"
                value={sortOptions.find(opt => opt.value === sortBy)}
                onChange={(option) => setSortBy(option?.value as "price" | "change" | "name")}
                options={sortOptions}
                isSearchable={false}
                menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                menuPosition="fixed"
                styles={{
                  control: (base) => ({
                    ...base,
                    backgroundColor: 'var(--muted)',
                    borderColor: 'var(--input)',
                    borderRadius: '0.5rem',
                    minHeight: '2.5rem',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'var(--ring)',
                    },
                  }),
                  singleValue: (base) => ({
                    ...base,
                    color: 'var(--foreground)',
                  }),
                  menuPortal: (base) => ({
                    ...base,
                    zIndex: 9999,
                  }),
                  menu: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                  }),
                  menuList: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    padding: '0.25rem',
                    borderRadius: '0.5rem',
                  }),
                  option: (base, state) => ({
                    ...base,
                    backgroundColor: state.isFocused
                      ? 'var(--accent)'
                      : state.isSelected
                        ? 'var(--primary)'
                        : 'var(--popover)',
                    color: state.isFocused
                      ? 'var(--accent-foreground)'
                      : 'var(--foreground)',
                    cursor: 'pointer',
                    opacity: 1,
                    '&:active': {
                      backgroundColor: 'var(--accent)',
                    },
                  }),
                  dropdownIndicator: (base) => ({
                    ...base,
                    color: 'var(--primary)',
                  }),
                  indicatorSeparator: () => ({
                    display: 'none',
                  }),
                }}
              />

              {/* Filter dropdown */}
              <Select
                instanceId="filter-select"
                className="react-select-container w-36"
                classNamePrefix="react-select"
                value={filterOptions.find(opt => opt.value === filterBy)}
                onChange={(option) => setFilterBy(option?.value as "all" | "gainers" | "losers")}
                options={filterOptions}
                isSearchable={false}
                menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                menuPosition="fixed"
                styles={{
                  control: (base) => ({
                    ...base,
                    backgroundColor: 'var(--muted)',
                    borderColor: 'var(--input)',
                    borderRadius: '0.5rem',
                    minHeight: '2.5rem',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'var(--ring)',
                    },
                  }),
                  singleValue: (base) => ({
                    ...base,
                    color: 'var(--foreground)',
                  }),
                  menuPortal: (base) => ({
                    ...base,
                    zIndex: 9999,
                  }),
                  menu: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                  }),
                  menuList: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    padding: '0.25rem',
                    borderRadius: '0.5rem',
                  }),
                  option: (base, state) => ({
                    ...base,
                    backgroundColor: state.isFocused
                      ? 'var(--accent)'
                      : state.isSelected
                        ? 'var(--primary)'
                        : 'var(--popover)',
                    color: state.isFocused
                      ? 'var(--accent-foreground)'
                      : 'var(--foreground)',
                    cursor: 'pointer',
                    opacity: 1,
                    '&:active': {
                      backgroundColor: 'var(--accent)',
                    },
                  }),
                  dropdownIndicator: (base) => ({
                    ...base,
                    color: 'var(--primary)',
                  }),
                  indicatorSeparator: () => ({
                    display: 'none',
                  }),
                }}
              />

              {/* Currency dropdown */}
              <Select
                instanceId="currency-select"
                className="react-select-container w-36"
                classNamePrefix="react-select"
                value={currencyOptions.find(opt => opt.value === currency)}
                onChange={(option) => setCurrency(option?.value as "usd" | "bhd")}
                options={currencyOptions}
                isSearchable={false}
                menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                menuPosition="fixed"
                styles={{
                  control: (base) => ({
                    ...base,
                    backgroundColor: 'var(--muted)',
                    borderColor: 'var(--input)',
                    borderRadius: '0.5rem',
                    minHeight: '2.5rem',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'var(--ring)',
                    },
                  }),
                  singleValue: (base) => ({
                    ...base,
                    color: 'var(--foreground)',
                  }),
                  menuPortal: (base) => ({
                    ...base,
                    zIndex: 9999,
                  }),
                  menu: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                  }),
                  menuList: (base) => ({
                    ...base,
                    backgroundColor: 'var(--popover)',
                    padding: '0.25rem',
                    borderRadius: '0.5rem',
                  }),
                  option: (base, state) => ({
                    ...base,
                    backgroundColor: state.isFocused
                      ? 'var(--accent)'
                      : state.isSelected
                        ? 'var(--primary)'
                        : 'var(--popover)',
                    color: state.isFocused
                      ? 'var(--accent-foreground)'
                      : 'var(--foreground)',
                    cursor: 'pointer',
                    opacity: 1,
                    '&:active': {
                      backgroundColor: 'var(--accent)',
                    },
                  }),
                  dropdownIndicator: (base) => ({
                    ...base,
                    color: 'var(--primary)',
                  }),
                  indicatorSeparator: () => ({
                    display: 'none',
                  }),
                }}
              />
            </div>
          </div>
        </div>
      </div>

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
