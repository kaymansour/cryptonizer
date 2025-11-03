"use client";

import { Coin } from "@/types/Coin";
import { convertPrice, formatNumber } from "@/utils/format";
import { Line } from "react-chartjs-2";
import "chart.js/auto";
import { useEffect, useState } from "react";
import { FiChevronDown, FiChevronUp, FiTrendingUp, FiTrendingDown } from "react-icons/fi";

interface CoinDetailProps {
  coin: Coin;
  currency: "usd" | "bhd";
}

export default function CoinDetail({ coin, currency }: CoinDetailProps) {
  const [coinDetail, setCoinDetail] = useState<Coin | null>(null);
  const [history, setHistory] = useState<number[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [description, setDescription] = useState<string>("No description available.");
  const [showDescription, setShowDescription] = useState<boolean>(false);
  const [imgError, setImgError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setFetchError(null);
        const res = await fetch(
          `http://localhost:8000/crypto/${coin.id}?currency=${currency}&days=7`
        );
        if (!res.ok) {
          throw new Error(`Failed to fetch data: ${res.status}`);
        }
        const data = await res.json();

        setDescription(data.description ?? "No description available.");
        setHistory(data.history?.map((p: number[]) => p[1]) ?? []);
        setLabels(data.history?.map((p: number[]) => new Date(p[0]).toLocaleDateString()) ?? []);

        setCoinDetail({
          ...coin,
          current_price: data.current_price,
          market_cap: data.market_cap,
          total_volume: data.total_volume,
          price_change_percentage_24h: data.price_change_percentage_24h,
          market_cap_rank: data.market_cap_rank,
        });
      } catch (err) {
        console.error("Error fetching coin details:", err);
        setFetchError(err instanceof Error ? err.message : "Failed to fetch coin details");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [coin.id, currency]);

  useEffect(() => {
    setImgError(false);
  }, [coin.id]);

  const currentPrice = coinDetail?.current_price ?? coin.current_price ?? 0;
  const marketCap = coinDetail?.market_cap ?? coin.market_cap ?? 0;
  const volume = coinDetail?.total_volume ?? coin.total_volume ?? 0;
  const change24h = coinDetail?.price_change_percentage_24h ?? coin.price_change_percentage_24h ?? 0;
  const marketCapRank = coinDetail?.market_cap_rank ?? coin.market_cap_rank;

  const isPositive = change24h >= 0;
  const currencySymbol = currency === "usd" ? "$" : "BD ";

  const chartData = {
    labels,
    datasets: [
      {
        label: `${coin.name} Price (${currency.toUpperCase()})`,
        data: history,
        borderColor: isPositive ? "#10b981" : "#ef4444",
        backgroundColor: isPositive ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
        tension: 0.4,
        fill: true,
        pointRadius: 0,
        borderWidth: 3,
        pointBackgroundColor: isPositive ? "#10b981" : "#ef4444",
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: "index" as const,
        intersect: false,
        backgroundColor: "rgba(15,23,42,0.9)",
        titleColor: "#e2e8f0",
        bodyColor: "#cbd5e1",
        borderColor: isPositive ? "#10b981" : "#ef4444",
        borderWidth: 1,
        callbacks: {
          label: function (context: any) {
            let value = context.parsed.y;
            if (currency === "bhd") {
              return `${currencySymbol}${value.toLocaleString(undefined, {
                minimumFractionDigits: 4,
                maximumFractionDigits: 6,
              })}`;
            } else {
              return `${currencySymbol}${value.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: value < 1 ? 6 : 2,
              })}`;
            }
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
          color: "rgba(255,255,255,0.1)",
        },
        ticks: {
          color: "#94a3b8",
          maxTicksLimit: 6,
        },
      },
      y: {
        grid: {
          color: "rgba(255,255,255,0.05)",
        },
        ticks: {
          color: "#94a3b8",
          callback: function (value: any) {
            if (typeof value === "number") {
              if (currency === "bhd") {
                return (
                  currencySymbol +
                  value.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 4,
                  })
                );
              } else {
                return (
                  currencySymbol +
                  value.toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })
                );
              }
            }
            return currencySymbol + value;
          },
        },
      },
    },
    interaction: {
      intersect: false,
      mode: "nearest" as const,
    },
  };

  if (loading) {
    return (
      <div className="min-h-screen p-4 bg-gradient-to-br from-slate-900 via-purple-900/30 to-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-emerald-500 mx-auto"></div>
          <p className="mt-4 text-slate-300">Loading coin details in {currency.toUpperCase()}...</p>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-screen p-4 bg-gradient-to-br from-slate-900 via-purple-900/30 to-slate-900 text-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-400 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-slate-200 mb-2">Failed to Load Data</h2>
          <p className="text-slate-400 mb-4">{fetchError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 bg-gradient-to-br from-slate-900 via-purple-900/30 to-slate-900 text-white">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-6 bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50">
          <div className="flex items-center gap-4">
            <div className="relative">
              {coin.image && !imgError ? (
                <img
                  src={coin.image}
                  alt={coin.name}
                  className="h-16 w-16 rounded-full shadow-lg border-2 border-slate-600"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="h-16 w-16 rounded-full shadow-lg border-2 border-slate-600 bg-gradient-to-br from-slate-700 to-slate-600 flex items-center justify-center">
                  <span className="text-slate-300 text-sm font-bold">
                    {coin.symbol?.slice(0, 3).toUpperCase() || "COIN"}
                  </span>
                </div>
              )}
              <div
                className={`absolute -bottom-1 -right-1 h-6 w-6 rounded-full border-2 border-slate-800 ${
                  isPositive ? "bg-emerald-500" : "bg-red-500"
                }`}
              >
                {isPositive ? (
                  <FiTrendingUp className="h-3 w-3 text-white mx-auto mt-1" />
                ) : (
                  <FiTrendingDown className="h-3 w-3 text-white mx-auto mt-1" />
                )}
              </div>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                {coin.name || "Unknown Coin"}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-lg text-slate-300 font-mono">
                  {coin.symbol?.toUpperCase() || "N/A"}
                </span>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-semibold ${
                    isPositive
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-red-500/20 text-red-300"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {change24h.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl md:text-3xl font-bold text-slate-100">
              {currencySymbol}
              {convertPrice(currentPrice, currency).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: currentPrice < 1 ? 6 : 2,
              })}
            </div>
            <div className="text-sm text-slate-400 mt-1">Displaying in {currency.toUpperCase()}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart Section */}
          <div className="lg:col-span-2 p-6 bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-300">Price Chart ({currency.toUpperCase()})</h3>
              <span className="text-sm text-slate-400">7-day history</span>
            </div>
            <div className="h-80">
              {history.length > 0 ? (
                <Line data={chartData} options={chartOptions} />
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400">
                  No chart data available in {currency.toUpperCase()}
                </div>
              )}
            </div>
          </div>

          {/* Stats Section */}
          <div className="space-y-4">
            <div className="p-6 bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50">
              <h3 className="text-lg font-semibold text-slate-300 mb-4">Market Statistics ({currency.toUpperCase()})</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400">Market Cap</span>
                  <span className="font-semibold text-slate-200">
                    {currencySymbol}
                    {formatNumber(convertPrice(marketCap, currency))}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400">24h Volume</span>
                  <span className="font-semibold text-slate-200">
                    {currencySymbol}
                    {formatNumber(convertPrice(volume, currency))}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-slate-400">24h Change</span>
                  <span className={`font-semibold ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                    {isPositive ? "+" : ""}
                    {change24h.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Rank & Info */}
            <div className="p-6 bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50">
              <h3 className="text-lg font-semibold text-slate-300 mb-2">Rank & Info</h3>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Market Cap Rank</span>
                <span className="font-semibold text-slate-200">#{marketCapRank || "N/A"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Description Section */}
        <div className="p-6 bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50">
          <button
            className="w-full flex justify-between items-center text-left group"
            onClick={() => setShowDescription(!showDescription)}
          >
            <h2 className="text-xl font-semibold text-slate-200 group-hover:text-white transition-colors">
              About {coin.name}
            </h2>
            <div
              className={`p-2 rounded-lg transition-all duration-300 group-hover:bg-slate-700/50 ${
                showDescription ? "bg-slate-700/50" : ""
              }`}
            >
              {showDescription ? (
                <FiChevronUp size={20} className="text-slate-400" />
              ) : (
                <FiChevronDown size={20} className="text-slate-400" />
              )}
            </div>
          </button>
          <div
            className={`overflow-hidden transition-all duration-500 ${
              showDescription ? "max-h-96 mt-4" : "max-h-0"
            }`}
          >
            <div className="prose prose-invert max-w-none">
              <p className="text-slate-300 leading-relaxed text-sm md:text-base">
                {description || "No description available for this cryptocurrency."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

