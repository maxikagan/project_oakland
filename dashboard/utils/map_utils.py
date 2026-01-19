"""
Map visualization utilities for the Stakeholder Ideology Dashboard.
"""

import pydeck as pdk
import numpy as np


def get_color_for_lean(lean_value, scale=0.5, neutral_zone=0.03):
    """
    Convert partisan lean to RGB color.

    Values > 0.5 (Republican) = Red
    Values < 0.5 (Democratic) = Blue
    Values near 0.5 (neutral) = Gray

    Args:
        lean_value: Partisan lean (0 = full Dem, 1 = full Rep, 0.5 = neutral)
        scale: How much deviation from 0.5 gives full color saturation
        neutral_zone: Deviation from 0.5 that still counts as neutral (grey)

    Returns:
        [R, G, B, A] color array
    """
    if np.isnan(lean_value):
        return [160, 160, 160, 150]

    deviation = lean_value - 0.5

    if abs(deviation) <= neutral_zone:
        return [160, 160, 160, 180]

    if deviation > 0:
        effective_dev = deviation - neutral_zone
    else:
        effective_dev = deviation + neutral_zone

    normalized = np.clip(effective_dev / scale, -1, 1)

    if normalized > 0:
        r = 255
        g = int(255 * (1 - normalized))
        b = int(255 * (1 - normalized))
    else:
        r = int(255 * (1 + normalized))
        g = int(255 * (1 + normalized))
        b = 255

    return [r, g, b, 180]


def create_scatter_layer(df, color_column='mean_rep_lean_2020', scale=0.2,
                         radius=100, size_by_visitors=False, min_radius=50, max_radius=500):
    """
    Create a pydeck ScatterplotLayer for POI visualization.

    Args:
        df: DataFrame with latitude, longitude, and color_column
        color_column: Column to use for coloring points
        scale: Color intensity scale (0.5 = full red/blue at 0.5 deviation from 0.5)
        radius: Base point radius in meters (used if size_by_visitors=False)
        size_by_visitors: If True, scale radius by total_visitors
        min_radius: Minimum radius when scaling by visitors
        max_radius: Maximum radius when scaling by visitors

    Returns:
        pydeck Layer
    """
    df = df.copy()
    df['color'] = df[color_column].apply(lambda x: get_color_for_lean(x, scale))

    if size_by_visitors and 'total_visitors' in df.columns:
        visitors = df['total_visitors'].fillna(0)
        log_visitors = np.log1p(visitors)
        if log_visitors.max() > log_visitors.min():
            normalized = (log_visitors - log_visitors.min()) / (log_visitors.max() - log_visitors.min())
        else:
            normalized = 0.5
        df['radius'] = min_radius + normalized * (max_radius - min_radius)
        get_radius = 'radius'
    else:
        get_radius = radius

    return pdk.Layer(
        'ScatterplotLayer',
        data=df,
        get_position=['longitude', 'latitude'],
        get_color='color',
        get_radius=get_radius,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        line_width_min_pixels=1,
    )


def create_map_view(center_lat=39.8283, center_lon=-98.5795, zoom=4, pitch=0):
    """
    Create a pydeck ViewState for the map.

    Args:
        center_lat: Center latitude (default: US center)
        center_lon: Center longitude (default: US center)
        zoom: Zoom level (default: 4 for continental US)
        pitch: Map tilt angle

    Returns:
        pydeck ViewState
    """
    return pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=pitch,
        bearing=0
    )


def create_tooltip():
    """Create tooltip configuration for POI hover.

    Note: Pydeck doesn't support Python format specifiers in tooltips.
    Data must be pre-formatted as strings before passing to the layer.
    Expected pre-formatted columns: display_name, brand_display, lean_display, visitors_display
    """
    return {
        "html": """
        <b>{display_name}</b><br/>
        {city}, {region}<br/>
        <hr style="margin: 4px 0"/>
        {brand_display}
        <b>Partisan Lean (2020):</b> {lean_display}<br/>
        <b>Total Visitors:</b> {visitors_display}<br/>
        <b>Category:</b> {top_category}
        """,
        "style": {
            "backgroundColor": "white",
            "color": "black",
            "padding": "10px",
            "borderRadius": "5px",
            "fontSize": "12px"
        }
    }


def create_deck(layers, view_state, tooltip=None):
    """
    Create a complete pydeck Deck object.

    Args:
        layers: List of pydeck layers
        view_state: pydeck ViewState
        tooltip: Tooltip configuration (optional)

    Returns:
        pydeck Deck
    """
    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style='light'
    )


def get_viewport_bounds(view_state, zoom_to_bounds_ratio=2.0):
    """
    Estimate viewport bounds from a ViewState.

    This is approximate - pydeck doesn't expose actual viewport bounds.

    Args:
        view_state: pydeck ViewState
        zoom_to_bounds_ratio: Adjustment factor

    Returns:
        (lat_min, lat_max, lon_min, lon_max)
    """
    lat_span = 180 / (2 ** view_state.zoom) * zoom_to_bounds_ratio
    lon_span = 360 / (2 ** view_state.zoom) * zoom_to_bounds_ratio

    lat_min = view_state.latitude - lat_span / 2
    lat_max = view_state.latitude + lat_span / 2
    lon_min = view_state.longitude - lon_span / 2
    lon_max = view_state.longitude + lon_span / 2

    return lat_min, lat_max, lon_min, lon_max
