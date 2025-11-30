import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
import io
import json
import tempfile

# ReportLab untuk PDF ringkasan volumetrik
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GeoViz Pro", layout="wide", page_icon="🌍")

# CSS Custom untuk sedikit mempercantik tampilan
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# FUNGSI HELPER UNTUK EXPORT LAPORAN VOLUMETRIK
# -------------------------------------------------------------------
def create_volumetric_report_pdf(vol_gas_cap, vol_oil_zone, vol_total_res,
                                 goc_input, woc_input,
                                 num_points, x_range, y_range, z_range):
    """Membuat laporan volumetrik dalam format PDF (ringkasan)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    story.append(Paragraph("Laporan Volumetrik Reservoir", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    date_str = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    story.append(Paragraph(f"<i>Dibuat pada: {date_str}</i>", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    story.append(Paragraph("Ringkasan Perhitungan", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    summary_data = [
        ['Parameter', 'Nilai'],
        ['Total Data Points', f"{num_points} titik"],
        ['Gas-Oil Contact (GOC)', f"{goc_input:.2f} m"],
        ['Water-Oil Contact (WOC)', f"{woc_input:.2f} m"],
        ['Rentang X', f"{x_range[0]:.2f} - {x_range[1]:.2f}"],
        ['Rentang Y', f"{y_range[0]:.2f} - {y_range[1]:.2f}"],
        ['Rentang Z (Kedalaman)', f"{z_range[0]:.2f} - {z_range[1]:.2f} m"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Volume Results
    story.append(Paragraph("Hasil Perhitungan Volume", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    volume_data = [
        ['Zona', 'Volume (m³)', 'Volume (Juta m³)'],
        ['Gas Cap', f"{vol_gas_cap:,.2f}", f"{vol_gas_cap/1e6:.2f}"],
        ['Oil Zone', f"{vol_oil_zone:,.2f}", f"{vol_oil_zone/1e6:.2f}"],
        ['Total Reservoir', f"{vol_total_res:,.2f}", f"{vol_total_res/1e6:.2f}"],
    ]
    
    volume_table = Table(volume_data, colWidths=[2*inch, 2*inch, 2*inch])
    volume_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(volume_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Notes
    story.append(Paragraph("Catatan:", styles['Heading3']))
    story.append(Paragraph(
        "• Volume dihitung berdasarkan Gross Rock Volume (GRV) menggunakan metode grid interpolation.<br/>"
        "• Gas Cap: Volume batuan di atas GOC<br/>"
        "• Oil Zone: Volume batuan antara GOC dan WOC<br/>"
        "• Total Reservoir: Volume batuan di atas WOC",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_volumetric_report_excel(vol_gas_cap, vol_oil_zone, vol_total_res,
                                   goc_input, woc_input,
                                   num_points, x_range, y_range, z_range, df):
    """Membuat laporan volumetrik dalam format Excel"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_df = pd.DataFrame({
            'Parameter': ['Total Data Points', 'GOC (m)', 'WOC (m)',
                          'X Min', 'X Max', 'Y Min', 'Y Max', 'Z Min (m)', 'Z Max (m)'],
            'Nilai': [num_points, goc_input, woc_input,
                      x_range[0], x_range[1], y_range[0], y_range[1], z_range[0], z_range[1]]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Volume Results
        volume_df = pd.DataFrame({
            'Zona': ['Gas Cap', 'Oil Zone', 'Total Reservoir'],
            'Volume (m³)': [vol_gas_cap, vol_oil_zone, vol_total_res],
            'Volume (Juta m³)': [vol_gas_cap/1e6, vol_oil_zone/1e6, vol_total_res/1e6]
        })
        volume_df.to_excel(writer, sheet_name='Volume Results', index=False)
        
        # Sheet 3: Raw Data
        df.to_excel(writer, sheet_name='Raw Data', index=False)
    
    buffer.seek(0)
    return buffer

