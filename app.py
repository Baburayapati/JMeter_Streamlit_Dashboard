
from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from main import build_report, build_comparison_report, build_single_report_frames


APP_TITLE = "CiscoIQ-SaaS-Support-Services Performance Dashboard"


st.set_page_config(page_title=APP_TITLE, layout="wide")


st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #eef7ff 0%, #f6f2ff 45%, #ecfff4 100%);
        color: #172033;
    }

    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0);
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.2rem;
        max-width: 1280px;
    }

    .dashboard-title {
        display: table;
        margin: 0 auto 0.45rem auto;
        background: linear-gradient(90deg, #154c79, #7b2cbf);
        color: white;
        padding: 10px 18px;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(21, 76, 121, 0.18);
        font-size: 18px;
        line-height: 1.2;
        font-weight: 700;
        text-align: center;
        width: auto;
        max-width: fit-content;
    }

    .dashboard-subtitle {
        text-align: center;
        font-size: 12px;
        color: #27364a;
        margin-bottom: 0.9rem;
    }

    .rules-section {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(21, 76, 121, 0.12);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 1rem;
    }

    .rules-section h3 {
        color: #154c79 !important;
        margin-top: 0.35rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 16px !important;
        line-height: 1.15 !important;
        font-weight: 600 !important;
    }

    .rules-section ul {
        margin-top: 0.2rem !important;
        margin-bottom: 0.6rem !important;
        padding-left: 1.25rem !important;
    }

    .rules-section li {
        font-size: 13px !important;
        line-height: 1.35 !important;
        font-weight: 400 !important;
        margin-bottom: 0.2rem !important;
    }

    .metric-pill {
        color: #2e7d32 !important;
        background: rgba(46, 125, 50, 0.08);
        border-radius: 7px;
        padding: 1px 6px;
        font-weight: 500;
        white-space: nowrap;
    }

    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(21, 76, 121, 0.18);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.06);
    }

    .stDownloadButton button,
    .stButton button {
        border-radius: 12px;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(21, 76, 121, 0.14);
        border-radius: 14px;
        padding: 0.75rem 0.85rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.045);
    }

    .section-card {
        background: rgba(255,255,255,0.76);
        border: 1px solid rgba(21,76,121,0.12);
        border-radius: 16px;
        padding: 1rem;
        margin-top: 0.7rem;
    }
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

    avg_col = "Avg ResTime in sec"
    max_col = "MaxRes Time in sec"
    p95_col = "95thPercentile Resp Time in Sec"

    for col in [avg_col, max_col, p95_col, "sampleCount", "errorCount", "errorPct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["SLA Sec"] = df["Feature"].str.upper().str.startswith("ASKAI").map({True: 10, False: 2})
    df["SLA Status"] = (df[avg_col] < df["SLA Sec"]).map({True: "PASS", False: "FAIL"})
    df["SLA Breach Sec"] = (df[avg_col] - df["SLA Sec"]).clip(lower=0).round(2)
    df["Track Type"] = df["Feature"].str.upper().str.startswith("ASKAI").map({True: "AskAI", False: "Other"})
    return df


def process_uploaded_file(path: Path, label: str) -> Dict[str, pd.DataFrame]:
    frames = build_single_report_frames(path)
    frames["APIs"] = add_ui_sla_columns(frames["APIs"])
    frames["Label"] = label
    return frames


def get_health_score(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    total_apis = len(df)
    pass_pct = (df["SLA Status"].eq("PASS").sum() / total_apis * 100) if total_apis else 0
    sample_total = pd.to_numeric(df.get("sampleCount", 0), errors="coerce").fillna(0).sum()
    error_total = pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0).sum()
    error_rate = (error_total / sample_total * 100) if sample_total else 0
    return round(max(0, min(100, pass_pct - error_rate)), 2)


def summarize_run(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return {
            "total_apis": 0,
            "sla_pass_pct": 0,
            "sla_fail_pct": 0,
            "avg_sec": 0,
            "p95_sec": 0,
            "errors": 0,
            "samples": 0,
            "health": 0,
        }
    total = len(df)
    pass_count = int(df["SLA Status"].eq("PASS").sum())
    fail_count = int(df["SLA Status"].eq("FAIL").sum())
    return {
        "total_apis": total,
        "sla_pass_pct": round(pass_count / total * 100, 2) if total else 0,
        "sla_fail_pct": round(fail_count / total * 100, 2) if total else 0,
        "avg_sec": round(float(df["Avg ResTime in sec"].mean()), 2),
        "p95_sec": round(float(df["95thPercentile Resp Time in Sec"].mean()), 2) if "95thPercentile Resp Time in Sec" in df.columns else 0,
        "errors": int(pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0).sum()),
        "samples": int(pd.to_numeric(df.get("sampleCount", 0), errors="coerce").fillna(0).sum()),
        "health": get_health_score(df),
    }


def render_kpis(df: pd.DataFrame) -> None:
    s = summarize_run(df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Health Score", s["health"])
    c2.metric("SLA Pass %", f'{s["sla_pass_pct"]}%')
    c3.metric("SLA Fail %", f'{s["sla_fail_pct"]}%')
    c4.metric("Avg Sec", s["avg_sec"])
    c5.metric("P95 Sec", s["p95_sec"])
    c6.metric("Errors", s["errors"])


def render_single_dashboard(frames: Dict[str, pd.DataFrame]) -> None:
    df = frames["APIs"].copy()
    st.subheader("📊 Interactive Dashboard")

    with st.container():
        f1, f2, f3, f4 = st.columns([2, 2, 1.3, 1.3])
        tracks = sorted(df["Feature"].dropna().astype(str).unique().tolist())
        selected_tracks = f1.multiselect("Tracks", tracks, default=tracks)
        selected_status = f2.multiselect("SLA Status", ["PASS", "FAIL"], default=["PASS", "FAIL"])
        selected_type = f3.multiselect("Track Type", ["AskAI", "Other"], default=["AskAI", "Other"])
        min_errors = f4.number_input("Min Errors", min_value=0, value=0, step=1)

    filtered = df[
        df["Feature"].isin(selected_tracks)
        & df["SLA Status"].isin(selected_status)
        & df["Track Type"].isin(selected_type)
        & (pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0) >= min_errors)
    ].copy()

    render_kpis(filtered)

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "SLA Drilldown", "Track Analysis", "API Data"])

    with tab1:
        c1, c2 = st.columns(2)
        sla_counts = filtered["SLA Status"].value_counts().reset_index()
        sla_counts.columns = ["SLA Status", "Count"]
        fig_pie = px.pie(
            sla_counts,
            names="SLA Status",
            values="Count",
            title="SLA Pass vs Fail",
            color="SLA Status",
            color_discrete_map={"PASS": "#2E7D32", "FAIL": "#C62828"},
            hole=0.35,
        )
        c1.plotly_chart(fig_pie, use_container_width=True)

        top_slow = filtered.sort_values("Avg ResTime in sec", ascending=False).head(10)
        fig_slow = px.bar(
            top_slow.sort_values("Avg ResTime in sec"),
            x="Avg ResTime in sec",
            y="API",
            orientation="h",
            title="Top 10 Slow APIs",
            text="Avg ResTime in sec",
        )
        fig_slow.update_traces(texttemplate="%{text:.2f}s", textposition="outside")
        fig_slow.update_layout(yaxis_title="", xaxis_title="Avg Response Time (sec)", height=480)
        c2.plotly_chart(fig_slow, use_container_width=True)

        err_df = filtered[pd.to_numeric(filtered.get("errorCount", 0), errors="coerce").fillna(0) > 0].sort_values("errorCount", ascending=False).head(10)
        fig_err = px.bar(
            err_df.sort_values("errorCount"),
            x="errorCount",
            y="API",
            orientation="h",
            title="Top 10 Error APIs",
            text="errorCount",
        )
        fig_err.update_traces(texttemplate="%{text}", textposition="outside")
        fig_err.update_layout(yaxis_title="", xaxis_title="Error Count", height=480)
        st.plotly_chart(fig_err, use_container_width=True)

    with tab2:
        fail_df = filtered[filtered["SLA Status"] == "FAIL"].sort_values("SLA Breach Sec", ascending=False)
        st.markdown("#### SLA Breach APIs")
        st.dataframe(
            fail_df[["Feature", "Scenario", "Endpoint", "SLA Sec", "Avg ResTime in sec", "SLA Breach Sec", "errorCount"]].head(200),
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        track_summary = (
            filtered.groupby(["Feature", "Track Type"], dropna=False)
            .agg(
                APIs=("API", "count"),
                Avg_Sec=("Avg ResTime in sec", "mean"),
                P95_Sec=("95thPercentile Resp Time in Sec", "mean"),
                Max_Sec=("MaxRes Time in sec", "max"),
                Errors=("errorCount", "sum"),
                SLA_Fails=("SLA Status", lambda x: (x == "FAIL").sum()),
            )
            .reset_index()
        )
        track_summary["SLA Fail %"] = (track_summary["SLA_Fails"] / track_summary["APIs"] * 100).round(2)
        track_summary = track_summary.sort_values(["SLA Fail %", "Avg_Sec"], ascending=False)

        fig_track = px.bar(
            track_summary.head(15).sort_values("Avg_Sec"),
            x="Avg_Sec",
            y="Feature",
            color="Track Type",
            orientation="h",
            title="Top Tracks by Avg Response Time",
            text="Avg_Sec",
        )
        fig_track.update_traces(texttemplate="%{text:.2f}s", textposition="outside")
        fig_track.update_layout(yaxis_title="", xaxis_title="Avg Response Time (sec)", height=560)
        st.plotly_chart(fig_track, use_container_width=True)

        st.dataframe(track_summary, use_container_width=True, hide_index=True)

    with tab4:
        display_cols = [
            "Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct",
            "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec",
            "95thPercentile Resp Time in Sec", "SLA Sec", "SLA Status", "SLA Breach Sec",
        ]
        cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[cols], use_container_width=True, hide_index=True)


