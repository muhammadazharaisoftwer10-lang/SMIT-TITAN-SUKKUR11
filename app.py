# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Students_Performance Dashboard –",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# Simple dark CSS to improve visuals
# -------------------------
st.markdown(
    """
    <style>
    /* page background */
    .stApp {
        background: linear-gradient(180deg, #0f1226 0%, #0b0d16 100%);
        color: #e6eef8;
    }
    /* card styling for dataframe and other containers */
    .stDataFrame, .css-1v0mbdj, .css-1d391kg {
        background: transparent;
        color: #e6eef8;
    }
    /* sidebar */
    .css-1d391kg .stMarkdown {
        color: #e6eef8;
    }
    /* headers */
    .stHeader, h1, h2, h3 {
        color: #f1f5ff !important;
    }
    /* small tweak for metric delta colors */
    .stMetricDelta {
        color: #bfe9ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Utils & Data Loading
# -------------------------
@st.cache_data(ttl=3600)
def load_data_from_csv(path: str):
    """Load CSV from given path"""
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        # return None to indicate failure and allow upload fallback
        return None

def sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure expected columns exist and clean names"""
    df = df.copy()
    # normalize column names
    df.columns = df.columns.str.strip().str.lower()
    # common expected columns mapping (in case of spaces)
    rename_map = {}
    for c in df.columns:
        if c.replace(" ", "") == "mathscore" or c == "math score":
            rename_map[c] = "math score"
        if c.replace(" ", "") == "readingscore" or c == "reading score":
            rename_map[c] = "reading score"
        if c.replace(" ", "") == "writingscore" or c == "writing score":
            rename_map[c] = "writing score"
    if rename_map:
        df = df.rename(columns=rename_map)
    return df

# Try default load
df = load_data_from_csv("Students_Performance.csv")

# If default failed, show friendly message and allow upload fallback
if df is None:
    st.sidebar.error("Default file `Students_Performance.csv` not found in app folder.")
    uploaded = st.sidebar.file_uploader(
        "Or upload your Students_Performance CSV (fallback):",
        type=["csv"],
        help="If you don't have the CSV in the app folder, upload it here."
    )
    if uploaded is not None:
        with st.spinner("Loading uploaded file..."):
            try:
                df = pd.read_csv(uploaded)
                st.sidebar.success("Uploaded file loaded.")
            except Exception as e:
                st.sidebar.error(f"Failed to read uploaded file: {e}")
                st.stop()
    else:
        st.sidebar.info("Place `Students_Performance.csv` in the app folder or upload one.")
        st.stop()

# sanitize
df = sanitize_df(df)

# -------------------------
# Validate necessary columns
# -------------------------
required_cols = {"gender", "math score", "reading score", "writing score", "test preparation course", "parental level of education"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"The dataset is missing required columns: {', '.join(missing)}. Please ensure these columns exist (case-insensitive).")
    st.stop()

# -------------------------
# Sidebar - Filters & Controls
# -------------------------
st.sidebar.markdown("## 🔎 Filters")
# defaults
default_genders = sorted(df["gender"].dropna().unique().tolist())
default_tests = sorted(df["test preparation course"].dropna().unique().tolist())
default_education = sorted(df["parental level of education"].dropna().unique().tolist())

# session-state helpers for reset
if "reset_filters" not in st.session_state:
    st.session_state.reset_filters = False

if st.sidebar.button("🔄 Reset filters"):
    # toggle reset - re-run will set to default
    st.session_state.reset_filters = True
else:
    # keep previous
    pass

if st.session_state.reset_filters:
    gender = st.sidebar.multiselect("Select Gender:", default_genders, default=default_genders)
    test = st.sidebar.multiselect("Test Preparation:", default_tests, default=default_tests)
    education = st.sidebar.multiselect("Parent Education:", default_education, default=default_education)
    st.session_state.reset_filters = False
else:
    gender = st.sidebar.multiselect("Select Gender:", default_genders, default=default_genders)
    test = st.sidebar.multiselect("Test Preparation:", default_tests, default=default_tests)
    education = st.sidebar.multiselect("Parent Education:", default_education, default=default_education)

# numeric score range sliders
min_math, max_math = int(df["math score"].min()), int(df["math score"].max())
min_read, max_read = int(df["reading score"].min()), int(df["reading score"].max())
min_write, max_write = int(df["writing score"].min()), int(df["writing score"].max())

st.sidebar.markdown("### Score Ranges")
math_range = st.sidebar.slider("Math score range", min_math, max_math, (min_math, max_math))
read_range = st.sidebar.slider("Reading score range", min_read, max_read, (min_read, max_read))
write_range = st.sidebar.slider("Writing score range", min_write, max_write, (min_write, max_write))

# download or export info
st.sidebar.markdown("---")
st.sidebar.markdown("Built by *Ahmed Sabur* • SMIT TITAN Sukkur")
st.sidebar.markdown("")

# -------------------------
# Filter dataframe
# -------------------------
filtered_df = df[
    (df["gender"].isin(gender)) &
    (df["test preparation course"].isin(test)) &
    (df["parental level of education"].isin(education)) &
    (df["math score"].between(math_range[0], math_range[1])) &
    (df["reading score"].between(read_range[0], read_range[1])) &
    (df["writing score"].between(write_range[0], write_range[1]))
].reset_index(drop=True)

# No-data warning
if filtered_df.empty:
    st.warning("⚠️ No records match the selected filters. Try widening the filters or reset them.")
    st.stop()

# -------------------------
# Header / Title
# -------------------------
left, right = st.columns([3, 1])
with left:
    st.markdown("## 🎓 SMIT TITAN Sukkur    Students Performance Dashboard –")
    st.markdown("### Interactive insights — use the sidebar to filter. ")
with right:
    st.metric("Total Students", int(filtered_df.shape[0]))

st.markdown("---")

# -------------------------
# KPI Cards Row
# -------------------------
avg_math = round(filtered_df["math score"].mean(), 2)
avg_read = round(filtered_df["reading score"].mean(), 2)
avg_write = round(filtered_df["writing score"].mean(), 2)
pass_rate = round((filtered_df[["math score", "reading score", "writing score"]].mean(axis=1) >= 50).mean() * 100, 2)

k1, k2, k3, k4 = st.columns(4)
k1.metric("🧠 Avg Math", f"{avg_math}")
k2.metric("📚 Avg Reading", f"{avg_read}")
k3.metric("✍️ Avg Writing", f"{avg_write}")
k4.metric("✅ Pass Rate (avg>=50)", f"{pass_rate} %")

st.markdown("---")

# -------------------------
# Plotly color palette (cool)
# -------------------------
cool_colors = ["#2A9DF4", "#6F42C1", "#5BC0EB", "#7B2CBF", "#1B3A8A"]

# -------------------------
# Chart 1: Average Scores by Gender (Grouped Bar)
# -------------------------
st.subheader("Average Scores by Gender")
with st.spinner("Rendering chart..."):
    avg_by_gender = filtered_df.groupby("gender")[["math score", "reading score", "writing score"]].mean().reset_index()
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=avg_by_gender["gender"],
        y=avg_by_gender["math score"],
        name="Math",
        marker_color=cool_colors[0],
        hovertemplate="Gender: %{x}<br>Math: %{y:.2f}<extra></extra>"
    ))
    fig_bar.add_trace(go.Bar(
        x=avg_by_gender["gender"],
        y=avg_by_gender["reading score"],
        name="Reading",
        marker_color=cool_colors[1],
        hovertemplate="Gender: %{x}<br>Reading: %{y:.2f}<extra></extra>"
    ))
    fig_bar.add_trace(go.Bar(
        x=avg_by_gender["gender"],
        y=avg_by_gender["writing score"],
        name="Writing",
        marker_color=cool_colors[2],
        hovertemplate="Gender: %{x}<br>Writing: %{y:.2f}<extra></extra>"
    ))
    fig_bar.update_layout(barmode='group', template='plotly_dark', legend=dict(orientation="h"))
    fig_bar.update_yaxes(title_text="Average Score")
    st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------
