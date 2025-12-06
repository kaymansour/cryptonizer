"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Trophy, Target, TrendingDown, BarChart3, Info } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, Tooltip, PieChart as RechartsPieChart, Pie, Cell, LabelList } from "recharts";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import type { ChartConfig } from "@/components/ui/chart";

// Lightweight hook to measure container size for charts
function useElementSize<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const rect = el.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    };

    // Initial update
    update();

    // Update on window resize
    const handleResize = () => update();
    window.addEventListener('resize', handleResize);

    const ro = new ResizeObserver(() => update());
    ro.observe(el);

    // Force update after a short delay to catch late renders
    const timer = setTimeout(update, 100);

    return () => {
      ro.disconnect();
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
    };
  }, []);

  return [ref, size] as const;
}

interface PortfolioData {
  symbols: string[];
  weights: Record<string, number>;
  initial_investment: number;
}

interface StrategyResult {
  strategy_name: string;
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  var_95: number;
  win_rate: number;
  best_day: number;
  worst_day: number;
  calmar_ratio: number;
  sortino_ratio: number;
  final_value: number;
}

interface ComparisonResult {
  success: boolean;
  comparison: Record<string, StrategyResult>;
  rankings: {
    total_return: Array<{ strategy: string; value: number }>;
    sharpe_ratio: Array<{ strategy: string; value: number }>;
    max_drawdown: Array<{ strategy: string; value: number }>;
    volatility: Array<{ strategy: string; value: number }>;
  };
  summary: {
    best_overall: string;
    most_consistent: string;
    lowest_risk: string;
  };
}

interface StrategyComparisonProps {
  portfolioData: PortfolioData;
}

const COLORS = [
  '#8b5cf6', // chart-1 equivalent (purple)
  '#6366f1', // chart-2 equivalent (indigo)
  '#a855f7', // chart-3 equivalent (purple-light)
  '#818cf8', // chart-4 equivalent (indigo-light)
  '#ec4899', // chart-5 equivalent (pink)
];

