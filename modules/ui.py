import streamlit as st
import pandas as pd
import json
import io
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from .utils import create_volumetric_report_pdf, create_volumetric_report_excel

def render_sidebar(df):
    """
    Merender sidebar dan mengembalikan parameter input.
    
    Args:
        df: DataFrame data points saat ini
        
    Returns:
        dict: Dictionary berisi parameter (goc, woc, porosity, sw, ntg, bo, bg)
    """
    params = {}
    
    with st.sidebar:
        st.header("🛠 Panel Input")
        # --- BAGIAN A: INPUT DATA ---
        st.markdown("### 📍 Input Koordinat")
        
        with st.form(key='input_form', clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                x_val = st.number_input("X (Timur-Barat)", value=0.0, step=10.0)
            with c2:
                y_val = st.number_input("Y (Utara-Selatan)", value=0.0, step=10.0)
            
            z_val = st.number_input("Z (Kedalaman/Depth)", value=1000.0, step=10.0,
                                    help="Makin besar angka, makin dalam")
            
            submit_button = st.form_submit_button(label='➕ Tambah Titik', type="primary")

        if submit_button:
            st.session_state['data_points'].append({'X': x_val, 'Y': y_val, 'Z': z_val})
            st.toast(f"Titik ({x_val}, {y_val}, {z_val}) berhasil disimpan!", icon='✅')
            st.rerun()

        # --- BAGIAN B: STATUS DATA ---
        if not df.empty:
            st.divider()
            st.markdown("### 📊 Status Data")
            
            m1, m2 = st.columns(2)
            m1.metric("Total Titik", len(df))
            m2.metric("Kedalaman Max", f"{df['Z'].max()} m")
            
            # --- BAGIAN C: KONTAK FLUIDA ---
            st.divider()
            st.markdown("### 💧 Kontak Fluida")
            
            min_z, max_z = df['Z'].min(), df['Z'].max()
            
            st.markdown(":red[Gas-Oil Contact (GOC)]")
            params['goc'] = st.number_input(
                "",
                value=float(min_z + (max_z - min_z) * 0.3),
                key="goc",
                label_visibility="collapsed"
            )
            
            st.markdown(":blue[Water-Oil Contact (WOC)]")
            params['woc'] = st.number_input(
                "",
                value=float(min_z + (max_z - min_z) * 0.7),
                key="woc",
                label_visibility="collapsed"
            )
            
            if params['goc'] > params['woc']:
                st.warning("⚠ Awas: GOC > WOC!")

            # --- PARAMETER PETROFISIKA ---
            st.divider()
            with st.expander("🧮 Parameter Petrofisika (Baru)", expanded=True):
                st.caption("Digunakan untuk menghitung STOIIP/GIIP")
                params['porosity'] = st.slider("Porositas (ϕ)", 0.05, 0.40, 0.20, 0.01)
                params['sw'] = st.slider("Water Saturation (Sw)", 0.1, 1.0, 0.3, 0.05)
                params['ntg'] = st.slider("Net-to-Gross (NTG)", 0.1, 1.0, 0.8, 0.05)
                params['bo'] = st.number_input("Faktor Vol. Formasi Minyak (Bo)", 1.0, 2.0, 1.2)
                params['bg'] = st.number_input("Faktor Ekspansi Gas (Bg)", 0.001, 0.1, 0.005, format="%.4f")
        
        st.markdown("---")
        
        # --- UPLOAD FILE DATA ---
        with st.expander("📂 Upload File", expanded=True):
            uploaded_file = st.file_uploader("Upload CSV/Excel (Wajib: X, Y, Z)", type=["csv", "xlsx"])
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                        
                    st.caption("🔎 Preview data yang kamu upload:")
                    st.dataframe(df_upload.head(), use_container_width=True)
                    
                    df_upload.columns = [c.upper() for c in df_upload.columns]
                    required_cols = {'X', 'Y', 'Z'}
                    
                    if required_cols.issubset(df_upload.columns):
                        st.success(f"File valid! {len(df_upload)} baris data.")
                        if st.button("📥 Muat Data ke Aplikasi", type="primary"):
                            new_data = df_upload[['X', 'Y', 'Z']].to_dict('records')
                            st.session_state['data_points'].extend(new_data)
                            st.toast(f"Berhasil menambahkan {len(new_data)} titik!", icon='✅')
                            st.rerun()
                    else:
                        st.error(f"Format salah! File harus punya kolom: {required_cols}")
                except Exception as e:
                    st.error(f"Error membaca file: {e}")

        # --- PENGATURAN DATA ---
        with st.expander("⚙ Pengaturan Data", expanded=False):
            if st.button("🔄 Reset Semua Data"):
                st.session_state['data_points'] = []
                st.rerun()
            
            if st.button("📂 Load Data Demo"):
                st.session_state['data_points'] = [
                    {'X': 100, 'Y': 100, 'Z': 1300}, {'X': 300, 'Y': 100, 'Z': 1300},
                    {'X': 100, 'Y': 300, 'Z': 1300}, {'X': 300, 'Y': 300, 'Z': 1300},
                    {'X': 200, 'Y': 200, 'Z': 1000},  # Puncak
                    {'X': 200, 'Y': 100, 'Z': 1150}, {'X': 200, 'Y': 300, 'Z': 1150},
                    {'X': 100, 'Y': 200, 'Z': 1150}, {'X': 300, 'Y': 200, 'Z': 1150},
                    {'X': 150, 'Y': 150, 'Z': 1100}, {'X': 250, 'Y': 250, 'Z': 1100},
                    {'X': 150, 'Y': 250, 'Z': 1100}, {'X': 250, 'Y': 150, 'Z': 1100}
                ]
                st.rerun()
        
        # --- EXPORT & SESSION MANAGEMENT ---
        with st.expander("💾 Export & Session", expanded=False):
            st.markdown("### 📤 Session Management")
            col_save1, col_save2 = st.columns(2)
            
            with col_save1:
                session_json = json.dumps(st.session_state['data_points'], indent=2)
                st.download_button(
                    label="💾 Save Session",
                    data=session_json,
                    file_name=f"reservoir_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Simpan data session untuk digunakan kembali"
                )
            
            with col_save2:
                uploaded_session = st.file_uploader("📂 Load Session (JSON)", type=["json"], key="session_upload")
                if uploaded_session is not None:
                    try:
                        session_data = json.load(uploaded_session)
                        if isinstance(session_data, list) and all(
                            ('X' in item and 'Y' in item and 'Z' in item) for item in session_data
                        ):
                            if st.button("📥 Muat Session", key="load_session"):
                                st.session_state['data_points'] = session_data
                                st.toast("Session berhasil dimuat!", icon='✅')
                                st.rerun()
                        else:
                            st.error("Format session tidak valid!")
                    except Exception as e:
                        st.error(f"Error membaca session: {e}")
    
    return params

def render_empty_state():
    st.info("👈 Silakan masukkan data koordinat melalui panel di sebelah kiri.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)

def render_metrics(vol_gas_cap, vol_oil_zone, vol_total_res, stoiip, giip):
    st.markdown("### 📊 Estimasi Volume & Cadangan")
    
    col_vol1, col_vol2, col_vol3 = st.columns(3)
    def fmt_vol(v): return f"{v/1e6:.2f} Juta m³"

    col_vol1.metric("🔴 Gross Gas Volume", fmt_vol(vol_gas_cap), help="Volume batuan gas cap")
    col_vol2.metric("🟢 Gross Oil Volume", fmt_vol(vol_oil_zone), help="Volume batuan oil zone")
    col_vol3.metric("🔵 Total Reservoir", fmt_vol(vol_total_res), help="Total volume batuan reservoir")

    st.caption("Ekspektasi Cadangan Minyak & Gas (In-Place):")
    c_res1, c_res2 = st.columns(2)
    c_res1.metric("🔥 GIIP (Gas In Place)", f"{giip/1e9:.2f} BCF", help="Miliar Kaki Kubik")
    c_res2.metric("🛢 STOIIP (Oil In Place)", f"{stoiip/1e6:.2f} MMbbls", help="Juta Barel Minyak")

def render_export_section(vol_gas_cap, vol_oil_zone, vol_total_res, goc, woc, df, grid_x, grid_y, grid_z):
    st.markdown("### 📄 Export Laporan Volumetrik")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        try:
            pdf_buffer = create_volumetric_report_pdf(
                vol_gas_cap, vol_oil_zone, vol_total_res,
                goc, woc,
                len(df),
                (df['X'].min(), df['X'].max()),
                (df['Y'].min(), df['Y'].max()),
                (df['Z'].min(), df['Z'].max())
            )
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name=f"volumetric_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error membuat PDF: {e}")
    
    with col_exp2:
        try:
            excel_buffer = create_volumetric_report_excel(
                vol_gas_cap, vol_oil_zone, vol_total_res,
                goc, woc,
                len(df),
                (df['X'].min(), df['X'].max()),
                (df['Y'].min(), df['Y'].max()),
                (df['Z'].min(), df['Z'].max()),
                df
            )
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_buffer,
                file_name=f"volumetric_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error membuat Excel: {e}")
    
    with col_exp3:
        try:
            grid_df = pd.DataFrame({
                'X': grid_x.flatten(),
                'Y': grid_y.flatten(),
                'Z': grid_z.flatten()
            })
            grid_csv = grid_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Grid Data (CSV)",
                data=grid_csv,
                file_name=f"grid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error membuat CSV: {e}")

