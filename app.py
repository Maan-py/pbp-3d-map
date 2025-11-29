import streamlit as st
import pandas as pd
import modules.config as config
import modules.ui as ui
import modules.calculations as calc

# --- KONFIGURASI HALAMAN ---
config.setup_page_config()
config.apply_custom_css()

# --- JUDUL UTAMA ---
st.title("🌍 3D Reservoir Visualization")
st.markdown("*Interactive Structural Map, Fluid Contact & Reserves Calculator*")

# --- 1. INISIALISASI SESSION STATE ---
if 'data_points' not in st.session_state:
    st.session_state['data_points'] = []

# --- 2. SIDEBAR & DATA ---
df = pd.DataFrame(st.session_state['data_points'])
params = ui.render_sidebar(df)

# --- 3. LOGIC VISUALISASI UTAMA ---
if df.empty:
    ui.render_empty_state()
else:
    # Minimal 4 titik untuk kontur yang baik
    if len(df) >= 4:
        # Hitung Grid
        grid_x, grid_y, grid_z = calc.calculate_grid(df)

        # Hitung Volume
        # Ambil parameter dari sidebar
        goc = params.get('goc', 0)
        woc = params.get('woc', 0)
        
        # Hitung range untuk volume calculation
        x_range = (df['X'].min(), df['X'].max())
        y_range = (df['Y'].min(), df['Y'].max())
        z_range = (df['Z'].min(), df['Z'].max()) # Untuk report nanti

        vol_total_res, vol_gas_cap, vol_oil_zone = calc.calculate_volumes(
            grid_z, x_range, y_range, goc, woc
        )

        # Hitung Reserves (STOIIP & GIIP)
        stoiip, giip = calc.calculate_reserves(
            vol_oil_zone, vol_gas_cap,
            params.get('ntg', 0.8),
            params.get('porosity', 0.2),
            params.get('sw', 0.3),
            params.get('bo', 1.2),
            params.get('bg', 0.005)
        )

        # Render Metrics
        ui.render_metrics(vol_gas_cap, vol_oil_zone, vol_total_res, stoiip, giip)

        # Render Export Section
        ui.render_export_section(
            vol_gas_cap, vol_oil_zone, vol_total_res,
            goc, woc,
            df, grid_x, grid_y, grid_z
        )

        # Render Tabs (Visualizations)
        ui.render_tabs(df, grid_x, grid_y, grid_z, goc, woc)

    else:
        st.warning("⚠ Data belum cukup untuk membuat kontur. Masukkan minimal 4 titik yang menyebar.")
        st.dataframe(df, use_container_width=True)
