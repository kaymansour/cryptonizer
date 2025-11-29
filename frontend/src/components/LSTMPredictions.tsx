"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, AlertCircle, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

interface PortfolioData {
    symbols: string[];
    weights: Record<string, number>;
    initial_investment: number;
}

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
    success: boolean;
    interval: string;
    steps: number;
    predictions: Record<string, SymbolPrediction>;
    note: string;
}

interface LSTMPredictionsProps {
    portfolioData: PortfolioData;
}

export default function LSTMPredictions({ portfolioData }: LSTMPredictionsProps) {
    const [predictions, setPredictions] = useState<PredictionsResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>("");
    const [interval, setInterval] = useState("4h");

    const fetchPredictions = async () => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch("http://localhost:8000/api/predict-next-candles", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    symbols: portfolioData.symbols,
                    interval: interval,
                    steps: 1,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setPredictions(data);
        } catch (err) {
            console.error("Prediction error:", err);
            setError("Failed to fetch predictions. Make sure LSTM models are trained.");
        } finally {
            setLoading(false);
        }
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
                return "text-green-400 bg-green-500/20";
            case "SELL":
                return "text-red-400 bg-red-500/20";
            default:
                return "text-gray-400 bg-gray-500/20";
        }
    };

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-purple-400" />
                            AI Price Predictions
                        </h3>
                        <p className="text-sm text-gray-400 mt-1">
                            LSTM neural network predictions for next candle
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Candle Interval
                        </label>
                        <select
                            value={interval}
                            onChange={(e) => setInterval(e.target.value)}
                            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="1h" className="bg-gray-800">1 Hour</option>
                            <option value="4h" className="bg-gray-800">4 Hours (Recommended)</option>
                        </select>
                    </div>
                    <div className="pt-6">
                        <Button
                            onClick={fetchPredictions}
                            disabled={loading}
                            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl px-6"
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                                    Predicting...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    Get Predictions
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-red-400" />
                        <p className="text-red-300">{error}</p>
                    </div>
                </div>
            )}

            {predictions && !loading && (
                <>
                    <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
                        <div className="flex items-start gap-2">
                            <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5" />
                            <p className="text-blue-300 text-sm">{predictions.note}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {Object.entries(predictions.predictions).map(([symbol, data]) => (
                            <div key={symbol} className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{data.symbol}</h4>
                                        <p className="text-sm text-gray-400">
                                            Current: {formatCurrency(data.current_price)}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <Badge className={
                                            data.overall_trend === "BULLISH"
                                                ? "bg-green-500/20 text-green-400"
                                                : "bg-red-500/20 text-red-400"
                                        }>
                                            {data.overall_trend === "BULLISH" ? (
                                                <TrendingUp className="h-3 w-3 mr-1" />
                                            ) : (
                                                <TrendingDown className="h-3 w-3 mr-1" />
                                            )}
                                            {data.overall_trend}
                                        </Badge>
                                        <p className="text-xs text-gray-400 mt-1">
                                            Confidence: {data.confidence}
                                        </p>
                                    </div>
                                </div>

                                {data.error ? (
                                    <div className="text-red-400 text-sm">{data.error}</div>
                                ) : (
                                    <div className="space-y-2">
                                        {data.predictions.map((pred) => (
                                            <div
                                                key={pred.step}
                                                className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="text-xs text-gray-400 font-mono w-12">
                                                        {pred.candle_time}
                                                    </div>
                                                    <ArrowRight className="h-3 w-3 text-gray-500" />
                                                    <div className="text-sm text-white">
                                                        {formatCurrency(pred.predicted_price)}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`text-sm font-medium ${pred.predicted_change_percent >= 0
                                                        ? 'text-green-400'
                                                        : 'text-red-400'
                                                        }`}>
                                                        {formatPercentage(pred.predicted_change_percent)}
                                                    </span>
                                                    <Badge className={getSignalColor(pred.signal)} variant="outline">
                                                        {pred.signal}
                                                    </Badge>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {!data.error && data.predictions.length > 0 && (
                                    <div className="mt-4 pt-4 border-t border-white/10">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-gray-400">7-Candle Projection:</span>
                                            <span className={`font-bold ${data.predictions[data.predictions.length - 1].predicted_price >= data.current_price
                                                ? 'text-green-400'
                                                : 'text-red-400'
                                                }`}>
                                                {formatCurrency(data.predictions[data.predictions.length - 1].predicted_price)}
                                                {' '}
                                                ({formatPercentage(
                                                    ((data.predictions[data.predictions.length - 1].predicted_price - data.current_price) /
                                                        data.current_price) * 100
                                                )})
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
