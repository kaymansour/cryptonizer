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
import Header from "@/components/Header";
import TopBanner from "@/components/TopBanner";
import Chatbot from "@/components/chatbot";
import Loading from "@/components/loading";

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

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"loading" | "success" | "error">("loading");
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
        console.log("✅ Backend connected:", data.message);
        setBackendStatus("success");
      })
      .catch((err) => {
        console.error("❌ Backend connection failed", err);
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
        throw new Error(errorData.error || 'Failed to fetch cryptocurrency data');
      }
      const data: CryptoData = await response.json();
      setCryptoData(data);

      const predictionRes = await fetch(`http://localhost:8000/predict/${symbol}`);
      if (!predictionRes.ok) {
        const errorData = await predictionRes.json();
        throw new Error(errorData.error || 'Failed to fetch prediction');
      }
      const predictionData: PredictionData = await predictionRes.json();
      setPrediction(predictionData);

    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
      setCryptoData(null);
      setPrediction(null);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: num < 1 ? 6 : 2,
    }).format(num);

  const formatPercentage = (num: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: 'exceptZero',
    }).format(num / 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-indigo-900 text-white">
      <Header />
      <TopBanner onSearch={handleSearch} />

      <main className="container mx-auto p-4">
        {backendStatus === "loading" && (
          <p className="text-center text-gray-400">Checking backend connection...</p>
        )}
        {backendStatus === "error" && (
          <p className="text-center text-red-500 font-semibold">
            Error: Could not connect to backend. Make sure FastAPI is running on port 8000.
          </p>
        )}

        <SignedOut>
          <div className="mt-20 flex flex-col items-center space-y-6">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Crypto Dashboard
            </h1>
            <p className="text-gray-300 max-w-md text-center">
              Sign in to access real-time cryptocurrency data and track market movements.
            </p>
            <SignInButton>
              <button className="mt-4 px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-700 text-white rounded-xl hover:from-cyan-700 hover:to-blue-800 transition font-semibold">
                Sign In
              </button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          <div className="flex flex-col items-center space-y-6 w-full">

            {cryptoData && (
              <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 max-w-2xl w-full border border-indigo-500/30">
                <div className="flex items-center mb-6">
                  <img src={cryptoData.image} alt={cryptoData.name} className="h-16 w-16 mr-4" />
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
                    <h3 className="text-gray-300 text-sm mb-1">Current Price</h3>
                    <p className="text-2xl font-bold">{formatNumber(cryptoData.current_price)}</p>
                  </div>

                  <div className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="text-gray-300 text-sm mb-1">24h Change</h3>
                    <p className={`text-2xl font-bold ${
                      cryptoData.price_change_percentage_24h >= 0 ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {formatPercentage(cryptoData.price_change_percentage_24h)}
                    </p>
                    <p className="text-sm mt-1">
                      {cryptoData.price_change_24h >= 0 ? '+' : ''}
                      {formatNumber(cryptoData.price_change_24h)}
                    </p>
                  </div>

                  <div className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="text-gray-300 text-sm mb-1">Market Cap</h3>
                    <p className="text-xl">{formatNumber(cryptoData.market_cap)}</p>
                    <p className="text-sm mt-1 text-gray-400">Rank: #1</p>
                  </div>

                  <div className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="text-gray-300 text-sm mb-1">24h Volume</h3>
                    <p className="text-xl">{formatNumber(cryptoData.total_volume)}</p>
                    <p className="text-sm mt-1 text-gray-400">
                      Volume/Market Cap: {((cryptoData.total_volume / cryptoData.market_cap) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {loading && (<Loading />)}

            {error && (
              <div className="mt-8 p-4 bg-red-900/50 rounded-xl max-w-2xl mx-auto text-center">
                <p className="text-red-300">{error}</p>
              </div>
            )}


            {/* ✅ PREDICTION DISPLAY */}
            {prediction && (
              <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 max-w-4xl w-full border border-indigo-500/30">
                <h3 className="text-2xl font-bold mb-6 text-cyan-300">Price Predictions</h3>

                {/* Actual vs Predicted */}
                <div className="mb-10">
                  <h4 className="text-lg font-semibold text-white mb-2">Actual vs Predicted Price</h4>
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
                  <h4 className="text-lg font-semibold text-white mb-2">10-Day Forecast</h4>
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
                  <h4 className="text-lg font-semibold text-white mb-2">Future Prices Table</h4>
                  <table className="w-full table-auto text-left text-white border border-indigo-700">
                    <thead className="bg-indigo-700/50">
                      <tr>
                        <th className="px-4 py-2">Day</th>
                        <th className="px-4 py-2">Predicted Price (USD)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {prediction.future.days.map((day, i) => (
                        <tr key={day} className="border-t border-indigo-700/30">
                          <td className="px-4 py-2">Day {day}</td>
                          <td className="px-4 py-2 font-semibold">${prediction.future.prices[i].toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Trend */}
                <div className="mt-4 text-lg">
                  <strong className="text-cyan-400">Trend:</strong>{" "}
                  <span className={prediction.future.trend === "increase" ? "text-green-400" : "text-red-400"}>
                    {prediction.future.trend === "increase" ? "⬆️ Increase" : "⬇️ Decrease"}
                  </span>
                </div>
              </div>
            )}

            {/* ✅ Base64 Image Plots */}
            {prediction && (
              <div className="mt-10 space-y-8">
                <h4 className="text-xl font-bold text-cyan-300">Model Visualizations</h4>

                <div className="bg-gray-900 p-4 rounded-lg shadow-lg">
                  <h5 className="text-white mb-2 font-semibold">Raw Close Price</h5>
                  <img
                    src={`data:image/png;base64,${prediction.plots.close_price}`}
                    alt="Close Price"
                    className="w-full rounded"
                  />
                </div>

                <div className="bg-gray-900 p-4 rounded-lg shadow-lg">
                  <h5 className="text-white mb-2 font-semibold">Moving Averages</h5>
                  <img
                    src={`data:image/png;base64,${prediction.plots.moving_average}`}
                    alt="Moving Averages"
                    className="w-full rounded"
                  />
                </div>

                <div className="bg-gray-900 p-4 rounded-lg shadow-lg">
                  <h5 className="text-white mb-2 font-semibold">Prediction vs Actual</h5>
                  <img
                    src={`data:image/png;base64,${prediction.plots.prediction}`}
                    alt="Prediction"
                    className="w-full rounded"
                  />
                </div>

                <div className="bg-gray-900 p-4 rounded-lg shadow-lg">
                  <h5 className="text-white mb-2 font-semibold">Future Forecast (10 days)</h5>
                  <img
                    src={`data:image/png;base64,${prediction.plots.future}`}
                    alt="Future Forecast"
                    className="w-full rounded"
                  />
                </div>
              </div>
            )}

            {!cryptoData && !loading && backendStatus === "success" && (
              <div className="mt-12 text-center max-w-2xl">
                <div className="bg-gradient-to-r from-cyan-700/20 to-blue-800/20 rounded-xl p-8 border border-cyan-500/30">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-cyan-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <h3 className="text-xl font-bold text-cyan-400 mb-2">Search for Cryptocurrency</h3>
                  <p className="text-gray-400">
                    Enter a cryptocurrency symbol (e.g., bitcoin, ethereum) in the search bar above 
                    to get real-time market data.
                  </p>
                </div>
              </div>
            )}
          </div>
        </SignedIn>
      </main>

      <Chatbot />
    </div>
  );
}
