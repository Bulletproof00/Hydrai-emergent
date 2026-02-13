import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8001")

st.set_page_config(page_title="CHAiNALYZE Baukasten", layout="wide")
st.title("CHAiNALYZE / Hydra AI")
page = st.sidebar.selectbox(
    "Page",
    ["Overview", "Instruments", "Providers", "LLM", "Agents", "Runs", "Alerts", "Ops/Health"],
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
