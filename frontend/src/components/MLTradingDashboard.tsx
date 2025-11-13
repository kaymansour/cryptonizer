"use client";

import { useState, useCallback, useMemo } from "react";
import { TrendingUp, Target, AlertTriangle, Activity } from "lucide-react";
import MLPredictionChart from "./MLPredictionChart";

interface PortfolioData {
    symbols: string[];
    weights: Record<string, number>;
    initial_investment: number;
}

interface MLBacktestResult {
    success: boolean;
    backtest_results: {
        summary: {
            initial_capital: number;
            final_value: number;
            total_return: number;
            annualized_return: number;
            volatility: number;
            sharpe_ratio: number;
            max_drawdown: number;
        };
        trading_stats: {
            total_trades: number;
            buy_trades: number;
            sell_trades: number;
            win_rate: number;
            avg_trade_size: number;
        };
        daily_values: Array<{
            date: string;
            portfolio_value: number;
        }>;
        predictions_by_symbol: Record<string, Array<{
            timestamp: string;
            actual_price: number;
            predicted_price: number;
            predicted_change: number;
            confidence: number;
        }>>;
        trade_history: Array<{
            timestamp: string;
            symbol: string;
            action: string;
            value: number;
        }>;
        config: {
            interval: string;
            signal_threshold: number;
            max_position_size: number;
            transaction_cost: number;
        };
    };
    summary: {
        initial_investment: number;
        final_value: number;
        total_return: number;
        annualized_return: number;
        sharpe_ratio: number;
        max_drawdown: number;
        period: string;
        total_trades: number;
        win_rate: number;
    };
}

interface MLTradingDashboardProps {
    portfolioData: PortfolioData;
}

export default function MLTradingDashboard({ portfolioData }: MLTradingDashboardProps) {
    const [backtestResult, setBacktestResult] = useState<MLBacktestResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>("");
    const [timeperiod, setTimeperiod] = useState("1y");
    const [interval, setInterval] = useState("4h");
    const [signalThreshold, setSignalThreshold] = useState(0.5);

    const timeperiods = useMemo(() => [
        { value: "1m", label: "1 Month", days: 30 },
        { value: "3m", label: "3 Months", days: 90 },
        { value: "6m", label: "6 Months", days: 180 },
        { value: "1y", label: "1 Year", days: 365 },
        { value: "2y", label: "2 Years (Max)", days: 730 },
    ], []);

    const intervalOptions = [
        { value: "1h", label: "1 Hour" },
        { value: "4h", label: "4 Hours (Recommended)" },
    ];

    const runMLBacktest = useCallback(async () => {
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
                interval: interval,
                signal_threshold: signalThreshold,
            };

            console.log("Running ML backtest with config:", requestData);

            const response = await fetch("http://localhost:8000/api/ml-backtest", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("ML backtest result:", data);
            setBacktestResult(data);
        } catch (err) {
            console.error("ML Backtest error:", err);
            setError(err instanceof Error ? err.message : "Failed to run ML backtest. Please make sure the backend is running and ML models are trained.");
        } finally {
            setLoading(false);
        }
    }, [portfolioData, timeperiod, interval, signalThreshold, timeperiods]);

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

    return (
        <div className="space-y-8">
            {/* Controls */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                <h3 className="text-xl font-semibold text-white mb-6">ML Trading Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                        <p className="text-xs text-gray-400 mt-1">Max 2 years for hourly data</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Candle Interval
                        </label>
                        <select
                            value={interval}
                            onChange={(e) => setInterval(e.target.value)}
                            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        >
                            {intervalOptions.map((option) => (
                                <option key={option.value} value={option.value} className="bg-gray-800">
                                    {option.label}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-400 mt-1">Trading frequency</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Signal Threshold ({signalThreshold.toFixed(2)})
                        </label>
                        <input
                            type="range"
                            min="0.1"
                            max="2.0"
                            step="0.1"
                            value={signalThreshold}
                            onChange={(e) => setSignalThreshold(parseFloat(e.target.value))}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-400 mt-1">Min % change to trigger trade</p>
                    </div>
                </div>

                <div className="mt-6">
                    <button
                        onClick={runMLBacktest}
                        disabled={loading}
                        className="w-full px-6 py-3 bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-600 hover:to-blue-600 text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "Running ML Backtest..." : "Run ML Backtest"}
                    </button>
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
                        <p className="text-gray-300">Training ML models and running backtest...</p>
                        <p className="text-sm text-gray-400 mt-2">This may take a few minutes</p>
                    </div>
                </div>
            )}

            {backtestResult && !loading && (
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
                                    <p className="text-gray-300 text-sm">Total Trades</p>
                                    <p className="text-2xl font-bold text-white">
                                        {backtestResult.summary.total_trades}
                                    </p>
                                </div>
                                <Activity className="h-8 w-8 text-blue-400" />
                            </div>
                        </div>

                        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-gray-300 text-sm">Win Rate</p>
                                    <p className="text-2xl font-bold text-white">
                                        {formatPercentage(backtestResult.summary.win_rate)}
                                    </p>
                                </div>
                                <Target className="h-8 w-8 text-emerald-400" />
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
                                <TrendingUp className="h-8 w-8 text-purple-400" />
                            </div>
                        </div>
                    </div>

                    {/* ML Prediction Charts for each symbol */}
                    {backtestResult.backtest_results.predictions_by_symbol &&
                        Object.entries(backtestResult.backtest_results.predictions_by_symbol).map(([symbol, predictions]) => (
                            <MLPredictionChart
                                key={symbol}
                                symbol={symbol}
                                predictions={predictions}
                            />
                        ))
                    }

                    {/* Trading Statistics */}
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
                            </div>
                        </div>

                        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                            <h3 className="text-xl font-semibold text-white mb-6">Trading Statistics</h3>
                            <div className="space-y-4">
                                <div className="flex justify-between">
                                    <span className="text-gray-300">Total Trades</span>
                                    <span className="text-white font-medium">{backtestResult.backtest_results.trading_stats.total_trades}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-300">Buy Trades</span>
                                    <span className="text-emerald-400 font-medium">{backtestResult.backtest_results.trading_stats.buy_trades}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-300">Sell Trades</span>
                                    <span className="text-red-400 font-medium">{backtestResult.backtest_results.trading_stats.sell_trades}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-300">Win Rate</span>
                                    <span className="text-white font-medium">{formatPercentage(backtestResult.backtest_results.trading_stats.win_rate)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-300">Avg Trade Size</span>
                                    <span className="text-white font-medium">{formatCurrency(backtestResult.backtest_results.trading_stats.avg_trade_size)}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ML Config Info */}
                    <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                        <h3 className="text-xl font-semibold text-white mb-4">ML Trading Configuration</h3>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <p className="text-gray-300 text-sm">Candle Interval</p>
                                <p className="text-white font-medium">{backtestResult.backtest_results.config.interval}</p>
                            </div>
                            <div>
                                <p className="text-gray-300 text-sm">Signal Threshold</p>
                                <p className="text-white font-medium">{backtestResult.backtest_results.config.signal_threshold}%</p>
                            </div>
                            <div>
                                <p className="text-gray-300 text-sm">Max Position Size</p>
                                <p className="text-white font-medium">{formatPercentage(backtestResult.backtest_results.config.max_position_size * 100)}</p>
                            </div>
                            <div>
                                <p className="text-gray-300 text-sm">Transaction Cost</p>
                                <p className="text-white font-medium">{formatPercentage(backtestResult.backtest_results.config.transaction_cost * 100)}</p>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