def render_comparison_dashboard(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.subheader("📈 Comparison Dashboard")

    combined = []
    for frames in run_frames:
        label = frames["Label"]
        df = frames["APIs"].copy()
        df["Run"] = label
        combined.append(df)

    all_df = pd.concat(combined, ignore_index=True) if combined else pd.DataFrame()
    if all_df.empty:
        st.warning("No API data available for comparison.")
        return

    summary_rows = []
    for label, g in all_df.groupby("Run"):
        row = summarize_run(g)
        row["Run"] = label
        summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows)

    st.dataframe(
        summary_df[["Run", "health", "total_apis", "sla_pass_pct", "sla_fail_pct", "avg_sec", "p95_sec", "errors", "samples"]],
        use_container_width=True,
        hide_index=True,
    )

    c1, c2 = st.columns(2)
    fig_avg = px.line(summary_df, x="Run", y="avg_sec", markers=True, title="Avg Response Time by Run")
    fig_avg.update_layout(xaxis_title="", yaxis_title="Avg Sec")
    c1.plotly_chart(fig_avg, use_container_width=True)

    fig_sla = px.bar(summary_df, x="Run", y="sla_fail_pct", title="SLA Fail % by Run", text="sla_fail_pct")
    fig_sla.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_sla.update_layout(xaxis_title="", yaxis_title="SLA Fail %")
    c2.plotly_chart(fig_sla, use_container_width=True)

    first_run = summary_df["Run"].iloc[0]
    last_run = summary_df["Run"].iloc[-1]
    first = all_df[all_df["Run"] == first_run][["API", "Feature", "Scenario", "Endpoint", "Avg ResTime in sec", "errorCount", "SLA Status"]]
    last = all_df[all_df["Run"] == last_run][["API", "Avg ResTime in sec", "errorCount", "SLA Status"]]
    diff = first.merge(last, on="API", how="outer", suffixes=(f" ({first_run})", f" ({last_run})"))
    diff["Avg Sec Delta"] = (
        pd.to_numeric(diff[f"Avg ResTime in sec ({last_run})"], errors="coerce")
        - pd.to_numeric(diff[f"Avg ResTime in sec ({first_run})"], errors="coerce")
    ).round(2)
    diff["Error Delta"] = (
        pd.to_numeric(diff[f"errorCount ({last_run})"], errors="coerce").fillna(0)
        - pd.to_numeric(diff[f"errorCount ({first_run})"], errors="coerce").fillna(0)
    ).astype(int)
    diff = diff.sort_values("Avg Sec Delta", ascending=False)

    st.markdown("#### Top Regressed APIs: Latest vs Baseline")
    st.dataframe(diff.head(50), use_container_width=True, hide_index=True)


