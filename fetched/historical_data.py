"""Backward compatibility shim for pipelines.historical_data."""

from pipelines.historical_data import *
from pipelines.historical_data import fetch_real_historical_data

if __name__ == "__main__":
    fetch_real_historical_data()