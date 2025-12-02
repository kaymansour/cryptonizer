"use client";

import { Coin } from "@/types/Coin";
import { formatNumber } from "@/utils/format";
import { Line } from "react-chartjs-2";
import "chart.js/auto";
import type { ChartOptions, TooltipItem } from "chart.js";
import { useEffect, useState } from "react";
import { FiChevronDown, FiChevronUp, FiTrendingUp, FiTrendingDown } from "react-icons/fi";
import { BentoCard, BentoGrid } from "@/components/ui/bento-grid";
import { DollarSign, BarChart3, Info } from "lucide-react";
import { Button } from "@/components/ui/button";

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
        console.log(`Fetching details for: ${coin.id} in ${currency}`);

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

  // API already returns prices in the requested currency, so don't re-convert them.
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

  const chartOptions: ChartOptions<"line"> = {
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
          label: function (context: TooltipItem<"line">) {
            const value = context.parsed.y ?? 0;
            // Format tooltip values based on the currency
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
          callback: function (value: string | number) {
            if (typeof value === 'number') {
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
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading coin details in {currency.toUpperCase()}...</p>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-destructive text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-foreground mb-2">Failed to Load Data</h2>
          <p className="text-muted-foreground mb-4">{fetchError}</p>
          <Button onClick={() => window.location.reload()} variant="outline" className="rounded-xl">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-6 bg-card backdrop-blur-xl rounded-2xl border border-border mb-8">
          <div className="flex items-center gap-4">
            <div className="relative">
              {coin.image && !imgError ? (
                <img
                  src={coin.image}
                  alt={coin.name}
                  className="h-16 w-16 rounded-full shadow-lg border-2 border-border"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="h-16 w-16 rounded-full shadow-lg border-2 border-border bg-linear-to-br from-muted to-muted-foreground/20 flex items-center justify-center">
                  <span className="text-muted-foreground text-sm font-bold">
                    {coin.symbol?.slice(0, 3).toUpperCase() || 'COIN'}
                  </span>
                </div>
              )}
              <div
                className={`absolute -bottom-1 -right-1 h-6 w-6 rounded-full border-2 border-background ${isPositive ? "bg-green-500" : "bg-red-500"
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
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">
                {coin.name || 'Unknown Coin'}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-lg text-muted-foreground font-mono">
                  {coin.symbol?.toUpperCase() || 'N/A'}
                </span>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-semibold ${isPositive
                      ? "bg-green-500/20 text-green-600 dark:text-green-400"
                      : "bg-red-500/20 text-red-600 dark:text-red-400"
                    }`}
                >
                  {isPositive ? "+" : ""}
                  {change24h.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl md:text-3xl font-bold text-foreground">
              {currencySymbol}
              {currentPrice.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: currentPrice < 1 ? 6 : 2,
              })}
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              Displaying in {currency.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Bento Grid Layout */}
        <BentoGrid className="lg:grid-rows-2 mb-8">
          {/* Price Chart Card - 2 columns */}
          <BentoCard
            name="Price Chart"
            className="lg:col-start-1 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={BarChart3}
            description={`7-day price history in ${currency.toUpperCase()}`}
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 h-80 mt-4">
              {history.length > 0 ? (
                <Line data={chartData} options={chartOptions} />
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  No chart data available in {currency.toUpperCase()}
                </div>
              )}
            </div>
          </BentoCard>

          {/* Market Statistics Card */}
          <BentoCard
            name="Market Statistics"
            className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={DollarSign}
            description={`Key metrics in ${currency.toUpperCase()}`}
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 space-y-4 mt-4">
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-muted-foreground">Market Cap</span>
                <span className="font-semibold text-foreground">
                  {currencySymbol}
                  {formatNumber(marketCap)}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-muted-foreground">24h Volume</span>
                <span className="font-semibold text-foreground">
                  {currencySymbol}
                  {formatNumber(volume)}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-muted-foreground">24h Change</span>
                <span
                  className={`font-semibold ${isPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                    }`}
                >
                  {isPositive ? "+" : ""}
                  {change24h.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">Market Rank</span>
                <span className="font-semibold text-foreground">
                  #{marketCapRank || 'N/A'}
                </span>
              </div>
            </div>
          </BentoCard>

          {/* About/Description Card - Full width */}
          <BentoCard
            name={`About ${coin.name}`}
            className="lg:col-start-1 lg:col-end-4 lg:row-start-2 lg:row-end-3 border-primary/40"
            Icon={Info}
            description="Learn more about this cryptocurrency"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4">
              <button
                className="w-full flex justify-between items-center text-left group mb-4"
                onClick={() => setShowDescription(!showDescription)}
              >
                <span className="text-sm font-semibold text-primary">
                  {showDescription ? "Hide Details" : "Show Details"}
                </span>
                <div className="p-2 rounded-lg transition-all duration-300 group-hover:bg-accent">
                  {showDescription ? (
                    <FiChevronUp size={20} className="text-muted-foreground" />
                  ) : (
                    <FiChevronDown size={20} className="text-muted-foreground" />
                  )}
                </div>
              </button>
              <div
                className={`overflow-hidden transition-all duration-500 ${showDescription ? "max-h-96 overflow-y-auto custom-scrollbar" : "max-h-0"
                  }`}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-muted-foreground leading-relaxed">
                    {description || "No description available for this cryptocurrency."}
                  </p>
                </div>
              </div>
            </div>
          </BentoCard>
        </BentoGrid>
      </div>
    </div>
  );
}

