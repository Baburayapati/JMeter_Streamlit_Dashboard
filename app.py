
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
    st.markdown(
        """
<div class="top-nav">
  <div class="brand">
    <div class="brand-icon">↯</div>
    <div>
      <div class="brand-title">CiscoIQ-SaaS-Support-Services Performance Dashboard</div>
      <div class="brand-sub">Real-time Performance Insights Across Regions</div>
    </div>
  </div>
  <div class="nav-time">Dashboard View<br/>Last Updated</div>
</div>
""",
        unsafe_allow_html=True,
    )

    tabs = ["Overview", "Compare", "Trends", "Drilldown", "Reports", "Chatbot"]

    # If a "View all..." button requested a tab switch, use it as the next radio default.
    if "nav_target" in st.session_state:
        requested = st.session_state.pop("nav_target")
        st.session_state["nav_tab_radio"] = requested

    current = st.session_state.get("nav_tab_radio", "Overview")
    index = tabs.index(current) if current in tabs else 0

    return st.radio(
        "Dashboard Navigation",
        tabs,
        horizontal=True,
        index=index,
        key="nav_tab_radio",
        label_visibility="collapsed",
    )


def kpi_cards(df: pd.DataFrame) -> None:
    s = summarize_run(df)
    sla_fail = round(100 - s["sla_compliance"], 2) if s["transactions"] else 0

    cols = st.columns(6)
    metrics = [
        ("Health Score", f"{s['performance_score']}/100", "Performance index"),
        ("SLA Pass %", f"{s['sla_compliance']}%", "APIs meeting SLA"),
        ("SLA Fail %", f"{sla_fail}%", "APIs breaching SLA"),
        ("Total APIs", f"{s['transactions']:,}", "Compared transactions"),
        ("Total Samples", f"{s['samples']:,}", "Executed samples"),
        ("Total Errors", f"{s['errors']:,}", "Failed samples"),
    ]

    for col, (label, value, help_text) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value, help=help_text)


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
    return result[:4]



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

    def build_section(tracks: List[str], is_askai: bool) -> pd.DataFrame:
        rows = []
        bucket_names = ["0-10s %", "10-20s %", "20-30s %", ">30s %"] if is_askai else ["0-2s %", "3-4s %", "4-6s %", ">6s %"]
        for track in tracks:
            for metric in ["Avg", "Min", "Max"]:
                row = {"Track": track if metric == "Avg" else "", "Metric": metric}
                for frames in run_frames:
                    label = frames["Label"]
                    values = metric_bucket_summary(frames["APIs"], track, metric, is_askai)
                    for name, value in zip(bucket_names + ["Max Seconds"], values):
                        row[f"{label} | {name}"] = value
                rows.append(row)
        return pd.DataFrame(rows)

    return build_section(askai_tracks, True), build_section(other_tracks, False)


