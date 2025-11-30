# ============================
# app.py — Part 1 (imports, helpers, sidebar, upload)
# Versi: final-ready (siap disambung part 2 & 3)
# ============================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
import io
import json
import tempfile
from interpolasi import generate_property_heatmap  # tetap dipakai jika ada implementasi di interpolasi.py

# ReportLab untuk PDF ringkasan volumetrik
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Proyek Pemetaan Bawah Permukaan IF-A", layout="wide", page_icon="🌍")

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
st.title("Proyek Pemetaan Bawah Permukaan IF-A")
st.title("🌍 3D Reservoir Visualization")
st.markdown("Interactive Structural Map, Fluid Contact & Reserves Calculator")

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
                st.toast(f"Titik terakhir {removed} dihapus.", icon="🗑")
                st.rerun()
            else:
                st.warning("Tidak ada titik untuk dihapus.")
    
    # --- EXPORT & SESSION MANAGEMENT ---
    with st.expander("💾 Export & Session", expanded=False):
        st.markdown("### 📤 Export CSV")

        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇ Download CSV Data",
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
# ==================================================
# =========== TABS VISUALISASI UTAMA ===============
# ==================================================

# Buat tab lengkap termasuk tab Isopach yang baru
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🗺 Peta Kontur 2D",
    "🧊 Model 3D",
    "📋 Data Mentah",
    "✂ Penampang",
    "🔥 Heatmap Property",
    "⭕ Before–After",
    "🟧 Isopach Map"  # <--- TAB BARU
])

# pastikan ada minimal info untuk min/max Z
if not df.empty:
    min_z, max_z = df['Z'].min(), df['Z'].max()
else:
    min_z, max_z = 0.0, 0.0

