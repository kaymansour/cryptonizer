"use client";

import { useSearchParams } from "next/navigation";
import { useCoin } from "@/hooks/useCoin";
import CoinDetail from "@/components/CoinDetail";

export default function CoinPage() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");
  const currency = searchParams.get("currency") as "usd" | "bhd" || "usd";
  
  const { coin, loading, error } = useCoin(id);

  if (loading) return <p className="text-white p-8">Loading...</p>;
  if (error) return <p className="text-white p-8">Error: {error}</p>;
  if (!coin) return <p className="text-white p-8">Coin not found</p>;

  return <CoinDetail coin={coin} currency={currency} />;
}