
from __future__ import annotations

from pathlib import Path
import re
import tempfile
import uuid
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from main import build_report, build_comparison_report, build_single_report_frames


APP_TITLE = "CiscoIQ-SaaS-Support-Services Performance Dashboard"


st.markdown("""
<style>
.stFileUploader {
    background: white;
    border-radius: 18px;
    padding: 14px;
    border: 1px solid #dbe4f0;
    box-shadow: 0 8px 24px rgba(15,23,42,.05);
}
.stButton>button[kind="primary"] {
    background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    height: 48px !important;
}

/* v59 main page exact polish */
.hero-title-box {
    display: table;
    margin: 18px auto 10px auto;
    width: auto;
    max-width: fit-content;
    background: linear-gradient(135deg,#07132f 0%, #102a63 55%, #2d2b7f 100%);
    color: white;
    border-radius: 18px;
    padding: 18px 28px;
    box-shadow: 0 16px 34px rgba(7,19,47,.18);
}
.hero-title-box h1 {
    margin: 0;
    font-size: 24px;
    line-height: 1.18;
    font-weight: 850;
    white-space: nowrap;
}
.hero-subtitle {
    text-align: center;
    color: #334155;
    font-size: 15px;
    margin: 0 auto 18px auto;
    max-width: 980px;
}

/* v61 dashboard header + tabs polish */
.top-nav {
    background: linear-gradient(90deg,#06122f 0%, #081a3f 54%, #0b1f55 100%) !important;
    color:white !important;
    border-radius: 0 0 16px 16px !important;
    padding: 14px 22px !important;
    margin: -0.6rem -1rem 12px -1rem !important;
    box-shadow: 0 10px 28px rgba(6,18,47,.22) !important;
}
.brand-icon {
    width:40px !important;
    height:40px !important;
    border-radius:12px !important;
    background:linear-gradient(135deg,#2563eb,#7c3aed) !important;
    font-size:20px !important;
}
.brand-title {
    font-size:22px !important;
    font-weight:900 !important;
    letter-spacing:-.35px !important;
}
.brand-sub {
    font-size:12px !important;
    opacity:.82 !important;
}
.nav-time {
    font-size:12px !important;
    opacity:.88 !important;
}

/* Streamlit radio used as dashboard tabs */
div[role="radiogroup"] {
    display:flex !important;
    justify-content:center !important;
    gap:14px !important;
    background: #ffffff !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 14px !important;
    padding: 10px !important;
    margin: 0 0 14px 0 !important;
    box-shadow: 0 8px 20px rgba(15,23,42,.045) !important;
}
div[role="radiogroup"] label {
    background: #f8fbff !important;
    border: 1px solid #e0e7f3 !important;
    border-radius: 12px !important;
    padding: 8px 14px !important;
    min-width: 118px !important;
    text-align: center !important;
    font-weight: 800 !important;
    color: #0f2b68 !important;
    transition: .15s ease-in-out !important;
}
div[role="radiogroup"] label:hover {
    border-color:#2563eb !important;
    box-shadow:0 8px 18px rgba(37,99,235,.12) !important;
}
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
    display:none !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg,#4f46e5,#2563eb) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 12px 24px rgba(37,99,235,.28) !important;
}

/* Overview title strip */
.overview-title-card {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:16px;
    padding:0;
    box-shadow:0 8px 22px rgba(15,23,42,.05);
    margin-bottom:12px;
}
.overview-title-pill {
    display:inline-block;
    background:linear-gradient(90deg,#2333a3,#3152d9);
    color:white;
    padding:9px 18px;
    border-radius:12px 12px 12px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}
.overview-title-sub {
    color:#667085;
    font-size:13px;
    padding:0 18px 12px 18px;
}


/* v62 Aggregated summary cards like reference image */
.agg-summary-card {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:0 0 12px 0;
    box-shadow:0 8px 22px rgba(15,23,42,.045);
    margin-bottom:14px;
}
.agg-summary-title {
    display:inline-block;
    background:linear-gradient(90deg,#2333a3,#3152d9);
    color:#ffffff;
    padding:9px 18px;
    border-radius:12px 12px 12px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}
.agg-kpi-row {
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap:0;
    padding:10px 16px 0 16px;
}
.agg-kpi {
    display:flex;
    align-items:center;
    gap:14px;
    min-height:130px;
    padding:10px 18px;
    border-right:1px solid #e5edf7;
}
.agg-kpi:last-child {
    border-right:none;
}
.agg-icon {
    width:44px;
    height:44px;
    border-radius:10px;
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:23px;
    font-weight:900;
    box-shadow:0 10px 20px rgba(15,23,42,.16);
    flex:0 0 44px;
}
.agg-label {
    font-size:13px;
    font-weight:850;
    color:#111827;
    margin-bottom:8px;
}
.agg-value {
    font-size:28px;
    font-weight:900;
    color:#111827;
    line-height:1.0;
    letter-spacing:-.4px;
}
.agg-suffix {
    font-size:13px;
    color:#667085;
    font-weight:650;
    margin-left:5px;
}
.agg-delta {
    font-size:12px;
    margin-top:10px;
    color:#667085;
    font-weight:650;
}
.agg-delta.good { color:#15803d; }
.agg-delta.bad { color:#ef4444; }
.agg-spark {
    width:132px;
    height:24px;
    margin-top:9px;
}
@media(max-width:1100px){
  .agg-kpi-row {grid-template-columns: repeat(2, 1fr);}
  .agg-kpi:nth-child(2n){border-right:none;}
}


/* v66 clickable top dashboard buttons */
.nav-button-row {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:10px;
    margin-bottom:14px;
    box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.nav-button-row + div button, .stButton > button {
    border-radius:12px !important;
    font-weight:800 !important;
}


/* v67 real clickable dashboard anchor tabs */
.dash-tabs {
    display:flex;
    justify-content:center;
    gap:12px;
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:10px;
    margin:0 0 14px 0;
    box-shadow:0 8px 20px rgba(15,23,42,.045);
    flex-wrap:wrap;
}
.dash-tab {
    text-decoration:none !important;
    background:#f8fbff;
    border:1px solid #e0e7f3;
    border-radius:12px;
    padding:9px 14px;
    min-width:118px;
    text-align:center;
    font-weight:850;
    color:#0f2b68 !important;
    transition:.15s ease-in-out;
    display:inline-block;
}
.dash-tab:hover {
    border-color:#2563eb;
    box-shadow:0 8px 18px rgba(37,99,235,.12);
    transform:translateY(-1px);
}
.dash-tab.active {
    background:linear-gradient(90deg,#4f46e5,#2563eb);
    color:#ffffff !important;
    border-color:transparent;
    box-shadow:0 12px 24px rgba(37,99,235,.28);
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title=APP_TITLE, layout="wide")

params = st.query_params
dashboard_only = params.get("view", "") == "dashboard"
run_id = params.get("run_id", "")


@st.cache_resource
def get_dashboard_store():
    return {}


dashboard_store = get_dashboard_store()


st.markdown(
    """
<style>
:root {
  --navy:#07132f;
  --navy2:#0a1b3f;
  --blue:#2563eb;
  --purple:#6d28d9;
  --green:#16a34a;
  --red:#dc2626;
  --orange:#f59e0b;
  --card:#ffffff;
  --border:#dbe4f0;
  --muted:#667085;
}
.stApp {
  background: #f4f7fb;
  color: #111827;
}
[data-testid="stHeader"] { background: transparent; }
.block-container {
  max-width: 1560px;
  padding: 0.6rem 1rem 1.6rem 1rem;
}
#MainMenu, footer { visibility: hidden; }
.app-shell {
  background: white;
  border: 1px solid #dce3ef;
  border-radius: 18px;
  padding: 12px;
  box-shadow: 0 10px 30px rgba(10,27,63,0.06);
}
.hero {
  background:
    radial-gradient(circle at 20% 20%, rgba(59,130,246,.22), transparent 28%),
    radial-gradient(circle at 80% 10%, rgba(124,58,237,.28), transparent 26%),
    linear-gradient(135deg,#07132f 0%, #0a1b3f 50%, #0f2b68 100%);
  color:white;
  border-radius: 18px;
  padding: 12px 22px;
  box-shadow: 0 14px 32px rgba(7,19,47,.18);
  margin-bottom: 18px;
}
.hero h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.15;
  font-weight: 850;
  letter-spacing:-.4px;
}
.hero p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,.82);
  font-size: 14px;
}
.hero-actions {
  display:flex;
  gap:12px;
  align-items:center;
  margin-top: 18px;
  flex-wrap: wrap;
}
.primary-pill {
  display:inline-block;
  background: linear-gradient(90deg,#4f46e5,#2563eb);
  color:white !important;
  text-decoration:none !important;
  padding: 10px 16px;
  border-radius: 12px;
  font-weight:750;
  box-shadow: 0 12px 24px rgba(37,99,235,.24);
}
.secondary-pill {
  display:inline-block;
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.20);
  color:white !important;
  text-decoration:none !important;
  padding: 9px 14px;
  border-radius: 12px;
  font-weight:650;
}
.top-nav {
  display:flex;
  align-items:center;
  justify-content:space-between;
  background: linear-gradient(90deg,#07132f,#0a1b3f);
  color:white;
  border-radius: 0 0 14px 14px;
  padding: 12px 18px;
  margin: -0.6rem -1rem 14px -1rem;
  box-shadow: 0 8px 22px rgba(7,19,47,.14);
}
.brand {
  display:flex;
  align-items:center;
  gap: 12px;
}
.brand-icon {
  width:34px;height:34px;border-radius:10px;
  background:linear-gradient(135deg,#4f46e5,#06b6d4);
  display:flex;align-items:center;justify-content:center;
  font-size:18px;
}
.brand-title { font-size:19px;font-weight:850;line-height:1.1; }
.brand-sub { font-size:11px;color:rgba(255,255,255,.72);margin-top:2px;}
.nav-tabs {
  display:flex;
  gap: 8px;
  align-items:center;
}
.nav-tab {
  color:white;
  padding:8px 12px;
  border-radius:10px;
  font-size:13px;
  font-weight:650;
  opacity:.9;
}
.nav-tab.active {
  background: linear-gradient(90deg,#4f46e5,#2563eb);
  box-shadow:0 8px 16px rgba(37,99,235,.28);
}
.nav-time {font-size:11px;color:rgba(255,255,255,.82);text-align:right;}
.panel {
  background: white;
  border: 1px solid var(--border);
  border-radius: 13px;
  padding: 14px;
  box-shadow: 0 8px 20px rgba(15,23,42,.045);
  margin-bottom: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 850;
  color: #0f2b68;
  margin-bottom: 12px;
  display:flex;
  align-items:center;
  justify-content:space-between;
}
.panel-title .tag {
  font-size:11px;
  background:#eef4ff;
  color:#2563eb;
  padding:3px 8px;
  border-radius:999px;
}
.kpi-grid {
  display:grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}
.kpi-card {
  background:white;
  border:1px solid var(--border);
  border-radius:14px;
  padding:14px;
  min-height:96px;
  box-shadow: 0 6px 18px rgba(15,23,42,.045);
  display:flex;
  gap:12px;
  align-items:flex-start;
}
.kpi-icon {
  width:38px;height:38px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  color:white;font-size:19px;flex:0 0 38px;
  box-shadow: 0 10px 18px rgba(0,0,0,.12);
}
.kpi-label { font-size:12px;color:#111827;font-weight:750; }
.kpi-value { font-size:24px;font-weight:850;color:#111827;margin-top:6px;line-height:1.0; }
.kpi-sub { font-size:11px;color:var(--muted);margin-top:8px; }
.kpi-sub.good { color:#15803d; }
.kpi-sub.bad { color:#dc2626; }
.grid-3 {
  display:grid;
  grid-template-columns: 1.1fr 1fr 1fr;
  gap:12px;
}
.grid-2 {
  display:grid;
  grid-template-columns: 1.1fr .9fr;
  gap:12px;
}
.side-card {
  background:white;
  border:1px solid var(--border);
  border-radius:13px;
  padding:14px;
  box-shadow: 0 8px 20px rgba(15,23,42,.045);
  margin-bottom:12px;
}
.insight-item {
  display:flex;
  gap:10px;
  align-items:flex-start;
  margin: 10px 0;
  font-size:13px;
  color:#1f2937;
}
.dot {
  width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  color:white;font-size:12px;font-weight:800;flex:0 0 22px;
}
.filter-card {
  background:#f8fbff;
  border:1px solid var(--border);
  border-radius:12px;
  padding: 12px;
}
.chat-card {
  background:white;
  border: 1px solid #c7b7ff;
  border-radius:13px;
  padding:14px;
  box-shadow: 0 8px 22px rgba(109,40,217,.10);
}
.chat-header {
  background:linear-gradient(90deg,#6d28d9,#7c3aed);
  color:white;
  padding:10px 12px;
  border-radius:10px;
  font-size:13px;
  font-weight:800;
  margin:-2px -2px 12px -2px;
}
.mini-link {
  color:#2563eb !important;
  font-size:12px;
  font-weight:700;
  text-decoration:none !important;
}
.stButton > button {
  border-radius: 10px !important;
  font-weight: 750 !important;
}
.stDownloadButton > button {
  border-radius: 10px !important;
  font-weight: 750 !important;
}
[data-testid="stFileUploader"] {
  background:white;
  border:1px dashed #a6b4ca;
  border-radius:14px;
  padding: 16px;
}
[data-testid="stMetric"] {
  background:white;
  border-radius: 12px;
}
.upload-card {
  max-width: 1100px;
  margin: 0 auto;
}
.main-page-card {
  background:white;
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
  box-shadow: 0 12px 30px rgba(15,23,42,.06);
  margin-bottom:16px;
}
.feature-grid {
  display:grid;
  grid-template-columns: repeat(3, 1fr);
  gap:12px;
  margin-top:14px;
}
.feature {
  border:1px solid #e3e9f5;
  border-radius:14px;
  padding:14px;
  background:#fbfdff;
}
.feature h4 { margin:0 0 6px 0;font-size:14px;color:#0f2b68; }
.feature p { margin:0;color:#667085;font-size:12px; }
@media(max-width:1100px){
  .kpi-grid,.grid-3,.grid-2,.feature-grid {grid-template-columns:1fr;}
  .nav-tabs {display:none;}
}

/* Executive KPI metric styling */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 14px !important;
    padding: 16px 16px !important;
    box-shadow: 0 8px 20px rgba(15,23,42,.055) !important;
    min-height: 104px !important;
}
div[data-testid="stMetricLabel"] {
    font-weight: 800 !important;
    color: #111827 !important;
}
div[data-testid="stMetricValue"] {
    font-weight: 850 !important;
    color: #111827 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


def get_store():
    return dashboard_store


def add_ui_sla_columns(apis_df: pd.DataFrame) -> pd.DataFrame:
    df = apis_df.copy()
    if df.empty:
        return df
    df["Feature"] = df["Feature"].astype(str)
    df["Scenario"] = df.get("Scenario", "").astype(str)
    df["Endpoint"] = df.get("Endpoint", "").astype(str)
    df["API"] = df["Feature"] + "/" + df["Scenario"] + "/" + df["Endpoint"]
    for col in [
        "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec",
        "90thPercentile Resp Time in Sec", "95thPercentile Resp Time in Sec",
        "99thPercentile Resp Time in Sec", "sampleCount", "errorCount", "errorPct",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["SLA Sec"] = df["Feature"].str.upper().str.startswith("ASKAI").map({True: 10, False: 2})
    df["SLA Status"] = (df["Avg ResTime in sec"] < df["SLA Sec"]).map({True: "PASS", False: "FAIL"})
    df["SLA Breach Sec"] = (df["Avg ResTime in sec"] - df["SLA Sec"]).clip(lower=0).round(2)
    df["Track Type"] = df["Feature"].str.upper().str.startswith("ASKAI").map({True: "AskAI", False: "Other"})
    return df


def process_uploaded_file(path: Path, label: str) -> Dict[str, pd.DataFrame]:
    frames = build_single_report_frames(path)
    frames["APIs"] = add_ui_sla_columns(frames["APIs"])
    frames["Label"] = label
    frames["Region"] = region_from_frames(frames)
    return frames


def region_from_frames(frames: Dict[str, pd.DataFrame]) -> str:
    info = frames.get("Run_Info")
    if info is not None and not info.empty and "Region" in info.columns:
        region = str(info.iloc[0].get("Region", "N/A")).strip()
        if region and region.upper() != "N/A":
            return region
    label = str(frames.get("Label", ""))
    upper = label.upper()
    for region in ["APJC", "EMEA", "US", "AMER", "EU", "LATAM", "INDIA"]:
        if re.search(rf"(?:^|[_\-\s]){region}(?:$|[_\-\s])", upper):
            return region
    return "Unknown"


def add_region_to_frames(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Dict[str, pd.DataFrame]]:
    for frames in run_frames:
        frames["Region"] = region_from_frames(frames)
    return run_frames


def summarize_run(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return dict(avg_sec=0, success_rate=0, error_rate=0, transactions=0, performance_score=0, sla_compliance=0, errors=0, samples=0, p95_sec=0, max_sec=0)
    samples = pd.to_numeric(df.get("sampleCount", 0), errors="coerce").fillna(0).sum()
    errors = pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0).sum()
    success_rate = round(((samples - errors) / samples) * 100, 2) if samples else 0
    error_rate = round((errors / samples) * 100, 2) if samples else 0
    sla_pass_pct = round(df["SLA Status"].eq("PASS").sum() / len(df) * 100, 2) if len(df) else 0
    score = round(max(0, min(100, sla_pass_pct - error_rate)), 2)
    return dict(
        avg_sec=round(float(df["Avg ResTime in sec"].mean()), 2),
        success_rate=success_rate,
        error_rate=error_rate,
        transactions=int(len(df)),
        performance_score=score,
        sla_compliance=sla_pass_pct,
        errors=int(errors),
        samples=int(samples),
        p95_sec=round(float(df["95thPercentile Resp Time in Sec"].mean()), 2) if "95thPercentile Resp Time in Sec" in df.columns else 0,
        max_sec=round(float(df["MaxRes Time in sec"].max()), 2) if "MaxRes Time in sec" in df.columns else 0,
    )


def safe_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in cols if c in df.columns]


def track_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = (
        df.groupby(["Feature", "Track Type"], dropna=False)
        .agg(
            APIs=("API", "count"),
            Avg_Sec=("Avg ResTime in sec", "mean"),
            P95_Sec=("95thPercentile Resp Time in Sec", "mean"),
            Max_Sec=("MaxRes Time in sec", "max"),
            Errors=("errorCount", "sum"),
            ErrorPct=("errorPct", "mean"),
            SLA_Fails=("SLA Status", lambda x: (x == "FAIL").sum()),
            Samples=("sampleCount", "sum"),
        )
        .reset_index()
    )
    out["SLA Fail %"] = (out["SLA_Fails"] / out["APIs"] * 100).round(2)
    for col in ["Avg_Sec", "P95_Sec", "Max_Sec", "ErrorPct"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).round(2)
    return out.sort_values(["P95_Sec", "Avg_Sec", "Errors"], ascending=False)


def sla_color_for_track(track_name: str, p95_value: float) -> float:
    threshold = 10 if str(track_name).upper().startswith("ASKAI") else 2
    return 1 if float(p95_value or 0) < threshold else 0


def combined_df(run_frames: List[Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    parts = []
    for frames in run_frames:
        tmp = frames["APIs"].copy()
        tmp["Run"] = frames["Label"]
        tmp["Region"] = frames.get("Region", region_from_frames(frames))
        parts.append(tmp)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()







def top_nav() -> str:
    current_tab = params.get("tab", "") or st.session_state.get("dashboard_tab", "Overview")
    if "nav_target" in st.session_state:
        current_tab = st.session_state.pop("nav_target")

    valid_tabs = ["Overview", "Track Comparison", "Compare", "Trends", "Drilldown", "Reports", "Chatbot"]
    if current_tab not in valid_tabs:
        current_tab = "Overview"
    st.session_state["dashboard_tab"] = current_tab

    current_run_id = params.get("run_id", "") or st.session_state.get("run_id", "")
    tabs = [
        ("Overview", "🏠 Overview"),
        ("Track Comparison", "📊 Track Comparison"),
        ("Compare", "🌐 Compare"),
        ("Trends", "📈 Trends"),
        ("Drilldown", "🔎 Drilldown"),
        ("Reports", "📄 Reports"),
        ("Chatbot", "💬 Chatbot"),
    ]

    links = ""
    for tab_value, tab_label in tabs:
        active_class = " active" if tab_value == current_tab else ""
        href = f"?view=dashboard&run_id={current_run_id}&tab={tab_value}"
        links += f'<a class="dash-tab{active_class}" href="{href}">{tab_label}</a>'

    st.markdown(
        f"""
<div class="top-nav">
  <div class="brand">
    <div class="brand-icon">📈</div>
    <div>
      <div class="brand-title">CiscoIQ-SaaS-Support-Services Performance Dashboard</div>
      <div class="brand-sub">Real-time performance insights across regions</div>
    </div>
  </div>
  <div class="nav-time">Dashboard View<br/>Last Updated</div>
</div>
<div class="dash-tabs">{links}</div>
""",
        unsafe_allow_html=True,
    )

    return current_tab


def kpi_cards(df: pd.DataFrame) -> None:
    s = summarize_run(df)
    sla_fail = round(100 - s["sla_compliance"], 2) if s["transactions"] else 0

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: transparent;
}}
.agg-summary-card {{
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:0 0 12px 0;
    box-shadow:0 8px 22px rgba(15,23,42,.045);
}}
.agg-summary-title {{
    display:inline-block;
    background:linear-gradient(90deg,#2333a3,#3152d9);
    color:#ffffff;
    padding:9px 18px;
    border-radius:12px 12px 12px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}}
.agg-kpi-row {{
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap:0;
    padding:10px 16px 0 16px;
}}
.agg-kpi {{
    display:flex;
    align-items:center;
    gap:14px;
    min-height:130px;
    padding:10px 18px;
    border-right:1px solid #e5edf7;
}}
.agg-kpi:last-child {{
    border-right:none;
}}
.agg-icon {{
    width:44px;
    height:44px;
    border-radius:10px;
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:23px;
    font-weight:900;
    box-shadow:0 10px 20px rgba(15,23,42,.16);
    flex:0 0 44px;
}}
.agg-label {{
    font-size:13px;
    font-weight:850;
    color:#111827;
    margin-bottom:8px;
}}
.agg-value {{
    font-size:28px;
    font-weight:900;
    color:#111827;
    line-height:1.0;
    letter-spacing:-.4px;
}}
.agg-suffix {{
    font-size:13px;
    color:#667085;
    font-weight:650;
    margin-left:5px;
}}
.agg-delta {{
    font-size:13px;
    margin-top:10px;
    color:#667085;
    font-weight:700;
    line-height:1.25;
    white-space:normal;
}}
.agg-delta.good {{ color:#15803d; }}
.agg-delta.bad {{ color:#ef4444; }}
.agg-spark {{
    width:132px;
    height:24px;
    margin-top:9px;
}}
@media(max-width:1100px){{
  .agg-kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .agg-kpi:nth-child(2n){{border-right:none;}}
}}
</style>
</head>
<body>
<div class="agg-summary-card">
  <div class="agg-summary-title">AGGREGATED PERFORMANCE OVERVIEW METRICS</div>
  <div class="agg-kpi-row">

    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#2563eb,#4f46e5);">🛡</div>
      <div>
        <div class="agg-label">Health Score</div>
        <div class="agg-value">{s['performance_score']}<span class="agg-suffix">/100</span></div>
        <svg class="agg-spark" viewBox="0 0 130 28" xmlns="http://www.w3.org/2000/svg">
          <polyline points="2,20 16,19 29,20 42,17 55,18 68,11 81,16 94,18 107,9 124,14 129,8"
            fill="none" stroke="#22a447" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#16843a;">✓</div>
      <div>
        <div class="agg-label">SLA Pass %</div>
        <div class="agg-value">{s['sla_compliance']}%</div>
        <div class="agg-delta good">▲ APIs meeting SLA</div>
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#dc2626;">×</div>
      <div>
        <div class="agg-label">SLA Fail %</div>
        <div class="agg-value">{sla_fail}%</div>
        <div class="agg-delta bad">▼ APIs breaching SLA</div>
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#2563eb,#3152d9);">♜</div>
      <div>
        <div class="agg-label">Total APIs</div>
        <div class="agg-value">{s['transactions']:,}</div>
        <div class="agg-delta good">▲ Compared APIs</div>
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#7c3aed,#a855f7);">◉</div>
      <div>
        <div class="agg-label">Total Samples</div>
        <div class="agg-value">{s['samples']:,}</div>
        <div class="agg-delta good">▲ Executed samples</div>
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#dc2626;">⚠</div>
      <div>
        <div class="agg-label">Total Errors</div>
        <div class="agg-value">{s['errors']:,}</div>
        <div class="agg-delta bad">▼ Failed samples</div>
      </div>
    </div>

  </div>
</div>
</body>
</html>
"""
    components.html(html, height=205, scrolling=False)


def sla_donut(df: pd.DataFrame):
    counts = df["SLA Status"].value_counts().reset_index()
    counts.columns = ["SLA Status", "Count"]
    fig = px.pie(
        counts,
        names="SLA Status",
        values="Count",
        hole=0.62,
        color="SLA Status",
        color_discrete_map={"PASS": "#2ca02c", "FAIL": "#ef4444"},
    )
    s = summarize_run(df)
    fig.update_layout(
        height=280,
        margin=dict(l=5, r=5, t=15, b=5),
        legend=dict(orientation="v", yanchor="middle", y=.5, xanchor="left", x=.82),
        annotations=[dict(text=f"<b>{s['sla_compliance']}%</b><br>PASS", x=.39, y=.5, font_size=18, showarrow=False)],
    )
    return fig


def get_filtered_frames(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Dict[str, pd.DataFrame]]:
    rows = []
    for frames in run_frames:
        info = frames.get("Run_Info")
        info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
        rows.append({
            "Label": frames["Label"],
            "Region": frames.get("Region", region_from_frames(frames)),
            "Date": str(info_row.get("Date", "N/A")),
            "Duration": str(info_row.get("Duration", "N/A")),
        })
    meta = pd.DataFrame(rows)
    files = meta["Label"].tolist()
    dates = sorted(meta["Date"].astype(str).unique().tolist())
    regions = sorted(meta["Region"].astype(str).unique().tolist())
    st.markdown('<div class="side-card"><div class="panel-title">DATA & FILTERS</div>', unsafe_allow_html=True)
    selected_files = st.multiselect("Result File", files, default=files)
    selected_dates = st.multiselect("Date", dates, default=dates)
    selected_regions = st.multiselect("Region", regions, default=regions)
    st.markdown("</div>", unsafe_allow_html=True)
    keep = meta[
        meta["Label"].isin(selected_files)
        & meta["Date"].isin(selected_dates)
        & meta["Region"].isin(selected_regions)
    ]["Label"].tolist()
    return [frames for frames in run_frames if frames["Label"] in keep] or run_frames


def auto_insights(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Tuple[str, str, str]]:
    df = combined_df(run_frames)
    s = summarize_run(df)
    tracks = track_summary(df)
    result = []
    if len(run_frames) > 1:
        summary_rows = []
        for frames in run_frames:
            row = summarize_run(frames["APIs"])
            row["Region"] = frames.get("Region", region_from_frames(frames))
            summary_rows.append(row)
        summary = pd.DataFrame(summary_rows)
        best = summary.sort_values("sla_compliance", ascending=False).iloc[0]
        worst = summary.sort_values("error_rate", ascending=False).iloc[0]
        result.append(("✓", "#16a34a", f"{best['Region']} has best SLA compliance at {best['sla_compliance']}%."))
        result.append(("!", "#ef4444", f"{worst['Region']} has highest error rate at {worst['error_rate']}%."))
    if not tracks.empty:
        worst_track = tracks.iloc[0]
        result.append(("⚠", "#f59e0b", f"{worst_track['Feature']} is top contributor for P95 latency at {worst_track['P95_Sec']}s."))
    result.append(("i", "#2563eb", f"Overall SLA compliance is {s['sla_compliance']}% with {s['errors']:,} errors."))
    return result[:5]



def response_bucket(value: float, is_askai: bool) -> str:
    value = float(value or 0)
    if is_askai:
        if value <= 10:
            return "0-10s %"
        if value <= 20:
            return "10-20s %"
        if value <= 30:
            return "20-30s %"
        return ">30s %"
    if value <= 2:
        return "0-2s %"
    if value <= 4:
        return "3-4s %"
    if value <= 6:
        return "4-6s %"
    return ">6s %"


def metric_bucket_summary(df: pd.DataFrame, track: str, metric: str, is_askai: bool) -> List[float]:
    col_map = {
        "Avg": "Avg ResTime in sec",
        "Min": "Min ResTime in sec",
        "Max": "MaxRes Time in sec",
    }
    col = col_map[metric]
    rows = df[df["Feature"].astype(str) == str(track)].copy()
    if rows.empty or col not in rows.columns:
        return [0, 0, 0, 0, 0]

    bucket_names = ["0-10s %", "10-20s %", "20-30s %", ">30s %"] if is_askai else ["0-2s %", "3-4s %", "4-6s %", ">6s %"]
    counts = dict.fromkeys(bucket_names, 0)
    values = pd.to_numeric(rows[col], errors="coerce").fillna(0)
    for value in values:
        counts[response_bucket(float(value), is_askai)] += 1
    total = len(values) if len(values) else 1
    percentages = [round(counts[name] / total * 100, 2) for name in bucket_names]
    return percentages + [round(float(values.max()), 2)]



def build_dashboard_track_comparison(run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    all_tracks = sorted(set().union(*[set(frames["APIs"]["Feature"].dropna().astype(str)) for frames in run_frames]))
    all_tracks = [t for t in all_tracks if t.lower() != "total" and "select customer" not in t.lower()]

    askai_tracks = [t for t in all_tracks if t.upper().startswith("ASKAI")]
    other_tracks = [t for t in all_tracks if not t.upper().startswith("ASKAI")]

    def metric_bucket_summary_for_rows(rows: pd.DataFrame, metric: str, is_askai: bool) -> List[float]:
        col_map = {
            "Avg": "Avg ResTime in sec",
            "Min": "Min ResTime in sec",
            "Max": "MaxRes Time in sec",
        }
        col = col_map[metric]
        bucket_names = ["0-10sec %", "10-20sec %", "20-30sec %", ">30sec %"] if is_askai else ["0-2sec %", "3-4sec %", "4-6sec %", ">6sec %"]
        if rows.empty or col not in rows.columns:
            return [0, 0, 0, 0, 0]

        counts = dict.fromkeys(bucket_names, 0)
        values = pd.to_numeric(rows[col], errors="coerce").fillna(0)
        for value in values:
            bucket = response_bucket(float(value), is_askai).replace("s %", "sec %")
            counts[bucket] = counts.get(bucket, 0) + 1
        total = len(values) if len(values) else 1
        percentages = [round(counts[name] / total * 100, 2) for name in bucket_names]
        return percentages + [round(float(values.max()), 2)]

    def build_section(tracks: List[str], is_askai: bool) -> pd.DataFrame:
        rows = []
        bucket_names = ["0-10sec %", "10-20sec %", "20-30sec %", ">30sec %"] if is_askai else ["0-2sec %", "3-4sec %", "4-6sec %", ">6sec %"]

        # Total rows first, matching Excel Track_Comparison style.
        for metric in ["Avg", "Min", "Max"]:
            row = {"Track": "Total" if metric == "Avg" else "", "Metric": metric}
            for frames in run_frames:
                label = frames["Label"]
                api_df = frames["APIs"].copy()
                if tracks:
                    api_df = api_df[api_df["Feature"].astype(str).isin(tracks)]
                values = metric_bucket_summary_for_rows(api_df, metric, is_askai)
                for name, value in zip(bucket_names + ["Max Seconds"], values):
                    row[name] = value
            rows.append(row)

        for track in tracks:
            for metric in ["Avg", "Min", "Max"]:
                row = {"Track": track if metric == "Avg" else "", "Metric": metric}
                for frames in run_frames:
                    label = frames["Label"]
                    api_rows = frames["APIs"][frames["APIs"]["Feature"].astype(str) == str(track)]
                    values = metric_bucket_summary_for_rows(api_rows, metric, is_askai)
                    for name, value in zip(bucket_names + ["Max Seconds"], values):
                        row[name] = value
                rows.append(row)
        return pd.DataFrame(rows)

    return build_section(askai_tracks, True), build_section(other_tracks, False)



def render_compare_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.markdown('<div class="panel"><div class="panel-title">TRACK COMPARISON <span class="tag">Same metrics as Excel Track_Comparison</span></div>', unsafe_allow_html=True)

    askai_df, other_df = build_dashboard_track_comparison(run_frames)

    st.markdown("### AskAI Tracks")
    st.caption("Buckets: 0-10sec %, 10-20sec %, 20-30sec %, >30sec %, Max Seconds")
    if not askai_df.empty:
        st.dataframe(askai_df, use_container_width=True, hide_index=True, height=420)
    else:
        st.info("No AskAI tracks found.")

    st.markdown("### Assets / Assessments / Home / Settings / Support Tracks")
    st.caption("Buckets: 0-2sec %, 3-4sec %, 4-6sec %, >6sec %, Max Seconds")
    if not other_df.empty:
        st.dataframe(other_df, use_container_width=True, hide_index=True, height=620)
    else:
        st.info("No non-AskAI tracks found.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_trends_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.markdown('<div class="panel"><div class="panel-title">TRENDS ACROSS RESULTS</div>', unsafe_allow_html=True)
    rows = []
    for frames in run_frames:
        row = summarize_run(frames["APIs"])
        row["Run"] = frames["Label"]
        row["Region"] = frames.get("Region", region_from_frames(frames))
        rows.append(row)
    summary = pd.DataFrame(rows)
    if len(summary) > 0:
        c1, c2 = st.columns(2)
        fig1 = px.line(summary, x="Run", y=["avg_sec", "p95_sec", "max_sec"], markers=True, title="Response Trend")
        fig1.update_layout(height=420, xaxis_title="", yaxis_title="Seconds")
        c1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(summary, x="Run", y=["error_rate", "sla_compliance"], markers=True, title="Error Rate / SLA Compliance Trend")
        fig2.update_layout(height=420, xaxis_title="", yaxis_title="%")
        c2.plotly_chart(fig2, use_container_width=True)

        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_drilldown_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    df = combined_df(run_frames)
    st.markdown('<div class="panel"><div class="panel-title">DRILLDOWN DATA</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    tracks = sorted(df["Feature"].dropna().astype(str).unique().tolist())
    selected_tracks = c1.multiselect("Track", tracks, default=tracks[: min(10, len(tracks))])
    selected_status = c2.multiselect("SLA Status", ["PASS", "FAIL"], default=["PASS", "FAIL"])
    sort_col = c3.selectbox("Sort by", ["Avg ResTime in sec", "95thPercentile Resp Time in Sec", "99thPercentile Resp Time in Sec", "MaxRes Time in sec", "errorCount", "sampleCount"])
    filtered = df[df["Feature"].isin(selected_tracks) & df["SLA Status"].isin(selected_status)].sort_values(sort_col, ascending=False)
    st.dataframe(filtered[standard_api_cols(filtered)], use_container_width=True, hide_index=True, height=650)
    st.markdown("</div>", unsafe_allow_html=True)


def render_reports_tab() -> None:
    st.markdown('<div class="panel"><div class="panel-title">REPORTS</div>', unsafe_allow_html=True)
    st.write("Download the generated Excel workbook from the upload page, or return to the upload page and generate a fresh report.")
    if st.session_state.get("excel_bytes"):
        st.download_button(
            "Download Excel Report",
            data=st.session_state.excel_bytes,
            file_name=st.session_state.report_file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="reports_tab_excel_download",
        )
    st.markdown("</div>", unsafe_allow_html=True)


def goto_tab_button(label: str, tab_name: str, key: str) -> None:
    if st.button(label, key=key):
        st.session_state["nav_target"] = tab_name
        st.rerun()



def render_executive_dashboard(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    selected_tab = top_nav()
    main_col, side_col = st.columns([4.35, .95], gap="medium")

    with side_col:
        selected_frames = get_filtered_frames(run_frames)
        insights = auto_insights(selected_frames)
        st.markdown('<div class="side-card"><div class="panel-title">INSIGHTS</div>', unsafe_allow_html=True)
        for icon, color, text in insights:
            st.markdown(f'<div class="insight-item"><div class="dot" style="background:{color};">{icon}</div><div>{text}</div></div>', unsafe_allow_html=True)
        goto_tab_button('View all Insights →', 'Trends', 'view_insights_btn')
        st.markdown("</div>", unsafe_allow_html=True)

        render_chatbot(selected_frames, key_suffix='side')

        try:
            dashboard_url = st.secrets.get("DASHBOARD_URL", "")
        except Exception:
            dashboard_url = ""
        if dashboard_url:
            st.markdown(f'<a class="primary-pill" href="{dashboard_url}?view=dashboard&tab=Overview" target="_blank" style="width:100%;text-align:center;">Open Dashboard in New Tab ↗</a>', unsafe_allow_html=True)

    with main_col:
        df = combined_df(selected_frames)

        if selected_tab in ["Track Comparison", "Compare"]:
            render_compare_tab(selected_frames)
            return
        if selected_tab == "Trends":
            render_trends_tab(selected_frames)
            return
        if selected_tab == "Drilldown":
            render_drilldown_tab(selected_frames)
            return
        if selected_tab == "Reports":
            render_reports_tab()
            return
        if selected_tab == "Chatbot":
            st.markdown('<div class="panel"><div class="panel-title">AI CHATBOT</div>', unsafe_allow_html=True)
            render_chatbot(selected_frames, key_suffix='tab')
            st.markdown("</div>", unsafe_allow_html=True)
            return

        kpi_cards(df)

        st.markdown('<div class="grid-3">', unsafe_allow_html=True)
        # Streamlit does not nest into raw grid well; use columns instead.
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1.25, 1, 1], gap="medium")
        tracks = track_summary(df)

        with c1:
            st.markdown('<div class="panel"><div class="panel-title">Response Time</div>', unsafe_allow_html=True)
            if not tracks.empty:
                chart_df = tracks.head(8).sort_values("P95_Sec")
                plot_df = chart_df[["Feature", "Avg_Sec", "P95_Sec", "Max_Sec"]].rename(
                    columns={
                        "Avg_Sec": "Avg",
                        "P95_Sec": "95th Percentile",
                        "Max_Sec": "Max",
                    }
                )
                long_df = plot_df.melt(id_vars="Feature", var_name="Metric", value_name="Seconds")
                fig = px.bar(long_df, x="Feature", y="Seconds", color="Metric", barmode="group", text="Seconds")
                fig.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
                fig.update_layout(height=330, margin=dict(l=8, r=10, t=5, b=95), xaxis_title="", yaxis_title="Seconds", legend_title="")
                st.plotly_chart(fig, use_container_width=True)
            goto_tab_button('View all APIs →', 'Drilldown', 'view_all_apis_btn')
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="panel"><div class="panel-title">SLA Status</div>', unsafe_allow_html=True)
            st.plotly_chart(sla_donut(df), use_container_width=True)
            goto_tab_button('View SLA Breaches →', 'Drilldown', 'view_sla_breaches_btn')
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="panel"><div class="panel-title">Top Error Transactions</div>', unsafe_allow_html=True)
            top_errors = df[pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0) > 0].sort_values("errorCount", ascending=False).head(5)
            if not top_errors.empty:
                fig = px.bar(top_errors.sort_values("errorCount"), x="errorCount", y="Scenario", orientation="h", text="errorCount", color_discrete_sequence=["#ef4444"])
                fig.update_traces(textposition="outside")
                fig.update_layout(height=300, margin=dict(l=8, r=18, t=5, b=40), xaxis_title="Errors", yaxis_title="", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No API errors found.")
            goto_tab_button('View all Errors →', 'Drilldown', 'view_all_errors_btn')
            st.markdown("</div>", unsafe_allow_html=True)

        c4, c5 = st.columns([1.05, 1.45], gap="medium")
        with c4:
            st.markdown('<div class="panel"><div class="panel-title">REGION COMPARISON</div>', unsafe_allow_html=True)
            rows = []
            for frames in selected_frames:
                row = summarize_run(frames["APIs"])
                row["Region"] = frames.get("Region", region_from_frames(frames))
                rows.append(row)
            summary = pd.DataFrame(rows)
            if not summary.empty:
                show = summary.groupby("Region").agg(
                    P95_sec=("p95_sec","mean"),
                    Avg_sec=("avg_sec","mean"),
                    Max_sec=("max_sec","max"),
                    Error_Rate=("error_rate","mean"),
                    SLA_Pass=("sla_compliance","mean"),
                ).reset_index().round(2)
                st.dataframe(show, use_container_width=True, hide_index=True, height=300)
            st.markdown("</div>", unsafe_allow_html=True)

        with c5:
            st.markdown('<div class="panel"><div class="panel-title">PERFORMANCE HEATMAP <span class="tag">Track × Region</span></div>', unsafe_allow_html=True)
            heat_rows = []
            for frames in selected_frames:
                region = frames.get("Region", region_from_frames(frames))
                ts = track_summary(frames["APIs"])
                ts["Region"] = region
                heat_rows.append(ts)
            heat = pd.concat(heat_rows, ignore_index=True) if heat_rows else pd.DataFrame()
            if not heat.empty:
                top_tracks = heat.groupby("Feature")["P95_Sec"].max().sort_values(ascending=False).head(10).index
                heat = heat[heat["Feature"].isin(top_tracks)]
                pivot = heat.pivot_table(index="Feature", columns="Region", values="P95_Sec", aggfunc="mean").fillna(0)
                match = pivot.copy()
                for track in match.index:
                    for col in match.columns:
                        match.loc[track, col] = sla_color_for_track(track, pivot.loc[track, col])
                fig = px.imshow(
                    match,
                    text_auto=False,
                    color_continuous_scale=[(0,"#ef4444"),(.499,"#ef4444"),(.5,"#22c55e"),(1,"#22c55e")],
                    zmin=0,zmax=1,aspect="auto",
                )
                fig.update_traces(text=pivot.round(2).astype(str)+"s", texttemplate="%{text}")
                fig.update_layout(height=430, margin=dict(l=8,r=8,t=8,b=8), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">TRACK COMPARISON SUMMARY <span class="tag">Total rows only</span></div>', unsafe_allow_html=True)
        askai_compare, other_compare = build_dashboard_track_comparison(selected_frames)

        if not askai_compare.empty:
            st.markdown("#### AskAI Tracks - Total")
            askai_total = askai_compare.iloc[:3].copy()
            st.dataframe(askai_total, use_container_width=True, hide_index=True, height=160)

        if not other_compare.empty:
            st.markdown("#### Assets / Assessments / Home / Settings / Support Tracks - Total")
            other_total = other_compare.iloc[:3].copy()
            st.dataframe(other_total, use_container_width=True, hide_index=True, height=160)

        goto_tab_button('Open Full Track Comparison →', 'Track Comparison', 'overview_full_compare_btn')
        st.markdown("</div>", unsafe_allow_html=True)


def standard_api_cols(df: pd.DataFrame) -> List[str]:
    return safe_cols(df, ["Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct", "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec", "90thPercentile Resp Time in Sec", "95thPercentile Resp Time in Sec", "99thPercentile Resp Time in Sec", "SLA Sec", "SLA Status", "SLA Breach Sec"])


def extract_top_n(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)|\bfirst\s+(\d+)|\b(\d+)\s+(?:slow|error|fail|api|apis)", question.lower())
    nums = [g for g in match.groups() if g] if match else []
    return max(1, min(100, int(nums[0]))) if nums else default


def metric_col(question: str) -> str:
    q = question.lower()
    if "p99" in q or "99" in q: return "99thPercentile Resp Time in Sec"
    if "p95" in q or "95" in q: return "95thPercentile Resp Time in Sec"
    if "p90" in q or "90" in q: return "90thPercentile Resp Time in Sec"
    if "max" in q or "maximum" in q: return "MaxRes Time in sec"
    if "min" in q or "minimum" in q: return "Min ResTime in sec"
    return "Avg ResTime in sec"


def match_rows(df: pd.DataFrame, question: str) -> pd.DataFrame:
    if df.empty: return df
    q = question.lower()
    searchable_cols = safe_cols(df, ["Feature","Scenario","Endpoint","API","SLA Status","Track Type"])
    stop = {"show","give","tell","what","which","where","when","how","the","and","or","for","api","apis","track","tracks","report","details","data","list","top","bottom","is","are","was","were","in","of","to","me","with","on","by","about","please"}
    tokens = [t for t in re.findall(r"[a-zA-Z0-9_./-]+", q) if len(t) >= 3 and t not in stop]
    if not tokens or not searchable_cols: return df.head(0)
    combined = pd.Series("", index=df.index, dtype=str)
    for col in searchable_cols:
        combined = combined + " " + df[col].astype(str).str.lower()
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask = mask | combined.str.contains(re.escape(token), na=False)
    return df[mask].copy()


def chat_answer(question: str, run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[str, pd.DataFrame | None]:
    q = question.lower().strip()
    if not run_frames: return "Upload and generate a dashboard first.", None
    df = combined_df(run_frames)
    label = "selected report(s)"
    n = extract_top_n(q)
    mcol = metric_col(q)
    if any(w in q for w in ["context","date","duration","region","users","devices","concurrent"]):
        rows = []
        for f in run_frames:
            info = f.get("Run_Info")
            if info is not None and not info.empty:
                row = info.iloc[0].to_dict(); row["Run"] = f["Label"]; row["Region"] = f.get("Region", region_from_frames(f)); rows.append(row)
        if rows:
            context = pd.DataFrame(rows)
            return "Report context extracted from uploaded filename(s).", context[safe_cols(context, ["Run","Region","Concurrent Users","Devices Count","Date","Duration"])]
        return "Report context was not available.", None
    if any(w in q for w in ["health","summary","overall","status","executive","overview"]):
        s = summarize_run(df)
        return f"Overall for **{label}**: Performance Score **{s['performance_score']}**, SLA Compliance **{s['sla_compliance']}%**, Success Rate **{s['success_rate']}%**, Error Rate **{s['error_rate']}%**, Avg Response **{s['avg_sec']} sec**, P95 **{s['p95_sec']} sec**, Errors **{s['errors']}**, Samples **{s['samples']}**.", None
    if any(w in q for w in ["sla","breach","breached","violate","violation","pass","failed","fail"]):
        fail = df[df["SLA Status"] == "FAIL"].sort_values("SLA Breach Sec", ascending=False)
        if "pass" in q and "fail" not in q and "breach" not in q:
            ok = df[df["SLA Status"] == "PASS"].copy()
            return "APIs passing SLA.", ok[standard_api_cols(ok)].head(n)
        if fail.empty: return "No SLA breaches found.", None
        return f"Top {min(n,len(fail))} SLA breaches.", fail[standard_api_cols(fail)].head(n)
    if any(w in q for w in ["error","errors","failure","failures","errorpct"]):
        err = df[pd.to_numeric(df.get("errorCount",0), errors="coerce").fillna(0)>0].copy()
        if err.empty: return "No API errors found.", None
        sort_col = "errorPct" if "percent" in q or "pct" in q else "errorCount"
        return f"Top {min(n,len(err))} error APIs sorted by {sort_col}.", err.sort_values(sort_col, ascending=False)[standard_api_cols(err)].head(n)
    if any(w in q for w in ["track","tracks","feature","features"]):
        ts = track_summary(df)
        return "Worst tracks by P95, Avg Sec, and Errors.", ts.head(n)
    if any(w in q for w in ["sample","samples","count","volume","load"]):
        sample_df = df.sort_values("sampleCount", ascending=False)
        return f"Top {min(n,len(sample_df))} APIs by sample count.", sample_df[standard_api_cols(sample_df)].head(n)
    if any(w in q for w in ["p90","p95","p99","percentile","90","95","99","slow","latency","response","time","avg","maximum","minimum","max","min"]):
        if mcol not in df.columns: return f"{mcol} is not available.", None
        top = df.sort_values(mcol, ascending=False)
        return f"Top {min(n,len(top))} APIs based on **{mcol}**.", top[standard_api_cols(top)].head(n)
    matched = match_rows(df, question)
    if not matched.empty:
        return f"I found {len(matched)} matching rows.", matched.sort_values(["SLA Breach Sec","Avg ResTime in sec","errorCount"], ascending=False)[standard_api_cols(matched)].head(n)
    return "I can answer only from the uploaded JMeter performance report. Try asking about SLA breaches, top slow APIs, P95/P99, errors, tracks, regions, samples, report context, or comparisons between uploaded runs.", None


def render_chatbot(run_frames: List[Dict[str, pd.DataFrame]], key_suffix: str = 'side') -> None:
    st.markdown('<div class="chat-card"><div class="chat-header">AI ASSISTANT</div>', unsafe_allow_html=True)
    st.write("Hi! I can help you analyze the performance data.")
    with st.expander("Try asking me", expanded=True):
        st.write("- Top slow APIs in APJC\n- Why SLA failed?\n- Compare error rate by region\n- Worst performing tracks\n- What changed between runs?\n- Which APIs have highest P99?\n- Show AskAI SLA breaches\n- Which track has most errors?\n- Show highest sample count APIs\n- What is report date and duration?")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("table") is not None:
                st.dataframe(msg["table"], use_container_width=True, hide_index=True)
    question = st.chat_input("Ask anything about performance...", key=f"chat_input_{key_suffix}_{st.session_state.get('run_id', 'no_run')}")
    if question:
        st.session_state.messages.append({"role":"user","content":question,"table":None})
        answer, table = chat_answer(question, run_frames)
        st.session_state.messages.append({"role":"assistant","content":answer,"table":table})
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)




def render_main_page() -> None:
    st.markdown(
        f"""
<div class="hero-title-box">
  <h1>{APP_TITLE}</h1>
</div>
<div class="hero-subtitle">
  Upload one JMeter statistics.json file for a normal dashboard report. Upload two or more files for comparison.
</div>
""",
        unsafe_allow_html=True,
    )



def dashboard_url_for_run(run_id_value: str) -> str:
    return f"?view=dashboard&run_id={run_id_value}"






def render_action_cards() -> None:
    has_report = bool(st.session_state.get("run_id") and st.session_state.get("excel_bytes"))
    run_id_value = st.session_state.get("run_id", "")
    dashboard_href = f"?view=dashboard&run_id={run_id_value}&tab=Overview" if has_report else "#"
    chatbot_href = f"?view=dashboard&run_id={run_id_value}&tab=Chatbot" if has_report else "#"

    st.markdown(
        """
<style>
.action-card-title {
    margin:0 0 8px 0;
    color:#0f2b68;
    font-size:19px;
    font-weight:800;
}
.action-card-text {
    margin:0 0 16px 0;
    color:#667085;
    font-size:13px;
    line-height:1.45;
    min-height:58px;
}
.action-link {
    display:inline-block;
    background:linear-gradient(90deg,#4f46e5,#2563eb);
    color:white !important;
    text-decoration:none !important;
    padding:10px 14px;
    border-radius:12px;
    font-weight:800;
    font-size:13px;
    box-shadow:0 10px 22px rgba(37,99,235,.22);
}
.action-link.purple {
    background:linear-gradient(90deg,#6d28d9,#7c3aed);
}
.action-link.disabled {
    background:#e5e7eb;
    color:#667085 !important;
    box-shadow:none;
    pointer-events:none;
}
</style>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">Executive Dashboard</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Open the leadership-ready dashboard with KPIs, region comparison, heatmaps and drilldowns.</div>', unsafe_allow_html=True)
            link_class = "action-link" if has_report else "action-link disabled"
            st.markdown(f'<a class="{link_class}" href="{dashboard_href}" target="_blank">Open Dashboard ↗</a>', unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">Excel Report</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Download the generated workbook with Insights, APIs, Transactions, Errors and Comparison sheets.</div>', unsafe_allow_html=True)
            if has_report:
                st.download_button(
                    "⬇ Download Excel Report",
                    data=st.session_state.excel_bytes,
                    file_name=st.session_state.report_file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_download_inside_card",
                    use_container_width=True,
                )
            else:
                st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_download_disabled_inside_card")

    with c3:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">AI Chatbot</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Open the dashboard chatbot and ask questions about SLA, slow APIs, errors, regions and comparisons.</div>', unsafe_allow_html=True)
            link_class = "action-link purple" if has_report else "action-link disabled"
            st.markdown(f'<a class="{link_class}" href="{chatbot_href}" target="_blank">Open Chatbot ↗</a>', unsafe_allow_html=True)



# Session state
if "excel_bytes" not in st.session_state: st.session_state.excel_bytes = None
if "run_frames" not in st.session_state: st.session_state.run_frames = []
if "report_file_name" not in st.session_state: st.session_state.report_file_name = "JMeter_Report.xlsx"
if "messages" not in st.session_state: st.session_state.messages = []
if "run_id" not in st.session_state: st.session_state.run_id = ""

if dashboard_only and run_id and run_id in dashboard_store:
    st.session_state.run_frames = dashboard_store[run_id]["run_frames"]
    st.session_state.excel_bytes = dashboard_store[run_id].get("excel_bytes")
    st.session_state.report_file_name = dashboard_store[run_id].get("report_file_name", "JMeter_Report.xlsx")

if dashboard_only:
    if st.session_state.run_frames:
        render_executive_dashboard(st.session_state.run_frames)
    else:
        st.warning("No dashboard data found for this tab. Please generate the report from the main page and click Open Dashboard in New Tab again.")
else:
    render_main_page()
    uploaded_files = st.file_uploader("Upload JMeter statistics.json file(s)", type=["json"], accept_multiple_files=True)
    generate_clicked = st.button("Generate Results", type="primary", disabled=not uploaded_files)
    if uploaded_files and generate_clicked:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            json_paths: List[Path] = []
            labels: List[str] = []
            run_frames: List[Dict[str, pd.DataFrame]] = []
            for idx, uploaded_file in enumerate(uploaded_files, start=1):
                clean_name = uploaded_file.name.replace(" ", "_")
                path = tmpdir / f"{idx}_{clean_name}"
                path.write_bytes(uploaded_file.getvalue())
                json_paths.append(path)
                label = Path(uploaded_file.name).stem
                labels.append(label)
                run_frames.append(process_uploaded_file(path, label))
            output_path = tmpdir / "JMeter_Report.xlsx"
            try:
                if len(json_paths) == 1:
                    build_report(json_paths[0], output_path)
                else:
                    build_comparison_report(json_paths, labels, output_path)
                run_frames = add_region_to_frames(run_frames)
                excel_bytes = output_path.read_bytes()
                new_run_id = uuid.uuid4().hex
                dashboard_store[new_run_id] = {"run_frames": run_frames, "excel_bytes": excel_bytes, "report_file_name": "JMeter_Report.xlsx"}
                st.session_state.excel_bytes = excel_bytes
                st.session_state.run_frames = run_frames
                st.session_state.report_file_name = "JMeter_Report.xlsx"
                st.session_state.messages = []
                st.session_state.run_id = new_run_id
                st.toast("Report generated successfully.", icon="✅")
            except Exception as exc:
                st.error(f"Failed to generate report: {exc}")

    render_action_cards()
