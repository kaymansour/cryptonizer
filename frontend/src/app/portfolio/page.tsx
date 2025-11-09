"use client";

import { useState } from "react";
import { Loader2, TrendingUp, Shield, Target, Sparkles, DollarSign, Clock } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Select from 'react-select';
import PortfolioResults from "@/components/PortfolioResults";
import BackToMain from "@/components/backtomain";
import { AlertDescription } from "@/components/ui/alert";
import { BentoCard, BentoGrid } from "@/components/ui/bento-grid";

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

// Time period options for react-select
const timePeriodOptions = [
  { value: "3mo", label: "3 Months - Recent trends" },
  { value: "6mo", label: "6 Months - Medium term" },
  { value: "1y", label: "1 Year - Recommended" },
  { value: "2y", label: "2 Years - Long term" },
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
      <div className="min-h-screen bg-background py-8">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-foreground mb-2">Portfolio Optimization Results</h1>
              <p className="text-muted-foreground">Your optimized cryptocurrency portfolio</p>
            </div>
            <Button
              onClick={resetForm}
              variant="outline"
              className="rounded-xl"
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
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="h-8 w-8 text-primary" />
            <h1 className="text-5xl font-bold text-foreground">
              Smart Portfolio Optimizer
            </h1>
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Build an optimized cryptocurrency portfolio tailored to your goals and risk tolerance
          </p>
        </div>

        {/* Bento Grid Layout */}
        <BentoGrid className="lg:grid-rows-3 mb-8">
          {/* Cryptocurrency Selection Card - Now 2 columns */}
          <BentoCard
            name="Select Assets"
            className="lg:col-start-1 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={TrendingUp}
            description="Choose your cryptocurrencies (2+ required)"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 flex flex-col h-full mt-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 overflow-y-auto custom-scrollbar flex-1 pr-2">
                {availableCryptos.map((crypto) => (
                  <div
                    key={crypto.symbol}
                    className={`cursor-pointer p-3 rounded-lg border transition-all h-fit ${selectedSymbols.includes(crypto.symbol)
                      ? "border-primary bg-primary/20"
                      : "border-border bg-card/50 hover:border-primary/40"
                      }`}
                    onClick={() => handleSymbolToggle(crypto.symbol)}
                  >
                    <div className="font-semibold text-foreground text-sm">{crypto.symbol}</div>
                    <div className="text-xs text-muted-foreground truncate">{crypto.name}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-border text-sm text-muted-foreground">
                Selected: <span className="text-primary font-semibold">{selectedSymbols.length}</span> assets
              </div>
            </div>
          </BentoCard>

          {/* Time Period Card */}
          <BentoCard
            name="Data Period"
            className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={Clock}
            description="Historical analysis timeframe"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4">
              <Select
                instanceId="time-period-select"
                className="react-select-container"
                classNamePrefix="react-select"
                value={timePeriodOptions.find(opt => opt.value === timePeriod)}
                onChange={(option) => setTimePeriod(option?.value || "1y")}
                options={timePeriodOptions}
                isSearchable={false}
                menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                menuPosition="fixed"
                styles={{
                  control: (base) => ({
                    ...base,
                    backgroundColor: 'hsl(var(--muted))',
                    borderColor: 'hsl(var(--input))',
                    borderRadius: '0.75rem',
                    padding: '0.25rem',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'hsl(var(--ring))',
                    },
                  }),
                  singleValue: (base) => ({
                    ...base,
                    color: 'hsl(var(--foreground))',
                  }),
                  menuPortal: (base) => ({
                    ...base,
                    zIndex: 9999,
                  }),
                  menu: (base) => ({
                    ...base,
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '0.75rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                  }),
                  menuList: (base) => ({
                    ...base,
                    backgroundColor: 'hsl(var(--popover))',
                    padding: '0.25rem',
                    borderRadius: '0.75rem',
                  }),
                  option: (base, state) => ({
                    ...base,
                    backgroundColor: state.isFocused
                      ? 'hsl(var(--accent))'
                      : state.isSelected
                        ? 'hsl(var(--primary) / 0.15)'
                        : 'hsl(var(--popover))',
                    color: state.isFocused
                      ? 'hsl(var(--accent-foreground))'
                      : 'hsl(var(--foreground))',
                    cursor: 'pointer',
                    borderRadius: '0.5rem',
                    '&:active': {
                      backgroundColor: 'hsl(var(--accent))',
                    },
                  }),
                  dropdownIndicator: (base) => ({
                    ...base,
                    color: 'hsl(var(--primary))',
                  }),
                  indicatorSeparator: () => ({
                    display: 'none',
                  }),
                }}
              />
            </div>
          </BentoCard>

          {/* Risk Tolerance Card */}
          <BentoCard
            name="Risk Level"
            className="lg:col-start-1 lg:col-end-2 lg:row-start-2 lg:row-end-4 border-primary/40"
            Icon={Shield}
            description="Your comfort with volatility"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 grid gap-2 mt-4">
              {[
                { value: "low", label: "Conservative" },
                { value: "medium", label: "Moderate" },
                { value: "high", label: "Aggressive" },
              ].map((option) => (
                <div
                  key={option.value}
                  className={`cursor-pointer p-3 rounded-lg border transition-all duration-300 ${riskTolerance === option.value
                    ? "border-primary bg-primary/20"
                    : "border-border bg-card/50 hover:border-primary/40"
                    }`}
                  onClick={() => setRiskTolerance(option.value)}
                >
                  <div className="font-semibold text-foreground text-sm">{option.label}</div>
                </div>
              ))}
            </div>
          </BentoCard>

          {/* Investment Amount Card - Now 1 column */}
          <BentoCard
            name="Investment Amount"
            className="lg:col-start-2 lg:col-end-3 lg:row-start-2 lg:row-end-3 border-primary/40"
            Icon={DollarSign}
            description="Set your portfolio investment amount"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 space-y-4 mt-4">
              <Input
                type="number"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(e.target.value)}
                placeholder="100000"
                className="text-lg w-full rounded-xl h-12"
              />
              <div className="grid grid-cols-3 gap-2">
                {[50000, 100000, 250000].map((amount) => (
                  <Button
                    key={amount}
                    onClick={() => setInvestmentAmount(amount.toString())}
                    size="sm"
                    variant={parseInt(investmentAmount) === amount ? "default" : "outline"}
                    className="rounded-xl transition-all"
                  >
                    ${(amount / 1000)}K
                  </Button>
                ))}
              </div>
            </div>
          </BentoCard>

          {/* Investment Goal Card */}
          <BentoCard
            name="Investment Goal"
            className="lg:col-start-3 lg:col-end-4 lg:row-start-2 lg:row-end-3 border-primary/40"
            Icon={Target}
            description="What you want to achieve"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 grid gap-2 mt-4">
              {[
                { value: "safety", label: "Preservation" },
                { value: "balanced", label: "Balanced" },
                { value: "growth", label: "Max Growth" },
              ].map((option) => (
                <div
                  key={option.value}
                  className={`cursor-pointer p-2 rounded-lg border transition-all duration-300 ${investmentGoal === option.value
                    ? "border-primary bg-primary/20"
                    : "border-border bg-card/50 hover:border-primary/40"
                    }`}
                  onClick={() => setInvestmentGoal(option.value)}
                >
                  <div className="font-semibold text-foreground text-sm">{option.label}</div>
                </div>
              ))}
            </div>
          </BentoCard>

          {/* Strategy Summary - Conditional */}
          {riskTolerance && investmentGoal && (
            <BentoCard
              name="Your Strategy"
              className="lg:col-start-2 lg:col-end-4 lg:row-start-3 lg:row-end-4 border-primary/40 bg-primary/10"
              Icon={Sparkles}
              description={getStrategyDescription()}
              href="#"
              cta=""
              background={
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
              }
            >
              <div className="relative z-10 mt-2">
                <div className="inline-block px-3 py-1 rounded-full bg-primary/20 border border-primary/40 text-primary text-xs">
                  Recommended
                </div>
              </div>
            </BentoCard>
          )}
        </BentoGrid>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/20 backdrop-blur-xl p-4 rounded-2xl border border-destructive/40 mt-6">
            <AlertDescription className="text-destructive-foreground">{error}</AlertDescription>
          </div>
        )}

        {/* Submit Button */}
        <div className="text-center mt-6">
          <Button
            onClick={optimizePortfolio}
            disabled={isLoading || selectedSymbols.length < 2}
            size="lg"
            className="w-full md:w-auto px-8 py-3 text-lg rounded-xl shadow-2xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
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
