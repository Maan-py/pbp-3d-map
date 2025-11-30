import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objects as go

def generate_property_heatmap(x, y, prop, prop_label="Property"):
    # Grid
    grid_x = np.linspace(min(x), max(x), 150)
    grid_y = np.linspace(min(y), max(y), 150)
    gx, gy = np.meshgrid(grid_x, grid_y)

    # Interpolasi
    grid_prop = griddata((x, y), prop, (gx, gy), method='cubic')

    # Plot Heatmap
    fig = go.Figure(data=go.Heatmap(
        x=grid_x,
        y=grid_y,
        z=grid_prop,
        colorscale='Turbo',
        colorbar=dict(title=prop_label)
    ))

    fig.update_layout(
        title=f"Heatmap Interpolasi {prop_label}",
        xaxis_title="X",
        yaxis_title="Y",
        height=700
    )

    return fig