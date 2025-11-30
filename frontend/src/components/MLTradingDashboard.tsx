"use client";

import { useState, useCallback, useMemo } from "react";
import { TrendingUp, Target, AlertTriangle, Activity, ArrowUpCircle, ArrowDownCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import MLPredictionChart from "./MLPredictionChart";
import Select from 'react-select';

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
            coins: number;
            price: number;
            value: number;
            predicted_change: number;
            confidence: number;
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
    const [signalThreshold, setSignalThreshold] = useState(2.0);
    const [maxPositionSize, setMaxPositionSize] = useState(0.6);
    const [rsiOversold, setRsiOversold] = useState(25);
    const [rsiOverbought, setRsiOverbought] = useState(60);
    const [currentPage, setCurrentPage] = useState(1);
    const [tradesPerPage] = useState(10);

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
                max_position_size: maxPositionSize,
                rsi_oversold: rsiOversold,
                rsi_overbought: rsiOverbought,
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
            setCurrentPage(1); // Reset to first page on new results
        } catch (err) {
            console.error("ML Backtest error:", err);
            setError(err instanceof Error ? err.message : "Failed to run ML backtest. Please make sure the backend is running and ML models are trained.");
        } finally {
            setLoading(false);
        }
    }, [portfolioData, timeperiod, interval, signalThreshold, maxPositionSize, rsiOversold, rsiOverbought, timeperiods]);

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
                        <Select
                            value={timeperiods.find(p => p.value === timeperiod)}
                            onChange={(option) => option && setTimeperiod(option.value)}
                            options={timeperiods}
                            className="react-select-container"
                            classNamePrefix="react-select"
                            styles={{
                                control: (base) => ({
                                    ...base,
                                    backgroundColor: 'var(--muted)',
                                    borderColor: 'var(--input)',
                                    borderRadius: '0.5rem',
                                    minHeight: '2.5rem',
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
                                    borderRadius: '0.5rem',
                                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                                }),
                                menuList: (base) => ({
                                    ...base,
                                    backgroundColor: 'var(--popover)',
                                    padding: '0.25rem',
                                    borderRadius: '0.5rem',
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
                        <p className="text-xs text-gray-400 mt-1">Max 2 years for hourly data</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Candle Interval
                        </label>
                        <Select
                            value={intervalOptions.find(opt => opt.value === interval)}
                            onChange={(option) => option && setInterval(option.value)}
                            options={intervalOptions}
                            className="react-select-container"
                            classNamePrefix="react-select"
                            styles={{
                                control: (base) => ({
                                    ...base,
                                    backgroundColor: 'var(--muted)',
                                    borderColor: 'var(--input)',
                                    borderRadius: '0.5rem',
                                    minHeight: '2.5rem',
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
                                    borderRadius: '0.5rem',
                                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
                                }),
                                menuList: (base) => ({
                                    ...base,
                                    backgroundColor: 'var(--popover)',
                                    padding: '0.25rem',
                                    borderRadius: '0.5rem',
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
                        <p className="text-xs text-gray-400 mt-1">Trading frequency</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Signal Threshold ({signalThreshold.toFixed(2)})
                        </label>
                        <Slider
                            defaultValue={[signalThreshold]}
                            value={[signalThreshold]}
                            min={0.1}
                            max={10.0}
                            step={0.1}
                            onValueChange={(value) => setSignalThreshold(value[0])}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-400 mt-1">Min % change to trigger trade</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Max Position Size ({(maxPositionSize * 100).toFixed(0)}%)
                        </label>
                        <Slider
                            defaultValue={[maxPositionSize]}
                            value={[maxPositionSize]}
                            min={0.1}
                            max={0.8}
                            step={0.05}
                            onValueChange={(value) => setMaxPositionSize(value[0])}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-400 mt-1">Max portfolio % per trade</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            RSI Oversold ({rsiOversold})
                        </label>
                        <Slider
                            defaultValue={[rsiOversold]}
                            value={[rsiOversold]}
                            min={15}
                            max={35}
                            step={1}
                            onValueChange={(value) => setRsiOversold(value[0])}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-400 mt-1">Buy signal threshold</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            RSI Overbought ({rsiOverbought})
                        </label>
                        <Slider
                            defaultValue={[rsiOverbought]}
                            value={[rsiOverbought]}
                            min={50}
                            max={85}
                            step={1}
                            onValueChange={(value) => setRsiOverbought(value[0])}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-400 mt-1">Sell signal threshold</p>
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

                    {/* Trade History with Pagination */}
                    {backtestResult.backtest_results.trade_history && backtestResult.backtest_results.trade_history.length > 0 && (
                        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                            <h3 className="text-xl font-semibold text-white mb-6">Trade History ({backtestResult.backtest_results.trade_history.length} trades)</h3>

                            {/* Trade Table */}
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-white/20">
                                            <th className="text-left py-3 px-4 text-gray-300 font-medium">Date & Time</th>
                                            <th className="text-left py-3 px-4 text-gray-300 font-medium">Symbol</th>
                                            <th className="text-center py-3 px-4 text-gray-300 font-medium">Action</th>
                                            <th className="text-right py-3 px-4 text-gray-300 font-medium">Price</th>
                                            <th className="text-right py-3 px-4 text-gray-300 font-medium">Coins</th>
                                            <th className="text-right py-3 px-4 text-gray-300 font-medium">Value</th>
                                            <th className="text-right py-3 px-4 text-gray-300 font-medium">Predicted Change</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {backtestResult.backtest_results.trade_history
                                            .slice((currentPage - 1) * tradesPerPage, currentPage * tradesPerPage)
                                            .map((trade, idx) => {
                                                const isBuy = trade.action === "BUY";
                                                return (
                                                    <tr key={idx} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                                                        <td className="py-3 px-4 text-gray-300">
                                                            {new Date(trade.timestamp).toLocaleString('en-US', {
                                                                month: 'short',
                                                                day: 'numeric',
                                                                year: 'numeric',
                                                                hour: '2-digit',
                                                                minute: '2-digit'
                                                            })}
                                                        </td>
                                                        <td className="py-3 px-4 text-white font-medium">
                                                            {trade.symbol.replace('-USD', '')}
                                                        </td>
                                                        <td className="py-3 px-4">
                                                            <div className="flex items-center justify-center gap-2">
                                                                {isBuy ? (
                                                                    <>
                                                                        <ArrowUpCircle className="h-4 w-4 text-emerald-400" />
                                                                        <span className="text-emerald-400 font-semibold">BUY</span>
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <ArrowDownCircle className="h-4 w-4 text-red-400" />
                                                                        <span className="text-red-400 font-semibold">SELL</span>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </td>
                                                        <td className="py-3 px-4 text-right text-white">
                                                            {formatCurrency(trade.price)}
                                                        </td>
                                                        <td className="py-3 px-4 text-right text-gray-300">
                                                            {trade.coins.toFixed(6)}
                                                        </td>
                                                        <td className="py-3 px-4 text-right text-white font-medium">
                                                            {formatCurrency(trade.value)}
                                                        </td>
                                                        <td className="py-3 px-4 text-right">
                                                            <span className={`font-medium ${trade.predicted_change > 0 ? 'text-emerald-400' :
                                                                trade.predicted_change < 0 ? 'text-red-400' : 'text-gray-400'
                                                                }`}>
                                                                {trade.predicted_change > 0 ? '+' : ''}{trade.predicted_change.toFixed(2)}%
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination Controls */}
                            <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
                                <div className="text-sm text-gray-300">
                                    Showing {((currentPage - 1) * tradesPerPage) + 1} to {Math.min(currentPage * tradesPerPage, backtestResult.backtest_results.trade_history.length)} of {backtestResult.backtest_results.trade_history.length} trades
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                        disabled={currentPage === 1}
                                        className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors flex items-center gap-2"
                                    >
                                        <ChevronLeft className="h-4 w-4" />
                                        Previous
                                    </button>
                                    <div className="flex items-center gap-2">
                                        {Array.from({ length: Math.ceil(backtestResult.backtest_results.trade_history.length / tradesPerPage) }, (_, i) => i + 1)
                                            .filter(page => {
                                                // Show first page, last page, current page, and pages around current
                                                const totalPages = Math.ceil(backtestResult.backtest_results.trade_history.length / tradesPerPage);
                                                return page === 1 ||
                                                    page === totalPages ||
                                                    Math.abs(page - currentPage) <= 1;
                                            })
                                            .map((page, idx, arr) => (
                                                <div key={page} className="flex items-center">
                                                    {idx > 0 && arr[idx - 1] !== page - 1 && (
                                                        <span className="text-gray-400 px-2">...</span>
                                                    )}
                                                    <button
                                                        onClick={() => setCurrentPage(page)}
                                                        className={`px-3 py-1 rounded-lg transition-colors ${currentPage === page
                                                            ? 'bg-emerald-500 text-white'
                                                            : 'bg-white/10 hover:bg-white/20 text-white'
                                                            }`}
                                                    >
                                                        {page}
                                                    </button>
                                                </div>
                                            ))}
                                    </div>
                                    <button
                                        onClick={() => setCurrentPage(p => Math.min(Math.ceil(backtestResult.backtest_results.trade_history.length / tradesPerPage), p + 1))}
                                        disabled={currentPage >= Math.ceil(backtestResult.backtest_results.trade_history.length / tradesPerPage)}
                                        className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors flex items-center gap-2"
                                    >
                                        Next
                                        <ChevronRight className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
