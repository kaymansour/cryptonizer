"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, TrendingUp, BarChart3, PieChart } from "lucide-react";
import BacktestDashboard from "../../components/BacktestDashboard";
import StrategyComparison from "@/components/StrategyComparison";
import BackToMain from "../../components/backtomain";

interface PortfolioData {
  symbols: string[];
  weights: Record<string, number>;
  initial_investment: number;
}

export default function BacktestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [activeTab, setActiveTab] = useState<"backtest" | "comparison">("backtest");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get portfolio data from URL params or localStorage
    const symbolsParam = searchParams.get("symbols");
    const weightsParam = searchParams.get("weights");
    const investmentParam = searchParams.get("investment");

    if (symbolsParam && weightsParam) {
      try {
        const symbols = JSON.parse(decodeURIComponent(symbolsParam));
        const weights = JSON.parse(decodeURIComponent(weightsParam));
        const investment = investmentParam ? parseFloat(investmentParam) : 100000;

        setPortfolioData({
          symbols,
          weights,
          initial_investment: investment,
        });
      } catch (error) {
        console.error("Error parsing portfolio data from URL:", error);
        // Try to get from localStorage as fallback
        const storedData = localStorage.getItem("portfolioData");
        if (storedData) {
          setPortfolioData(JSON.parse(storedData));
        }
      }
    } else {
      // Try to get from localStorage
      const storedData = localStorage.getItem("portfolioData");
      if (storedData) {
        setPortfolioData(JSON.parse(storedData));
      }
    }

    setLoading(false);
  }, [searchParams]);

  const handleGoBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-emerald-400 mx-auto mb-4"></div>
          <p className="text-xl text-gray-300">Loading backtesting data...</p>
        </div>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="bg-red-500/20 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="h-8 w-8 text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">No Portfolio Data Found</h2>
          <p className="text-gray-300 mb-6">
            Please go back to the portfolio optimization page and create a portfolio first.
          </p>
          <button
            onClick={() => router.push("/portfolio")}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors"
          >
            Go to Portfolio Optimizer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={handleGoBack}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-xl rounded-lg border border-white/20 text-white transition-all duration-300"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white">Portfolio Backtesting</h1>
              <p className="text-gray-300">Historical performance analysis and strategy comparison</p>
            </div>
          </div>
        </div>

        {/* Portfolio Summary */}
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 mb-8">
          <h3 className="text-xl font-semibold text-white mb-4">Portfolio Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-300 text-sm">Assets</p>
              <p className="text-white font-medium">{portfolioData.symbols.join(", ")}</p>
            </div>
            <div>
              <p className="text-gray-300 text-sm">Initial Investment</p>
              <p className="text-white font-medium">${portfolioData.initial_investment.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-300 text-sm">Allocation</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(portfolioData.weights).map(([symbol, weight]) => (
                  <span
                    key={symbol}
                    className="px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded text-sm"
                  >
                    {symbol.replace("-USD", "")}: {((weight as number) * 100).toFixed(1)}%
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab("backtest")}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-all duration-300 ${
              activeTab === "backtest"
                ? "bg-emerald-600 text-white"
                : "bg-white/10 hover:bg-white/20 text-gray-300 hover:text-white"
            }`}
          >
            <BarChart3 className="h-5 w-5" />
            Historical Performance
          </button>
          <button
            onClick={() => setActiveTab("comparison")}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-all duration-300 ${
              activeTab === "comparison"
                ? "bg-emerald-600 text-white"
                : "bg-white/10 hover:bg-white/20 text-gray-300 hover:text-white"
            }`}
          >
            <PieChart className="h-5 w-5" />
            Strategy Comparison
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "backtest" && <BacktestDashboard portfolioData={portfolioData} />}
        {activeTab === "comparison" && <StrategyComparison portfolioData={portfolioData} />}

        <BackToMain />
      </div>
    </div>
  );
}