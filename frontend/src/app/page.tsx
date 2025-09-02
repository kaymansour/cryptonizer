"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation"; // Next.js 13+ App Router
import { Sparklines, SparklinesLine } from "react-sparklines";

interface Coin {
  id: string;
  symbol: string;
  name: string;
  image: string;
  current_price: number;
  price_change_percentage_24h: number;
  sparkline_in_24h?: number[];
}

export default function HomePage() {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const router = useRouter();
  const prevPrices = useRef<Map<string, number>>(new Map());

  const fetchCoins = async () => {
    try {
      const res = await fetch("http://localhost:8000/coins");
      const data: Coin[] = await res.json();

      let changed = false;
      data.forEach((coin) => {
        if (prevPrices.current.has(coin.id) && prevPrices.current.get(coin.id) !== coin.current_price) {
          changed = true;
        }
        prevPrices.current.set(coin.id, coin.current_price);
      });

      setCoins(data);

      if (changed) {
        setTimeout(() => window.location.reload(), 1000);
      }
    } catch (err) {
      console.error("Error fetching coins:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoins();
    const interval = setInterval(fetchCoins, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredCoins = coins.filter(
    (coin) =>
      coin.name.toLowerCase().includes(search.toLowerCase()) ||
      coin.symbol.toLowerCase().includes(search.toLowerCase())
  );

  const goToPrediction = (symbol: string) => router.push(`/predict/${symbol.toLowerCase()}`);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-900 text-white py-8">
      <main className="container mx-auto px-6">
        {/* Search */}
        <div className="mb-8 flex justify-center">
          <input
            type="text"
            placeholder="Search by name or symbol..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="p-3 rounded-xl w-full max-w-md bg-gray-800/40 text-white placeholder-gray-400 backdrop-blur-md focus:outline-none focus:ring-2 focus:ring-cyan-400 transition"
          />
        </div>

        {loading && (
          <p className="text-gray-300 text-center animate-pulse">Loading coins...</p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredCoins.map((coin) => (
            <div
              key={coin.id}
              className={`relative bg-white/10 backdrop-blur-xl p-6 rounded-3xl shadow-xl border-l-4 transition-transform transform hover:scale-105 hover:shadow-2xl hover:border-cyan-400 duration-300 ${
                coin.price_change_percentage_24h >= 0 ? "border-green-400" : "border-red-400"
              }`}
            >
              <div className="flex justify-center mb-4">
                <img
                  src={coin.image}
                  alt={coin.name}
                  className="h-16 w-16 rounded-full border-2 border-gray-600 p-1 shadow-md"
                />
              </div>

              <h2 className="text-xl font-bold text-center mb-2">
                {coin.name} ({coin.symbol.toUpperCase()})
              </h2>

              {/* Sparkline */}
              <div className="mb-4">
                {coin.sparkline_in_24h && (
                  <Sparklines data={coin.sparkline_in_24h} width={120} height={40} margin={5}>
                    <SparklinesLine
                      color={coin.price_change_percentage_24h >= 0 ? "#34d399" : "#f87171"}
                      style={{ strokeWidth: 3, fill: "rgba(255,255,255,0.05)" }}
                    />
                  </Sparklines>
                )}
              </div>

              {/* Price */}
              <p
                className={`text-center font-extrabold text-2xl mb-1 ${
                  prevPrices.current.get(coin.id) !== coin.current_price ? "animate-pulse text-yellow-400" : ""
                }`}
              >
                ${coin.current_price.toLocaleString()}
              </p>

              {/* 24h Change */}
              <p
                className={`text-center font-semibold mb-2 flex justify-center items-center gap-2 ${
                  coin.price_change_percentage_24h >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {coin.price_change_percentage_24h >= 0 ? "⬆️" : "⬇️"}{" "}
                {coin.price_change_percentage_24h.toFixed(2)}% (24h)
              </p>

              {/* Progress Bar */}
              <div className="h-2 w-full rounded-full bg-gray-700/30 overflow-hidden mb-4">
                <div
                  className={`h-2 rounded-full ${
                    coin.price_change_percentage_24h >= 0 ? "bg-green-400" : "bg-red-400"
                  }`}
                  style={{
                    width: `${Math.min(Math.abs(coin.price_change_percentage_24h), 100)}%`,
                    transition: "width 0.5s ease",
                  }}
                />
              </div>

              {/* Prediction Button */}
              <button
                onClick={() => goToPrediction(coin.symbol)}
                className="w-full py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold rounded-2xl shadow-lg transition"
              >
                View Prediction
              </button>
            </div>
          ))}
        </div>
      </main>

      {/* Animations */}
      <style jsx>{`
        .animate-fade-in {
          animation: fadeIn 0.8s ease forwards;
        }
        @keyframes fadeIn {
          0% {
            opacity: 0;
            transform: translateY(10px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
