
from __future__ import annotations

from pathlib import Path
import re
import tempfile
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from main import build_report, build_comparison_report, build_single_report_frames


APP_TITLE = "CiscoIQ-SaaS-Support-Services Performance Dashboard"

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #eef7ff 0%, #f6f2ff 45%, #ecfff4 100%);
}
[data-testid="stHeader"] { background: rgba(255,255,255,0); }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1500px; }
.dashboard-title {
    display: table; margin: 0 auto 0.45rem auto;
    background: linear-gradient(90deg, #137333, #0b8043);
    color: white; padding: 10px 18px; border-radius: 10px;
    box-shadow: 0 8px 24px rgba(19,115,51,0.20);
    font-size: 18px; line-height: 1.2; font-weight: 800;
    text-align: center; width: auto; max-width: fit-content;
}
.dashboard-subtitle {
    text-align: center; font-size: 12px; color: #27364a; margin-bottom: 0.75rem;
}
.open-link {
    display: inline-block; text-decoration: none !important; color: #fff !important;
    background: linear-gradient(90deg, #1565c0, #0b8043);
    padding: 8px 14px; border-radius: 9px; font-weight: 700; font-size: 13px;
    box-shadow: 0 5px 16px rgba(21,101,192,0.22); margin-bottom: 0.65rem;
}
.panel {
    background: rgba(255,255,255,0.88);
    border: 1px solid rgba(21,76,121,0.16);
    border-radius: 11px; padding: 0.65rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.045);
    margin-bottom: 0.75rem;
}
.panel-title {
    text-align: center; color: white; font-size: 14px; font-weight: 800;
    padding: 6px 8px; border-radius: 8px; margin-bottom: 0.45rem;
}
.green-title { background: linear-gradient(90deg, #137333, #0b8043); }
.blue-title { background: linear-gradient(90deg, #0d47a1, #1565c0); }
.purple-title { background: linear-gradient(90deg, #4527a0, #7b1fa2); }
.teal-title { background: linear-gradient(90deg, #006064, #00838f); }
.insight-box {
    background: #eaf4ff; border: 1px solid #90caf9; border-radius: 10px;
    padding: 0.85rem; font-size: 13px; color: #12324f; min-height: 86px;
}
.rules-section {
    background: rgba(255,255,255,0.72); border: 1px solid rgba(21,76,121,0.12);
    border-radius: 12px; padding: 0.7rem 0.9rem; margin-bottom: 0.8rem;
}
.rules-section h3 {
    color: #154c79 !important; margin-top: 0.25rem !important;
    margin-bottom: 0.2rem !important; font-size: 15px !important;
    line-height: 1.15 !important; font-weight: 650 !important;
}
.rules-section li {
    font-size: 12.5px !important; line-height: 1.3 !important;
    font-weight: 400 !important; margin-bottom: 0.15rem !important;
}
.metric-pill {
    color: #2e7d32 !important; background: rgba(46,125,50,0.08);
    border-radius: 7px; padding: 1px 6px; font-weight: 500; white-space: nowrap;
}
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.86); border: 1px solid rgba(21,76,121,0.18);
    border-radius: 14px; padding: 12px; box-shadow: 0 8px 22px rgba(0,0,0,0.055);
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.92); border: 1px solid rgba(21,76,121,0.14);
    border-radius: 12px; padding: 0.55rem 0.65rem;
    box-shadow: 0 5px 16px rgba(0,0,0,0.045);
}
.stDownloadButton button, .stButton button { border-radius: 10px; font-weight: 700; }
</style>
    """,
    unsafe_allow_html=True,
)


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
    return frames


def summarize_run(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return dict(avg_sec=0, success_rate=0, error_rate=0, transactions=0, performance_score=0, sla_compliance=0, errors=0, samples=0, p95_sec=0)
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




def region_from_frames(frames: Dict[str, pd.DataFrame]) -> str:
    info = frames.get("Run_Info")
    if info is not None and not info.empty and "Region" in info.columns:
        region = str(info.iloc[0].get("Region", "N/A")).strip()
        return region if region and region.upper() != "N/A" else "Unknown"
    label = str(frames.get("Label", ""))
    upper = label.upper()
    for region in ["US", "EMEA", "APJC", "AMER", "EU", "LATAM", "INDIA"]:
        if re.search(rf"(?:^|[_\-\s]){region}(?:$|[_\-\s])", upper):
            return region
    return "Unknown"


def add_region_to_frames(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Dict[str, pd.DataFrame]]:
    for frames in run_frames:
        frames["Region"] = region_from_frames(frames)
    return run_frames


def sla_color_for_track(track_name: str, p95_value: float) -> float:
    """Return 1 when within SLA, 0 when breached. Used for green/red heatmaps."""
    threshold = 10 if str(track_name).upper().startswith("ASKAI") else 2
    return 1 if float(p95_value or 0) < threshold else 0


def render_open_new_tab_button() -> None:
    """Open current app in a new tab. If DASHBOARD_URL secret exists, open that URL."""
    try:
        dashboard_url = st.secrets.get("DASHBOARD_URL", "")
    except Exception:
        dashboard_url = ""

    if dashboard_url:
        st.markdown(
            f'<div style="text-align:center"><a class="open-link" href="{dashboard_url}" target="_blank">Open Dashboard in New Tab ↗</a></div>',
            unsafe_allow_html=True,
        )
    else:
        components.html(
            """
            <div style="text-align:center; margin: 0 0 10px 0;">
              <button
                onclick="window.open(window.parent.location.href, '_blank')"
                style="
                  background: linear-gradient(90deg, #1565c0, #0b8043);
                  color: white;
                  padding: 8px 14px;
                  border: 0;
                  border-radius: 9px;
                  font-weight: 700;
                  font-size: 13px;
                  box-shadow: 0 5px 16px rgba(21,101,192,0.22);
                  cursor: pointer;">
                Open Dashboard in New Tab ↗
              </button>
            </div>
            """,
            height=44,
        )


def render_region_comparison(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    region_rows = []
    for frames in run_frames:
        df = frames["APIs"].copy()
        region = frames.get("Region", region_from_frames(frames))
        s = summarize_run(df)
        s["Region"] = region
        s["Run"] = frames["Label"]
        region_rows.append(s)

    if not region_rows:
        return

    region_summary = pd.DataFrame(region_rows)
    available_regions = sorted(region_summary["Region"].dropna().astype(str).unique().tolist())

    st.markdown('<div class="panel"><div class="panel-title teal-title">REGION COMPARISON</div>', unsafe_allow_html=True)

    selected_regions = st.multiselect(
        "Compare Regions",
        available_regions,
        default=available_regions,
        help="Upload files with region names like US, EMEA, or APJC in the filename. Example: ..._US_1Hour_April-19-2026_Report.json",
    )

    filtered_summary = region_summary[region_summary["Region"].isin(selected_regions)].copy()
    if filtered_summary.empty:
        st.warning("No selected region data found.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.dataframe(
        filtered_summary[["Region", "Run", "avg_sec", "p95_sec", "success_rate", "error_rate", "sla_compliance", "performance_score", "transactions"]],
        use_container_width=True,
        hide_index=True,
    )

    c1, c2 = st.columns(2)
    fig_region_p95 = px.bar(
        filtered_summary,
        x="Region",
        y="p95_sec",
        color="Region",
        text="p95_sec",
        title="Region Comparison - P95 Response Time",
    )
    fig_region_p95.update_traces(texttemplate="%{text:.2f}s", textposition="outside")
    fig_region_p95.update_layout(height=300, margin=dict(l=10, r=10, t=45, b=30), xaxis_title="", yaxis_title="P95 sec")
    c1.plotly_chart(fig_region_p95, use_container_width=True)

    fig_region_error = px.bar(
        filtered_summary,
        x="Region",
        y="error_rate",
        color="Region",
        text="error_rate",
        title="Region Comparison - Error Rate %",
    )
    fig_region_error.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_region_error.update_layout(height=300, margin=dict(l=10, r=10, t=45, b=30), xaxis_title="", yaxis_title="Error Rate %")
    c2.plotly_chart(fig_region_error, use_container_width=True)

    # Track x Region heatmap based on P95 SLA status: green only when meeting SLA, red when breaching.
    region_track_rows = []
    for frames in run_frames:
        region = frames.get("Region", region_from_frames(frames))
        if region not in selected_regions:
            continue
        ts = track_summary(frames["APIs"])
        for _, row in ts.iterrows():
            region_track_rows.append({
                "Region": region,
                "Track": row["Feature"],
                "P95 Sec": row["P95_Sec"],
                "SLA Match": sla_color_for_track(row["Feature"], row["P95_Sec"]),
            })

    region_track_df = pd.DataFrame(region_track_rows)
    if not region_track_df.empty:
        top_tracks = (
            region_track_df.groupby("Track")["P95 Sec"]
            .max()
            .sort_values(ascending=False)
            .head(12)
            .index
            .tolist()
        )
        region_track_df = region_track_df[region_track_df["Track"].isin(top_tracks)]
        p95_pivot = region_track_df.pivot_table(index="Track", columns="Region", values="P95 Sec", aggfunc="mean").fillna(0)
        match_pivot = region_track_df.pivot_table(index="Track", columns="Region", values="SLA Match", aggfunc="mean").reindex(index=p95_pivot.index, columns=p95_pivot.columns).fillna(0)

        fig_region_heat = px.imshow(
            match_pivot,
            text_auto=False,
            color_continuous_scale=[(0, "#C62828"), (0.499, "#C62828"), (0.5, "#2E7D32"), (1, "#2E7D32")],
            aspect="auto",
            title="Region Performance Heatmap: Green = P95 Meets SLA, Red = SLA Breach",
            zmin=0,
            zmax=1,
        )
        # Put P95 values as text; color is based only on SLA match.
        fig_region_heat.update_traces(text=p95_pivot.round(2).astype(str) + "s", texttemplate="%{text}")
        fig_region_heat.update_layout(height=360, margin=dict(l=10, r=10, t=55, b=25), coloraxis_showscale=False)
        st.plotly_chart(fig_region_heat, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_kpis(df: pd.DataFrame) -> None:
    s = summarize_run(df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Avg Response", f'{s["avg_sec"]}s')
    c2.metric("Success Rate", f'{s["success_rate"]}%')
    c3.metric("Error Rate", f'{s["error_rate"]}%')
    c4.metric("Transactions", s["transactions"])
    c5.metric("Perf. Score", f'{s["performance_score"]}/100')
    c6.metric("SLA Compliance", f'{s["sla_compliance"]}%')


def plot_sla_donut(df: pd.DataFrame):
    counts = df["SLA Status"].value_counts().reset_index()
    counts.columns = ["SLA Status", "Count"]
    fig = px.pie(
        counts, names="SLA Status", values="Count", hole=0.55,
        color="SLA Status", color_discrete_map={"PASS": "#2E7D32", "FAIL": "#C62828"},
        title="SLA Status",
    )
    fig.update_layout(height=210, margin=dict(l=5, r=5, t=40, b=5), legend_title_text="")
    return fig


def auto_insight(run_frames: List[Dict[str, pd.DataFrame]]) -> str:
    latest = run_frames[-1]
    df = latest["APIs"]
    s = summarize_run(df)
    tracks = track_summary(df)
    if len(run_frames) > 1:
        first = summarize_run(run_frames[0]["APIs"])
        delta = round(s["p95_sec"] - first["p95_sec"], 2)
        direction = "higher" if delta > 0 else "lower"
        return f"Latest run P95 is {abs(delta)}s {direction} than baseline. SLA compliance is {s['sla_compliance']}% and error rate is {s['error_rate']}%."
    if not tracks.empty:
        worst = tracks.iloc[0]
        return f"{worst['Feature']} has the highest P95 at {worst['P95_Sec']}s. SLA compliance is {s['sla_compliance']}% with {s['errors']} total errors."
    return f"SLA compliance is {s['sla_compliance']}% and average response time is {s['avg_sec']}s."


def render_tableau_dashboard(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    latest = run_frames[-1]
    df = latest["APIs"].copy()

    st.markdown('<div class="panel"><div class="panel-title green-title">AGGREGATED PERFORMANCE OVERVIEW</div>', unsafe_allow_html=True)
    render_kpis(df)
    st.markdown("</div>", unsafe_allow_html=True)

    left, mid, right = st.columns([1.05, 1.05, 1.15])

    with left:
        st.markdown('<div class="panel"><div class="panel-title blue-title">WITHIN RUN COMPARISON</div>', unsafe_allow_html=True)
        tracks = track_summary(df)
        if not tracks.empty:
            fig_p95 = px.bar(tracks.head(8).sort_values("P95_Sec"), x="Feature", y="P95_Sec", title="Response Time (P95)", text="P95_Sec")
            fig_p95.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
            fig_p95.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=50), xaxis_title="", yaxis_title="P95 sec")
            st.plotly_chart(fig_p95, use_container_width=True)

        c1, c2 = st.columns(2)
        c1.plotly_chart(plot_sla_donut(df), use_container_width=True)

        top_errors = df[pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0) > 0].sort_values("errorCount", ascending=False).head(5)
        if not top_errors.empty:
            fig_err = px.bar(top_errors.sort_values("errorCount"), x="errorCount", y="Scenario", orientation="h", title="Top Error Transactions", text="errorCount")
            fig_err.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10), xaxis_title="Errors", yaxis_title="")
            c2.plotly_chart(fig_err, use_container_width=True)
        else:
            c2.info("No API errors found.")

        if not tracks.empty:
            st.markdown("##### Top Slow Tracks (P95)")
            st.dataframe(tracks[["Feature", "P95_Sec", "Avg_Sec", "Errors", "SLA Fail %"]].head(5), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with mid:
        st.markdown('<div class="panel"><div class="panel-title purple-title">CROSS RUN / PROGRAM COMPARISON</div>', unsafe_allow_html=True)
        if len(run_frames) > 1:
            summary_rows = []
            for frames in run_frames:
                row = summarize_run(frames["APIs"])
                row["Run"] = frames["Label"]
                summary_rows.append(row)
            summary = pd.DataFrame(summary_rows)
            st.dataframe(summary[["Run", "avg_sec", "p95_sec", "success_rate", "error_rate", "sla_compliance", "performance_score"]], use_container_width=True, hide_index=True)
            fig_trend = px.line(summary, x="Run", y=["avg_sec", "p95_sec"], markers=True, title="Trend Across Uploaded Runs")
            fig_trend.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=45), xaxis_title="", yaxis_title="Seconds")
            st.plotly_chart(fig_trend, use_container_width=True)

            combined = []
            for frames in run_frames:
                tmp = track_summary(frames["APIs"])
                tmp["Run"] = frames["Label"]
                combined.append(tmp)
            heat = pd.concat(combined, ignore_index=True) if combined else pd.DataFrame()
            if not heat.empty:
                pivot = heat.pivot_table(index="Feature", columns="Run", values="P95_Sec", aggfunc="mean").fillna(0)
                pivot = pivot.loc[pivot.max(axis=1).sort_values(ascending=False).head(8).index]
                match = pivot.copy()
                for track_name in match.index:
                    for col_name in match.columns:
                        match.loc[track_name, col_name] = sla_color_for_track(track_name, pivot.loc[track_name, col_name])
                fig_heat = px.imshow(
                    match,
                    text_auto=False,
                    title="Performance Heatmap: Green = P95 Meets SLA, Red = SLA Breach",
                    color_continuous_scale=[(0, "#C62828"), (0.499, "#C62828"), (0.5, "#2E7D32"), (1, "#2E7D32")],
                    aspect="auto",
                    zmin=0,
                    zmax=1,
                )
                fig_heat.update_traces(text=pivot.round(2).astype(str) + "s", texttemplate="%{text}")
                fig_heat.update_layout(height=310, margin=dict(l=10, r=10, t=50, b=20), coloraxis_showscale=False)
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            tracks = track_summary(df)
            if not tracks.empty:
                st.dataframe(tracks[["Feature", "Track Type", "APIs", "Avg_Sec", "P95_Sec", "Max_Sec", "Errors", "SLA Fail %"]].head(10), use_container_width=True, hide_index=True)
                p95_table = tracks.head(12).copy()
                p95_table["SLA Match"] = p95_table.apply(lambda r: sla_color_for_track(r["Feature"], r["P95_Sec"]), axis=1)
                heat_values = p95_table.set_index("Feature")[["SLA Match"]]
                p95_text = p95_table.set_index("Feature")[["P95_Sec"]].round(2).astype(str) + "s"
                fig_heat = px.imshow(
                    heat_values,
                    text_auto=False,
                    title="Metrics Dashboard by Track: Green = P95 Meets SLA, Red = SLA Breach",
                    color_continuous_scale=[(0, "#C62828"), (0.499, "#C62828"), (0.5, "#2E7D32"), (1, "#2E7D32")],
                    aspect="auto",
                    zmin=0,
                    zmax=1,
                )
                fig_heat.update_traces(text=p95_text, texttemplate="%{text}")
                fig_heat.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=20), coloraxis_showscale=False)
                st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title teal-title">DEGRADATION / INSIGHTS</div>', unsafe_allow_html=True)
        tracks = track_summary(df)
        if len(run_frames) > 1:
            summary_rows = []
            for frames in run_frames:
                row = summarize_run(frames["APIs"])
                row["Run"] = frames["Label"]
                summary_rows.append(row)
            summary = pd.DataFrame(summary_rows)
            fig_error = px.line(summary, x="Run", y="error_rate", markers=True, title="Error Rate Over Runs")
            fig_error.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=45), xaxis_title="", yaxis_title="Error Rate %")
            st.plotly_chart(fig_error, use_container_width=True)
        elif not tracks.empty:
            fig_dist = px.bar(tracks.head(8).sort_values("P95_Sec"), x="P95_Sec", y="Feature", orientation="h", title="Metrics Distribution (P95)", text="P95_Sec")
            fig_dist.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
            fig_dist.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10), xaxis_title="P95 sec", yaxis_title="")
            st.plotly_chart(fig_dist, use_container_width=True)

        st.markdown(f'<div class="insight-box">💡 {auto_insight(run_frames)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_drilldown(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.subheader("🔍 Drilldown")
    df = run_frames[-1]["APIs"]
    f1, f2, f3 = st.columns([2, 2, 2])
    tracks = sorted(df["Feature"].dropna().astype(str).unique().tolist())
    selected_tracks = f1.multiselect("Tracks", tracks, default=tracks[: min(8, len(tracks))])
    statuses = f2.multiselect("SLA Status", ["PASS", "FAIL"], default=["PASS", "FAIL"])
    sort_by = f3.selectbox("Sort by", ["Avg ResTime in sec", "95thPercentile Resp Time in Sec", "MaxRes Time in sec", "errorCount", "sampleCount"])
    filtered = df[df["Feature"].isin(selected_tracks) & df["SLA Status"].isin(statuses)].sort_values(sort_by, ascending=False)
    cols = ["Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct", "Avg ResTime in sec", "95thPercentile Resp Time in Sec", "99thPercentile Resp Time in Sec", "MaxRes Time in sec", "SLA Sec", "SLA Status", "SLA Breach Sec"]
    st.dataframe(filtered[safe_cols(filtered, cols)].head(500), use_container_width=True, hide_index=True)


def standard_api_cols(df: pd.DataFrame) -> List[str]:
    return safe_cols(df, ["Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct", "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec", "90thPercentile Resp Time in Sec", "95thPercentile Resp Time in Sec", "99thPercentile Resp Time in Sec", "SLA Sec", "SLA Status", "SLA Breach Sec"])


def extract_top_n(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)|\bfirst\s+(\d+)|\b(\d+)\s+(?:slow|error|fail|api|apis)", question.lower())
    if not match:
        return default
    nums = [g for g in match.groups() if g]
    return max(1, min(100, int(nums[0]))) if nums else default


def metric_col(question: str) -> str:
    q = question.lower()
    if "p99" in q or "99" in q:
        return "99thPercentile Resp Time in Sec"
    if "p95" in q or "95" in q:
        return "95thPercentile Resp Time in Sec"
    if "p90" in q or "90" in q:
        return "90thPercentile Resp Time in Sec"
    if "max" in q or "maximum" in q:
        return "MaxRes Time in sec"
    if "min" in q or "minimum" in q:
        return "Min ResTime in sec"
    return "Avg ResTime in sec"


def match_rows(df: pd.DataFrame, question: str) -> pd.DataFrame:
    if df.empty:
        return df
    q = question.lower()
    searchable_cols = safe_cols(df, ["Feature", "Scenario", "Endpoint", "API", "SLA Status", "Track Type"])
    stop = {"show", "give", "tell", "what", "which", "where", "when", "how", "the", "and", "or", "for", "api", "apis", "track", "tracks", "report", "details", "data", "list", "top", "bottom", "is", "are", "was", "were", "in", "of", "to", "me", "with", "on", "by", "about", "please"}
    tokens = [t for t in re.findall(r"[a-zA-Z0-9_./-]+", q) if len(t) >= 3 and t not in stop]
    if not tokens or not searchable_cols:
        return df.head(0)
    combined = pd.Series("", index=df.index, dtype=str)
    for col in searchable_cols:
        combined = combined + " " + df[col].astype(str).str.lower()
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask = mask | combined.str.contains(re.escape(token), na=False)
    return df[mask].copy()


def chat_answer(question: str, run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[str, pd.DataFrame | None]:
    q = question.lower().strip()
    if not run_frames:
        return "Upload and generate a dashboard first.", None
    df = run_frames[-1]["APIs"].copy()
    label = run_frames[-1]["Label"]
    n = extract_top_n(q)
    mcol = metric_col(q)

    if any(w in q for w in ["context", "date", "duration", "region", "users", "devices", "concurrent"]):
        rows = []
        for f in run_frames:
            info = f.get("Run_Info")
            if info is not None and not info.empty:
                row = info.iloc[0].to_dict()
                row["Run"] = f["Label"]
                rows.append(row)
        if rows:
            context = pd.DataFrame(rows)
            return "Report context extracted from uploaded filename(s).", context[safe_cols(context, ["Run", "Concurrent Users", "Devices Count", "Date", "Duration", "Region"])]
        return "Report context was not available.", None

    if any(w in q for w in ["compare", "comparison", "baseline", "regress", "regression", "delta", "difference"]):
        if len(run_frames) < 2:
            return "Comparison needs two or more uploaded JSON files.", None
        if any(w in q for w in ["regress", "delta", "difference", "changed", "worse", "improve"]):
            first_label = run_frames[0]["Label"]
            last_label = run_frames[-1]["Label"]
            first = run_frames[0]["APIs"][["API", "Feature", "Scenario", "Endpoint", "Avg ResTime in sec", "errorCount", "SLA Status"]]
            last = run_frames[-1]["APIs"][["API", "Avg ResTime in sec", "errorCount", "SLA Status"]]
            diff = first.merge(last, on="API", how="outer", suffixes=(f" ({first_label})", f" ({last_label})"))
            diff["Avg Sec Delta"] = (pd.to_numeric(diff[f"Avg ResTime in sec ({last_label})"], errors="coerce") - pd.to_numeric(diff[f"Avg ResTime in sec ({first_label})"], errors="coerce")).round(2)
            diff["Error Delta"] = (pd.to_numeric(diff[f"errorCount ({last_label})"], errors="coerce").fillna(0) - pd.to_numeric(diff[f"errorCount ({first_label})"], errors="coerce").fillna(0)).astype(int)
            return "Latest vs baseline API comparison. Positive Avg Sec Delta means slower in latest run.", diff.sort_values(["Avg Sec Delta", "Error Delta"], ascending=False).head(n)
        rows = []
        for f in run_frames:
            row = summarize_run(f["APIs"])
            row["Run"] = f["Label"]
            rows.append(row)
        return "Run-level comparison summary.", pd.DataFrame(rows)

    if any(w in q for w in ["health", "summary", "overall", "status", "executive", "overview"]):
        s = summarize_run(df)
        return f"Overall for **{label}**: Performance Score **{s['performance_score']}**, SLA Compliance **{s['sla_compliance']}%**, Success Rate **{s['success_rate']}%**, Error Rate **{s['error_rate']}%**, Avg Response **{s['avg_sec']} sec**, P95 **{s['p95_sec']} sec**, Errors **{s['errors']}**, Samples **{s['samples']}**.", None

    if any(w in q for w in ["sla", "breach", "breached", "violate", "violation", "pass", "failed", "fail"]):
        if "pass" in q and "fail" not in q and "breach" not in q:
            ok = df[df["SLA Status"] == "PASS"].copy()
            return f"APIs passing SLA for **{label}**.", ok[standard_api_cols(ok)].head(n)
        fail = df[df["SLA Status"] == "FAIL"].sort_values("SLA Breach Sec", ascending=False)
        if fail.empty:
            return f"No SLA breaches found in **{label}**.", None
        return f"Top {min(n, len(fail))} SLA breaches for **{label}**.", fail[standard_api_cols(fail)].head(n)

    if any(w in q for w in ["error", "errors", "failure", "failures", "errorpct"]):
        err = df[pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0) > 0].copy()
        if err.empty:
            return f"No API errors found in **{label}**.", None
        sort_col = "errorPct" if "percent" in q or "pct" in q else "errorCount"
        return f"Top {min(n, len(err))} error APIs for **{label}** sorted by {sort_col}.", err.sort_values(sort_col, ascending=False)[standard_api_cols(err)].head(n)

    if any(w in q for w in ["track", "tracks", "feature", "features"]):
        ts = track_summary(df)
        matched = match_rows(ts.rename(columns={"Feature": "API"}), question)
        if not matched.empty:
            return "Matching track summary rows.", matched.head(n)
        return f"Worst tracks for **{label}** by P95, Avg Sec, and Errors.", ts.head(n)

    if any(w in q for w in ["sample", "samples", "count", "volume", "load"]):
        sample_df = df.sort_values("sampleCount", ascending=False)
        return f"Top {min(n, len(sample_df))} APIs by sample count for **{label}**.", sample_df[standard_api_cols(sample_df)].head(n)

    if any(w in q for w in ["p90", "p95", "p99", "percentile", "90", "95", "99", "slow", "latency", "response", "time", "avg", "maximum", "minimum", "max", "min"]):
        if mcol not in df.columns:
            return f"{mcol} is not available in this report.", None
        top = df.sort_values(mcol, ascending=False)
        return f"Top {min(n, len(top))} APIs for **{label}** based on **{mcol}**.", top[standard_api_cols(top)].head(n)

    matched = match_rows(df, question)
    if not matched.empty:
        matched = matched.sort_values(["SLA Breach Sec", "Avg ResTime in sec", "errorCount"], ascending=False)
        return f"I found {len(matched)} matching API rows. Showing most relevant rows.", matched[standard_api_cols(matched)].head(n)

    return "I can answer questions like: top slow APIs, SLA breaches, top errors, worst tracks, P95/P99, samples, report context, compare runs, or keyword searches for an API/endpoint.", None


st.markdown(f"<div class='dashboard-title'>{APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Upload one JMeter <code>statistics.json</code> file for a normal dashboard. Upload two or more files for comparison.</div>", unsafe_allow_html=True)

render_open_new_tab_button()

st.markdown(
    """
<div class="rules-section">
<h3>SLA Rules</h3>
<ul>
<li>AskAI APIs: SLA is &lt; 10 sec</li>
<li>Assets, Assessments, Home, Settings and Support APIs: SLA is &lt; 2 sec</li>
</ul>
<h3>Track Comparison Metrics</h3>
<ul>
<li>AskAI tracks:
<span class="metric-pill">0-10s</span>,
<span class="metric-pill">10-20s</span>,
<span class="metric-pill">20-30s</span>,
<span class="metric-pill">&gt;30s</span>
</li>
<li>Assets, Assessments, Home, Settings and Support tracks:
<span class="metric-pill">0-2s</span>,
<span class="metric-pill">3-4s</span>,
<span class="metric-pill">4-6s</span>,
<span class="metric-pill">&gt;6s</span>
</li>
</ul>
</div>
""",
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader("Upload statistics.json file(s)", type=["json"], accept_multiple_files=True)

if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None
if "run_frames" not in st.session_state:
    st.session_state.run_frames = []
if "report_file_name" not in st.session_state:
    st.session_state.report_file_name = "JMeter_Report.xlsx"
if "messages" not in st.session_state:
    st.session_state.messages = []

generate_clicked = st.button("Generate Tableau Dashboard + Excel Report", type="primary", disabled=not uploaded_files)

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
                st.success("Single Tableau dashboard and Excel report generated successfully.")
            else:
                build_comparison_report(json_paths, labels, output_path)
                st.success("Comparison Tableau dashboard and Excel report generated successfully.")

            run_frames = add_region_to_frames(run_frames)
            st.session_state.excel_bytes = output_path.read_bytes()
            st.session_state.run_frames = run_frames
            st.session_state.report_file_name = "JMeter_Report.xlsx"
            st.session_state.messages = []
        except Exception as exc:
            st.error(f"Failed to generate report: {exc}")

if st.session_state.excel_bytes:
    st.download_button(
        label="Download Excel Report",
        data=st.session_state.excel_bytes,
        file_name=st.session_state.report_file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

if st.session_state.run_frames:
    render_tableau_dashboard(st.session_state.run_frames)
    render_region_comparison(st.session_state.run_frames)
    render_drilldown(st.session_state.run_frames)

    st.divider()
    st.subheader("🤖 Performance Chatbot")
    with st.expander("Example questions", expanded=False):
        st.write(
            "- What are the top slow APIs?\n"
            "- Which APIs are breaching SLA?\n"
            "- Show top error APIs\n"
            "- Which tracks are worst?\n"
            "- Give overall health summary\n"
            "- Compare runs\n"
            "- Show regression\n"
            "- What is the report date and duration?"
        )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("table") is not None:
                st.dataframe(msg["table"], use_container_width=True, hide_index=True)

    question = st.chat_input("Ask about SLA, slow APIs, errors, tracks, context, or comparison...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question, "table": None})
        answer, table = chat_answer(question, st.session_state.run_frames)
        st.session_state.messages.append({"role": "assistant", "content": answer, "table": table})
        st.rerun()
