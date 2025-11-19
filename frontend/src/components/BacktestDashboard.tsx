"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle } from "lucide-react";
import { XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area } from "recharts";

// Minimal container size hook to avoid ResponsiveContainer width/height -1
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

interface BacktestResult {
  success: boolean;
  summary: {
    initial_investment: number;
    final_value: number;
    total_return: number;
    annualized_return: number;
    volatility: number;
    sharpe_ratio?: number;
    max_drawdown: number;
    var_95: number;
    win_rate: number;
    best_day: number;
    worst_day: number;
    calmar_ratio?: number;
    sortino_ratio?: number;
  };
  daily_values: Array<{
    date: string;
    portfolio_value: number;
    daily_return: number;
    cumulative_return: number;
  }>;
  rebalancing?: {
    frequency: string;
    dates: string[];
    total_rebalances: number;
  };
}

interface BacktestDashboardProps {
  portfolioData: PortfolioData;
}

export default function BacktestDashboard({ portfolioData }: BacktestDashboardProps) {
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [timeperiod, setTimeperiod] = useState("1y");
  const [rebalanceFreq, setRebalanceFreq] = useState("monthly");
  const [areaRef, areaSize] = useElementSize<HTMLDivElement>();

  const timeperiods = useMemo(() => [
    { value: "3m", label: "3 Months", days: 90 },
    { value: "6m", label: "6 Months", days: 180 },
    { value: "1y", label: "1 Year", days: 365 },
    { value: "2y", label: "2 Years", days: 730 },
    { value: "3y", label: "3 Years", days: 1095 },
  ], []);

  const rebalanceOptions = [
    { value: "never", label: "Never" },
    { value: "monthly", label: "Monthly" },
    { value: "weekly", label: "Weekly" },
    { value: "quarterly", label: "Quarterly" },
  ];

  const runBacktest = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const selectedPeriod = timeperiods.find(p => p.value === timeperiod);
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - (selectedPeriod?.days || 365) * 24 * 60 * 60 * 1000);

      const requestData = {
        symbols: portfolioData.symbols,
        weights: portfolioData.weights,
        initial_investment: portfolioData.initial_investment,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        rebalance_frequency: rebalanceFreq,
      };

      const response = await fetch("http://localhost:8000/api/backtest-portfolio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Backtest API response:", data);
      
      // Extract and transform backtest_results from the response
      if (data.backtest_results) {
        // Transform daily_data arrays into daily_values array of objects
        let daily_values: Array<{
          date: string;
          portfolio_value: number;
          daily_return: number;
          cumulative_return: number;
        }> = [];
        
        if (data.backtest_results.daily_data) {
          const dailyData = data.backtest_results.daily_data;
          daily_values = dailyData.dates.map((date: string, index: number) => ({
            date: date,
            portfolio_value: dailyData.portfolio_values[index],
            daily_return: dailyData.returns[index],
            cumulative_return: dailyData.cumulative_returns[index],
          }));
        }
        
        const result = {
          success: data.success,
          summary: data.backtest_results.summary,
          daily_values: daily_values,
          rebalancing: data.backtest_results.rebalancing,
        };
        console.log("Processed backtest result:", result);
        console.log("Daily values count:", result.daily_values.length);
        setBacktestResult(result);
      } else {
        console.log("Using data directly (no nested backtest_results)");
        setBacktestResult(data);
      }
    } catch (err) {
      console.error("Backtest error:", err);
      setError("Failed to run backtest. Please make sure the backend is running and try again.");
    } finally {
      setLoading(false);
    }
  }, [portfolioData, timeperiod, rebalanceFreq, timeperiods]);

  useEffect(() => {
    if (portfolioData) {
      runBacktest();
    }
  }, [portfolioData, runBacktest]);

  const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return 'N/A';
    }
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
        <h3 className="text-xl font-semibold text-white mb-6">Backtest Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
              Rebalancing Frequency
            </label>
            <select
              value={rebalanceFreq}
              onChange={(e) => setRebalanceFreq(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {rebalanceOptions.map((option) => (
                <option key={option.value} value={option.value} className="bg-gray-800">
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-red-300">{error}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-8">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mb-4"></div>
            <p className="text-gray-300">Running backtest analysis...</p>
          </div>
        </div>
      )}

      {backtestResult && !loading && (
        <>
          {/* Validate backtest result structure */}
          {!backtestResult.summary ? (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                <p className="text-red-300">Invalid backtest result received. Please try again.</p>
              </div>
            </div>
          ) : (
            <>
              {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-300 text-sm">Total Return</p>
                  <p className={`text-2xl font-bold ${(backtestResult.summary.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {formatPercentage(backtestResult.summary.total_return)}
                  </p>
                </div>
                <TrendingUp className={`h-8 w-8 ${(backtestResult.summary.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-300 text-sm">Final Value</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(backtestResult.summary.final_value)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-emerald-400" />
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-300 text-sm">Sharpe Ratio</p>
                  <p className="text-2xl font-bold text-white">
                    {backtestResult.summary.sharpe_ratio?.toFixed(3) || 'N/A'}
                  </p>
                </div>
                <Target className="h-8 w-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-300 text-sm">Max Drawdown</p>
                  <p className="text-2xl font-bold text-red-400">
                    {formatPercentage(backtestResult.summary.max_drawdown)}
                  </p>
                </div>
                <TrendingDown className="h-8 w-8 text-red-400" />
              </div>
            </div>
          </div>

          {/* Portfolio Value Chart */}
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Portfolio Value Over Time</h3>
            <div ref={areaRef} className="h-80 w-full">
              {backtestResult.daily_values && backtestResult.daily_values.length > 0 ? (
                <AreaChart width={areaSize.width > 0 ? areaSize.width : 1000} height={320} data={backtestResult.daily_values}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9ca3af"
                    tick={{ fontSize: 12 }}
                    tickFormatter={formatDate}
                  />
                  <YAxis 
                    stroke="#9ca3af"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value: number) => formatCurrency(value)}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#f3f4f6'
                    }}
                    labelFormatter={formatDate}
                    formatter={(value: number) => [formatCurrency(value), 'Portfolio Value']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="portfolio_value" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    fill="url(#colorValue)" 
                  />
                </AreaChart>
              ) : (
                <div className="h-80 w-full flex items-center justify-center">
                  <p className="text-gray-400">No chart data available</p>
                </div>
              )}
            </div>
          </div>

          {/* Detailed Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Performance Metrics</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-300">Initial Investment</span>
                  <span className="text-white font-medium">{formatCurrency(backtestResult.summary.initial_investment)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Final Value</span>
                  <span className="text-white font-medium">{formatCurrency(backtestResult.summary.final_value)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Total Return</span>
                  <span className={`font-medium ${(backtestResult.summary.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {formatPercentage(backtestResult.summary.total_return)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Annualized Return</span>
                  <span className={`font-medium ${(backtestResult.summary.annualized_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {formatPercentage(backtestResult.summary.annualized_return)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Volatility</span>
                  <span className="text-white font-medium">{formatPercentage(backtestResult.summary.volatility)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Win Rate</span>
                  <span className="text-white font-medium">{formatPercentage(backtestResult.summary.win_rate)}</span>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Risk Metrics</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-300">Sharpe Ratio</span>
                  <span className="text-white font-medium">{backtestResult.summary.sharpe_ratio?.toFixed(3) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Sortino Ratio</span>
                  <span className="text-white font-medium">{backtestResult.summary.sortino_ratio?.toFixed(3) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Calmar Ratio</span>
                  <span className="text-white font-medium">{backtestResult.summary.calmar_ratio?.toFixed(3) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Max Drawdown</span>
                  <span className="text-red-400 font-medium">{formatPercentage(backtestResult.summary.max_drawdown)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Value at Risk (95%)</span>
                  <span className="text-red-400 font-medium">{formatPercentage(backtestResult.summary.var_95)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Best Day</span>
                  <span className="text-emerald-400 font-medium">{formatPercentage(backtestResult.summary.best_day)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Worst Day</span>
                  <span className="text-red-400 font-medium">{formatPercentage(backtestResult.summary.worst_day)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Rebalancing Info */}
          {backtestResult.rebalancing && (
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Rebalancing Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-gray-300 text-sm">Frequency</p>
                  <p className="text-white font-medium capitalize">{backtestResult.rebalancing.frequency}</p>
                </div>
                <div>
                  <p className="text-gray-300 text-sm">Total Rebalances</p>
                  <p className="text-white font-medium">{backtestResult.rebalancing.total_rebalances}</p>
                </div>
                <div>
                  <p className="text-gray-300 text-sm">Last Rebalance</p>
                  <p className="text-white font-medium">
                    {backtestResult.rebalancing.dates.length > 0 
                      ? formatDate(backtestResult.rebalancing.dates[backtestResult.rebalancing.dates.length - 1])
                      : 'N/A'
                    }
                  </p>
                </div>
              </div>
            </div>
          )}
            </>
          )}
        </>
      )}
    </div>
  );
}

