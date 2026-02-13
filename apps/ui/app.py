import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8001")

st.set_page_config(page_title="CHAiNALYZE Baukasten", layout="wide")
st.title("CHAiNALYZE / Hydra AI")
page = st.sidebar.selectbox(
    "Page",
    ["Overview", "Instruments", "Providers", "LLM", "Agents", "Features", "Feature Backfill", "Feature Explorer", "Runs", "Alerts", "Ops/Health"],
)


def api_get(path: str, **kwargs):
    return requests.get(f"{API_URL}{path}", timeout=20, **kwargs).json()


def api_post(path: str, json_data: dict):
    return requests.post(f"{API_URL}{path}", json=json_data, timeout=20).json()


if page == "Overview":
    st.subheader("Global Status")
    st.json(api_get("/health"))
    instruments = api_get("/instruments")
    st.dataframe(pd.DataFrame(instruments))

elif page == "Instruments":
    st.subheader("Instruments")
    st.dataframe(pd.DataFrame(api_get("/instruments")))
    with st.form("add_inst"):
        symbol = st.text_input("symbol", value="BTCUSDT")
        display_name = st.text_input("display_name", value="Bitcoin")
        asset_class = st.selectbox("asset_class", ["crypto", "metals", "index"])
        submitted = st.form_submit_button("Add/Save")
        if submitted:
            st.json(api_post("/instruments", {"symbol": symbol, "display_name": display_name, "asset_class": asset_class}))

elif page == "Providers":
    st.subheader("Provider Toolbox")
    st.dataframe(pd.DataFrame(api_get("/providers")))
    with st.form("provider_form"):
        ptype = st.selectbox("provider_type", ["binance_spot", "demo_csv", "generic_http"])
        name = st.text_input("name", value="My Provider")
        enabled = st.checkbox("enabled", value=True)
        secret = st.text_input("secret (write-only)", type="password")
        submitted = st.form_submit_button("Create Provider")
        if submitted:
            payload = {"provider_type": ptype, "name": name, "enabled": enabled, "settings_jsonb": {}, "secret": secret or None}
            st.json(api_post("/providers", payload))

elif page == "LLM":
    st.subheader("Gemini Settings")
    st.json(api_get("/llm"))
    with st.form("llm_form"):
        enabled = st.checkbox("Enable Gemini", value=False)
        model = st.text_input("Model", value="gemini-1.5-flash")
        api_key = st.text_input("API key (write-only)", type="password")
        submitted = st.form_submit_button("Save LLM Settings")
        if submitted:
            st.json(api_post("/llm", {"enabled": enabled, "settings_jsonb": {"model": model}, "secret": api_key or None}))
    if st.button("Test LLM"):
        st.json(api_post("/llm/test", {}))

elif page == "Agents":
    st.subheader("Agents Toolbox")
    st.dataframe(pd.DataFrame(api_get("/agents")))
    agent_name = st.text_input("agent name", value="RegimeDetectionAgent")
    with st.form("agent_form"):
        enabled = st.checkbox("enabled", value=True)
        mode = st.selectbox("mode", ["deterministic", "llm_augmented"])
        model = st.text_input("model", value="gemini-1.5-flash")
        system_prompt = st.text_area("system_prompt", value="Return strict JSON")
        user_tpl = st.text_area("user_prompt_template", value="Analyze {symbol}")
        submitted = st.form_submit_button("Save Agent Config")
        if submitted:
            st.json(requests.put(f"{API_URL}/agents/{agent_name}", json={"enabled": enabled, "mode": mode, "model": model, "system_prompt": system_prompt, "user_prompt_template": user_tpl}, timeout=20).json())
    if st.button("Save Prompt Version"):
        st.json(api_post(f"/agents/{agent_name}/version", {}))
    st.write("Versions")
    st.dataframe(pd.DataFrame(api_get(f"/agents/{agent_name}/versions")))


elif page == "Features":
    st.subheader("Feature Definitions")
    st.dataframe(pd.DataFrame(api_get("/features/definitions")))
    registry = api_get("/features/registry")
    st.write("Available indicators", registry)
    with st.form("feature_def"):
        mode = st.selectbox("type", ["indicator", "formula"])
        name = st.text_input("name", value="BTCUSDT_rsi_14_1h")
        instrument_id = st.number_input("instrument_id", min_value=1, value=1)
        timeframe = st.selectbox("timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
        feature_key = st.text_input("feature_key", value="rsi_14")
        indicator_type = st.selectbox("indicator_type", ["rsi", "ema", "atr", "macd", "bbands", "sma", "vwap", "roc", "volume_sma"])
        formula_expr = st.text_input("formula_expr", value="rsi_14 < 30")
        submitted = st.form_submit_button("Save Feature")
        if submitted:
            payload = {
                "name": name,
                "enabled": True,
                "instrument_id": int(instrument_id),
                "timeframe": timeframe,
                "feature_key": feature_key,
                "type": mode,
                "indicator_type": indicator_type if mode == "indicator" else None,
                "params_jsonb": {"length": 14, "source": "close"} if mode == "indicator" else {},
                "formula_expr": formula_expr if mode == "formula" else None,
                "output_schema_jsonb": {"kind": "bool" if feature_key.endswith("_bool") else "num"},
            }
            st.json(api_post("/features/definitions", payload))

    expr = st.text_input("Validate formula", value="close > ema_200")
    if st.button("Validate"):
        st.json(api_post("/features/validate-formula", {"expression": expr}))

elif page == "Feature Backfill":
    st.subheader("Feature Backfill")
    defs = api_get("/features/definitions")
    st.dataframe(pd.DataFrame(defs))
    with st.form("backfill"):
        feature_id = st.number_input("feature_definition_id", min_value=1, value=1)
        instrument_id = st.number_input("instrument_id", min_value=1, value=1)
        days = st.slider("days", 1, 365, 30)
        submitted = st.form_submit_button("Run Backfill")
        if submitted:
            st.json(api_post(f"/features/definitions/{int(feature_id)}/backfill", {"instrument_id": int(instrument_id), "days": int(days)}))

elif page == "Feature Explorer":
    st.subheader("Feature Explorer")
    symbol = st.text_input("instrument symbol", value="BTCUSDT")
    tf = st.selectbox("tf", ["1h", "4h", "1d"])
    feature_key = st.text_input("feature_key", value="rsi_14")
    values = api_get("/features/values", params={"instrument": symbol, "tf": tf, "feature_key": feature_key})
    df = pd.DataFrame(values)
    st.dataframe(df)
    if not df.empty and "value_num" in df.columns:
        st.line_chart(df.set_index("ts")["value_num"])

elif page == "Runs":
    st.subheader("Runs")
    runs = api_get("/runs")
    st.dataframe(pd.DataFrame(runs))

elif page == "Alerts":
    st.subheader("Alert Settings")
    st.json(api_get("/alerts/config"))
    with st.form("alerts"):
        enabled = st.checkbox("Telegram enabled")
        token = st.text_input("telegram secret (write-only)", type="password")
        submitted = st.form_submit_button("Save")
        if submitted:
            st.json(api_post("/alerts/config", {"telegram_enabled": enabled, "telegram_secret": token or None, "rules_jsonb": {}}))

else:
    st.subheader("Ops / Health")
    st.json(api_get("/health"))
    st.info("Use /metrics for Prometheus scraping.")
