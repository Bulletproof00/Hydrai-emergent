import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8001")

st.set_page_config(page_title="CHAiNALYZE Dashboard", layout="wide")
st.title("CHAiNALYZE / Hydra AI Dashboard")

page = st.sidebar.selectbox("Page", ["Overview", "Instrument Detail", "Runs"])

if page == "Overview":
    st.header("Overview")
    instruments = requests.get(f"{API_URL}/instruments", timeout=10).json()
    st.dataframe(pd.DataFrame(instruments))

elif page == "Instrument Detail":
    instruments = requests.get(f"{API_URL}/instruments", timeout=10).json()
    symbols = [i["symbol"] for i in instruments] or ["BTC/USDT"]
    symbol = st.selectbox("Symbol", symbols)
    candles = requests.get(f"{API_URL}/candles", params={"symbol": symbol, "tf": "5m"}, timeout=10).json()
    findings = requests.get(f"{API_URL}/latest/findings", params={"symbol": symbol}, timeout=10).json()
    signals = requests.get(f"{API_URL}/latest/signals", params={"symbol": symbol}, timeout=10).json()

    if candles:
        df = pd.DataFrame(candles)
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df["ts"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                )
            ]
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Findings")
    st.dataframe(pd.DataFrame(findings))
    st.subheader("Signals")
    st.dataframe(pd.DataFrame(signals))

else:
    st.header("Runs")
    st.info("Use /runs/{run_id} endpoint from API for detailed run inspection in MVP.")
