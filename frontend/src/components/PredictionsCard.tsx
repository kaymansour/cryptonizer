"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Sparkles, ChevronDown, ChevronUp, ArrowRight, ArrowUpCircle, ArrowDownCircle, MinusCircle } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

interface CandlePrediction {
    step: number;
    current_price: number;
    predicted_price: number;
    predicted_change_percent: number;
    signal: string;
    candle_time: string;
}

interface SymbolPrediction {
    symbol: string;
    current_price: number;
    predictions: CandlePrediction[];
    overall_trend: string;
    confidence: string;
    error?: string;
}

interface PredictionsResult {
    predictions: Record<string, SymbolPrediction>;
}

interface PredictionsCardProps {
    symbols: string[];
}

export default function PredictionsCard({ symbols }: PredictionsCardProps) {
    const [predictions, setPredictions] = useState<PredictionsResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [expandedSymbols, setExpandedSymbols] = useState<Set<string>>(new Set());

    const fetchPredictions = async () => {
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/predict-next-candles", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    symbols: symbols,
                    interval: "4h",
                    steps: 1,
                }),
            });

            const data = await response.json();
            setPredictions(data);
            // Auto-expand all symbols
            const allSymbols = new Set(Object.keys(data.predictions));
            setExpandedSymbols(allSymbols);
        } catch (err) {
            console.error("Prediction error:", err);
        } finally {
            setLoading(false);
        }
    };

    const toggleSymbol = (symbol: string) => {
        const newExpanded = new Set(expandedSymbols);
        if (newExpanded.has(symbol)) {
            newExpanded.delete(symbol);
        } else {
            newExpanded.add(symbol);
        }
        setExpandedSymbols(newExpanded);
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    };

    const formatPercentage = (value: number) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    const getSignalColor = (signal: string) => {
        switch (signal) {
            case "BUY":
                return "bg-green-500/20 text-green-400 border-green-500/30";
            case "SELL":
                return "bg-red-500/20 text-red-400 border-red-500/30";
            default:
                return "bg-gray-500/20 text-gray-400 border-gray-500/30";
        }
    };

    const getSignalAction = (signal: string) => {
        switch (signal) {
            case "BUY":
                return (
                    <span className="flex items-center gap-2">
                        <ArrowUpCircle className="h-4 w-4" />
                        LONG Position
                    </span>
                );
            case "SELL":
                return (
                    <span className="flex items-center gap-2">
                        <ArrowDownCircle className="h-4 w-4" />
                        SHORT Position
                    </span>
                );
            default:
                return (
                    <span className="flex items-center gap-2">
                        <MinusCircle className="h-4 w-4" />
                        HOLD / No Position
                    </span>
                );
        }
    };

    return (
        <div className="space-y-4">
            {!predictions ? (
                <Button
                    onClick={fetchPredictions}
                    disabled={loading}
                    className="w-full bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl h-12"
                >
                    {loading ? (
                        <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                            Getting AI Predictions...
                        </>
                    ) : (
                        <>
                            <Sparkles className="h-4 w-4 mr-2" />
                            Get Next Candle Prediction
                        </>
                    )}
                </Button>
            ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                    {Object.entries(predictions.predictions).map(([symbol, data]) => (
                        <div key={symbol} className="bg-white/5 rounded-lg border border-white/10">
                            {/* Symbol Header */}
                            <button
                                onClick={() => toggleSymbol(symbol)}
                                className="w-full p-3 flex items-center justify-between hover:bg-white/5 transition-colors rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-white font-bold">{data.symbol}</span>
                                    <Badge className={
                                        data.overall_trend === "BULLISH"
                                            ? "bg-green-500/20 text-green-400 text-xs"
                                            : "bg-red-500/20 text-red-400 text-xs"
                                    }>
                                        {data.overall_trend === "BULLISH" ? (
                                            <TrendingUp className="h-3 w-3 mr-1" />
                                        ) : (
                                            <TrendingDown className="h-3 w-3 mr-1" />
                                        )}
                                        {data.overall_trend}
                                    </Badge>
                                </div>
                                {expandedSymbols.has(symbol) ? (
                                    <ChevronUp className="h-4 w-4 text-gray-400" />
                                ) : (
                                    <ChevronDown className="h-4 w-4 text-gray-400" />
                                )}
                            </button>

                            {/* Expanded Candles */}
                            {expandedSymbols.has(symbol) && (
                                <div className="px-3 pb-3 space-y-2">
                                    {data.error ? (
                                        <p className="text-xs text-red-400 py-2">{data.error}</p>
                                    ) : (
                                        <>
                                            {/* Current Price */}
                                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs text-gray-400">Current Price</span>
                                                    <span className="text-white font-bold font-mono">
                                                        {formatCurrency(data.current_price)}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Individual Candle Predictions */}
                                            {data.predictions.map((candle, idx) => (
                                                <div
                                                    key={candle.step}
                                                    className={`border rounded-lg p-3 ${candle.signal === "BUY"
                                                        ? "bg-green-500/5 border-green-500/30"
                                                        : candle.signal === "SELL"
                                                            ? "bg-red-500/5 border-red-500/30"
                                                            : "bg-gray-500/5 border-gray-500/30"
                                                        }`}
                                                >
                                                    {/* Candle Header */}
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs font-mono text-gray-400">
                                                                {candle.candle_time}
                                                            </span>
                                                            <ArrowRight className="h-3 w-3 text-gray-500" />
                                                            <span className="text-xs text-gray-400">
                                                                Candle #{candle.step}
                                                            </span>
                                                        </div>
                                                        <Badge variant="outline" className={`text-xs ${getSignalColor(candle.signal)}`}>
                                                            {candle.signal}
                                                        </Badge>
                                                    </div>

                                                    {/* Price Info */}
                                                    <div className="grid grid-cols-2 gap-2 mb-2">
                                                        <div>
                                                            <p className="text-xs text-gray-500">Entry Price</p>
                                                            <p className="text-sm font-mono text-white">
                                                                {formatCurrency(candle.current_price)}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-gray-500">Target Price</p>
                                                            <p className={`text-sm font-mono font-bold ${candle.predicted_change_percent >= 0
                                                                ? 'text-green-400'
                                                                : 'text-red-400'
                                                                }`}>
                                                                {formatCurrency(candle.predicted_price)}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    {/* Expected Move */}
                                                    <div className="bg-white/5 rounded p-2 mb-2">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-xs text-gray-400">Expected Move</span>
                                                            <span className={`text-sm font-bold ${candle.predicted_change_percent >= 0
                                                                ? 'text-green-400'
                                                                : 'text-red-400'
                                                                }`}>
                                                                {formatPercentage(candle.predicted_change_percent)}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    {/* Trading Action */}
                                                    <div className="pt-2 border-t border-white/10">
                                                        <p className="text-xs text-gray-500 mb-1">Recommended Action:</p>
                                                        <p className={`text-sm font-semibold ${candle.signal === "BUY"
                                                            ? "text-green-400"
                                                            : candle.signal === "SELL"
                                                                ? "text-red-400"
                                                                : "text-gray-400"
                                                            }`}>
                                                            {getSignalAction(candle.signal)}
                                                        </p>
                                                    </div>
                                                </div>
                                            ))}
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
