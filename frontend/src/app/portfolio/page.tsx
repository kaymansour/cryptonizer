"use client";

import { useState } from "react";
import { Loader2, TrendingUp, Shield, Target, Sparkles, DollarSign, Clock } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PortfolioResults from "@/components/PortfolioResults";
import BackToMain from "@/components/backtomain";
import { AlertDescription } from "@/components/ui/alert";

interface OptimizationResult {
  success: boolean;
  portfolio: {
    weights: Record<string, number>;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    objective: string;
    symbols: string[];
  };
  allocation: {
    allocation: Record<string, number>;
    leftover: number;
    latest_prices: Record<string, number>;
    total_value: number;
  };
  metrics: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    var_95: number;
    max_drawdown: number;
    weights: Record<string, number>;
  };
  efficient_frontier: {
    volatilities: number[];
    returns: number[];
  };
  symbols: string[];
  period: string;
}

const availableCryptos = [
  { symbol: "BTC", name: "Bitcoin", description: "The original cryptocurrency" },
  { symbol: "ETH", name: "Ethereum", description: "Smart contract platform" },
  { symbol: "ADA", name: "Cardano", description: "Proof-of-stake blockchain" },
  { symbol: "SOL", name: "Solana", description: "High-performance blockchain" },
  { symbol: "DOT", name: "Polkadot", description: "Multi-chain protocol" },
  { symbol: "MATIC", name: "Polygon", description: "Ethereum scaling solution" },
  { symbol: "AVAX", name: "Avalanche", description: "Fast consensus platform" },
  { symbol: "LINK", name: "Chainlink", description: "Decentralized oracle network" },
  { symbol: "ATOM", name: "Cosmos", description: "Internet of blockchains" },
  { symbol: "XRP", name: "XRP", description: "Digital payment protocol" },
];