# --- JUDUL UTAMA ---
st.title("🌍 3D Reservoir Visualization")
st.markdown("*Interactive Structural Map, Fluid Contact & Reserves Calculator*")

# --- 1. INISIALISASI SESSION STATE ---
if 'data_points' not in st.session_state:
    st.session_state['data_points'] = []

# --- 2. SIDEBAR ---
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

    # --- BAGIAN B: STATUS DATA ---
    df = pd.DataFrame(st.session_state['data_points'])
    
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
        goc_input = st.number_input(
            "",
            value=float(min_z + (max_z - min_z) * 0.3),
            key="goc",
            label_visibility="collapsed"
        )
        
        st.markdown(":blue[Water-Oil Contact (WOC)]")
        woc_input = st.number_input(
            "",
            value=float(min_z + (max_z - min_z) * 0.7),
            key="woc",
            label_visibility="collapsed"
        )
        
        if goc_input > woc_input:
            st.warning("⚠ Awas: GOC > WOC!")

        # --- PARAMETER PETROFISIKA ---
        st.divider()
        with st.expander("🧮 Parameter Petrofisika (Baru)", expanded=True):
            st.caption("Digunakan untuk menghitung STOIIP/GIIP")
            porosity = st.slider("Porositas (ϕ)", 0.05, 0.40, 0.20, 0.01)
            sw = st.slider("Water Saturation (Sw)", 0.1, 1.0, 0.3, 0.05)
            ntg = st.slider("Net-to-Gross (NTG)", 0.1, 1.0, 0.8, 0.05)
            bo = st.number_input("Faktor Vol. Formasi Minyak (Bo)", 1.0, 2.0, 1.2)
            bg = st.number_input("Faktor Ekspansi Gas (Bg)", 0.001, 0.1, 0.005, format="%.4f")
    
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
            
        # --- Hapus titik terakhir ---
        if st.button("➖ Hapus Titik Terakhir"):
            if len(st.session_state['data_points']) > 0:
                removed = st.session_state['data_points'].pop()
                st.toast(f"Titik terakhir {removed} dihapus.", icon="🗑️")
                st.rerun()
            else:
                st.warning("Tidak ada titik untuk dihapus.")
    
    # --- EXPORT & SESSION MANAGEMENT ---
    with st.expander("💾 Export & Session", expanded=False):
        st.markdown("### 📤 Export CSV")

        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇️ Download CSV Data",
                data=csv_data,
                file_name=f"reservoir_points_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Belum ada data untuk diexport.")

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

