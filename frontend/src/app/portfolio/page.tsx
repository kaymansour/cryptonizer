"use client";

import { useState } from "react";
import { Loader2, TrendingUp, Shield, Target, BarChart3, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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

        {/* Cards Grid */}
       <div className="grid gap-5 grid-cols-[repeat(auto-fit,minmax(600px,1fr))]">

          {/* Investment Amount Card */}
          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-emerald-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 className="h-6 w-6 text-emerald-400" />
              <h2 className="text-xl font-bold text-white">Investment Amount</h2>
            </div>
            <p className="text-gray-300 mb-4">
              How much would you like to invest in your portfolio?
            </p>
            <div className="space-y-4">
              <Input
                type="number"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(e.target.value)}
                placeholder="100000"
                className="text-lg w-full bg-white/5 border-white/20 text-white rounded-xl"
              />
              <div className="grid grid-cols-3 gap-2">
                {[50000, 100000, 250000].map((amount) => (
                  <Button
                    key={amount}
                    onClick={() => setInvestmentAmount(amount.toString())}
                    className={`rounded-xl transition-all ${
                      parseInt(investmentAmount) === amount 
                        ? 'bg-emerald-500 hover:bg-emerald-600 text-white' 
                        : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                    }`}
                  >
                    ${amount.toLocaleString()}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          {/* Risk Tolerance Card */}
          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-blue-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="h-6 w-6 text-blue-400" />
              <h2 className="text-xl font-bold text-white">Risk Tolerance</h2>
            </div>
            <p className="text-gray-300 mb-4">
              How comfortable are you with potential losses for higher returns?
            </p>
            <div className="grid gap-3">
              {[
                { value: "low", label: "Conservative", desc: "I prefer stable returns and minimal risk", color: "emerald" },
                { value: "medium", label: "Moderate", desc: "I can accept some risk for better returns", color: "blue" },
                { value: "high", label: "Aggressive", desc: "I'm comfortable with high risk for maximum returns", color: "purple" },
              ].map((option) => (
                <div
                  key={option.value}
                  className={`cursor-pointer p-4 rounded-xl border transition-all duration-300 ${
                    riskTolerance === option.value
                      ? `border-${option.color}-400 bg-${option.color}-500/20 shadow-lg`
                      : "border-white/20 bg-white/5 hover:border-white/40 hover:bg-white/10"
                  }`}
                  onClick={() => setRiskTolerance(option.value)}
                >
                  <div className="font-semibold text-white">{option.label}</div>
                  <div className="text-sm text-gray-300">{option.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Investment Goal Card */}
          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-purple-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-4">
              <Target className="h-6 w-6 text-purple-400" />
              <h2 className="text-xl font-bold text-white">Investment Goal</h2>
            </div>
            <p className="text-gray-300 mb-4">
              What's your primary goal for this investment?
            </p>
            <div className="grid gap-3">
              {[
                { value: "safety", label: "Capital Preservation", desc: "Protect my money from major losses", color: "emerald" },
                { value: "balanced", label: "Balanced Growth", desc: "Steady growth with reasonable risk", color: "blue" },
                { value: "growth", label: "Maximum Growth", desc: "Highest possible returns", color: "purple" },
              ].map((option) => (
                <div
                  key={option.value}
                  className={`cursor-pointer p-4 rounded-xl border transition-all duration-300 ${
                    investmentGoal === option.value
                      ? `border-${option.color}-400 bg-${option.color}-500/20 shadow-lg`
                      : "border-white/20 bg-white/5 hover:border-white/40 hover:bg-white/10"
                  }`}
                  onClick={() => setInvestmentGoal(option.value)}
                >
                  <div className="font-semibold text-white">{option.label}</div>
                  <div className="text-sm text-gray-300">{option.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Cryptocurrency Selection Card */}
          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-orange-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="h-6 w-6 text-orange-400" />
              <h2 className="text-xl font-bold text-white">Select Cryptocurrencies</h2>
            </div>
            <p className="text-gray-300 mb-4">
              Choose at least 2 cryptocurrencies for your portfolio (more = better diversification)
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableCryptos.map((crypto) => (
                <div
                  key={crypto.symbol}
                  className={`cursor-pointer p-4 rounded-xl border transition-all duration-300 backdrop-blur-sm ${
                    selectedSymbols.includes(crypto.symbol)
                      ? "border-emerald-400/40 bg-emerald-500/20 shadow-lg"
                      : "border-white/20 bg-white/5 hover:border-white/40 hover:bg-white/10"
                  }`}
                  onClick={() => handleSymbolToggle(crypto.symbol)}
                >
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      checked={selectedSymbols.includes(crypto.symbol)}
                      onChange={() => handleSymbolToggle(crypto.symbol)}
                      className="data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500"
                    />
                    <div>
                      <div className="font-semibold text-white">{crypto.symbol} - {crypto.name}</div>
                      <div className="text-sm text-gray-300">{crypto.description}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-sm text-gray-300">
              Selected: <span className="text-emerald-400 font-semibold">{selectedSymbols.join(", ")}</span> ({selectedSymbols.length} cryptocurrencies)
            </div>
          </div>

          {/* Time Period Card */}
          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-cyan-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
            <h2 className="text-xl font-bold text-white mb-4">Historical Data Period</h2>
            <p className="text-gray-300 mb-4">
              How much historical data should we use to analyze the cryptocurrencies?
            </p>
            <Select value={timePeriod} onValueChange={setTimePeriod}>
              <SelectTrigger className="bg-white/5 border-white/20 text-white rounded-xl w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3mo">3 Months (Recent trends)</SelectItem>
                <SelectItem value="6mo">6 Months (Medium term)</SelectItem>
                <SelectItem value="1y">1 Year (Recommended)</SelectItem>
                <SelectItem value="2y">2 Years (Long term)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Recommended Strategy */}
          {riskTolerance && investmentGoal && (
            <div className="bg-gradient-to-r from-emerald-500/20 to-green-600/20 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-emerald-400/40 hover:scale-[1.02] hover:shadow-2xl transition-all duration-300">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-400" />
                <h3 className="text-lg font-bold text-emerald-400">Recommended Strategy</h3>
              </div>
              <p className="text-emerald-300 mt-2">{getStrategyDescription()}</p>
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
