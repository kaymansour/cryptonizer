#!/usr/bin/env python3
"""
Cleanup script to delete all old scaler files
Run this BEFORE retraining models to ensure no mismatched scaler/model pairs
"""

import os
import glob

# Find all scaler files in models directory
scaler_files = glob.glob("models/*_scaler.pkl")

print(f"\n{'='*60}")
print("SCALER CLEANUP")
print(f"{'='*60}\n")

if not scaler_files:
    print("✅ No scaler files found - already clean!")
else:
    print(f"Found {len(scaler_files)} scaler files to delete:\n")
    
    for scaler_file in scaler_files:
        print(f"  🗑️  Deleting: {scaler_file}")
        try:
            os.remove(scaler_file)
            print(f"     ✅ Deleted")
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Cleanup complete! Safe to retrain models now.")
    print(f"{'='*60}\n")
