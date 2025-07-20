"use client"

import { useEffect, useState } from "react"
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs"

type Prices = Record<string, { usd: number }>

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"loading" | "success" | "error">("loading")
  const [prices, setPrices] = useState<Prices | null>(null)
  const [pricesLoading, setPricesLoading] = useState(false)
  const [pricesError, setPricesError] = useState(false)

  // Check backend status on mount
  useEffect(() => {
    fetch("http://localhost:8000/api/status")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ Backend connected:", data.message)
        setBackendStatus("success")
      })
      .catch((err) => {
        console.error("❌ Backend connection failed", err)
        setBackendStatus("error")
      })
  }, [])

  // Fetch crypto prices only if backend connected
  useEffect(() => {
    if (backendStatus === "success") {
      setPricesLoading(true)
      fetch("http://localhost:8000/api/crypto-prices")
        .then((res) => res.json())
        .then((data) => {
          setPrices(data)
          setPricesLoading(false)
          setPricesError(false)
        })
        .catch((err) => {
          console.error("Error fetching prices:", err)
          setPricesError(true)
          setPricesLoading(false)
        })
    }
  }, [backendStatus])

  return (
    <main className="min-h-screen p-10 bg-gray-100 flex flex-col items-center justify-center space-y-8 text-center">

      {/* Backend status */}
      {backendStatus === "loading" && (
        <p className="text-gray-500">Checking backend connection...</p>
      )}
      {backendStatus === "error" && (
        <p className="text-red-600 font-semibold">Error: Could not connect to backend</p>
      )}

      <SignedOut>
        <h1 className="text-3xl font-bold text-gray-800">Welcome to the Crypto App</h1>
        <SignInButton>
          <button className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition">
            Sign In
          </button>
        </SignInButton>
      </SignedOut>

      <SignedIn>
        <div className="flex flex-col items-center space-y-6 max-w-4xl w-full">
          <h2 className="text-3xl font-semibold text-green-700">You are logged in</h2>
          <UserButton afterSignOutUrl="/" />

          {/* Crypto Prices */}
          <section className="w-full">
            <h3 className="text-2xl font-bold mb-6">🚀 Live Crypto Prices</h3>

            {pricesLoading && <p className="text-gray-600">Loading prices...</p>}
            {pricesError && <p className="text-red-600">Failed to load prices.</p>}

            {prices && (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {Object.entries(prices).map(([coin, value]) => (
                  <div
                    key={coin}
                    className="bg-white rounded-2xl shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow duration-300"
                  >
                    <h4 className="text-xl font-semibold text-gray-700 mb-2">
                      {coin.toUpperCase()}
                    </h4>
                    <p className="text-2xl font-bold text-green-600">
                      ${value.usd.toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </SignedIn>
    </main>
  )
}
