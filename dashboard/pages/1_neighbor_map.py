"""
Neighbor Comparison Map - Interactive POI visualization.

Shows POIs colored by excess partisan lean (deviation from local neighbors).
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_poi_data,
    load_filter_options,
    filter_poi_by_category,
    filter_poi_by_naics,
)
from utils.map_utils import (
    create_scatter_layer,
    create_map_view,
    create_tooltip,
    create_deck,
)

st.set_page_config(
    page_title="Neighbor Map",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Partisan Lean Map")
st.markdown("""
POIs colored by **consumer partisan lean** - red indicates more Republican customers,
blue indicates more Democratic customers. Filter by category or NAICS to compare similar businesses.
""")


STATE_CENTERS = {
    "AL": (32.8, -86.8, 7), "AK": (64.0, -153.0, 4), "AZ": (34.3, -111.7, 6),
    "AR": (34.9, -92.4, 7), "CA": (37.2, -119.4, 6), "CO": (39.0, -105.5, 7),
    "CT": (41.6, -72.7, 8), "DE": (39.0, -75.5, 8), "FL": (28.6, -82.4, 6),
    "GA": (32.6, -83.4, 7), "HI": (20.8, -156.3, 7), "ID": (44.4, -114.6, 6),
    "IL": (40.0, -89.2, 7), "IN": (39.9, -86.3, 7), "IA": (42.0, -93.5, 7),
    "KS": (38.5, -98.4, 7), "KY": (37.8, -85.7, 7), "LA": (31.0, -91.9, 7),
    "ME": (45.3, -69.0, 7), "MD": (39.0, -76.8, 8), "MA": (42.2, -71.5, 8),
    "MI": (44.3, -85.4, 6), "MN": (46.3, -94.3, 6), "MS": (32.7, -89.7, 7),
    "MO": (38.4, -92.5, 7), "MT": (47.0, -109.6, 6), "NE": (41.5, -99.8, 7),
    "NV": (39.3, -116.6, 6), "NH": (43.6, -71.5, 8), "NJ": (40.2, -74.7, 8),
    "NM": (34.4, -106.1, 6), "NY": (42.9, -75.5, 7), "NC": (35.5, -79.8, 7),
    "ND": (47.4, -100.3, 7), "OH": (40.4, -82.8, 7), "OK": (35.6, -97.5, 7),
    "OR": (43.9, -120.6, 6), "PA": (40.9, -77.8, 7), "RI": (41.7, -71.5, 9),
    "SC": (33.9, -80.9, 7), "SD": (44.4, -100.2, 7), "TN": (35.8, -86.3, 7),
    "TX": (31.5, -99.4, 6), "UT": (39.3, -111.7, 6), "VT": (44.0, -72.7, 8),
    "VA": (37.5, -78.8, 7), "WA": (47.4, -120.5, 7), "WV": (38.9, -80.5, 7),
    "WI": (44.6, -89.7, 7), "WY": (43.0, -107.5, 6), "DC": (38.9, -77.0, 11)
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "Washington DC"
}


@st.cache_data(ttl=3600)
def get_sampled_data(state, category, naics_2, sample_size=50000):
    """Load and sample POI data for a specific state."""
    df = load_poi_data()
    if df is None:
        return None

    if state != "All States":
        df = df[df['region'] == state]

    df = filter_poi_by_category(df, category)
    df = filter_poi_by_naics(df, naics_2, level=2)

    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)

    return df


with st.sidebar:
    st.header("Location")

    state_options = ["All States"] + sorted(STATE_NAMES.keys())
    state_display = ["All States"] + [f"{k} - {v}" for k, v in sorted(STATE_NAMES.items())]
    selected_idx = st.selectbox("State", range(len(state_options)),
                                format_func=lambda i: state_display[i], index=0)
    selected_state = state_options[selected_idx]

    st.header("Filters")

    filter_opts = load_filter_options()

    if filter_opts:
        categories = ["All"] + [c['category'] for c in filter_opts.get('categories', [])]
        selected_category = st.selectbox("Category", categories, index=0)

        naics_codes = ["All"] + [n['naics_2'] for n in filter_opts.get('naics_codes', [])]
        selected_naics = st.selectbox("NAICS (2-digit)", naics_codes, index=0)
    else:
        selected_category = "All"
        selected_naics = "All"
        st.warning("Filter options not loaded")

    st.header("Map Settings")
    color_scale = st.slider("Color intensity", 0.05, 0.5, 0.15, 0.01,
                           help="Excess lean value for full color saturation")
    point_radius = st.slider("Point size", 50, 500, 150, 10)
    sample_size = st.slider("Max points", 10000, 100000, 50000, 5000,
                           help="Sample size for performance")


df = get_sampled_data(selected_state, selected_category, selected_naics, sample_size)

if df is None:
    st.error("Data not available. Please wait for data preparation to complete.")
    st.stop()

if len(df) == 0:
    st.warning("No POIs match the current filters.")
    st.stop()

if selected_state == "All States":
    st.info(f"Showing {len(df):,} POIs (sampled from national dataset)")
else:
    st.info(f"Showing {len(df):,} POIs in {STATE_NAMES.get(selected_state, selected_state)}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("POIs Displayed", f"{len(df):,}")
with col2:
    st.metric("Unique Brands", f"{df['brand'].nunique():,}")
with col3:
    mean_lean = df['mean_rep_lean_2020'].mean()
    st.metric("Mean Rep Lean", f"{mean_lean:.3f}" if pd.notna(mean_lean) else "N/A")
with col4:
    std_lean = df['mean_rep_lean_2020'].std()
    st.metric("Std Dev", f"{std_lean:.3f}" if pd.notna(std_lean) else "N/A")

if selected_state != "All States" and selected_state in STATE_CENTERS:
    center_lat, center_lon, zoom = STATE_CENTERS[selected_state]
else:
    center_lat, center_lon, zoom = 39.8, -98.5, 4
view_state = create_map_view(center_lat, center_lon, zoom)

try:
    map_df = df.copy()

    if 'location_name' in map_df.columns:
        map_df['display_name'] = map_df['location_name'].fillna('Unknown')
    else:
        map_df['display_name'] = map_df['brand'].fillna(map_df['top_category'].fillna('Unknown'))

    def format_brand(brand):
        if pd.isna(brand) or brand == 'Unbranded' or brand == '':
            return ''
        return f'<b>Brand:</b> {brand}<br/>'
    map_df['brand_display'] = map_df['brand'].apply(format_brand)

    map_df['lean_display'] = map_df['mean_rep_lean_2020'].apply(
        lambda x: f'{x:.3f}' if pd.notna(x) else 'N/A'
    )
    map_df['visitors_display'] = map_df['total_visitors'].apply(
        lambda x: f'{int(x):,}' if pd.notna(x) else 'N/A'
    )

    layer = create_scatter_layer(map_df, color_column='mean_rep_lean_2020', scale=color_scale,
                                radius=point_radius, size_by_visitors=True)
    tooltip = create_tooltip()
    deck = create_deck([layer], view_state, tooltip)
    st.pydeck_chart(deck, use_container_width=True)
except Exception as e:
    st.error(f"Error rendering map: {e}")
    st.write("Falling back to simple map...")
    st.map(df[['latitude', 'longitude']].dropna().head(10000))

st.markdown("---")

st.subheader("Legend")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("🔴 **Red**: Republican-leaning customers (>0.5)")
with col2:
    st.markdown("⚪ **Gray/White**: Neutral (~0.5)")
with col3:
    st.markdown("🔵 **Blue**: Democratic-leaning customers (<0.5)")

st.markdown("---")

st.subheader("Sample Data")
with st.expander("Show data table"):
    display_cols = ['brand', 'city', 'region', 'mean_rep_lean_2020',
                   'total_visitors', 'top_category', 'naics_code']
    display_df = df[display_cols].sort_values('mean_rep_lean_2020', ascending=False).head(100)
    st.dataframe(display_df.round(3), width="stretch")
