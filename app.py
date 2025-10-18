# app.py
# 🎓 TITAN SUKKUR — Full Premium Students Analysis Dashboard (Single-file)
# Auto-load Students_Performance.csv (or demo), Dark Blue theme, Plotly interactive charts,
# KPIs, filters, Top Students, Subject analysis, Gender comparison, CSV & Excel export.

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import io
from datetime import datetime

# --- Page config ---
st.set_page_config(page_title="TITAN SUKKUR Students Analysis Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Styling: Dark Blue Premium ---
st.markdown(
    """
    <style>
    :root {
        --primary:#06283D;
        --accent:#1673B1;
        --muted:#9AAFC3;
        --bg: linear-gradient(180deg,#071426 0%, #021424 100%);
    }
    body, .reportview-container, .main {
        background: var(--bg);
        color: #e6f2ff;
    }
    .big-header {
        font-size:26px;
        font-weight:800;
        color:#9fe0ff;
        letter-spacing:0.6px;
    }
    .sub-header {
        color:var(--muted);
        font-size:13px;
        margin-top:-6px;
    }
    .logo-text {
        font-weight:900;
        color:#eaf6ff;
        font-size:18px;
        letter-spacing:1px;
    }
    .kpi {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-left: 4px solid var(--accent);
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .small { color: var(--muted); font-size:12px; }
    .card-title { color:#d8eefc; font-weight:700; margin-bottom:6px; }
    .stButton>button { background: linear-gradient(90deg,var(--accent), #0B4F8A); color: white; border: none; }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
hcol1, hcol2 = st.columns([0.18, 0.82])
with hcol1:
    st.markdown('<div class="logo-text">SMIT<br><span style="font-size:12px;font-weight:700;">TITAN SUKKUR</span></div>', unsafe_allow_html=True)
with hcol2:
    st.markdown('<div class="big-header">🎓 TITAN SUKKUR Students Analysis Dashboard (Full Premium)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive analytics — filters, charts, rankings, and downloadable reports.</div>', unsafe_allow_html=True)
st.markdown("---")

# --- Data loading (auto load file or demo) ---
@st.cache_data
def load_from_csv(path="Students_Performance.csv"):
    return pd.read_csv(path)

@st.cache_data
def demo_data(n=300, seed=42):
    rng = np.random.default_rng(seed)
    genders = ["female", "male"]
    races = ["group A","group B","group C","group D","group E"]
    pedu = ["some high school","high school","some college","associate's degree","bachelor's degree","master's degree"]
    lunch = ["standard","free/reduced"]
    prep = ["none","completed"]
    df = pd.DataFrame({
        "gender": rng.choice(genders, n),
        "race/ethnicity": rng.choice(races, n),
        "parental level of education": rng.choice(pedu, n),
        "lunch": rng.choice(lunch, n),
        "test preparation course": rng.choice(prep, n),
        "math score": rng.integers(35, 100, n),
        "reading score": rng.integers(30, 100, n),
        "writing score": rng.integers(28, 100, n)
    })
    return df

# Attempt to load provided CSV; if missing -> demo automatically
df = None
data_source = "local"
try:
    df = load_from_csv()
except FileNotFoundError:
    df = demo_data()
    data_source = "demo (auto-loaded)"
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    df = demo_data()
    data_source = f"demo (auto-loaded due to error)"

st.sidebar.header("Data")
st.sidebar.markdown(f"**Source:** {data_source}")

# Normalize column names
df.columns = [c.strip() for c in df.columns]

# Helper: find column case-insensitively
def find_col(name_lower):
    for c in df.columns:
        if c.lower() == name_lower:
            return c
    return None

col_gender = find_col("gender")
col_race = find_col("race/ethnicity")
col_peducation = find_col("parental level of education")
col_lunch = find_col("lunch")
col_testprep = find_col("test preparation course")
col_math = find_col("math score")
col_read = find_col("reading score")
col_write = find_col("writing score")

# Ensure numeric for score columns
for c in [col_math, col_read, col_write]:
    if c:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# --- Sidebar Filters (no file upload) ---
st.sidebar.header("Filters & Controls")
if col_gender:
    genders = sorted(df[col_gender].dropna().unique().tolist())
    sel_gender = st.sidebar.multiselect("Gender", options=genders, default=genders)
else:
    sel_gender = None

if col_testprep:
    prep_opts = sorted(df[col_testprep].dropna().unique().tolist())
    sel_prep = st.sidebar.multiselect("Test Preparation", options=prep_opts, default=prep_opts)
else:
    sel_prep = None

if col_peducation:
    pedu_opts = sorted(df[col_peducation].dropna().unique().tolist())
    sel_pedu = st.sidebar.multiselect("Parent Education", options=pedu_opts, default=pedu_opts)
else:
    sel_pedu = None

# Score sliders with safe defaults
def min_max_for(col, default=(0,100)):
    if col and df[col].notna().any():
        return int(df[col].min()), int(df[col].max())
    return default

math_min, math_max = min_max_for(col_math)
read_min, read_max = min_max_for(col_read)
write_min, write_max = min_max_for(col_write)

sel_math = st.sidebar.slider("Math score range", 0, 100, (math_min, math_max))
sel_read = st.sidebar.slider("Reading score range", 0, 100, (read_min, read_max))
sel_write = st.sidebar.slider("Writing score range", 0, 100, (write_min, write_max))

# Quick toggle: show detailed analysis
detailed = st.sidebar.checkbox("Show advanced subjects analysis", value=True)

# Apply filters
filtered = df.copy()
if col_gender and sel_gender:
    filtered = filtered[filtered[col_gender].isin(sel_gender)]
if col_testprep and sel_prep:
    filtered = filtered[filtered[col_testprep].isin(sel_prep)]
if col_peducation and sel_pedu:
    filtered = filtered[filtered[col_peducation].isin(sel_pedu)]
if col_math:
    filtered = filtered[(filtered[col_math] >= sel_math[0]) & (filtered[col_math] <= sel_math[1])]
if col_read:
    filtered = filtered[(filtered[col_read] >= sel_read[0]) & (filtered[col_read] <= sel_read[1])]
if col_write:
    filtered = filtered[(filtered[col_write] >= sel_write[0]) & (filtered[col_write] <= sel_write[1])]

# --- Top KPI row ---
st.subheader("Overview")
k1, k2, k3, k4 = st.columns([1.2,1.2,1.2,1.0])

def safe_mean(d, c):
    return round(d[c].mean(),2) if (c and c in d.columns and d[c].notna().any()) else "N/A"

with k1:
    st.markdown('<div class="kpi"><div style="font-size:13px;color:#9fe0ff;font-weight:700">Average Math</div>'
                f'<div style="font-size:22px;margin-top:6px">{safe_mean(filtered, col_math)}</div>'
                '<div class="small">Filtered average</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown('<div class="kpi"><div style="font-size:13px;color:#9fe0ff;font-weight:700">Average Reading</div>'
                f'<div style="font-size:22px;margin-top:6px">{safe_mean(filtered, col_read)}</div>'
                '<div class="small">Filtered average</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown('<div class="kpi"><div style="font-size:13px;color:#9fe0ff;font-weight:700">Average Writing</div>'
                f'<div style="font-size:22px;margin-top:6px">{safe_mean(filtered, col_write)}</div>'
                '<div class="small">Filtered average</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown('<div class="kpi"><div style="font-size:13px;color:#9fe0ff;font-weight:700">Records</div>'
                f'<div style="font-size:22px;margin-top:6px">{len(filtered):,}</div>'
                '<div class="small">Rows shown</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- Main layout ---
left, right = st.columns((2.2, 1))

with left:
    # 1) Gender vs Subject comparison (grouped bars)
    st.markdown("### Gender vs Average Scores")
    if col_gender and any([col_math, col_read, col_write]):
        score_cols = [c for c in [col_math, col_read, col_write] if c]
        agg = filtered.groupby(col_gender)[score_cols].mean().reset_index()
        # melt for plotly grouped bar
        melt = agg.melt(id_vars=[col_gender], value_vars=score_cols, var_name="subject", value_name="avg_score")
        # short subject names
        melt["subject_label"] = melt["subject"].map({col_math:"Math", col_read:"Reading", col_write:"Writing"})
        fig1 = px.bar(melt, x=col_gender, y="avg_score", color="subject_label", barmode="group",
                      labels={col_gender:"Gender", "avg_score":"Average Score", "subject_label":"Subject"},
                      height=420)
        fig1.update_layout(template="plotly_dark", margin=dict(l=8,r=8,t=30,b=8))
        st.plotly_chart(fig1, use_container_width=True, config={"displaylogo": False})
        if st.button("Expand: Gender vs Subjects", key="exp_gender_subject"):
            st.plotly_chart(fig1.update_layout(height=760), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Not enough columns to show Gender vs Subjects chart.")

    # 2) Distribution per subject (hist + box)
    st.markdown("### Subject Distributions")
    cols_to_show = []
    if col_math:
        cols_to_show.append(col_math)
    if col_read:
        cols_to_show.append(col_read)
    if col_write:
        cols_to_show.append(col_write)

    if cols_to_show:
        # create a subplot-like vertical stack - show each
        for c in cols_to_show:
            friendly = "Math" if c==col_math else ("Reading" if c==col_read else "Writing")
            fig_hist = px.histogram(filtered, x=c, nbins=20, marginal="box", title=f"{friendly} Score Distribution", height=300)
            fig_hist.update_layout(template="plotly_dark", margin=dict(l=8,r=8,t=30,b=8))
            st.plotly_chart(fig_hist, use_container_width=True, config={"displaylogo": False})
            if st.button(f"Expand: {friendly} Distribution", key=f"exp_{c}"):
                st.plotly_chart(fig_hist.update_layout(height=760), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("No subject score columns found for distributions.")

    # 3) Correlation heatmap
    st.markdown("### Correlation Heatmap (scores)")
    score_cols_present = [c for c in [col_math, col_read, col_write] if c and c in filtered.columns]
    if len(score_cols_present) >= 2:
        corr = filtered[score_cols_present].corr()
        fig_heat = ff.create_annotated_heatmap(
            z=np.round(corr.values, 2),
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale='Blues',
            showscale=True
        )
        fig_heat.update_layout(template="plotly_dark", height=380, margin=dict(l=8,r=8,t=8,b=8))
        st.plotly_chart(fig_heat, use_container_width=True, config={"displaylogo": False})
        if st.button("Expand: Correlation Heatmap", key="exp_heat"):
            st.plotly_chart(fig_heat.update_layout(height=760), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Not enough score columns for correlation heatmap.")

    # 4) Advanced: Subject Radar (if detailed checked)
    if detailed and len(score_cols_present) == 3:
        st.markdown("### Subjects Radar (average per group)")
        # group by race or gender preference
        groupby_col = col_race if col_race else col_gender
        if groupby_col:
            grp = filtered.groupby(groupby_col)[score_cols_present].mean().reset_index()
            # create a radar per top 4 groups
            topg = grp.sort_values(score_cols_present[0], ascending=False).head(4)
            fig_radar = px.line_polar()
            # prepare traces
            fig = px.line_polar()
            for i, row in topg.iterrows():
                values = row[score_cols_present].tolist()
                labels = ["Math" if c==col_math else ("Reading" if c==col_read else "Writing") for c in score_cols_present]
                # close polygon
                fig.add_trace(px.line_polar(r=values+[values[0]], theta=labels+[labels[0]], name=str(row[groupby_col])).data[0])
            fig.update_layout(template="plotly_dark", height=420, polar=dict(radialaxis=dict(visible=True, range=[0,100])))
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("No grouping column (race/gender) found for radar chart.")

with right:
    st.markdown("### Filters Summary")
    def join_or_all(sel):
        if isinstance(sel, list):
            return ", ".join(sel) if sel else "All"
        return str(sel)
    st.markdown(f"- **Gender:** {join_or_all(sel_gender)}")
    st.markdown(f"- **Test Prep:** {join_or_all(sel_prep)}")
    st.markdown(f"- **Parent Edu:** {join_or_all(sel_pedu)}")
    st.markdown(f"- **Math range:** {sel_math[0]} — {sel_math[1]}")
    st.markdown(f"- **Reading range:** {sel_read[0]} — {sel_read[1]}")
    st.markdown(f"- **Writing range:** {sel_write[0]} — {sel_write[1]}")
    st.markdown("---")

    # Data preview
    st.markdown("### Data Preview")
    st.dataframe(filtered.head(8), height=220)

    # Top Students ranking
    st.markdown("### Top Students (by average score)")
    tmp = filtered.copy()
    if score_cols_present:
        tmp["avg_score"] = tmp[score_cols_present].mean(axis=1)
        top_n = st.number_input("Show top N students", min_value=3, max_value=200, value=10, step=1)
        top_table = tmp.sort_values("avg_score", ascending=False).head(int(top_n))
        display_cols = [c for c in [col_gender, col_peducation, col_testprep] if c in top_table.columns]
        display_cols += score_cols_present + ["avg_score"]
        top_table = top_table[display_cols].reset_index(drop=True)
        # round numeric columns for neatness
        for c in score_cols_present + ["avg_score"]:
            if c in top_table.columns:
                top_table[c] = top_table[c].round(2)
        st.dataframe(top_table, height=320)
    else:
        st.info("No score columns available to compute top students.")

    st.markdown("---")
    # Export buttons: CSV + Excel report
    st.markdown("### Export / Reports")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered CSV", csv_bytes, file_name="students_filtered.csv", mime="text/csv")

    def create_excel_report(df_report):
        """
        Create an Excel file in-memory with:
        - Sheet1: filtered data
        - Sheet2: summary KPIs
        - Sheet3: top students
        Returns bytes
        """
        output = io.BytesIO()
        # Use pandas ExcelWriter (openpyxl)
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Sheet: data
            df_report.to_excel(writer, sheet_name="Filtered Data", index=False)
            # Summary
            summary = {}
            if col_math: summary["Avg Math"] = round(df_report[col_math].mean(),2)
            if col_read: summary["Avg Reading"] = round(df_report[col_read].mean(),2)
            if col_write: summary["Avg Writing"] = round(df_report[col_write].mean(),2)
            summary["Rows"] = len(df_report)
            pd.DataFrame(list(summary.items()), columns=["Metric","Value"]).to_excel(writer, sheet_name="Summary", index=False)
            # Top students
            if score_cols_present:
                tmp2 = df_report.copy()
                tmp2["avg_score"] = tmp2[score_cols_present].mean(axis=1)
                top = tmp2.sort_values("avg_score", ascending=False).head(50)
                top.to_excel(writer, sheet_name="Top Students", index=False)
            writer.save()
            processed_data = output.getvalue()
        return processed_data

    try:
        excel_bytes = create_excel_report(filtered)
        st.download_button("Download Excel Report (.xlsx)", excel_bytes, file_name=f"students_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.info("Excel export requires openpyxl. Install `openpyxl` to enable Excel report.")
        # fallback: provide CSV only (already provided)

st.markdown("---")

# --- Insights row ---
ins1, ins2, ins3 = st.columns(3)
with ins1:
    st.markdown("**Mean of Averages**")
    if score_cols_present:
        filtered["avg_score"] = filtered[score_cols_present].mean(axis=1)
        st.metric("Mean Avg Score", round(filtered["avg_score"].mean(),2))
    else:
        st.write("N/A")
with ins2:
    st.markdown("**Completed Test Prep**")
    if col_testprep and filtered[col_testprep].dtype == object:
        completed = filtered[filtered[col_testprep].str.lower() == "completed"].shape[0]
        st.metric("Completed", f"{completed}")
    else:
        st.write("N/A")
with ins3:
    st.markdown("**High Achievers (avg >= 85)**")
    if "avg_score" in filtered.columns:
        ha = filtered[filtered["avg_score"] >= 85].shape[0]
        st.metric("Count", f"{ha}")
    else:
        st.write("N/A")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#9aaec6">Built by Ahmed Sabur • SMIT TITAN SUKKUR • Full Premium Dashboard • Plotly</div>', unsafe_allow_html=True)
