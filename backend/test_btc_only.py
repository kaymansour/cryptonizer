#!/usr/bin/env python3
"""
Test script: Delete BTC scaler and retrain only BTC model
Use this to verify the fix works before retraining all models
"""

import os
import glob

print(f"\n{'='*60}")
print("BTC-ONLY TEST")
print(f"{'='*60}\n")

# Step 1: Delete only BTC scalers
btc_scalers = glob.glob("models/BTC-USD*_scaler.pkl")

if btc_scalers:
    print(f"Found {len(btc_scalers)} BTC scaler file(s):\n")
    for scaler in btc_scalers:
        print(f"  🗑️  Deleting: {scaler}")
        try:
            os.remove(scaler)
            print(f"     ✅ Deleted\n")
        except Exception as e:
            print(f"     ❌ Error: {e}\n")
else:
    print("⚠️  No BTC scaler files found\n")

print(f"{'='*60}")
print("TRAINING BTC MODEL")
print(f"{'='*60}\n")

# Step 2: Train only BTC
from models.hybrid_predictor import HybridPredictor

predictor = HybridPredictor("BTC-USD", interval="4h", auto_select=False)
result = predictor.train(epochs=100, batch_size=32)

print(f"\n{'='*60}")
print("TRAINING COMPLETE")
print(f"{'='*60}")
print(f"Model Type: {result.get('model_type', 'Unknown')}")
print(f"Test MSE: {result['test_loss']:.6f}")
print(f"Test MAE: {result['test_mae']:.6f}")
print(f"Training Samples: {result['training_samples']}")
print(f"Test Samples: {result['test_samples']}")

# Step 3: Test a prediction
print(f"\n{'='*60}")
print("TESTING PREDICTION")
print(f"{'='*60}\n")

import yfinance as yf
data = yf.download("BTC-USD", period="2mo", interval="4h", progress=False)
pred = predictor.predict_next(data)

print(f"Current Price: ${pred['current_price']:,.2f}")
print(f"Predicted Price: ${pred['predicted_price']:,.2f}")
print(f"Predicted Change: {pred['predicted_change_percent']:.2f}%")
print(f"Signal: {pred['signal']}")

print(f"\n{'='*60}")
if abs(pred['predicted_change_percent']) < 10:
    print("✅ LOOKS GOOD! Prediction is realistic (< 10%)")
    print("   Safe to delete all scalers and retrain all models")
else:
    print("⚠️  WARNING! Prediction seems unrealistic (> 10%)")
    print("   There may still be an issue")
print(f"{'='*60}\n")
