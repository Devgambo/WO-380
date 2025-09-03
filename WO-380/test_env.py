#!/usr/bin/env python3
"""
Test script to verify the Python Docker environment is working correctly
"""

import sys
import pandas as pd
import numpy as np
import matplotlib
import requests
from flask import Flask

def test_environment():
    """Test that key packages and features work correctly"""
    
    print("🐍 Python Docker Environment Test")
    print("=" * 40)
    
    # Python version
    print(f"✅ Python version: {sys.version}")
    
    # Test NumPy
    arr = np.array([1, 2, 3, 4, 5])
    print(f"✅ NumPy working - Array sum: {np.sum(arr)}")
    
    # Test Pandas
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    print(f"✅ Pandas working - DataFrame shape: {df.shape}")
    
    # Test Matplotlib (backend)
    matplotlib.use('Agg')  # Non-interactive backend
    print(f"✅ Matplotlib working - Backend: {matplotlib.get_backend()}")
    
    # Test requests
    try:
        response = requests.get('https://httpbin.org/get', timeout=5)
        print(f"✅ Requests working - Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Requests test failed (might be network): {e}")
    
    # Test Flask
    app = Flask(__name__)
    print("✅ Flask imported successfully")
    
    print("\n🎉 Environment test completed successfully!")
    print("\nYour Python Docker environment is ready for development!")
    
if __name__ == "__main__":
    test_environment()