# Chart 2: Distribution of Reading Scores (Histogram + KDE approximated)
# -------------------------
st.subheader("Distribution of Reading Scores")
with st.spinner("Rendering distribution..."):
    fig_hist = px.histogram(
        filtered_df,
        x="reading score",
        nbins=25,
        marginal="box",
        title="Reading Score Distribution",
        labels={"reading score": "Reading Score"},
        template="plotly_dark",
    )
    fig_hist.update_traces(marker=dict(color=cool_colors[3]))
    st.plotly_chart(fig_hist, use_container_width=True)

# -------------------------
# Chart 3: Scatter - Math vs Reading colored by Test Preparation
# -------------------------
st.subheader("Math vs Reading (by Test Preparation)")
with st.spinner("Rendering scatter..."):
    fig_scatter = px.scatter(
        filtered_df,
        x="math score",
        y="reading score",
        color="test preparation course",
        hover_data=["writing score", "parental level of education", "gender"],
        labels={"math score": "Math Score", "reading score": "Reading Score"},
        title="Math vs Reading",
        template="plotly_dark",
        color_discrete_sequence=cool_colors
    )
    fig_scatter.update_layout(legend=dict(orientation="h"))
    st.plotly_chart(fig_scatter, use_container_width=True)

# -------------------------
# Chart 4: Correlation Heatmap
# -------------------------
st.subheader("Correlation Heatmap (Scores)")
with st.spinner("Rendering heatmap..."):
    corr = filtered_df[["math score", "reading score", "writing score"]].corr()
    heatmap = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale="Bluered",
            zmin=-1, zmax=1,
            colorbar=dict(title="Correlation")
        )
    )
    heatmap.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(heatmap, use_container_width=True)