export default function StrategyComparison({ portfolioData }: StrategyComparisonProps) {
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [timeperiod, setTimeperiod] = useState("1y");
  const [mounted, setMounted] = useState(false);
  const [barRef, barSize] = useElementSize<HTMLDivElement>();
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([
    "optimized", "equal_weight", "btc_only", "eth_only", "btc_eth_60_40"
  ]);

  const timeperiods = useMemo(() => [
    { value: "3m", label: "3 Months", days: 90 },
    { value: "6m", label: "6 Months", days: 180 },
    { value: "1y", label: "1 Year", days: 365 },
    { value: "2y", label: "2 Years", days: 730 },
  ], []);

  const strategyOptions = useMemo(() => [
    {
      value: "optimized",
      label: "Optimized Portfolio",
      description:
        "Portfolio weights computed by the optimizer to balance expected return and risk (e.g., maximize Sharpe or meet constraints). " +
        "May incorporate historical returns, covariance, and model-driven forecasts when enabled. Best when you want a risk-aware, data-driven allocation rather than a simple heuristic.",
      short: "Risk-adjusted, data-driven allocation (optimizer-driven)."
    },
    {
      value: "equal_weight",
      label: "Equal Weight",
      description:
        "Simple and robust baseline: allocates the same percentage to every asset in the portfolio. " +
        "Reduces concentration risk and is easy to rebalance. It ignores market cap and forecasts, so it can overweight smaller assets relative to their size.",
      short: "Uniform allocation across assets; low complexity, good baseline."
    },
    {
      value: "btc_only",
      label: "Bitcoin Only",
      description:
        "Concentrated exposure to Bitcoin (100% allocation). " +
        "Suitable if you believe Bitcoin will outperform the rest of the market. High potential return but also high single-asset risk and volatility; no diversification benefits.",
      short: "100% BTC; high conviction, high volatility."
    },
    {
      value: "eth_only",
      label: "Ethereum Only",
      description:
        "Concentrated exposure to Ethereum (100% allocation). " +
        "Captures ETH-specific upside (smart contract/platform adoption) but sacrifices diversification. Expect different volatility and drivers versus Bitcoin.",
      short: "100% ETH; focused exposure to Ethereum's fundamentals."
    },
    {
      value: "btc_eth_60_40",
      label: "60/40 BTC/ETH",
      description:
        "A balanced, two-asset allocation: 60% Bitcoin and 40% Ethereum. " +
        "Reduces single-asset concentration compared to 'BTC Only' while keeping meaningful exposure to Bitcoin's market leadership. Good for users who want tilt toward BTC but still benefit from ETH's performance.",
      short: "60% BTC / 40% ETH; diversified between the two largest assets."
    },
    {
      value: "market_cap_weighted",
      label: "Market Cap Weighted",
      description:
        "Passive market-capitalization weighting: larger-cap coins receive larger allocations. " +
        "This mirrors many index-style strategies and tends to be low turnover. It passively reflects market structure but can overweight overvalued assets and underweight emerging opportunities.",
      short: "Passive market-cap weighting; low turnover, mirrors market structure."
    },
  ], []);

  const runComparison = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const selectedPeriod = timeperiods.find(p => p.value === timeperiod);
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - (selectedPeriod?.days || 365) * 24 * 60 * 60 * 1000);

      const requestData = {
        symbols: portfolioData.symbols,
        optimized_weights: portfolioData.weights,
        initial_investment: portfolioData.initial_investment,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        rebalance_frequency: "monthly",
        include_benchmarks: selectedStrategies,
      };

      const response = await fetch("http://localhost:8000/api/compare-strategies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Normalize backend response shape to frontend expectations
      const cr = data.comparison_results || data; // backend wraps under comparison_results
      const comparison = cr.comparison || cr.comparison_summary || {};
      const rankings = cr.rankings || {
        total_return: [],
        sharpe_ratio: [],
        max_drawdown: [],
        volatility: [],
      };

      const summary = {
        best_overall:
          (rankings.sharpe_ratio && rankings.sharpe_ratio[0]?.strategy) ||
          Object.entries(comparison)
            .sort((a, b) => ((b[1] as StrategyResult)?.sharpe_ratio || 0) - ((a[1] as StrategyResult)?.sharpe_ratio || 0))[0]?.[0] ||
          undefined,
        most_consistent:
          (rankings.volatility && rankings.volatility[0]?.strategy) ||
          Object.entries(comparison)
            .sort((a, b) => ((a[1] as StrategyResult)?.volatility || 0) - ((b[1] as StrategyResult)?.volatility || 0))[0]?.[0] ||
          undefined,
        lowest_risk:
          (rankings.max_drawdown && rankings.max_drawdown[0]?.strategy) ||
          Object.entries(comparison)
            .sort((a, b) => ((a[1] as StrategyResult)?.max_drawdown || 0) - ((b[1] as StrategyResult)?.max_drawdown || 0))[0]?.[0] ||
          undefined,
      };

      const normalized: ComparisonResult = {
        success: true,
        comparison: comparison as Record<string, StrategyResult>,
        rankings,
        summary: summary,
      };

      setComparisonResult(normalized);
    } catch (err) {
      console.error("Strategy comparison error:", err);
      setError("Failed to run strategy comparison. Please make sure the backend is running and try again.");
    } finally {
      setLoading(false);
    }
  }, [portfolioData, timeperiod, selectedStrategies, timeperiods]);

  useEffect(() => {
    if (portfolioData) {
      runComparison();
    }
  }, [portfolioData, runComparison]);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleStrategyToggle = (strategy: string) => {
    setSelectedStrategies(prev =>
      prev.includes(strategy)
        ? prev.filter(s => s !== strategy)
        : [...prev, strategy]
    );
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getStrategyDisplayName = (strategy?: string) => {
    if (!strategy || typeof strategy !== 'string') return 'Unknown Strategy';
    if (strategy === "optimized") return "Optimized Portfolio";
    const option = strategyOptions.find(opt => opt.value === strategy);
    return option ? option.label : strategy.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const getPerformanceColor = (value: number, isInverse: boolean = false) => {
    if (isInverse) {
      return value < 0 ? 'text-emerald-400' : 'text-red-400';
    }
    return value >= 0 ? 'text-emerald-400' : 'text-red-400';
  };

  const prepareChartData = () => {
    if (!comparisonResult || !comparisonResult.comparison) return [];

    return Object.entries(comparisonResult.comparison).map(([strategy, data]) => ({
      strategy: getStrategyDisplayName(strategy),
      'Total Return (%)': Number(data.total_return) || 0,
      'Sharpe Ratio': Number(data.sharpe_ratio) || 0,
      'Max Drawdown (%)': Math.abs(Number(data.max_drawdown) || 0),
      'Volatility (%)': Number(data.volatility) || 0,
    }));
  };

  const preparePieData = () => {
    if (!comparisonResult || !comparisonResult.comparison) return [];

    return Object.entries(comparisonResult.comparison).map(([strategy, data]) => ({
      name: getStrategyDisplayName(strategy),
      value: Number(data.final_value) || 0,
      return: Number(data.total_return) || 0,
    }));
  };

  const chartConfig = {
    totalReturn: {
      label: "Total Return %",
      color: "#8b5cf6",
    },
    sharpeRatio: {
      label: "Sharpe Ratio",
      color: "#6366f1",
    },
  } satisfies ChartConfig;

  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="bg-card backdrop-blur-xl rounded-2xl border border-border p-6">
        <h3 className="text-xl font-semibold text-card-foreground mb-6">Comparison Configuration</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Time Period
            </label>
            <select
              value={timeperiod}
              onChange={(e) => setTimeperiod(e.target.value)}
              className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-secondary-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {timeperiods.map((period) => (
                <option key={period.value} value={period.value} className="bg-popover text-popover-foreground">
                  {period.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Benchmark Strategies
            </label>
            <TooltipProvider>
              <div className="grid grid-cols-2 gap-2">
                {strategyOptions.map((strategy) => (
                  <div
                    key={strategy.value}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-secondary border border-border hover:bg-accent transition-colors"
                  >
                    <Checkbox
                      id={strategy.value}
                      checked={selectedStrategies.includes(strategy.value)}
                      onCheckedChange={() => handleStrategyToggle(strategy.value)}
                    />
                    <label
                      htmlFor={strategy.value}
                      className="text-sm text-secondary-foreground cursor-pointer flex-1"
                    >
                      {strategy.label}
                    </label>
                    <UITooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{strategy.description}</p>
                      </TooltipContent>
                    </UITooltip>
                  </div>
                ))}
              </div>
            </TooltipProvider>
          </div>
        </div>
      </div>

      <div className="bg-amber-500/20 border border-amber-500/30 rounded-lg p-4">
        <p className="text-amber-300 text-sm">
          This is a <strong>passive buy-and-hold</strong> backtest with periodic rebalancing.
          It does not use ML predictions. For ML-driven trading results, see the ML Trading tab.
        </p>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-red-400" />
            <p className="text-red-300">{error}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="bg-card backdrop-blur-xl rounded-2xl border border-border p-8">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mb-4"></div>
            <p className="text-muted-foreground">Comparing strategies...</p>
          </div>
        </div>
      )}

      {mounted && comparisonResult && !loading && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 backdrop-blur-xl rounded-2xl border border-emerald-400/30 p-6">
              <div className="flex items-center gap-3 mb-2">
                <Trophy className="h-6 w-6 text-emerald-400" />
                <h4 className="text-lg font-semibold text-white">Best Overall</h4>
              </div>
              <p className="text-emerald-300 text-xl font-bold">
                {getStrategyDisplayName(comparisonResult.summary.best_overall)}
              </p>
              <p className="text-emerald-200 text-sm mt-1">Highest risk-adjusted returns</p>
            </div>

            <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-xl rounded-2xl border border-blue-400/30 p-6">
              <div className="flex items-center gap-3 mb-2">
                <Target className="h-6 w-6 text-blue-400" />
                <h4 className="text-lg font-semibold text-white">Most Consistent</h4>
              </div>
              <p className="text-blue-300 text-xl font-bold">
                {getStrategyDisplayName(comparisonResult.summary.most_consistent)}
              </p>
              <p className="text-blue-200 text-sm mt-1">Lowest volatility</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-xl rounded-2xl border border-purple-400/30 p-6">
              <div className="flex items-center gap-3 mb-2">
                <BarChart3 className="h-6 w-6 text-purple-400" />
                <h4 className="text-lg font-semibold text-white">Lowest Risk</h4>
              </div>
              <p className="text-purple-300 text-xl font-bold">
                {getStrategyDisplayName(comparisonResult.summary.lowest_risk)}
              </p>
              <p className="text-purple-200 text-sm mt-1">Smallest maximum drawdown</p>
            </div>
          </div>

          {/* Performance Comparison Chart */}
          <div className="bg-card backdrop-blur-xl rounded-2xl border border-border p-6">
            <h3 className="text-xl font-semibold text-card-foreground mb-6">Total Return Comparison</h3>
            <ChartContainer config={chartConfig} className="h-80 w-full">
              <BarChart accessibilityLayer data={prepareChartData()}>
                <CartesianGrid vertical={false} className="stroke-border" />
                <XAxis
                  dataKey="strategy"
                  tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                  className="fill-muted-foreground"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <ChartTooltip
                  cursor={false}
                  content={<ChartTooltipContent hideLabel hideIndicator />}
                />
                <Bar dataKey="Total Return (%)">
                  <LabelList
                    position="top"
                    dataKey="strategy"
                    fillOpacity={1}
                    className="fill-muted-foreground"
                    fontSize={10}
                  />
                  {prepareChartData().map((item) => (
                    <Cell
                      key={item.strategy}
                      fill={item['Total Return (%)'] >= 0 ? '#10b981' : '#ef4444'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
          </div>

          {/* Final Portfolio Values & Metrics */}
          <div className="bg-card backdrop-blur-xl rounded-2xl border border-border p-6">
            <h3 className="text-xl font-semibold text-card-foreground mb-6">Strategy Performance Overview</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Pie Chart Section */}
              <div className="flex items-center justify-center">
                <ChartContainer config={chartConfig} className="h-96 w-full">
                  <RechartsPieChart>
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent hideLabel />}
                    />
                    <Pie data={preparePieData()} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={120} innerRadius={70} paddingAngle={2}>
                      {preparePieData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                  </RechartsPieChart>
                </ChartContainer>
              </div>

              {/* Combined Metrics Table */}
              <div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left text-muted-foreground py-2 px-2"></th>
                        <th className="text-left text-muted-foreground py-2 px-2">Strategy</th>
                        <th className="text-right text-muted-foreground py-2 px-2">Final Value</th>
                        <th className="text-right text-muted-foreground py-2 px-2">Return</th>
                        <th className="text-right text-muted-foreground py-2 px-2">Sharpe</th>
                        <th className="text-right text-muted-foreground py-2 px-2">Drawdown</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(comparisonResult.comparison).map(([strategy, data], index) => (
                        <tr key={strategy} className="border-b border-border/50">
                          <td className="py-3 px-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: COLORS[index % COLORS.length] }}
                            />
                          </td>
                          <td className="py-3 px-2 text-card-foreground font-medium">
                            {getStrategyDisplayName(strategy)}
                          </td>
                          <td className="py-3 px-2 text-right text-card-foreground font-medium">
                            {formatCurrency(data.final_value)}
                          </td>
                          <td className={`py-3 px-2 text-right font-medium ${getPerformanceColor(data.total_return)}`}>
                            {formatPercentage(data.total_return)}
                          </td>
                          <td className="py-3 px-2 text-right text-muted-foreground">
                            {data.sharpe_ratio.toFixed(3)}
                          </td>
                          <td className="py-3 px-2 text-right text-red-400">
                            {formatPercentage(data.max_drawdown)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Rankings */}
          <div className="bg-card backdrop-blur-xl rounded-2xl border border-border p-6">
            <h3 className="text-xl font-semibold text-card-foreground mb-6">Strategy Rankings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <h4 className="text-emerald-400 font-medium mb-3">Total Return</h4>
                {comparisonResult.rankings.total_return.slice(0, 3).map((item, index) => (
                  <div key={item.strategy} className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-sm">#{index + 1}</span>
                      <span className="text-card-foreground text-sm">{getStrategyDisplayName(item.strategy)}</span>
                    </div>
                    <span className="text-emerald-400 text-sm font-medium">
                      {formatPercentage(item.value)}
                    </span>
                  </div>
                ))}
              </div>

              <div>
                <h4 className="text-blue-400 font-medium mb-3">Sharpe Ratio</h4>
                {comparisonResult.rankings.sharpe_ratio.slice(0, 3).map((item, index) => (
                  <div key={item.strategy} className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-sm">#{index + 1}</span>
                      <span className="text-card-foreground text-sm">{getStrategyDisplayName(item.strategy)}</span>
                    </div>
                    <span className="text-blue-400 text-sm font-medium">
                      {item.value.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>

              <div>
                <h4 className="text-purple-400 font-medium mb-3">Lowest Drawdown</h4>
                {comparisonResult.rankings.max_drawdown.slice(0, 3).map((item, index) => (
                  <div key={item.strategy} className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-sm">#{index + 1}</span>
                      <span className="text-card-foreground text-sm">{getStrategyDisplayName(item.strategy)}</span>
                    </div>
                    <span className="text-purple-400 text-sm font-medium">
                      {formatPercentage(item.value)}
                    </span>
                  </div>
                ))}
              </div>

              <div>
                <h4 className="text-yellow-400 font-medium mb-3">Lowest Volatility</h4>
                {comparisonResult.rankings.volatility.slice(0, 3).map((item, index) => (
                  <div key={item.strategy} className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-sm">#{index + 1}</span>
                      <span className="text-card-foreground text-sm">{getStrategyDisplayName(item.strategy)}</span>
                    </div>
                    <span className="text-yellow-400 text-sm font-medium">
                      {formatPercentage(item.value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
