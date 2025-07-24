"use client";

import { useEffect, useState } from "react";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import Header from "@/components/Header";
import TopBanner from "@/components/TopBanner";
import Chatbot from "@/components/chatbot";

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

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"loading" | "success" | "error">("loading");
  const [cryptoData, setCryptoData] = useState<CryptoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check backend status on mount
  useEffect(() => {
     fetch("http://localhost:8000/api/status") // ✅ matches FastAPI

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
    
    try {
      const response = await fetch(`http://localhost:8000/crypto/${symbol}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch cryptocurrency data');
      }
      
      const data: CryptoData = await response.json();
      setCryptoData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cryptocurrency data');
      setCryptoData(null);
    } finally {
      setLoading(false);
    }
  };

  // Format large numbers
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: num < 1 ? 6 : 2,
    }).format(num);
  };

  // Format percentage
  const formatPercentage = (num: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: 'exceptZero'
    }).format(num / 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-indigo-900 text-white">
      <Header />
      <TopBanner onSearch={handleSearch} />
      
      <main className="container mx-auto p-4">
        {/* Backend status */}
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
            {loading && (
              <div className="mt-8 text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
                <p className="mt-2 text-cyan-300">Fetching crypto data...</p>
              </div>
            )}
            
            {error && (
              <div className="mt-8 p-4 bg-red-900/50 rounded-xl max-w-2xl mx-auto text-center">
                <p className="text-red-300">{error}</p>
              </div>
            )}
            
            {cryptoData && (
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
                    <h3 className="text-gray-300 text-sm mb-1">Current Price</h3>
                    <p className="text-2xl font-bold">
                      {formatNumber(cryptoData.current_price)}
                    </p>
                  </div>
                  
                  <div className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="text-gray-300 text-sm mb-1">24h Change</h3>
                    <p className={`text-2xl font-bold ${
                      cryptoData.price_change_percentage_24h >= 0 
                        ? 'text-green-500' 
                        : 'text-red-500'
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
                    <p className="text-xl">
                      {formatNumber(cryptoData.market_cap)}
                    </p>
                    <p className="text-sm mt-1 text-gray-400">
                      Rank: #1 {/* You would need to add rank to your API response */}
                    </p>
                  </div>
                  
                  <div className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="text-gray-300 text-sm mb-1">24h Volume</h3>
                    <p className="text-xl">
                      {formatNumber(cryptoData.total_volume)}
                    </p>
                    <p className="text-sm mt-1 text-gray-400">
                      Volume/Market Cap: {((cryptoData.total_volume / cryptoData.market_cap) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {!cryptoData && !loading && backendStatus === "success" && (
              <div className="mt-12 text-center max-w-2xl">
                <div className="bg-gradient-to-r from-cyan-700/20 to-blue-800/20 rounded-xl p-8 border border-cyan-500/30">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="h-16 w-16 mx-auto text-cyan-500 mb-4" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={1.5} 
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" 
                    />
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