# -------------------------
# Table & Download
# -------------------------
st.subheader("Filtered Data (preview)")
st.dataframe(filtered_df.head(50), use_container_width=True)

# Download filtered data
def convert_df_to_csv(df_in: pd.DataFrame) -> bytes:
    return df_in.to_csv(index=False).encode('utf-8')

csv_bytes = convert_df_to_csv(filtered_df)
st.download_button(
    label="⬇️ Download filtered data as CSV",
    data=csv_bytes,
    file_name="filtered_students_performance.csv",
    mime="text/csv",
)

# -------------------------
# Additional Insights: Top performers & distribution by parental education
# -------------------------
st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 10 Students (by average score)")
    top10 = filtered_df.copy()
    top10["avg_score"] = top10[["math score", "reading score", "writing score"]].mean(axis=1)
    top10 = top10.sort_values("avg_score", ascending=False).head(10)
    st.table(top10[["gender", "parental level of education", "test preparation course", "math score", "reading score", "writing score", "avg_score"]].reset_index(drop=True))

with col_right:
    st.subheader("Average Scores by Parental Education")
    avg_by_edu = filtered_df.groupby("parental level of education")[["math score", "reading score", "writing score"]].mean().reset_index()
    fig_edu = go.Figure()
    fig_edu.add_trace(go.Bar(x=avg_by_edu["parental level of education"], y=avg_by_edu["math score"], name="Math", marker_color=cool_colors[0]))
    fig_edu.add_trace(go.Bar(x=avg_by_edu["parental level of education"], y=avg_by_edu["reading score"], name="Reading", marker_color=cool_colors[1]))
    fig_edu.add_trace(go.Bar(x=avg_by_edu["parental level of education"], y=avg_by_edu["writing score"], name="Writing", marker_color=cool_colors[2]))
    fig_edu.update_layout(barmode='group', template="plotly_dark", xaxis_tickangle=-45, height=420, legend=dict(orientation="h"))
    st.plotly_chart(fig_edu, use_container_width=True)

# -------------------------
# Footer & small tips
# -------------------------
st.markdown("---")
st.markdown(
    "Made with ❤️ by **Ahmed Sabur** • Interactive charts with Plotly • Dark cool theme • Use the sidebar to tweak filters."
)
st.caption("Tip: Hover on the charts to get more details. Use the Download button to export filtered rows.")

# End of app
