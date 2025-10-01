"use client";
import { Sparklines, SparklinesLine } from "react-sparklines";
import { Coin } from "../types/Coin";
import { formatNumber, convertPrice } from "../utils/format";

interface CoinCardProps {
  coin: Coin; // The coin data to display
  currency: "usd" | "bhd"; // Selected currency for prices
  onViewDetails: (id: string) => void; // Pass both id and symbol
  isTopGainer?: boolean; // Optional flag to highlight top gainers
}

export default function CoinCard({ coin, currency, onViewDetails, isTopGainer }: CoinCardProps) {
  return (
    <div
      className={`relative bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border transition-transform duration-300 hover:scale-[1.03] hover:shadow-2xl
      ${coin.price_change_percentage_24h >= 0 ? "border-emerald-400/40" : "border-red-400/40"}`}
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
        />
      </div>

      {/* Coin Name & Symbol */}
      <h2 className="text-lg font-bold text-center">{coin.name}</h2>
      <p className="text-sm text-gray-400 text-center uppercase">{coin.symbol}</p>

      {/* Price & 24h Change */}
      <div className="text-center mt-2">
        <p
          className={`text-2xl font-extrabold ${
            coin.price_change_percentage_24h >= 0 ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {currency === "usd" ? "$" : "BD "}
          {convertPrice(coin.current_price, currency).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            coin.price_change_percentage_24h >= 0
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-red-500/20 text-red-400"
          }`}
        >
          {coin.price_change_percentage_24h.toFixed(2)}%
        </span>
      </div>

      {/* Sparkline chart */}
      {coin.sparkline_in_24h && (
        <div className="mt-3">
          <Sparklines data={coin.sparkline_in_24h} width={160} height={50}>
            <SparklinesLine
              color={coin.price_change_percentage_24h >= 0 ? "#10b981" : "#ef4444"}
            />
          </Sparklines>
        </div>
      )}

      {/* Market Cap & Volume */}
      <div className="mt-3 text-xs text-gray-400 space-y-1">
        {coin.market_cap && (
          <div className="flex justify-between">
            <span>Market Cap:</span>
            <span>
              {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(coin.market_cap, currency))}
            </span>
          </div>
        )}
        {coin.total_volume && (
          <div className="flex justify-between">
            <span>Volume:</span>
            <span>
              {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(coin.total_volume, currency))}
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
