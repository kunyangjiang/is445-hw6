# put streamlit code here as needed
import altair as alt
import pandas as pd
import streamlit as st

DATA_URL = (
    "https://raw.githubusercontent.com/UIUC-iSchool-DataViz/"
    "is445_data/main/building_inventory.csv"
)

st.set_page_config(
    page_title="Illinois Building Inventory | IS 445",
    page_icon="🏢",
    layout="wide",
)


@st.cache_data(ttl=3600)
def load_data():
    data = pd.read_csv(DATA_URL)
    data["Year Constructed"] = pd.to_numeric(
        data["Year Constructed"], errors="coerce"
    )
    data["Square Footage"] = pd.to_numeric(
        data["Square Footage"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
    data["Usage Description"] = data["Usage Description"].fillna("Unknown")
    data["Agency Name"] = data["Agency Name"].fillna("Unknown")
    # Keep plausible construction years and positive building sizes.
    data = data.loc[
        data["Year Constructed"].between(1800, 2025)
        & (data["Square Footage"] > 0)
    ].copy()
    data["Decade"] = (data["Year Constructed"] // 10 * 10).astype(int)
    return data


st.title("Illinois Public Building Inventory")
st.write(
    "Two views of the same dataset: **when and why public buildings were built**, "
    "and **how their sizes compare across uses**."
)

try:
    data = load_data()
except Exception as exc:
    st.error(f"The public CSV could not be loaded: {exc}")
    st.stop()

if data.empty:
    st.error("No valid building records were found.")
    st.stop()

st.sidebar.header("Explore the data")
agencies = ["All agencies"] + sorted(data["Agency Name"].unique().tolist())
selected_agency = st.sidebar.selectbox("Agency", agencies)

min_year = int(data["Year Constructed"].min())
max_year = int(data["Year Constructed"].max())
year_range = st.sidebar.slider(
    "Construction year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered = data.loc[
    data["Year Constructed"].between(year_range[0], year_range[1])
].copy()
if selected_agency != "All agencies":
    filtered = filtered.loc[filtered["Agency Name"] == selected_agency].copy()

if filtered.empty:
    st.warning("No buildings match these filters. Try a wider year range.")
    st.stop()

# Use the same eight most common categories in both figures.
top_uses = filtered["Usage Description"].value_counts().head(8).index.tolist()
plot_data = filtered.loc[filtered["Usage Description"].isin(top_uses)].copy()

metric1, metric2 = st.columns(2)
metric1.metric("Buildings matching filters", f"{len(filtered):,}")
metric2.metric("Building-use categories displayed", len(top_uses))
st.caption(
    "Use the sidebar to filter both charts. The figures show the eight most "
    "common building uses within the current selection."
)

st.subheader("1. Building use by construction decade")
counts = (
    plot_data.groupby(["Decade", "Usage Description"], as_index=False)
    .size()
    .rename(columns={"size": "Buildings"})
)
click_use = alt.selection_point(
    fields=["Usage Description"], on="click", clear="dblclick", name="use_picker"
)
heatmap = (
    alt.Chart(counts)
    .mark_rect(stroke="white", strokeWidth=0.6)
    .encode(
        x=alt.X("Decade:O", title="Decade constructed", sort="ascending"),
        y=alt.Y("Usage Description:N", title="Building use", sort=top_uses),
        color=alt.Color(
            "Buildings:Q", title="Number of buildings", scale=alt.Scale(scheme="blues")
        ),
        opacity=alt.condition(click_use, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("Usage Description:N", title="Use"),
            alt.Tooltip("Decade:O", title="Decade"),
            alt.Tooltip("Buildings:Q", title="Buildings", format=","),
        ],
    )
    .add_params(click_use)
    .properties(height=340)
)
st.altair_chart(heatmap, use_container_width=True)
st.caption("Click a heatmap cell to highlight its building use; double-click to reset.")
st.write(
    "This heatmap highlights how the number of recorded public buildings varies "
    "by **construction decade** and **building use**. I used rectangular cells "
    "because they make comparisons across two discrete categories easy. A "
    "sequential blue color scale represents building counts without implying "
    "that categories have a numerical order. Clicking a cell highlights its "
    "use category, while the sidebar filters let readers focus on an agency or "
    "time period. With more time, I would add a normalized view showing the "
    "percentage of each decade made up by each use."
)

st.subheader("2. Building size distributions by use")
boxplot = (
    alt.Chart(plot_data)
    .mark_boxplot(extent=1.5, size=24)
    .encode(
        x=alt.X(
            "Square Footage:Q",
            title="Building size (square feet, log scale)",
            scale=alt.Scale(type="log"),
            axis=alt.Axis(format="~s"),
        ),
        y=alt.Y("Usage Description:N", title="Building use", sort=top_uses),
        color=alt.Color("Usage Description:N", legend=None),
    )
    .properties(height=340)
)
st.altair_chart(boxplot, use_container_width=True)
st.write(
    "This box plot compares **building size distributions** across the same "
    "eight use categories. Unlike a bar chart of averages, a box plot shows "
    "the median, middle 50% of values, and potential outliers. Square footage "
    "is shown on a logarithmic x-axis because building sizes can differ by "
    "orders of magnitude; a linear axis would compress smaller buildings. "
    "The consistent category order helps readers compare the two views. With "
    "more time, I would let users choose between a log and linear scale."
)

st.divider()
st.subheader("Source and relationship to Homework #5")
st.markdown(f"[Illinois Building Inventory dataset]({DATA_URL}) — UIUC IS 445 course data.")
st.write(
    "Homework #5 used the Illinois Professional Licenses dataset and included "
    "a horizontal bar chart and a yearly line chart. This assignment uses a "
    "different dataset and new heatmap and box-plot designs. No HW5 figures "
    "or written explanations were copied into this app."
)
st.caption(
    "Data note: records with unknown/implausible construction years or "
    "nonpositive/missing square footage are excluded from both plots. "
    "These plots describe inventory records, not annual construction totals."
)