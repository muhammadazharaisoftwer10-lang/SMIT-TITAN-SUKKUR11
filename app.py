# app.py
# SMIT TITAN SUKKUR — Stylish Students Performance Dashboard (Single-file)
# Requirements:
#   pip install streamlit pandas plotly numpy
# Optional (for nicer table display): pip install openpyxl

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(
    page_title="SMIT TITAN SUKKUR Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Styles (blue professional) ---
st.markdown(
    """
    <style>
    /* Body + background */
    .reportview-container, .main {
        background: linear-gradient(180deg,#f6f9ff 0%, #ffffff 100%);
    }
    /* Header */
    .big-header {
        font-size:28px;
        font-weight:700;
        color:#0b4f8a;
        letter-spacing:0.4px;
    }
    .sub-header {
        color:#2b6cb0;
        font-size:14px;
        margin-top: -6px;
    }
    /* KPI card */
    .kpi {
        background: linear-gradient(180deg,#ffffff,#f1f8ff);
        border-left: 4px solid #2b6cb0;
        padding: 14px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(43,108,176,0.08);
    }
    .small {
        color:#6b7280;
        font-size:12px;
    }
    .logo-text {
        font-weight:800;
        color:#0b4f8a;
        font-size:18px;
        letter-spacing:1px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header with text logo ---
header_col1, header_col2 = st.columns([0.18, 0.82])
with header_col1:
    st.markdown('<div class="logo-text">SMIT<br><span style="font-size:12px;font-weight:600;">TITAN SUKKUR</span></div>', unsafe_allow_html=True)
with header_col2:
    st.markdown('<div class="big-header">SMIT TITAN SUKKUR — Students Performance Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive visual analytics for student scores — filter, explore and export</div>', unsafe_allow_html=True)

st.markdown("---")

# --- Data loader with cache ---
@st.cache_data
def load_data_from_file(uploaded=None):
    """Load CSV from local file or uploaded file-like object."""
    if uploaded is not None:
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_csv("Students_Performance.csv")
    # normalize column names to expected lower-case form
    df.columns = [c.strip() for c in df.columns]
    return df

# If file missing, let user upload
try:
    df = load_data_from_file()
except FileNotFoundError:
    st.error("Students_Performance.csv not found. Please upload your CSV file below.")
    uploaded_file = st.file_uploader("Upload Students_Performance.csv", type=["csv"])
    if uploaded_file:
        try:
            df = load_data_from_file(uploaded_file)
            st.success("File uploaded and loaded successfully.")
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")
            st.stop()
    else:
        st.stop()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# --- Validate expected columns ---
expected = {"gender","race/ethnicity","parental level of education","lunch","test preparation course",
            "math score","reading score","writing score"}
missing = expected - set([c.lower() for c in df.columns])
if missing:
    st.warning(f"Your CSV is missing these expected columns (case-sensitive check): {missing}. The app will still try to work with what it has.")
# Make sure numeric types
for col in ["math score","reading score","writing score"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Sidebar filters ---
st.sidebar.header("Filters")
# Helpful: map column names case-insensitively
def get_col(name_options):
    for n in name_options:
        if n in df.columns:
            return n
    # fallback try lower-case keys
    for c in df.columns:
        if c.lower() in name_options:
            return c
    return None

col_gender = get_col(["gender", "Gender"])
col_peducation = get_col(["parental level of education","parental level of education"])
col_test = get_col(["test preparation course","test preparation course"])
col_math = get_col(["math score","math score"])
col_read = get_col(["reading score","reading score"])
col_write = get_col(["writing score","writing score"])

# Provide filter widgets with safe defaults
if col_gender:
    gender_opts = sorted(df[col_gender].dropna().unique().tolist())
    gender = st.sidebar.multiselect("Gender", options=gender_opts, default=gender_opts)
else:
    gender = None

if col_test:
    test_opts = sorted(df[col_test].dropna().unique().tolist())
    test_prep = st.sidebar.multiselect("Test Preparation", options=test_opts, default=test_opts)
else:
    test_prep = None

if col_peducation:
    pedu_opts = sorted(df[col_peducation].dropna().unique().tolist())
    pedu = st.sidebar.multiselect("Parent Education Level", options=pedu_opts, default=pedu_opts)
else:
    pedu = None

# Score range sliders
min_math = int(np.nanmin(df[col_math])) if col_math and df[col_math].notna().any() else 0
max_math = int(np.nanmax(df[col_math])) if col_math and df[col_math].notna().any() else 100
math_range = st.sidebar.slider("Math score range", min_value=0, max_value=100, value=(min_math, max_math))

# Apply filters to dataframe
filtered = df.copy()
if col_gender and gender is not None:
    filtered = filtered[filtered[col_gender].isin(gender)]
if col_test and test_prep is not None:
    filtered = filtered[filtered[col_test].isin(test_prep)]
if col_peducation and pedu is not None:
    filtered = filtered[filtered[col_peducation].isin(pedu)]
# numeric range
if col_math:
    filtered = filtered[(filtered[col_math] >= math_range[0]) & (filtered[col_math] <= math_range[1])]

# --- Top bar KPIs ---
st.subheader("Overview")
k1, k2, k3, k4 = st.columns([1.2,1.2,1.2,1.2])

def metric_block(col, label, value, delta=None):
    with col:
        st.markdown(f'<div class="kpi"><div style="font-size:14px;color:#0b4f8a;font-weight:700">{label}</div>'
                    f'<div style="font-size:26px;margin-top:6px">{value}</div>'
                    f'<div class="small" style="margin-top:8px">{delta if delta else ""}</div></div>', unsafe_allow_html=True)

# compute averages safely
def safe_mean(df, c):
    return round(df[c].mean(),2) if (c in df.columns and df[c].notna().any()) else "N/A"

metric_block(k1, "Average Math Score", safe_mean(filtered, col_math))
metric_block(k2, "Average Reading Score", safe_mean(filtered, col_read))
metric_block(k3, "Average Writing Score", safe_mean(filtered, col_write))
metric_block(k4, "Filtered Rows", len(filtered))

st.markdown("---")

# --- Layout for charts and controls ---
left, right = st.columns((2.2, 1))

with left:
    # Visual 1: Average Scores by Gender (Plotly)
    st.markdown("### Average Math Score by Gender")
    if col_gender and col_math:
        agg = filtered.groupby(col_gender)[col_math].mean().reset_index().rename(columns={col_gender:"gender", col_math:"math_avg"})
        fig_gender = px.bar(
            agg, x=col_gender, y="math_avg",
            labels={col_gender:"Gender","math_avg":"Avg Math Score"},
            text=agg["math_avg"].round(2),
            height=340
        )
        fig_gender.update_layout(template="plotly_white", title=None, margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig_gender, use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove":["lasso2d","select2d"]})
        # Expand button for this chart
        if st.button("Expand: Gender Math Chart", key="expand_gender"):
            st.plotly_chart(fig_gender.update_layout(height=720), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gender or Math score column not found in dataset.")

    st.markdown("### Distribution of Reading Scores")
    if col_read:
        fig_hist = px.histogram(filtered, x=col_read, nbins=20, marginal="box", opacity=0.9, height=360,
                                labels={col_read:"Reading Score"}, title=None)
        fig_hist.update_layout(template="plotly_white", margin=dict(l=20,r=20,t=10,b=20))
        st.plotly_chart(fig_hist, use_container_width=True, config={"displaylogo": False})
        if st.button("Expand: Reading Distribution", key="expand_read"):
            st.plotly_chart(fig_hist.update_layout(height=720), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Reading score column not found.")

    st.markdown("### Correlation Heatmap (scores)")
    # Heatmap with plotly
    score_cols = [c for c in [col_math, col_read, col_write] if c and c in filtered.columns]
    if len(score_cols) >= 2:
        corr = filtered[score_cols].corr()
        fig_heat = ff.create_annotated_heatmap(
            z=np.round(corr.values, 2),
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale='Blues',
            showscale=True
        )
        fig_heat.update_layout(height=360, template="plotly_white", margin=dict(l=20,r=20,t=10,b=10))
        st.plotly_chart(fig_heat, use_container_width=True, config={"displaylogo": False})
        if st.button("Expand: Correlation Heatmap", key="expand_heat"):
            st.plotly_chart(fig_heat.update_layout(height=720), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Not enough score columns for correlation heatmap.")

with right:
    st.markdown("### Filters Summary")
    st.markdown(f"- Gender: **{', '.join(gender) if gender else 'All'}**")
    st.markdown(f"- Test Prep: **{', '.join(test_prep) if test_prep else 'All'}**")
    st.markdown(f"- Parent Edu: **{', '.join(pedu) if pedu else 'All'}**")
    st.markdown(f"- Math range: **{math_range[0]} — {math_range[1]}**")
    st.markdown("---")

    # Download filtered CSV
    st.markdown("### Export")
    csv_bytes = filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Download Filtered CSV", csv_bytes, file_name="students_filtered.csv", mime="text/csv")

    st.markdown("---")
    # Quick small table preview
    st.markdown("### Data Preview")
    st.dataframe(filtered.head(8), height=240)
    st.markdown("---")
    # Top Students ranking
    st.markdown("### Top Students (by average score)")
    if set([col_math,col_read,col_write]) <= set(filtered.columns):
        filtered["avg_score"] = filtered[[col_math,col_read,col_write]].mean(axis=1)
    else:
        # attempt to compute avg from available score cols
        available = [c for c in [col_math,col_read,col_write] if c in filtered.columns]
        if available:
            filtered["avg_score"] = filtered[available].mean(axis=1)
        else:
            filtered["avg_score"] = np.nan

    # show top N
    top_n = st.number_input("Show top N students", min_value=3, max_value=50, value=10, step=1)
    top_table = filtered.sort_values("avg_score", ascending=False).head(top_n)[
        [c for c in [col_gender, col_peducation, col_test, col_math, col_read, col_write, "avg_score"] if c in filtered.columns]
    ].reset_index(drop=True)
    # format: round scores
    for c in [col_math, col_read, col_write, "avg_score"]:
        if c in top_table.columns:
            top_table[c] = top_table[c].round(2)
    st.dataframe(top_table, height=320)

# --- Footer / credits ---
st.markdown("---")
st.markdown('<div style="text-align:center;color:#6b7280">Built by Ahmed Sabur • SMIT TITAN SUKKUR • Powered by Streamlit & Plotly</div>', unsafe_allow_html=True)