def render_compare_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.markdown('<div class="panel"><div class="panel-title">TRACK COMPARISON DASHBOARD <span class="tag">Same logic as Excel Track_Comparison</span></div>', unsafe_allow_html=True)

    if len(run_frames) < 2:
        st.info("Upload two or more JSON reports to see side-by-side comparison.")
    else:
        askai_df, other_df = build_dashboard_track_comparison(run_frames)

        st.markdown("### AskAI Tracks — 0-10s / 10-20s / 20-30s / >30s")
        if not askai_df.empty:
            st.dataframe(askai_df, use_container_width=True, hide_index=True, height=360)
        else:
            st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_disabled_btn")
            st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_disabled_btn")
            st.info("No AskAI tracks found.")

        st.markdown("### Assets / Assessments / Home / Settings / Support Tracks — 0-2s / 3-4s / 4-6s / >6s")
        if not other_df.empty:
            st.dataframe(other_df, use_container_width=True, hide_index=True, height=520)
        else:
            st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_disabled_btn")
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

        render_chatbot(selected_frames)

        try:
            dashboard_url = st.secrets.get("DASHBOARD_URL", "")
        except Exception:
            dashboard_url = ""
        if dashboard_url:
            st.markdown(f'<a class="primary-pill" href="{dashboard_url}?view=dashboard" target="_blank" style="width:100%;text-align:center;">Open Dashboard in New Tab ↗</a>', unsafe_allow_html=True)

    with main_col:
        df = combined_df(selected_frames)

        if selected_tab == "Compare":
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
            render_chatbot(selected_frames)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        st.markdown('<div class="panel"><div class="panel-title"><span>AGGREGATED PERFORMANCE OVERVIEW METRICS</span><span class="tag">Across Selected Results</span></div>', unsafe_allow_html=True)
        kpi_cards(df)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="grid-3">', unsafe_allow_html=True)
        # Streamlit does not nest into raw grid well; use columns instead.
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1.25, 1, 1], gap="medium")
        tracks = track_summary(df)

        with c1:
            st.markdown('<div class="panel"><div class="panel-title">Response Time (P95)</div>', unsafe_allow_html=True)
            if not tracks.empty:
                chart_df = tracks.head(9).sort_values("P95_Sec")
                fig = px.bar(chart_df, x="Feature", y="P95_Sec", text="P95_Sec", color_discrete_sequence=["#0b72d9"])
                fig.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
                fig.update_layout(height=300, margin=dict(l=8, r=10, t=5, b=88), xaxis_title="", yaxis_title="P95 (sec)", showlegend=False)
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

        c4, c5, c6 = st.columns([1.05, 1.0, .75], gap="medium")
        with c4:
            st.markdown('<div class="panel"><div class="panel-title">REGION COMPARISON (P95)</div>', unsafe_allow_html=True)
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
                st.dataframe(show, use_container_width=True, hide_index=True, height=230)
            st.markdown("</div>", unsafe_allow_html=True)

        with c5:
            st.markdown('<div class="panel"><div class="panel-title">PERFORMANCE HEATMAP (P95) <span class="tag">Track × Region</span></div>', unsafe_allow_html=True)
            heat_rows = []
            for frames in selected_frames:
                region = frames.get("Region", region_from_frames(frames))
                ts = track_summary(frames["APIs"])
                ts["Region"] = region
                heat_rows.append(ts)
            heat = pd.concat(heat_rows, ignore_index=True) if heat_rows else pd.DataFrame()
            if not heat.empty:
                top_tracks = heat.groupby("Feature")["P95_Sec"].max().sort_values(ascending=False).head(8).index
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
                fig.update_layout(height=310, margin=dict(l=8,r=8,t=8,b=8), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c6:
            st.markdown('<div class="panel"><div class="panel-title">P95 by Region</div>', unsafe_allow_html=True)
            if not summary.empty:
                fig = px.bar(show, x="Region", y="P95_sec", text="P95_sec", color="Region")
                fig.update_traces(texttemplate="%{text:.2f}s", textposition="outside")
                fig.update_layout(height=145, margin=dict(l=6,r=8,t=4,b=25), showlegend=False, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
                fig2 = px.bar(show, x="Region", y="Error_Rate", text="Error_Rate", color="Region")
                fig2.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                fig2.update_layout(height=145, margin=dict(l=6,r=8,t=4,b=25), showlegend=False, xaxis_title="", yaxis_title="Err %")
                st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">TOP SLOW TRACKS DETAILS (P95 / AVG / MAX)</div>', unsafe_allow_html=True)
        if not heat.empty:
            # Region comparison style table.
            table_rows = []
            for feature in heat.groupby("Feature")["P95_Sec"].max().sort_values(ascending=False).head(8).index:
                row = {"Track / Feature": feature}
                subset = heat[heat["Feature"] == feature]
                for _, r in subset.iterrows():
                    reg = r["Region"]
                    row[f"{reg} P95 (s)"] = r["P95_Sec"]
                    row[f"{reg} Avg (s)"] = r["Avg_Sec"]
                    row[f"{reg} Max (s)"] = r["Max_Sec"]
                row["SLA Fail %"] = round(float(subset["SLA Fail %"].mean()),2)
                row["Errors"] = int(subset["Errors"].sum())
                table_rows.append(row)
            detail = pd.DataFrame(table_rows)
            st.dataframe(detail, use_container_width=True, hide_index=True, height=330)
        else:
            st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_disabled_btn")
            st.dataframe(tracks[["Feature","P95_Sec","Avg_Sec","Max_Sec","Errors","SLA Fail %"]].head(10), use_container_width=True, hide_index=True)
        goto_tab_button('View all Tracks →', 'Compare', 'view_all_tracks_btn')
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


def render_chatbot(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.markdown('<div class="chat-card"><div class="chat-header">AI ASSISTANT</div>', unsafe_allow_html=True)
    st.write("Hi! I can help you analyze the performance data.")
    with st.expander("Try asking me", expanded=True):
        st.write("- Top slow APIs in APJC\n- Why SLA failed?\n- Compare error rate by region\n- Worst performing tracks\n- What changed between runs?\n- Which APIs have highest P99?\n- Show AskAI SLA breaches\n- Which track has most errors?\n- Show highest sample count APIs\n- What is report date and duration?")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("table") is not None:
                st.dataframe(msg["table"], use_container_width=True, hide_index=True)
    question = st.chat_input("Ask anything about performance...")
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
    dashboard_href = f"?view=dashboard&run_id={run_id_value}" if has_report else "#"

    st.markdown(
        """
<style>
.action-card-box {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:18px;
    padding:18px;
    min-height:190px;
    box-shadow:0 10px 26px rgba(15,23,42,.06);
    margin-bottom: 8px;
}
.action-card-box h3 {
    margin:0 0 8px 0;
    color:#0f2b68;
    font-size:19px;
}
.action-card-box p {
    margin:0 0 14px 0;
    color:#667085;
    font-size:13px;
    line-height:1.45;
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
        link_class = "action-link" if has_report else "action-link disabled"
        st.markdown(
            f"""
<div class="action-card-box">
  <h3>Executive Dashboard</h3>
  <p>Open the leadership-ready dashboard with KPIs, region comparison, heatmaps and drilldowns.</p>
  <a class="{link_class}" href="{dashboard_href}" target="_blank">Open Dashboard ↗</a>
</div>
""",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
<div class="action-card-box">
  <h3>Excel Report</h3>
  <p>Download the generated workbook with Insights, APIs, Transactions, Errors and Comparison sheets.</p>
""",
            unsafe_allow_html=True,
        )
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
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        link_class = "action-link purple" if has_report else "action-link disabled"
        st.markdown(
            f"""
<div class="action-card-box">
  <h3>AI Chatbot</h3>
  <p>Open the dashboard chatbot and ask questions about SLA, slow APIs, errors, regions and comparisons.</p>
  <a class="{link_class}" href="{dashboard_href}" target="_blank">Open Chatbot ↗</a>
</div>
""",
            unsafe_allow_html=True,
        )



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
