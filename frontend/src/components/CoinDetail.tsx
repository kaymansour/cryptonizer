"use client";

import { Coin } from "@/types/Coin";
import { convertPrice, formatNumber } from "@/utils/format";
import { Line } from "react-chartjs-2";
import "chart.js/auto";
import { useEffect, useState } from "react";

interface CoinDetailProps {
  coin: Coin;
  currency: "usd" | "bhd";
}

export default function CoinDetail({ coin, currency }: CoinDetailProps) {
  const [history, setHistory] = useState<number[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [description, setDescription] = useState<string>("");

  // Fetch historical prices and description
  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(
          `https://api.coingecko.com/api/v3/coins/${coin.id}?localization=false&market_data=true&sparkline=false`
        );
        const data = await res.json();
        setDescription(data.description?.en || "No description available.");

        const resHistory = await fetch(
          `https://api.coingecko.com/api/v3/coins/${coin.id}/market_chart?vs_currency=${currency}&days=7`
        );
        const dataHistory = await resHistory.json();

        setHistory(dataHistory.prices.map((p: number[]) => p[1]));
        setLabels(
          dataHistory.prices.map((p: number[]) =>
            new Date(p[0]).toLocaleDateString()
          )
        );
      } catch (err) {
        console.error(err);
      }
    }
    fetchData();
  }, [coin.id, currency]);

  // Safely get values or fallback to 0
  const currentPrice = coin.current_price ?? 0;
  const marketCap = coin.market_cap ?? 0;
  const volume = coin.total_volume ?? 0;
  const change24h = coin.price_change_percentage_24h ?? 0;

  const chartData = {
    labels,
    datasets: [
      {
        label: `${coin.name} Price (${currency.toUpperCase()})`,
        data: history,
        borderColor: "rgba(75,192,192,1)",
        fill: false,
      },
    ],
  };

  return (
    <div className="min-h-screen p-8 bg-slate-900 text-white">
      <div className="max-w-3xl mx-auto bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg">
        {/* Header */}
        <div className="flex items-center gap-4 mb-4">
          <img
            src={coin.image}
            alt={coin.name}
            className="h-16 w-16 rounded-full"
          />
          <h1 className="text-3xl font-bold">{coin.name}</h1>
          <span className="uppercase text-gray-300">{coin.symbol}</span>
        </div>

        {/* Info */}
        <div className="space-y-2 mb-6">
          <p>
            Current Price: {currency === "usd" ? "$" : "BD "}
            {convertPrice(currentPrice, currency).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>

          <p>24h Change: {change24h.toFixed(2)}%</p>

          {coin.market_cap !== undefined && (
            <p>
              Market Cap: {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(marketCap, currency))}
            </p>
          )}

          {coin.total_volume !== undefined && (
            <p>
              Volume: {currency === "usd" ? "$" : "BD "}
              {formatNumber(convertPrice(volume, currency))}
            </p>
          )}
        </div>

        {/* Graph */}
        <div className="bg-slate-800 p-4 rounded-xl mb-6">
          <h2 className="text-xl font-semibold mb-2">7-Day Price Chart</h2>
          <Line data={chartData} />
        </div>

        {/* Description */}
        <div className="bg-slate-800 p-4 rounded-xl">
          <h2 className="text-xl font-semibold mb-2">About {coin.name}</h2>
          <p className="text-gray-300 text-sm leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