def make_chat_answer(question: str, run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[str, pd.DataFrame | None]:
    q = question.lower().strip()
    if not run_frames:
        return "Upload and generate a report first. Then I can answer questions about SLA, slow APIs, errors, tracks, and comparison.", None

    latest = run_frames[-1]
    df = latest["APIs"].copy()
    label = latest["Label"]

    if "compare" in q or "baseline" in q or "regress" in q or "improve" in q:
        if len(run_frames) < 2:
            return "Comparison needs two or more uploaded JSON files.", None

        combined = []
        for frames in run_frames:
            tmp = frames["APIs"].copy()
            tmp["Run"] = frames["Label"]
            combined.append(tmp)
        all_df = pd.concat(combined, ignore_index=True)
        summary_rows = []
        for run, g in all_df.groupby("Run"):
            row = summarize_run(g)
            row["Run"] = run
            summary_rows.append(row)
        summary = pd.DataFrame(summary_rows)
        answer = "Comparison summary by run. Focus on higher SLA Fail %, Avg Sec, P95 Sec, and Errors."
        return answer, summary[["Run", "health", "sla_fail_pct", "avg_sec", "p95_sec", "errors", "samples"]]

    if "slow" in q or "latency" in q or "response" in q:
        top = df.sort_values("Avg ResTime in sec", ascending=False).head(10)
        answer = f"Top slow APIs for **{label}** based on Avg Response Time."
        return answer, top[["Feature", "Scenario", "Endpoint", "Avg ResTime in sec", "95thPercentile Resp Time in Sec", "SLA Status"]]

    if "error" in q or "failures" in q or "failing" in q:
        top = df[pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0) > 0].sort_values("errorCount", ascending=False).head(10)
        if top.empty:
            return f"No API errors found in **{label}**.", None
        answer = f"Top error APIs for **{label}**."
        return answer, top[["Feature", "Scenario", "Endpoint", "errorCount", "errorPct", "Avg ResTime in sec", "SLA Status"]]

    if "sla" in q or "breach" in q:
        summary = summarize_run(df)
        fail_df = df[df["SLA Status"] == "FAIL"].sort_values("SLA Breach Sec", ascending=False).head(20)
        answer = (
            f"For **{label}**, SLA Pass is **{summary['sla_pass_pct']}%**, "
            f"SLA Fail is **{summary['sla_fail_pct']}%**, and Health Score is **{summary['health']}**. "
            "Below are the top SLA breaches."
        )
        return answer, fail_df[["Feature", "Scenario", "Endpoint", "SLA Sec", "Avg ResTime in sec", "SLA Breach Sec"]]

    if "track" in q or "feature" in q:
        track_summary = (
            df.groupby("Feature")
            .agg(
                APIs=("API", "count"),
                Avg_Sec=("Avg ResTime in sec", "mean"),
                Max_Sec=("MaxRes Time in sec", "max"),
                Errors=("errorCount", "sum"),
                SLA_Fails=("SLA Status", lambda x: (x == "FAIL").sum()),
            )
            .reset_index()
        )
        track_summary["SLA Fail %"] = (track_summary["SLA_Fails"] / track_summary["APIs"] * 100).round(2)
        track_summary = track_summary.sort_values(["SLA Fail %", "Avg_Sec"], ascending=False).head(15)
        return f"Worst tracks for **{label}** by SLA Fail % and Avg Sec.", track_summary

    if "health" in q or "summary" in q or "overall" in q:
        s = summarize_run(df)
        answer = (
            f"Overall for **{label}**: Health Score **{s['health']}**, "
            f"SLA Pass **{s['sla_pass_pct']}%**, SLA Fail **{s['sla_fail_pct']}%**, "
            f"Avg Response **{s['avg_sec']} sec**, P95 **{s['p95_sec']} sec**, "
            f"Errors **{s['errors']}**, Samples **{s['samples']}**."
        )
        return answer, None

    answer = (
        "I can answer questions like: "
        "`top slow APIs`, `top error APIs`, `SLA breaches`, `worst tracks`, "
        "`overall health`, or `compare runs`."
    )
    return answer, None