export default function PortfolioOptimizer() {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(["BTC", "ETH"]);
  const [investmentAmount, setInvestmentAmount] = useState<string>("100000");
  const [riskTolerance, setRiskTolerance] = useState<string>("");
  const [investmentGoal, setInvestmentGoal] = useState<string>("");
  const [timePeriod, setTimePeriod] = useState<string>("1y");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [showQuestions, setShowQuestions] = useState(true);

  const handleSymbolToggle = (symbol: string) => {
    setSelectedSymbols((prev) =>
      prev.includes(symbol) ? prev.filter((s) => s !== symbol) : [...prev, symbol]
    );
  };

  const getObjectiveFromAnswers = () => {
    if (riskTolerance === "low" || investmentGoal === "safety") return "min_volatility";
    if (riskTolerance === "high" && investmentGoal === "growth") return "max_sharpe";
    if (investmentGoal === "balanced") return "max_sharpe";
    return "max_sharpe";
  };

  const getStrategyDescription = () => {
    const objective = getObjectiveFromAnswers();
    switch (objective) {
      case "min_volatility":
        return "Conservative Strategy - Minimize portfolio risk and volatility";
      case "max_sharpe":
        return "Balanced Strategy - Optimize risk-adjusted returns (Sharpe ratio)";
      default:
        return "Balanced Strategy - Optimize risk-adjusted returns";
    }
  };

  const optimizePortfolio = async () => {
    if (selectedSymbols.length < 2) {
      setError("Please select at least 2 cryptocurrencies for diversification");
      return;
    }
    if (!riskTolerance || !investmentGoal) {
      setError("Please answer all questions to determine the best strategy for you");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const objective = getObjectiveFromAnswers();
      const response = await fetch("http://localhost:8000/api/optimize-portfolio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: selectedSymbols,
          total_value: parseFloat(investmentAmount),
          objective,
          period: timePeriod,
        }),
      });

      if (!response.ok) throw new Error("Failed to optimize portfolio");

      const data = await response.json();
      setResult(data);
      setShowQuestions(false);
    } catch (err) {
      console.error("Portfolio optimization error:", err);
      setError("Failed to optimize portfolio. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setResult(null);
    setShowQuestions(true);
    setError("");
  };

  if (!showQuestions && result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 py-8">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Portfolio Optimization Results</h1>
              <p className="text-gray-300">Your optimized cryptocurrency portfolio</p>
            </div>
            <Button 
              onClick={resetForm} 
              className="bg-white/10 backdrop-blur-xl border border-white/20 hover:bg-white/20 text-white rounded-xl"
            >
              Create New Portfolio
            </Button>
          </div>
          <PortfolioResults result={result} />
          <BackToMain />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="h-8 w-8 text-emerald-400" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Smart Portfolio Optimizer
            </h1>
            <Sparkles className="h-8 w-8 text-cyan-400" />
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Build an optimized cryptocurrency portfolio tailored to your goals and risk tolerance
          </p>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid w-full auto-rows-[18rem] grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Investment Amount Card - Large */}
          <div className="col-span-1 md:col-span-2 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/10 backdrop-blur-xl border border-emerald-400/40 p-6 hover:shadow-2xl transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <DollarSign className="h-8 w-8 text-emerald-400" />
                <h3 className="text-xl font-bold text-white">Investment Amount</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">Set your portfolio investment amount</p>
              <div className="space-y-4 mt-auto">
                <Input
                  type="number"
                  value={investmentAmount}
                  onChange={(e) => setInvestmentAmount(e.target.value)}
                  placeholder="100000"
                  className="text-lg w-full bg-white/5 border-white/20 text-white rounded-xl h-12"
                />
                <div className="grid grid-cols-3 gap-2">
                  {[50000, 100000, 250000].map((amount) => (
                    <Button
                      key={amount}
                      onClick={() => setInvestmentAmount(amount.toString())}
                      size="sm"
                      className={`rounded-xl transition-all ${
                        parseInt(investmentAmount) === amount 
                          ? 'bg-emerald-500 hover:bg-emerald-600 text-white' 
                          : 'bg-white/10 border border-white/20 text-white hover:bg-white/20'
                      }`}
                    >
                      ${(amount / 1000)}K
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Time Period Card */}
          <div className="col-span-1 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/10 backdrop-blur-xl border border-cyan-400/40 p-6 hover:shadow-2xl transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent" />
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="h-8 w-8 text-cyan-400" />
                <h3 className="text-xl font-bold text-white">Data Period</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">Historical analysis timeframe</p>
              <div className="mt-auto">
                <Select value={timePeriod} onValueChange={setTimePeriod}>
                  <SelectTrigger className="bg-white/5 border-white/20 text-white rounded-xl w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3mo">3 Months</SelectItem>
                    <SelectItem value="6mo">6 Months</SelectItem>
                    <SelectItem value="1y">1 Year</SelectItem>
                    <SelectItem value="2y">2 Years</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Risk Tolerance Card */}
          <div className="col-span-1 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/10 backdrop-blur-xl border border-blue-400/40 p-6 hover:shadow-2xl transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="h-8 w-8 text-blue-400" />
                <h3 className="text-xl font-bold text-white">Risk Level</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">Your comfort with volatility</p>
              <div className="grid gap-2 mt-auto">
                {[
                  { value: "low", label: "Conservative", color: "emerald" },
                  { value: "medium", label: "Moderate", color: "blue" },
                  { value: "high", label: "Aggressive", color: "purple" },
                ].map((option) => (
                  <div
                    key={option.value}
                    className={`cursor-pointer p-2 rounded-lg border transition-all duration-300 ${
                      riskTolerance === option.value
                        ? `border-${option.color}-400 bg-${option.color}-500/20`
                        : "border-white/20 bg-white/5 hover:border-white/40"
                    }`}
                    onClick={() => setRiskTolerance(option.value)}
                  >
                    <div className="font-semibold text-white text-sm">{option.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Investment Goal Card */}
          <div className="col-span-1 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/10 backdrop-blur-xl border border-purple-400/40 p-6 hover:shadow-2xl transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <Target className="h-8 w-8 text-purple-400" />
                <h3 className="text-xl font-bold text-white">Goal</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">What you want to achieve</p>
              <div className="grid gap-2 mt-auto">
                {[
                  { value: "safety", label: "Preservation", color: "emerald" },
                  { value: "balanced", label: "Balanced", color: "blue" },
                  { value: "growth", label: "Max Growth", color: "purple" },
                ].map((option) => (
                  <div
                    key={option.value}
                    className={`cursor-pointer p-2 rounded-lg border transition-all duration-300 ${
                      investmentGoal === option.value
                        ? `border-${option.color}-400 bg-${option.color}-500/20`
                        : "border-white/20 bg-white/5 hover:border-white/40"
                    }`}
                    onClick={() => setInvestmentGoal(option.value)}
                  >
                    <div className="font-semibold text-white text-sm">{option.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cryptocurrency Selection Card - Spans 2 columns */}
          <div className="col-span-1 md:col-span-1 row-span-1 md:row-span-2 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/10 backdrop-blur-xl border border-orange-400/40 p-6 hover:shadow-2xl transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent" />
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <TrendingUp className="h-8 w-8 text-orange-400" />
                <h3 className="text-xl font-bold text-white">Select Assets</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">Choose your cryptocurrencies (2+ required)</p>
              <div className="grid grid-cols-2 gap-2 overflow-y-auto custom-scrollbar flex-1 pr-2">
                {availableCryptos.map((crypto) => (
                  <div
                    key={crypto.symbol}
                    className={`cursor-pointer p-3 rounded-lg border transition-all h-fit ${
                      selectedSymbols.includes(crypto.symbol)
                        ? "border-emerald-400/60 bg-emerald-500/20"
                        : "border-white/20 bg-white/5 hover:border-white/40"
                    }`}
                    onClick={() => handleSymbolToggle(crypto.symbol)}
                  >
                    <div className="font-semibold text-white text-sm">{crypto.symbol}</div>
                    <div className="text-xs text-gray-400 truncate">{crypto.name}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-white/20 text-sm text-gray-300">
                Selected: <span className="text-emerald-400 font-semibold">{selectedSymbols.length}</span> assets
              </div>
            </div>
          </div>

          {/* Strategy Summary - Conditional */}
          {riskTolerance && investmentGoal && (
            <div className="col-span-1 md:col-span-2 group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-500/20 to-green-600/10 backdrop-blur-xl border border-emerald-400/40 p-6 hover:shadow-2xl transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-3">
                  <Sparkles className="h-8 w-8 text-emerald-400" />
                  <div>
                    <h3 className="text-xl font-bold text-white">Your Strategy</h3>
                    <div className="inline-block px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs mt-1">
                      Recommended
                    </div>
                  </div>
                </div>
                <p className="text-emerald-200 text-lg">{getStrategyDescription()}</p>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-500/20 backdrop-blur-xl p-4 rounded-2xl border border-red-400/40 mt-6">
            <AlertDescription className="text-red-300">{error}</AlertDescription>
          </div>
        )}

        {/* Submit Button */}
        <div className="text-center mt-6">
          <Button
            onClick={optimizePortfolio}
            disabled={isLoading || selectedSymbols.length < 2}
            size="lg"
            className="w-full md:w-auto px-8 py-3 text-lg bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white rounded-xl shadow-2xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Optimizing Your Portfolio...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Optimize My Portfolio
              </>
            )}
          </Button>
        </div>

        <BackToMain />
      </div>
    </div>
  );
}
