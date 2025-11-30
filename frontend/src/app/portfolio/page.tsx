"use client";

import { useState } from "react";
import { Loader2, TrendingUp, Shield, Target, Sparkles, DollarSign, Clock } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Select from 'react-select';
import PortfolioResults from "@/components/PortfolioResults";
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
  { symbol: "BNB", name: "Binance Coin", description: "Binance's native cryptocurrency" },
  { symbol: "ADA", name: "Cardano", description: "Proof-of-stake blockchain" },
  { symbol: "SOL", name: "Solana", description: "High-performance blockchain" },
  { symbol: "DOT", name: "Polkadot", description: "Multi-chain protocol" },
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
  const [useLSTM, setUseLSTM] = useState<boolean>(true);
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

      // Use LSTM-enhanced endpoint if enabled, otherwise use traditional optimization
      const endpoint = useLSTM
        ? "http://localhost:8000/api/optimize-portfolio-lstm"
        : "http://localhost:8000/api/optimize-portfolio";

      const response = await fetch(endpoint, {
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

          {/* Time Period & LSTM Toggle Card */}
          <BentoCard
            name="Configuration"
            className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={Clock}
            description="Analysis settings"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4 space-y-4">
              {/* Time Period Select */}
              <div>
                <label className="text-xs text-muted-foreground mb-2 block">Historical Period</label>
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
                      backgroundColor: 'var(--muted)',
                      borderColor: 'var(--input)',
                      borderRadius: '0.75rem',
                      padding: '0.25rem',
                      cursor: 'pointer',
                      '&:hover': {
                        borderColor: 'var(--ring)',
                      },
                    }),
                    singleValue: (base) => ({
                      ...base,
                      color: 'var(--foreground)',
                    }),
                    menuPortal: (base) => ({
                      ...base,
                      zIndex: 9999,
                    }),
                    menu: (base) => ({
                      ...base,
                      backgroundColor: 'var(--popover)',
                      border: '1px solid var(--border)',
                      borderRadius: '0.75rem',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                    }),
                    menuList: (base) => ({
                      ...base,
                      backgroundColor: 'var(--popover)',
                      padding: '0.25rem',
                      borderRadius: '0.75rem',
                    }),
                    option: (base, state) => ({
                      ...base,
                      backgroundColor: state.isFocused
                        ? 'var(--accent)'
                        : state.isSelected
                          ? 'var(--primary)'
                          : 'var(--popover)',
                      color: state.isFocused
                        ? 'var(--accent-foreground)'
                        : 'var(--foreground)',
                      cursor: 'pointer',
                      borderRadius: '0.5rem',
                      opacity: 1,
                      '&:active': {
                        backgroundColor: 'var(--accent)',
                      },
                    }),
                    dropdownIndicator: (base) => ({
                      ...base,
                      color: 'var(--primary)',
                    }),
                    indicatorSeparator: () => ({
                      display: 'none',
                    }),
                  }}
                />
              </div>

              {/* LSTM Toggle */}
              <div className="pt-3 border-t border-border">
                <label className="text-xs text-muted-foreground mb-2 block">AI Enhancement</label>
                <div
                  className={`cursor-pointer p-3 rounded-lg border transition-all duration-300 ${useLSTM
                    ? "border-primary bg-primary/20"
                    : "border-border bg-card/50 hover:border-primary/40"
                    }`}
                  onClick={() => setUseLSTM(!useLSTM)}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={useLSTM}
                      onChange={(e) => setUseLSTM(e.target.checked)}
                      className="w-5 h-5 rounded accent-primary cursor-pointer"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="flex-1">
                      <div className="font-semibold text-foreground text-sm flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        LSTM Predictions
                      </div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {useLSTM ? "AI-powered optimization enabled" : "Traditional MPT only"}
                      </div>
                    </div>
                  </div>
                </div>
                {useLSTM && (
                  <div className="mt-2 p-2 rounded-lg bg-primary/10 border border-primary/30">
                    <div className="text-xs text-primary">
                      Using 60% ML predictions + 40% historical data
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Weight limits: 5% min, 50% max per asset
                    </div>
                  </div>
                )}
              </div>
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
                type="text"
                value={investmentAmount.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
                onChange={(e) => {
                  // Remove commas and non-numeric characters except digits
                  const value = e.target.value.replace(/,/g, "");
                  if (value === "" || /^\d+$/.test(value)) {
                    setInvestmentAmount(value);
                  }
                }}
                placeholder="100,000"
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
                    ${(amount / 1000).toLocaleString()}K
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
      </div>
    </div>
  );
}