def render_tabs(df, grid_x, grid_y, grid_z, goc, woc):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺 Peta Kontur 2D",
        "🧊 Model 3D",
        "📋 Data Mentah",
        "✂ Penampang (Baru)"
    ])

    min_z, max_z = df['Z'].min(), df['Z'].max()

    # === TAB 1: 2D ===
    with tab1:
        fig_2d = go.Figure()

        fig_2d.add_trace(go.Contour(
            z=grid_z,
            x=grid_x[0, :], # grid_x is meshgrid, so take first row
            y=grid_y[:, 0], # grid_y is meshgrid, so take first col
            colorscale='Greys',
            opacity=0.4,
            contours=dict(
                start=min_z,
                end=max_z,
                size=(max_z - min_z) / 10,
                showlabels=True
            ),
            name='Structure'
        ))

        conditions = [
            (df['Z'] < goc),
            (df['Z'] >= goc) & (df['Z'] <= woc),
            (df['Z'] > woc)
        ]
        choices = ['Gas Cap', 'Oil Zone', 'Aquifer']
        colors_map = {'Gas Cap': 'red', 'Oil Zone': 'green', 'Aquifer': 'blue'}
        df['Fluid'] = np.select(conditions, choices, default='Unknown')

        for fluid in choices:
            subset = df[df['Fluid'] == fluid]
            if not subset.empty:
                fig_2d.add_trace(go.Scatter(
                    x=subset['X'],
                    y=subset['Y'],
                    mode='markers+text',
                    text=subset['Z'].astype(int),
                    textposition="top center",
                    marker=dict(
                        size=12,
                        color=colors_map[fluid],
                        line=dict(width=1, color='black')
                    ),
                    name=fluid
                ))

        fig_2d.update_layout(
            height=650,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate"
        )
        st.plotly_chart(fig_2d, use_container_width=True)

        # Export 2D
        st.markdown("#### 📤 Export Visualisasi 2D")
        col_2d1, col_2d2 = st.columns(2)
        with col_2d1:
            try:
                img_2d_png = fig_2d.to_image(format="png", width=1200, height=800)
                st.download_button(
                    label="🖼️ Download PNG",
                    data=img_2d_png,
                    file_name=f"contour_2d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"Error export PNG: {e}")
        with col_2d2:
            try:
                img_2d_pdf = fig_2d.to_image(format="pdf", width=1200, height=800)
                st.download_button(
                    label="📄 Download PDF",
                    data=img_2d_pdf,
                    file_name=f"contour_2d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error export PDF: {e}")

    # === TAB 2: 3D ===
    with tab2:
        fig_3d = go.Figure()
        
        fig_3d.add_trace(go.Surface(
            z=grid_z,
            x=grid_x,
            y=grid_y,
            colorscale='Earth_r',
            opacity=0.9,
            name='Structure'
        ))
        
        def create_plane(z_lvl, color, name):
            return go.Surface(
                z=z_lvl * np.ones_like(grid_z),
                x=grid_x,
                y=grid_y,
                colorscale=[[0, color], [1, color]],
                opacity=0.4,
                showscale=False,
                name=name
            )

        fig_3d.add_trace(create_plane(goc, 'red', 'GOC'))
        fig_3d.add_trace(create_plane(woc, 'blue', 'WOC'))

        for _, row in df.iterrows():
            fig_3d.add_trace(go.Scatter3d(
                x=[row['X'], row['X']],
                y=[row['Y'], row['Y']],
                z=[min_z, row['Z']],
                mode='lines+markers',
                marker=dict(size=3, color='black'),
                line=dict(color='black', width=4),
                showlegend=False
            ))

        fig_3d.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Depth',
                zaxis=dict(autorange="reversed")
            ),
            height=650,
            margin=dict(l=0, r=0, b=0, t=0)
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        # Export 3D
        st.markdown("#### 📤 Export Visualisasi 3D")
        col_3d1, col_3d2 = st.columns(2)
        with col_3d1:
            try:
                img_3d_png = fig_3d.to_image(format="png", width=1200, height=800)
                st.download_button(
                    label="🖼️ Download PNG",
                    data=img_3d_png,
                    file_name=f"model_3d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"Error export PNG: {e}")
        with col_3d2:
            try:
                img_3d_pdf = fig_3d.to_image(format="pdf", width=1200, height=800)
                st.download_button(
                    label="📄 Download PDF",
                    data=img_3d_pdf,
                    file_name=f"model_3d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error export PDF: {e}")

    # === TAB 3: DATA MENTAH ===
    with tab3:
        st.dataframe(df, use_container_width=True)

        st.markdown("#### 📤 Export Data Mentah")
        col_raw1, col_raw2 = st.columns(2)
        with col_raw1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        with col_raw2:
            try:
                excel_buffer_raw = io.BytesIO()
                with pd.ExcelWriter(excel_buffer_raw, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Raw Data', index=False)
                excel_buffer_raw.seek(0)
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_buffer_raw,
                    file_name=f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error export Excel: {e}")

    # === TAB 4: CROSS SECTION ===
    with tab4:
        st.markdown("##### ✂ Penampang Melintang (Cross-Section)")
        st.caption("Geser slider untuk memotong peta dari Barat ke Timur pada posisi Y tertentu.")
        
        y_min, y_max = df['Y'].min(), df['Y'].max()
        slice_y = st.slider(
            "Pilih Posisi Irisan Y",
            float(y_min),
            float(y_max),
            float((y_min + y_max) / 2)
        )
        
        # grid_y is meshgrid, so grid_y[:, 0] is the y-axis vector
        idx_y = (np.abs(grid_y[:, 0] - slice_y)).argmin()
        z_profile = grid_z[idx_y, :]
        
        fig_xs = go.Figure()
        fig_xs.add_trace(go.Scatter(
            x=grid_x[0, :],
            y=z_profile,
            mode='lines',
            fill='tozeroy',
            line=dict(color='brown'),
            name='Top Structure'
        ))
        
        fig_xs.add_hline(y=goc, line_dash="dash", line_color="red", annotation_text="GOC")
        fig_xs.add_hline(y=woc, line_dash="dash", line_color="blue", annotation_text="WOC")
        
        fig_xs.update_yaxes(autorange="reversed", title="Depth (m)")
        fig_xs.update_layout(
            title=f"Irisan pada Y = {slice_y:.1f}",
            xaxis_title="X Coordinate",
            height=500
        )
        st.plotly_chart(fig_xs, use_container_width=True)
