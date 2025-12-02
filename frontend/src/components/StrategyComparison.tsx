"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Trophy, Target, TrendingDown, BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, Tooltip, PieChart as RechartsPieChart, Pie, Cell } from "recharts";
import { Checkbox } from "@/components/ui/checkbox"

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

    update();

    const ro = new ResizeObserver(() => update());
    ro.observe(el);
    return () => ro.disconnect();
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

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function StrategyComparison({ portfolioData }: StrategyComparisonProps) {
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [timeperiod, setTimeperiod] = useState("1y");
  const [mounted, setMounted] = useState(false);
  const [barRef, barSize] = useElementSize<HTMLDivElement>();
  const [pieRef, pieSize] = useElementSize<HTMLDivElement>();
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
    { value: "optimized", label: "Optimized Portfolio", description: "Your optimized portfolio weights" },
    { value: "equal_weight", label: "Equal Weight", description: "Equal allocation across all assets" },
    { value: "btc_only", label: "Bitcoin Only", description: "100% Bitcoin allocation" },
    { value: "eth_only", label: "Ethereum Only", description: "100% Ethereum allocation" },
    { value: "btc_eth_60_40", label: "60/40 BTC/ETH", description: "60% Bitcoin, 40% Ethereum" },
    { value: "market_cap_weighted", label: "Market Cap Weighted", description: "Weighted by market capitalization" },
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
      'Total Return (%)': data.total_return,
      'Sharpe Ratio': data.sharpe_ratio,
      'Max Drawdown (%)': Math.abs(data.max_drawdown),
      'Volatility (%)': data.volatility,
    }));
  };

  const preparePieData = () => {
    if (!comparisonResult || !comparisonResult.comparison) return [];

    return Object.entries(comparisonResult.comparison).map(([strategy, data]) => ({
      name: getStrategyDisplayName(strategy),
      value: data.final_value,
      return: data.total_return,
    }));
  };

  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
        <h3 className="text-xl font-semibold text-white mb-6">Comparison Configuration</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Time Period
            </label>
            <select
              value={timeperiod}
              onChange={(e) => setTimeperiod(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {timeperiods.map((period) => (
                <option key={period.value} value={period.value} className="bg-gray-800">
                  {period.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Benchmark Strategies
            </label>
            <div className="grid grid-cols-2 gap-2">
              {strategyOptions.map((strategy) => (
                <div
                  key={strategy.value}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-white/10 border border-white/20 hover:bg-white/20 transition-colors"
                >
                  <Checkbox
                    id={strategy.value}
                    checked={selectedStrategies.includes(strategy.value)}
                    onCheckedChange={() => handleStrategyToggle(strategy.value)}
                  />
                  <label
                    htmlFor={strategy.value}
                    className="text-sm text-gray-300 cursor-pointer flex-1"
                  >
                    {strategy.label}
                  </label>
                </div>
              ))}
            </div>
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
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-8">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mb-4"></div>
            <p className="text-gray-300">Comparing strategies...</p>
          </div>
        </div>
      )}

      {mounted && comparisonResult && !loading && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-linear-to-br from-emerald-500/20 to-emerald-600/20 backdrop-blur-xl rounded-2xl border border-emerald-400/30 p-6">
              <div className="flex items-center gap-3 mb-2">
                <Trophy className="h-6 w-6 text-emerald-400" />
                <h4 className="text-lg font-semibold text-white">Best Overall</h4>
              </div>
              <p className="text-emerald-300 text-xl font-bold">
                {getStrategyDisplayName(comparisonResult.summary.best_overall)}
              </p>
              <p className="text-emerald-200 text-sm mt-1">Highest risk-adjusted returns</p>
            </div>

            <div className="bg-linear-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-xl rounded-2xl border border-blue-400/30 p-6">
              <div className="flex items-center gap-3 mb-2">
                <Target className="h-6 w-6 text-blue-400" />
                <h4 className="text-lg font-semibold text-white">Most Consistent</h4>
              </div>
              <p className="text-blue-300 text-xl font-bold">
                {getStrategyDisplayName(comparisonResult.summary.most_consistent)}
              </p>
              <p className="text-blue-200 text-sm mt-1">Lowest volatility</p>
            </div>

            <div className="bg-linear-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-xl rounded-2xl border border-purple-400/30 p-6">
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
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Performance Comparison</h3>
            <div ref={barRef} className="h-80 min-w-0 min-h-0 w-full">
              {barSize.width > 0 ? (
                <BarChart width={Math.max(1, Math.floor(barSize.width))} height={320} data={prepareChartData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="strategy"
                    stroke="#9ca3af"
                    tick={{ fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#f3f4f6'
                    }}
                  />
                  <Legend
                    wrapperStyle={{ color: '#9ca3af' }}
                    iconType="rect"
                  />
                  <Bar dataKey="Total Return (%)" fill="#10b981" name="Total Return %" />
                  <Bar dataKey="Sharpe Ratio" fill="#3b82f6" name="Sharpe Ratio" />
                </BarChart>
              ) : (
                <div className="h-80 w-full" />
              )}
            </div>
          </div>

          {/* Final Value Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Final Portfolio Values</h3>
              <div ref={pieRef} className="h-64 min-w-0 min-h-0 w-full">
                {pieSize.width > 0 ? (
                  <RechartsPieChart width={Math.max(1, Math.floor(pieSize.width))} height={256}>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#f3f4f6'
                      }}
                      formatter={(value: number, name: string) => [
                        formatCurrency(value),
                        name === 'value' ? 'Final Value' : name
                      ]}
                    />
                    <Pie data={preparePieData()} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={2}>
                      {preparePieData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                  </RechartsPieChart>
                ) : (
                  <div className="h-64 w-full" />
                )}
              </div>
              <div className="mt-4 space-y-2">
                {preparePieData().map((entry, index) => (
                  <div key={entry.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-gray-300 text-sm">{entry.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{formatCurrency(entry.value)}</div>
                      <div className={`text-sm ${getPerformanceColor(entry.return)}`}>
                        {formatPercentage(entry.return)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Detailed Metrics Table */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Strategy Metrics</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/20">
                      <th className="text-left text-gray-300 py-2">Strategy</th>
                      <th className="text-right text-gray-300 py-2">Return</th>
                      <th className="text-right text-gray-300 py-2">Sharpe</th>
                      <th className="text-right text-gray-300 py-2">Drawdown</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparisonResult.comparison).map(([strategy, data]) => (
                      <tr key={strategy} className="border-b border-white/10">
                        <td className="py-3 text-white font-medium">
                          {getStrategyDisplayName(strategy)}
                        </td>
                        <td className={`py-3 text-right font-medium ${getPerformanceColor(data.total_return)}`}>
                          {formatPercentage(data.total_return)}
                        </td>
                        <td className="py-3 text-right text-gray-300">
                          {data.sharpe_ratio.toFixed(3)}
                        </td>
                        <td className="py-3 text-right text-red-400">
                          {formatPercentage(data.max_drawdown)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Rankings */}
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Strategy Rankings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <h4 className="text-emerald-400 font-medium mb-3">Total Return</h4>
                {comparisonResult.rankings.total_return.slice(0, 3).map((item, index) => (
                  <div key={item.strategy} className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm">#{index + 1}</span>
                      <span className="text-white text-sm">{getStrategyDisplayName(item.strategy)}</span>
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
                      <span className="text-gray-400 text-sm">#{index + 1}</span>
                      <span className="text-white text-sm">{getStrategyDisplayName(item.strategy)}</span>
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
                      <span className="text-gray-400 text-sm">#{index + 1}</span>
                      <span className="text-white text-sm">{getStrategyDisplayName(item.strategy)}</span>
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
                      <span className="text-gray-400 text-sm">#{index + 1}</span>
                      <span className="text-white text-sm">{getStrategyDisplayName(item.strategy)}</span>
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
