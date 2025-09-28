"use client";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);

import { useEffect, useState } from "react";
import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";
import TopBanner from "@/components/TopBanner";
import Loading from "@/components/loading";
import Backtomain from "@/components/backtomain";

interface CryptoData {
  name: string;
  symbol: string;
  current_price: number;
  market_cap: number;
  total_volume: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  last_updated: string;
  image: string;
}

interface PredictionData {
  history: {
    dates: string[];
    actual: number[];
    predicted: number[];
  };
  future: {
    days: number[];
    prices: number[];
    trend: string;
  };
  plots: {
    close_price: string;
    moving_average: string;
    prediction: string;
    future: string;
  };
}

export default function PredictPage() {
  const [backendStatus, setBackendStatus] = useState<
    "loading" | "success" | "error"
  >("loading");
  const [cryptoData, setCryptoData] = useState<CryptoData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/status")
      .then((res) => {
        if (!res.ok) throw new Error("Backend not responding");
        return res.json();
      })
      .then((data) => {
        setBackendStatus("success");
      })
      .catch(() => {
        setBackendStatus("error");
      });
  }, []);

  const handleSearch = async (symbol: string) => {
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await fetch(`http://localhost:8000/crypto/${symbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to fetch cryptocurrency data");
      }
      const data: CryptoData = await response.json();
      setCryptoData(data);

      const predictionRes = await fetch(
        `http://localhost:8000/predict/${symbol}`
      );
      if (!predictionRes.ok) {
        const errorData = await predictionRes.json();
        throw new Error(errorData.error || "Failed to fetch prediction");
      }
      const predictionData: PredictionData = await predictionRes.json();
      setPrediction(predictionData);
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
      setCryptoData(null);
      setPrediction(null);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: num < 1 ? 6 : 2,
    }).format(num);

  const formatPercentage = (num: number) =>
    new Intl.NumberFormat("en-US", {
      style: "percent",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: "exceptZero",
    }).format(num / 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-indigo-900 text-white">
      <main className="container mx-auto p-4">
        {/* Backend Status */}
        {backendStatus === "loading" && (
          <p className="text-center text-gray-400">
            Checking backend connection...
          </p>
        )}
        {backendStatus === "error" && (
          <p className="text-center text-red-500 font-semibold">
            ❌ Error: Could not connect to backend. Make sure FastAPI is running on port 8000.
          </p>
        )}

        {/* Signed Out */}
        <SignedOut>
          <div className="mt-20 flex flex-col items-center space-y-6">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Crypto Learning Dashboard
            </h1>
            <p className="text-gray-300 max-w-md text-center">
              Sign in to explore live cryptocurrency prices and see how machine learning models predict future trends.
            </p>
            <SignInButton>
              <button className="mt-4 px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-700 text-white rounded-xl hover:from-cyan-700 hover:to-blue-800 transition font-semibold">
                Sign In
              </button>
            </SignInButton>
          </div>
        </SignedOut>

        {/* Signed In */}
        <SignedIn>
          <div className="flex flex-col items-center space-y-4 w-full">
            {/* Welcome & Search */}
            {!cryptoData && !loading && backendStatus === "success" && (
              <div className="w-full max-w-2xl">
                <div className="mb-8 text-center">
                  <h2 className="text-3xl font-bold mb-2 text-cyan-300">Welcome to the Crypto Prediction Dashboard</h2>
                  <p className="text-gray-300 mb-4">
                    Enter a cryptocurrency symbol (like <span className="font-mono text-cyan-200">BTC</span> or <span className="font-mono text-cyan-200">ETH</span>) to see live data and AI-powered price predictions.
                  </p>
                </div>
                <TopBanner onSearch={handleSearch} />
              </div>
            )}

            {/* Loading */}
            {loading && <Loading />}

            {/* Error */}
            {error && (
              <div className="mt-8 p-4 bg-red-900/50 rounded-xl max-w-2xl mx-auto text-center">
                <p className="text-red-300">{error}</p>
              </div>
            )}

            {/* Crypto Snapshot */}
            {cryptoData && (
              <>
                <div className="flex items-center justify-center mt-8 mb-4 space-x-4">
                  <Backtomain />
                  <h2 className="text-3xl font-bold text-center m-0">
                    📊 <span className="text-cyan-300">Prediction Dashboard</span> for {cryptoData.name} ({cryptoData.symbol.toUpperCase()})
                  </h2>
                </div>
                <div className="mb-8 text-center text-gray-300">
                  <span className="inline-block bg-indigo-700/30 px-4 py-2 rounded-lg">
                    <strong>Step 1:</strong> Review the latest market data.<br />
                    <strong>Step 2:</strong> Explore predictions and trends below.
                  </span>
                </div>
                <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 max-w-2xl w-full border border-indigo-500/30">
                  <div className="flex items-center mb-6">
                    <img
                      src={cryptoData.image}
                      alt={cryptoData.name}
                      className="h-16 w-16 mr-4"
                    />
                    <div>
                      <h2 className="text-2xl font-bold">
                        {cryptoData.name} ({cryptoData.symbol.toUpperCase()})
                      </h2>
                      <p className="text-gray-400 text-sm">
                        Last updated: {new Date(cryptoData.last_updated).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-700/50 p-4 rounded-lg">
                      <h3 className="text-gray-300 text-sm mb-1 flex items-center">
                        Current Price 💰
                        <span title="The latest price for one coin." className="ml-2 text-xs text-cyan-400 cursor-help">?</span>
                      </h3>
                      <p className="text-2xl font-bold text-cyan-300">
                        {formatNumber(cryptoData.current_price)}
                      </p>
                      <p className="text-xs text-gray-400">
                        The most recent value for this cryptocurrency.
                      </p>
                    </div>
                    <div className="bg-gray-700/50 p-4 rounded-lg">
                      <h3 className="text-gray-300 text-sm mb-1 flex items-center">
                        24h Change 📈
                        <span title="How much the price changed in the last 24 hours." className="ml-2 text-xs text-cyan-400 cursor-help">?</span>
                      </h3>
                      <p
                        className={`text-2xl font-bold ${
                          cryptoData.price_change_percentage_24h >= 0
                            ? "text-green-400"
                            : "text-red-400"
                        }`}
                      >
                        {formatPercentage(cryptoData.price_change_percentage_24h)}
                      </p>
                      <p className="text-sm mt-1">
                        {cryptoData.price_change_24h >= 0 ? "+" : ""}
                        {formatNumber(cryptoData.price_change_24h)}
                      </p>
                      <p className="text-xs text-gray-400">
                        Change in price over the last day.
                      </p>
                    </div>
                    <div className="bg-gray-700/50 p-4 rounded-lg">
                      <h3 className="text-gray-300 text-sm mb-1 flex items-center">
                        Market Cap 🌍
                        <span title="Total value of all coins in circulation." className="ml-2 text-xs text-cyan-400 cursor-help">?</span>
                      </h3>
                      <p className="text-xl text-cyan-200">
                        {formatNumber(cryptoData.market_cap)}
                      </p>
                      <p className="text-xs text-gray-400">
                        The combined value of all coins.
                      </p>
                    </div>
                    <div className="bg-gray-700/50 p-4 rounded-lg">
                      <h3 className="text-gray-300 text-sm mb-1 flex items-center">
                        24h Volume 🔄
                        <span title="Total amount traded in the last 24 hours." className="ml-2 text-xs text-cyan-400 cursor-help">?</span>
                      </h3>
                      <p className="text-xl text-cyan-200">
                        {formatNumber(cryptoData.total_volume)}
                      </p>
                      <p className="text-xs text-gray-400">
                        How much was bought and sold in the last day.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Prediction Section */}
            {prediction && (
              <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 max-w-4xl w-full border border-indigo-500/30">
                <h3 className="text-2xl font-bold mb-6 text-cyan-300">
                  🔮 Price Predictions
                </h3>
                {/* Actual vs Predicted */}
                <div className="mb-10">
                  <h4 className="text-lg font-semibold text-white mb-2">
                    Actual vs Predicted Price
                  </h4>
                  <p className="text-sm text-gray-400 mb-4">
                    This chart compares the <span className="text-green-400">real prices</span> with the <span className="text-red-400">model’s predictions</span>. It shows how accurate the model has been.
                  </p>
                  <Line
                    data={{
                      labels: prediction.history.dates,
                      datasets: [
                        {
                          label: "Actual Price",
                          data: prediction.history.actual,
                          borderColor: "green",
                          fill: false,
                          tension: 0.4,
                        },
                        {
                          label: "Predicted Price",
                          data: prediction.history.predicted,
                          borderColor: "red",
                          fill: false,
                          tension: 0.4,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { labels: { color: "white" } },
                      },
                      scales: {
                        x: { ticks: { color: "white" } },
                        y: { ticks: { color: "white" } },
                      },
                    }}
                  />
                </div>
                {/* Future Forecast */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-2">
                    10-Day Forecast
                  </h4>
                  <p className="text-sm text-gray-400 mb-4">
                    Based on patterns in the past, here’s where the model thinks prices might go over the next 10 days.
                  </p>
                  <Line
                    data={{
                      labels: prediction.future.days.map((day) => `Day ${day}`),
                      datasets: [
                        {
                          label: "Future Price",
                          data: prediction.future.prices,
                          borderColor: "purple",
                          fill: false,
                          tension: 0.4,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { labels: { color: "white" } },
                      },
                      scales: {
                        x: { ticks: { color: "white" } },
                        y: { ticks: { color: "white" } },
                      },
                    }}
                  />
                </div>
                {/* Table */}
                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-white mb-2">
                    Future Prices Table
                  </h4>
                  <p className="text-sm text-gray-400 mb-4">
                    Exact predicted values for each future day.
                  </p>
                  <table className="w-full table-auto text-left text-white border border-indigo-700">
                    <thead className="bg-indigo-700/50">
                      <tr>
                        <th className="px-4 py-2">Day</th>
                        <th className="px-4 py-2">Predicted Price (USD)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {prediction.future.days.map((day, i) => (
                        <tr
                          key={day}
                          className="border-t border-indigo-700/30"
                        >
                          <td className="px-4 py-2">Day {day}</td>
                          <td className="px-4 py-2 font-semibold">
                            ${prediction.future.prices[i].toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Trend */}
                <div className="mt-4 text-lg">
                  <strong className="text-cyan-400">Overall Trend:</strong>{" "}
                  <span
                    className={
                      prediction.future.trend === "increase"
                        ? "text-green-400"
                        : "text-red-400"
                    }
                  >
                    {prediction.future.trend === "increase"
                      ? "⬆️ Likely Increase"
                      : "⬇️ Likely Decrease"}
                  </span>
                  <p className="text-sm text-gray-400">
                    This is the model’s overall expectation for the coming days.
                  </p>
                </div>
              </div>
            )}
          </div>
        </SignedIn>
      </main>
    </div>
  );
}