"use client";

import { useSearchParams } from "next/navigation";
import { useCoin } from "@/hooks/useCoinDetails";
import CoinDetail from "@/components/CoinDetail";
import LoadingSkeleton from "@/components/skeleton-coin";

export default function CoinPage() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");        // coin id
  const symbol = searchParams.get("symbol"); // optional coin symbol
  const currency = (searchParams.get("currency") as "usd" | "bhd") || "usd";

  // Pass either id or symbol to your hook
  const { coin, loading, error } = useCoin(id || symbol);

  if (loading) return <LoadingSkeleton />;
  if (error) return <p className="text-white p-8">Error: {error}</p>;
  if (!coin) return <p className="text-white p-8">Coin not found</p>;

  return <CoinDetail coin={coin} currency={currency} />;
}