# --- 3. LOGIC VISUALISASI UTAMA ---
if df.empty:
    st.info("👈 Silakan masukkan data koordinat melalui panel di sebelah kiri.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
else:
    # Minimal 4 titik untuk kontur yang baik
    if len(df) >= 4:
        df_unique = df.groupby(['X', 'Y'], as_index=False)['Z'].mean()
        grid_x = np.linspace(df['X'].min(), df['X'].max(), 100)
        grid_y = np.linspace(df['Y'].min(), df['Y'].max(), 100)
        grid_x, grid_y = np.meshgrid(grid_x, grid_y)

        try:
            grid_z = griddata(
                (df_unique['X'], df_unique['Y']),
                df_unique['Z'],
                (grid_x, grid_y),
                method='cubic'
            )
        except Exception:
            grid_z = griddata(
                (df_unique['X'], df_unique['Y']),
                df_unique['Z'],
                (grid_x, grid_y),
                method='linear'
            )

        # --- PERHITUNGAN VOLUME ---
        st.markdown("### 📊 Estimasi Volume & Cadangan")
        
        x_min, x_max = df['X'].min(), df['X'].max()
        y_min, y_max = df['Y'].min(), df['Y'].max()
        nx, ny = 100, 100
        
        dx = (x_max - x_min) / (nx - 1)
        dy = (y_max - y_min) / (ny - 1)
        cell_area = dx * dy
        
        # Volume di atas WOC (Total Reservoir)
        thick_above_woc = woc_input - grid_z
        thick_above_woc[thick_above_woc < 0] = 0
        vol_total_res = np.nansum(thick_above_woc) * cell_area
        
        # Volume di atas GOC (Gas Cap)
        thick_above_goc = goc_input - grid_z
        thick_above_goc[thick_above_goc < 0] = 0
        vol_gas_cap = np.nansum(thick_above_goc) * cell_area
        
        # Volume Oil = selisih
        vol_oil_zone = max(0, vol_total_res - vol_gas_cap)

        # STOIIP & GIIP
        stoiip = (vol_oil_zone * ntg * porosity * (1 - sw)) / bo
        giip = (vol_gas_cap * ntg * porosity * (1 - sw)) / bg

        col_vol1, col_vol2, col_vol3 = st.columns(3)
        def fmt_vol(v): return f"{v/1e6:.2f} Juta m³"

        col_vol1.metric("🔴 Gross Gas Volume", fmt_vol(vol_gas_cap), help="Volume batuan gas cap")
        col_vol2.metric("🟢 Gross Oil Volume", fmt_vol(vol_oil_zone), help="Volume batuan oil zone")
        col_vol3.metric("🔵 Total Reservoir", fmt_vol(vol_total_res), help="Total volume batuan reservoir")

        st.caption("Ekspektasi Cadangan Minyak & Gas (In-Place):")
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("🔥 GIIP (Gas In Place)", f"{giip/1e9:.2f} BCF", help="Miliar Kaki Kubik")
        c_res2.metric("🛢 STOIIP (Oil In Place)", f"{stoiip/1e6:.2f} MMbbls", help="Juta Barel Minyak")

        # --- EXPORT LAPORAN VOLUMETRIK ---
        st.markdown("### 📄 Export Laporan Volumetrik")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            try:
                pdf_buffer = create_volumetric_report_pdf(
                    vol_gas_cap, vol_oil_zone, vol_total_res,
                    goc_input, woc_input,
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
                    goc_input, woc_input,
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

        # --- TABS VISUALISASI (4 TAB) ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺 Peta Kontur 2D",
            "🧊 Model 3D",
            "📋 Data Mentah",
            "✂ Penampang (Baru)"
        ])

        # === TAB 1: 2D ===
        with tab1:
            fig_2d = go.Figure()

            fig_2d.add_trace(go.Contour(
                z=grid_z,
                x=np.linspace(df['X'].min(), df['X'].max(), 100),
                y=np.linspace(df['Y'].min(), df['Y'].max(), 100),
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
                (df['Z'] < goc_input),
                (df['Z'] >= goc_input) & (df['Z'] <= woc_input),
                (df['Z'] > woc_input)
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

            fig_3d.add_trace(create_plane(goc_input, 'red', 'GOC'))
            fig_3d.add_trace(create_plane(woc_input, 'blue', 'WOC'))

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
            
            slice_y = st.slider(
                "Pilih Posisi Irisan Y",
                float(y_min),
                float(y_max),
                float((y_min + y_max) / 2)
            )
            
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
            
            fig_xs.add_hline(y=goc_input, line_dash="dash", line_color="red", annotation_text="GOC")
            fig_xs.add_hline(y=woc_input, line_dash="dash", line_color="blue", annotation_text="WOC")
            
            fig_xs.update_yaxes(autorange="reversed", title="Depth (m)")
            fig_xs.update_layout(
                title=f"Irisan pada Y = {slice_y:.1f}",
                xaxis_title="X Coordinate",
                height=500
            )
            st.plotly_chart(fig_xs, use_container_width=True)

    else:
        st.warning("⚠ Data belum cukup untuk membuat kontur. Masukkan minimal 4 titik yang menyebar.")
        st.dataframe(df, use_container_width=True)

# === TAB 5: FITUR EKSTENSI ===
from extra_features import run_extra_features

tab_extra = st.tabs(["🧩 Fitur Ekstensi"])[0]
with tab_extra:
    run_extra_features(df)