# ==================================================
# ========= IF DATA >= 4 (semua fitur ON) ==========
# ==================================================
if len(df) >= 4:

    # -------- GRID INTERPOLASI DASAR --------
    df_unique = df.groupby(['X','Y'], as_index=False)['Z'].mean()

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
    except:
        grid_z = griddata(
            (df_unique['X'], df_unique['Y']),
            df_unique['Z'],
            (grid_x, grid_y),
            method='linear'
        )

    # ==================================================
    # ==================== TAB 1 =======================
    # ==================================================
    with tab1:
        fig_2d = go.Figure()
        fig_2d.add_trace(go.Contour(
            z=grid_z,
            x=np.linspace(df['X'].min(), df['X'].max(), grid_z.shape[1]),
            y=np.linspace(df['Y'].min(), df['Y'].max(), grid_z.shape[0]),
            colorscale='Greys',
            opacity=0.45,
            contours=dict(
                start=min_z,
                end=max_z,
                size=(max_z-min_z)/10 if max_z != min_z else 1,
                showlabels=True
            ),
            name='Surface'
        ))

        # titik-titik
        df['Fluid'] = np.where(df['Z'] < goc_input, 'Gas Cap',
                        np.where(df['Z'] <= woc_input, 'Oil Zone', 'Aquifer'))
        colors_map = {'Gas Cap':'red','Oil Zone':'green','Aquifer':'blue'}

        for fluid in ['Gas Cap','Oil Zone','Aquifer']:
            sub = df[df['Fluid']==fluid]
            if len(sub)>0:
                fig_2d.add_trace(go.Scatter(
                    x=sub['X'], y=sub['Y'],
                    mode='markers+text',
                    text=sub['Z'].astype(int),
                    textposition="top center",
                    marker=dict(size=10, color=colors_map[fluid], line=dict(color='black',width=1)),
                    name=fluid
                ))

        fig_2d.update_layout(
            height=650,
            margin=dict(l=20,r=20,t=40,b=20),
            xaxis_title="X",
            yaxis_title="Y"
        )
        st.plotly_chart(fig_2d, use_container_width=True)

    # ==================================================
    # ==================== TAB 2 =======================
    # ==================================================
    with tab2:
        fig_3d = go.Figure()

        fig_3d.add_trace(go.Surface(
            x=grid_x, y=grid_y, z=grid_z,
            colorscale="Earth_r", opacity=0.9, name="Structure"
        ))

        def plane(level,color,name):
            return go.Surface(
                x=grid_x, y=grid_y,
                z=np.ones_like(grid_z)*level,
                opacity=0.4,
                colorscale=[[0,color],[1,color]],
                showscale=False,
                name=name
            )

        fig_3d.add_trace(plane(goc_input,'red',"GOC"))
        fig_3d.add_trace(plane(woc_input,'blue',"WOC"))

        fig_3d.update_layout(
            scene=dict(
                zaxis=dict(autorange="reversed"),
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Depth"
            ),
            height=650
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    # ==================================================
    # ==================== TAB 3 =======================
    # ==================================================
    with tab3:
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "⬇ Download CSV Data",
            df.to_csv(index=False),
            file_name="raw_data.csv",
            mime="text/csv"
        )

    # ==================================================
    # ==================== TAB 4 =======================
    # ==================================================
    with tab4:
        st.markdown("### ✂ Cross Section (Penampang)")

        slice_y = st.slider(
            "Pilih posisi Y",
            float(df['Y'].min()),
            float(df['Y'].max()),
            float((df['Y'].min()+df['Y'].max())/2)
        )

        idx = (np.abs(grid_y[:,0] - slice_y)).argmin()
        z_profile = grid_z[idx,:]

        fig_xs = go.Figure()
        fig_xs.add_trace(go.Scatter(
            x=grid_x[0,:],
            y=z_profile,
            mode="lines",
            fill="tozeroy"
        ))
        fig_xs.add_hline(y=goc_input, line_dash="dash", line_color="red", annotation_text="GOC")
        fig_xs.add_hline(y=woc_input, line_dash="dash", line_color="blue", annotation_text="WOC")

        fig_xs.update_yaxes(autorange="reversed", title="Depth")
        fig_xs.update_xaxes(title="X")
        fig_xs.update_layout(height=500, title=f"Cross-section @ Y = {slice_y}")
        st.plotly_chart(fig_xs, use_container_width=True)

    # ==================================================
    # ==================== TAB 5 =======================
    # ==================================================
    with tab5:
        st.subheader("🔥 Heatmap Interpolasi Property")

        df_prop = df.copy()
        df_prop["Porosity"] = porosity
        df_prop["Sw"] = sw
        df_prop["NTG"] = ntg

        option = st.selectbox(
            "Pilih Properti",
            ["Porosity","Sw","NTG","Depth (Z)","Upload CSV VALUE"]
        )

        if option == "Upload CSV VALUE":
            uploaded = st.file_uploader("Upload Properti (kolom VALUE)", type="csv")
            if uploaded:
                prop_df = pd.read_csv(uploaded)
                if "VALUE" in prop_df.columns and len(prop_df)==len(df):
                    prop_values = prop_df["VALUE"].values
                else:
                    st.error("Format salah! CSV harus punya kolom VALUE & jumlah baris harus sama.")
                    prop_values = None
            else:
                prop_values = None
        else:
            prop_values = df["Z"].values if option=="Depth (Z)" else df_prop[option].values

        if prop_values is not None:
            try:
                grid_prop = griddata((df["X"],df["Y"]), prop_values, (grid_x,grid_y), method="cubic")
            except:
                grid_prop = griddata((df["X"],df["Y"]), prop_values, (grid_x,grid_y), method="linear")

            fig_heat = go.Figure(go.Heatmap(
                x=np.linspace(df['X'].min(),df['X'].max(),grid_prop.shape[1]),
                y=np.linspace(df['Y'].min(),df['Y'].max(),grid_prop.shape[0]),
                z=grid_prop,
                colorscale="Viridis"
            ))
            fig_heat.update_layout(
                height=650,
                title=f"Heatmap {option}"
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # download CSV
            heat_df = pd.DataFrame({
                "X":grid_x.flatten(),
                "Y":grid_y.flatten(),
                option: grid_prop.flatten()
            })
            st.download_button(
                f"⬇ Download Heatmap {option}",
                heat_df.to_csv(index=False),
                file_name=f"heatmap_{option}.csv",
                mime="text/csv"
            )

    # ==================================================
    # ==================== TAB 6 =======================
    # ==================================================
    with tab6:
        st.subheader("⭕ Perbandingan 3D Before – After")

        colA, colB = st.columns(2)
        with colA:
            before_file = st.file_uploader("Upload BEFORE", type="csv")
        with colB:
            after_file = st.file_uploader("Upload AFTER", type="csv")

        if before_file and after_file:
            df_b = pd.read_csv(before_file)
            df_a = pd.read_csv(after_file)

            if not {"X","Y","Z"}.issubset(df_b.columns) or not {"X","Y","Z"}.issubset(df_a.columns):
                st.error("File harus punya kolom X,Y,Z!")
                st.stop()

            # interpolasi BEFORE
            gxb = np.linspace(df_b["X"].min(), df_b["X"].max(), 100)
            gyb = np.linspace(df_b["Y"].min(), df_b["Y"].max(), 100)
            gxb,gyb = np.meshgrid(gxb,gyb)
            try:
                gzb = griddata((df_b["X"],df_b["Y"]), df_b["Z"], (gxb,gyb), method="linear")
            except:
                gzb = None

            # interpolasi AFTER
            gxa = np.linspace(df_a["X"].min(), df_a["X"].max(), 100)
            gya = np.linspace(df_a["Y"].min(), df_a["Y"].max(), 100)
            gxa,gya = np.meshgrid(gxa,gya)
            try:
                gza = griddata((df_a["X"],df_a["Y"]), df_a["Z"], (gxa,gya), method="linear")
            except:
                gza = None

            # plot
            from plotly.subplots import make_subplots
            fig = make_subplots(rows=1, cols=2,
                specs=[[{"type":"surface"},{"type":"surface"}]],
                subplot_titles=["Before", "After"]
            )

            fig.add_trace(go.Surface(x=gxb,y=gyb,z=gzb,colorscale="Viridis"),1,1)
            fig.add_trace(go.Surface(x=gxa,y=gya,z=gza,colorscale="Turbo"),1,2)
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

            # selisih
            if gzb is not None and gza is not None and gzb.shape==gza.shape:
                diff = gza - gzb
                fig_d = go.Figure(go.Surface(
                    x=gxa, y=gya, z=diff, colorscale="RdBu"
                ))
                fig_d.update_layout(title="Perbedaan Elevasi", height=600)
                st.plotly_chart(fig_d, use_container_width=True)
            else:
                st.warning("Grid before & after tidak cocok ukuran.")

    # ==================================================
    # ==================== TAB 7 (ISOPACH) =============
    # ==================================================
    with tab7:
        st.subheader("🟧 Isopach Map (Ketebalan Formasi)")

        st.markdown("""
        **Isopach = Thickness Map**  
        Mengukur *perbedaan* antara horizon **Top** dan **Base**.
        """)

        iso_mode = st.radio(
            "Mode Input:",
            ["Gunakan Z (Top + Base otomatis)", "Upload Top & Base"]
        )

        # ===================== CASE 1: PAKAI Z ====================
        if iso_mode == "Gunakan Z (Top + Base otomatis)":
            st.info("Top = nilai Z terendah pada tiap XY, Base = nilai Z tertinggi.")

            df_tb = df.copy()
            df_top = df_tb.groupby(["X","Y"])["Z"].min().reset_index()
            df_base = df_tb.groupby(["X","Y"])["Z"].max().reset_index()

            df_iso = df_top.copy()
            df_iso["Base"] = df_base["Z"]
            df_iso["Thickness"] = df_iso["Base"] - df_iso["Z"]

        # ===================== CASE 2: UPLOAD ====================
        else:
            top_file = st.file_uploader("Upload Top (kolom: X,Y,Z)", type="csv")
            base_file = st.file_uploader("Upload Base (kolom: X,Y,Z)", type="csv")

            if top_file and base_file:
                df_top = pd.read_csv(top_file)
                df_base = pd.read_csv(base_file)

                if not {"X","Y","Z"}.issubset(df_top.columns) or not {"X","Y","Z"}.issubset(df_base.columns):
                    st.error("Format harus punya X,Y,Z!")
                    st.stop()

                df_iso = df_top.copy()
                df_iso["Base"] = df_base["Z"]
                df_iso["Thickness"] = df_iso["Base"] - df_iso["Z"]
            else:
                st.info("Menunggu file upload...")
                st.stop()

        # -------- INTERPOLASI THICKNESS --------
        try:
            grid_thick = griddata(
                (df_iso["X"],df_iso["Y"]),
                df_iso["Thickness"],
                (grid_x,grid_y),
                method="cubic"
            )
        except:
            grid_thick = griddata(
                (df_iso["X"],df_iso["Y"]),
                df_iso["Thickness"],
                (grid_x,grid_y),
                method="linear"
            )

        # -------------- PLOT ---------------------
        fig_iso = go.Figure(go.Contour(
            x=np.linspace(df['X'].min(), df['X'].max(), 100),
            y=np.linspace(df['Y'].min(), df['Y'].max(), 100),
            z=grid_thick,
            colorscale="Oranges",
            contours=dict(showlabels=True),
            colorbar=dict(title="Thickness (m)")
        ))
        fig_iso.update_layout(height=650, title="Isopach Map")
        st.plotly_chart(fig_iso, use_container_width=True)

        # download CSV
        iso_df = pd.DataFrame({
            "X":grid_x.flatten(),
            "Y":grid_y.flatten(),
            "Thickness":grid_thick.flatten()
        })
        st.download_button(
            "⬇ Download Isopach CSV",
            iso_df.to_csv(index=False),
            file_name=f"isopach_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ==================================================
# ========== IF DATA < 4, TAB WARNING MODE =========
# ==================================================
else:
    for t in [tab1,tab2,tab3,tab4,tab5,tab6,tab7]:
        with t:
            st.warning("Minimal 4 titik diperlukan untuk fitur ini.")
            st.dataframe(df, use_container_width=True)
# ============================================================
#           PERHITUNGAN VOLUME RESERVOIR (RINGKAS)
# ============================================================

st.subheader("📦 Perhitungan Volume Reservoir (Simplified)")

col_v1, col_v2, col_v3 = st.columns(3)

phi = col_v1.number_input("Porosity (ϕ)", 0.00, 1.00, 0.20)
sw  = col_v2.number_input("Water Saturation (Sw)", 0.00, 1.00, 0.30)
ntg = col_v3.number_input("Net-to-Gross (NTG)", 0.00, 1.00, 0.80)

# -----------------------------
# AUTO-DETECT Kolom X,Y,Z
# -----------------------------
possible_x = ["X","x","Easting","Longitude","Long"]
possible_y = ["Y","y","Northing","Latitude","Lat"]
possible_z = ["Z","z","Depth","TVD","Elevation"]

col_x = next((c for c in possible_x if c in df.columns), None)
col_y = next((c for c in possible_y if c in df.columns), None)
col_z = next((c for c in possible_z if c in df.columns), None)

if col_x is None or col_y is None:
    st.error("❌ Tidak dapat menemukan kolom X/Y pada data!")
    st.stop()

# -----------------------------
# Ketebalan
# -----------------------------
if col_z:
    thickness = df[col_z]   # pakai Z langsung
else:
    thickness = st.number_input("Masukkan Thickness", 0.0, 500.0, 50.0)

# -----------------------------
# HITUNG AREA
# -----------------------------
xmin, xmax = df[col_x].min(), df[col_x].max()
ymin, ymax = df[col_y].min(), df[col_y].max()

area = (xmax - xmin) * (ymax - ymin)

# -----------------------------
# VOLUME
# -----------------------------
bulk_volume  = area * (thickness.mean() if hasattr(thickness,"mean") else thickness)
net_volume   = bulk_volume * ntg
pore_volume  = net_volume  * phi
hcpv         = pore_volume * (1 - sw)

# -----------------------------
# TAMPILKAN
# -----------------------------
st.write("### 📊 Hasil Perhitungan")

col_r1, col_r2 = st.columns(2)

col_r1.metric("Area (m²)", f"{area:,.2f}")
col_r2.metric("Bulk Volume (m³)", f"{bulk_volume:,.2f}")
col_r1.metric("Net Volume (m³)", f"{net_volume:,.2f}")
col_r2.metric("Pore Volume (m³)", f"{pore_volume:,.2f}")

st.metric("🔥 Hydrocarbon Pore Volume (HCPV)", f"{hcpv:,.2f} m³")

st.caption("""
Perhitungan ini merupakan estimasi cepat.  
Untuk perhitungan STOIIP/GIIP lengkap, gunakan bagian awal aplikasi (volumetrik utama).
""")