# Header
st.markdown(f"<div class='dashboard-title'>{APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='dashboard-subtitle'>Upload one JMeter <code>statistics.json</code> file for a normal dashboard report. Upload two or more files for comparison.</div>",
    unsafe_allow_html=True,
)

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

uploaded_files = st.file_uploader(
    "Upload statistics.json file(s)",
    type=["json"],
    accept_multiple_files=True,
)

if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None
if "run_frames" not in st.session_state:
    st.session_state.run_frames = []
if "report_file_name" not in st.session_state:
    st.session_state.report_file_name = "JMeter_Report.xlsx"
if "messages" not in st.session_state:
    st.session_state.messages = []

generate_clicked = st.button("Generate Dashboard + Excel Report", type="primary", disabled=not uploaded_files)

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
                st.success("Single dashboard and Excel report generated successfully.")
            else:
                build_comparison_report(json_paths, labels, output_path)
                st.success("Comparison dashboard and Excel report generated successfully.")

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
    if len(st.session_state.run_frames) == 1:
        render_single_dashboard(st.session_state.run_frames[0])
    else:
        render_comparison_dashboard(st.session_state.run_frames)

    st.divider()
    st.subheader("🤖 Performance Chatbot")

    with st.expander("Example questions", expanded=False):
        st.write(
            "- What are the top slow APIs?\n"
            "- Which APIs are breaching SLA?\n"
            "- Show top error APIs\n"
            "- Which tracks are worst?\n"
            "- Give overall health summary\n"
            "- Compare runs"
        )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("table") is not None:
                st.dataframe(msg["table"], use_container_width=True, hide_index=True)

    question = st.chat_input("Ask about SLA, slow APIs, errors, tracks, or comparison...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question, "table": None})
        answer, table = make_chat_answer(question, st.session_state.run_frames)
        st.session_state.messages.append({"role": "assistant", "content": answer, "table": table})
        st.rerun()
