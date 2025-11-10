"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function PredictionDetailPage() {
  const { symbol } = useParams();
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPrediction() {
      try {
        const res = await fetch(`http://localhost:8000/predict/${symbol}-USD`);
        if (!res.ok) throw new Error(`Failed to fetch prediction (${res.status})`);
        const result = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (symbol) fetchPrediction();
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="animate-spin h-12 w-12 border-4 border-emerald-400 border-t-transparent rounded-full mb-4"></div>
        <p>Generating prediction for {symbol}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white text-center">
        <p className="text-red-400 mb-2">❌ Error: {error}</p>
        <a href="/" className="text-emerald-400 underline">Back to Home</a>
      </div>
    );
  }

  if (!data) return null;

  const details = data.details || {};
  const weights = details.weights || {};
  const rmse = details.rmse || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/30 to-slate-900 text-white p-6">
      <div className="max-w-4xl mx-auto bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-8 shadow-xl">
        <h1 className="text-3xl font-bold text-emerald-400 mb-4">
          {data.symbol} – Ensemble Prediction Report
        </h1>

        <p className="text-slate-400 mb-6">Interval: {data.interval}</p>

        <div className="bg-slate-900/50 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-emerald-300 mb-2">🧠 Prediction Summary</h2>
          <p className="text-slate-200 text-lg mb-2">
            Next Predicted Price:{" "}
            <span className="text-emerald-400 font-bold">
              ${data.prediction.toFixed(2)}
            </span>
          </p>
          <p className="text-slate-400 text-sm">
            Predicted for: {data.predicted_for_bhd}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-emerald-300 mb-3">
              ⚙️ Model Contributions
            </h3>
            <ul className="text-slate-300 space-y-1">
              <li>BLSTM Prediction: ${details.blstm?.toFixed(2)}</li>
              <li>XGBoost Prediction: ${details.xgb?.toFixed(2)}</li>
            </ul>
            <div className="mt-3 text-slate-400 text-sm">
              Weights → BLSTM: {(weights.blstm * 100).toFixed(2)}% | 
              XGB: {(weights.xgb * 100).toFixed(2)}%
            </div>
          </div>

          <div className="bg-slate-900/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-emerald-300 mb-3">
              📊 Model Performance
            </h3>
            {rmse && (
              <ul className="text-slate-300 space-y-1">
                <li>BLSTM RMSE: {rmse.rmse_lstm?.toFixed(4) ?? "N/A"}</li>
                <li>XGBoost RMSE: {rmse.rmse_xgb?.toFixed(4) ?? "N/A"}</li>
              </ul>
            )}
          </div>
        </div>

        <div className="mt-8 text-center">
          <a
            href="/"
            className="inline-block px-6 py-3 bg-emerald-500/20 border border-emerald-400/30 rounded-xl hover:bg-emerald-500/30 transition-all text-emerald-300"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
