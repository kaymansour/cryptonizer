"""
Debug yfinance data structure
"""

import yfinance as yf
import pandas as pd

# Test single symbol
print("Testing single symbol download...")
data_single = yf.download('BTC-USD', period='5d', progress=False)
print("Single symbol data:")
print(f"Type: {type(data_single)}")
print(f"Shape: {data_single.shape}")
print(f"Columns: {data_single.columns.tolist()}")
print(f"Index: {data_single.index}")
print("Sample data:")
print(data_single.head(2))

print("\n" + "="*50 + "\n")

# Test multiple symbols
print("Testing multiple symbol download...")
data_multi = yf.download(['BTC-USD', 'ETH-USD'], period='5d', progress=False)
print("Multiple symbols data:")
print(f"Type: {type(data_multi)}")
print(f"Shape: {data_multi.shape}")
print(f"Columns: {data_multi.columns}")
print(f"Column levels: {data_multi.columns.nlevels}")
print("Sample data:")
print(data_multi.head(2))

# Test accessing Close price for single symbol
print("\n" + "="*30 + "\n")
print("Accessing Close price for single symbol:")
close_single = data_single['Close']
print(f"Type: {type(close_single)}")
print(f"Shape: {close_single.shape}")
print("Sample:")
print(close_single.head(2))
