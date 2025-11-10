"use client";
import { Sparklines, SparklinesLine } from "react-sparklines";
import { Coin } from "../types/Coin";
import { formatNumber, convertPrice } from "../utils/format";

interface CoinCardProps {
  coin: Coin;
  currency: "usd" | "bhd";
  onViewDetails: (id: string) => void;
  isTopGainer?: boolean;
}

export default function CoinCard({ coin, currency, onViewDetails, isTopGainer }: CoinCardProps) {
  const priceChange = coin.price_change_percentage_24h ?? 0;
  const currentPrice = coin.current_price ?? 0;
  const marketCap = coin.market_cap ?? null;
  const totalVolume = coin.total_volume ?? null;

  const isPositive = priceChange >= 0;
  const currencySymbol = currency === "usd" ? "$" : "BD ";

  return (
    <div
      className={`relative bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border transition-transform duration-300 hover:scale-[1.03] hover:shadow-2xl
      ${isPositive ? "border-emerald-400/40" : "border-red-400/40"}`}
    >
      {/* Top Gainer Badge */}
      {isTopGainer && (
        <span className="absolute -top-3 left-4 bg-gradient-to-r from-emerald-400 to-green-600 text-xs font-bold px-3 py-1 rounded-full shadow-md">
          🚀 Top Gainer
        </span>
      )}

      {/* Coin Image */}
      <div className="flex justify-center mb-4">
        <img
          src={coin.image}
          alt={coin.name}
          className="h-16 w-16 rounded-full shadow-md group-hover:scale-110 transition-transform"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://cdn-icons-png.flaticon.com/512/1490/1490858.png"; // fallback image
          }}
        />
      </div>

      {/* Coin Name & Symbol */}
      <h2 className="text-lg font-bold text-center">{coin.name || "Unknown"}</h2>
      <p className="text-sm text-gray-400 text-center uppercase">{coin.symbol || "N/A"}</p>

      {/* Price & 24h Change */}
      <div className="text-center mt-2">
        <p
          className={`text-2xl font-extrabold ${isPositive ? "text-emerald-400" : "text-red-400"}`}
        >
          {currencySymbol}
          {convertPrice(currentPrice, currency).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            isPositive ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
          }`}
        >
          {typeof priceChange === "number" ? priceChange.toFixed(2) : "0.00"}%
        </span>
      </div>

      {/* Sparkline chart */}
      {Array.isArray(coin.sparkline_in_24h) && coin.sparkline_in_24h.length > 0 && (
        <div className="mt-3">
          <Sparklines data={coin.sparkline_in_24h} width={160} height={50}>
            <SparklinesLine color={isPositive ? "#10b981" : "#ef4444"} />
          </Sparklines>
        </div>
      )}

      {/* Market Cap & Volume */}
      <div className="mt-3 text-xs text-gray-400 space-y-1">
        {marketCap !== null && (
          <div className="flex justify-between">
            <span>Market Cap:</span>
            <span>
              {currencySymbol}
              {formatNumber(convertPrice(marketCap, currency))}
            </span>
          </div>
        )}
        {totalVolume !== null && (
          <div className="flex justify-between">
            <span>Volume:</span>
            <span>
              {currencySymbol}
              {formatNumber(convertPrice(totalVolume, currency))}
            </span>
          </div>
        )}
      </div>

      {/* Action Button */}
      <div className="mt-4">
        <button
          onClick={() => onViewDetails(coin.id)}
          className="w-full py-2 bg-white/10 border border-white/20 rounded-xl hover:bg-white/20"
        >
          View Details
        </button>
      </div>
    </div>
  );
}
