"use client";

import { useRef, useState, useEffect } from "react";
import { XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, Legend } from "recharts";

// Hook to get element size
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

interface PredictionData {
    timestamp: string;
    actual_price: number;
    predicted_price: number;
    predicted_change: number;
    confidence: number;
}

interface MLPredictionChartProps {
    predictions: PredictionData[];
    symbol: string;
}

export default function MLPredictionChart({ predictions, symbol }: MLPredictionChartProps) {
    const [chartRef, chartSize] = useElementSize<HTMLDivElement>();

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    // Prepare chart data
    const chartData = predictions.map((pred) => ({
        timestamp: pred.timestamp,
        actual: pred.actual_price,
        predicted: pred.predicted_price,
    }));

    // Calculate prediction accuracy
    const accuracy = predictions.length > 0
        ? predictions.reduce((acc, pred) => {
            const error = Math.abs(pred.actual_price - pred.predicted_price);
            const percentError = (error / pred.actual_price) * 100;
            return acc + (100 - percentError);
        }, 0) / predictions.length
        : 0;

    return (
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">
                    {symbol} - ML Predictions vs Actual Prices
                </h3>
                <div className="text-right">
                    <p className="text-sm text-gray-300">Prediction Accuracy</p>
                    <p className="text-2xl font-bold text-emerald-400">{accuracy.toFixed(2)}%</p>
                </div>
            </div>

            <div ref={chartRef} className="h-96 w-full min-w-0 min-h-0">
                {chartSize.width > 0 && chartData.length > 0 ? (
                    <LineChart
                        width={Math.max(1, Math.floor(chartSize.width))}
                        height={384}
                        data={chartData}
                    >
                        <defs>
                            <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="timestamp"
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
                            formatter={(value: number, name: string) => [
                                formatCurrency(value),
                                name === 'actual' ? 'Actual Price' : 'Predicted Price'
                            ]}
                        />
                        <Legend
                            wrapperStyle={{ color: '#f3f4f6' }}
                            formatter={(value: string) => (
                                value === 'actual' ? 'Actual Price' : 'Predicted Price'
                            )}
                        />
                        <Line
                            type="monotone"
                            dataKey="actual"
                            stroke="#10b981"
                            strokeWidth={2}
                            dot={false}
                            name="actual"
                        />
                        <Line
                            type="monotone"
                            dataKey="predicted"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={false}
                            name="predicted"
                        />
                    </LineChart>
                ) : (
                    <div className="h-96 w-full flex items-center justify-center">
                        <p className="text-gray-400">No prediction data available</p>
                    </div>
                )}
            </div>
        </div>
    );
}
