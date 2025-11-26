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
  const isUp = (coin.price_change_percentage_24h ?? 0) >= 0;

  return (
    <div
      className={`relative p-5 rounded-3xl backdrop-blur-2xl border shadow-md transition-all duration-300
      bg-gradient-to-br from-white/10 to-white/5 dark:from-zinc-800/40 dark:to-zinc-900/20
      hover:scale-[1.03] hover:shadow-xl hover:border-primary/40`}
    >

      {/* Top Gainer Badge */}
      {isTopGainer && (
        <span className="absolute -top-3 left-4 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full shadow-sm">
          Top Gainer
        </span>
      )}

      {/* Coin Image */}
      <div className="flex justify-center mb-4">
        <img
          src={coin.image}
          alt={coin.name}
          className="h-16 w-16 rounded-full shadow-lg transition-transform duration-300 hover:scale-110"
        />
      </div>

      {/* Name + Symbol */}
      <h2 className="text-xl font-bold text-center tracking-tight">{coin.name}</h2>
      <p className="text-xs text-muted-foreground text-center uppercase">{coin.symbol}</p>

      {/* Price */}
      <div className="text-center mt-4 mb-2">
        <p className="text-3xl font-extrabold tracking-tight">
          {currency === "usd" ? "$" : "BD "}
          {convertPrice(coin.current_price, currency).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>

        {/* Price Change Bubble */}
        <span
          className={`inline-block px-3 py-1 mt-2 rounded-full text-sm font-semibold shadow-sm 
          ${isUp ? "bg-green-500/20 text-green-500" : "bg-red-500/20 text-red-500"}`}
        >
          {(coin.price_change_percentage_24h ?? 0).toFixed(2)}%
        </span>
      </div>

      {/* Sparkline */}
      {coin.sparkline_in_24h && (
        <div className="mt-3">
          <Sparklines data={coin.sparkline_in_24h} width={160} height={60}>
            <SparklinesLine
              color={isUp ? "#22c55e" : "#ef4444"}
              style={{ strokeWidth: 3, fill: "none" }}
            />
          </Sparklines>
        </div>
      )}

      {/* Stats */}
      <div className="mt-4 text-sm text-muted-foreground space-y-2">
        {coin.market_cap && (
          <div className="flex justify-between">
            <span className="font-medium">Market Cap:</span>
            <span className="font-bold text-foreground">
              {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(coin.market_cap, currency))}
            </span>
          </div>
        )}

        {coin.total_volume && (
          <div className="flex justify-between">
            <span className="font-medium">Volume:</span>
            <span className="font-bold text-foreground">
              {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(coin.total_volume, currency))}
            </span>
          </div>
        )}
      </div>

      {/* Button */}
      <div className="mt-5">
   <button
  onClick={() => onViewDetails(coin.id)}
  className="w-full py-2 rounded-xl border bg-white/5 dark:bg-zinc-800/50
  hover:bg-gradient-to-r hover:from-purple-800/70 hover:to-indigo-900/70
  hover:text-white transition-all duration-300 font-semibold tracking-wide"
>
  View Details
</button>





      </div>
    </div>
  );
}
