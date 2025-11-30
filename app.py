import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
import io
import json
import tempfile
from interpolasi import generate_property_heatmap

# ReportLab untuk PDF ringkasan volumetrik
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Projek Pemetaan Bawah Permukaan IF-A", layout="wide", page_icon="🌍")

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

                # Fitur: Mengecek kekosongan data & integritas awal
                if df_upload.empty:
                    st.error("❌ Eits, file ini kosong !")
                    st.stop() # Stop program biar gak error di bawah
                
                # Cek sekilas apakah data aman
                if {'X', 'Y', 'Z'}.issubset(df_upload.columns):
                    st.toast("✅ Data Integrity Check: OK", icon="🛡")
                    
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
        # ===============================================
        #  🤖 NEW FEATURE: SMART ASSISTANT INTEGRATION
        # ===============================================
        st.markdown("---")
        st.subheader("🤖 Smart Assistant: Interpretasi Otomatis")
        
        with st.container(border=True):
            col_assist1, col_assist2 = st.columns([1, 2])
            
            # Kolom Kiri: Analisis Kedalaman Sederhana
            with col_assist1:
                st.write("#### 📝 Ringkasan Lapangan")
                avg_depth = df['Z'].mean()
                
                # Logic: Kategori Kedalaman
                if avg_depth < 1000:
                    depth_status = "Dangkal (Shallow)"
                    depth_icon = "☀️"
                    depth_desc = "Biaya pengeboran relatif murah."
                elif avg_depth < 2500:
                    depth_status = "Menengah (Medium)"
                    depth_icon = "🌊"
                    depth_desc = "Operasional standar."
                else:
                    depth_status = "Dalam (Deep)"
                    depth_icon = "⚓"
                    depth_desc = "Memerlukan rig spesifikasi tinggi."
                
                st.metric(label="Rata-rata Kedalaman", value=f"{avg_depth:.0f} m", delta=depth_status, delta_color="off")
                st.info(f"{depth_icon} {depth_desc}")

            # Kolom Kanan: Analisis Detail (Logic If-Else)
            with col_assist2:
                st.write("#### 🧠 Analisis Reservoir")
                analysis_points = []
                
                # Logic 1: Kualitas Batuan (Porositas)
                if porosity >= 0.25:
                    analysis_points.append(f"✅ **Kualitas Batuan Sangat Baik** (Porositas {porosity*100:.0f}%): Batuan memiliki ruang pori yang besar, minyak mudah tersimpan.")
                elif porosity >= 0.15:
                    analysis_points.append(f"⚖️ **Kualitas Batuan Cukup Baik** (Porositas {porosity*100:.0f}%): Kualitas reservoir standar industri.")
                else:
                    analysis_points.append(f"⚠️ **Kualitas Batuan Rendah** (Porositas {porosity*100:.0f}%): Batuan 'tight', mungkin membutuhkan stimulasi (fracking).")

                # Logic 2: Skala Cadangan (STOIIP)
                stoiip_mmbbls = stoiip / 1e6
                if stoiip_mmbbls > 50:
                    analysis_points.append(f"🌟 **Potensi Besar (Giant Field)**: Cadangan {stoiip_mmbbls:.1f} MMbbls sangat ekonomis dan strategis.")
                elif stoiip_mmbbls > 5:
                    analysis_points.append(f"💰 **Potensi Komersial**: Cadangan {stoiip_mmbbls:.1f} MMbbls layak dikembangkan secara ekonomi.")
                else:
                    analysis_points.append(f"📉 **Potensi Marginal**: Cadangan {stoiip_mmbbls:.1f} MMbbls tergolong kecil, perlu perhitungan biaya yang ketat.")
                
                # Logic 3: Fluid Contact Warning
                if (woc_input - goc_input) > 0 and (woc_input - goc_input) < 10:
                    analysis_points.append("🚨 **Warning Zona Minyak**: Zona minyak sangat tipis (< 10m). Hati-hati terhadap 'coning' air atau gas saat produksi.")
                
                # Render Bullet Points
                for point in analysis_points:
                    st.markdown(point)
        # ===============================================

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

        # --- TABS VISUALISASI (5 TAB) ---
      # --- TABS VISUALISASI (5 TAB) ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺 Peta Kontur 2D",
    "🧊 Model 3D",
    "📋 Data Mentah",
    "✂ Penampang (Baru)",
    "🔥 Heatmap Property",
    "⭕ Perbandingan 3D (Before After)"
])

# pastikan ada minimal info untuk min_z / max_z (dipakai di beberapa tab)
if not df.empty:
    min_z, max_z = df['Z'].min(), df['Z'].max()
else:
    min_z, max_z = 0.0, 0.0

# --- jika data cukup, jalankan perhitungan dan isi semua tab ---
if len(df) >= 4:
    # grid & interpolasi (siapkan aman dengan try/except)
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

    # -- PERHITUNGAN VOLUME & CADANGAN (tetap di sini, karena cuma kalau data cukup) --
    x_min, x_max = df['X'].min(), df['X'].max()
    y_min, y_max = df['Y'].min(), df['Y'].max()
    nx, ny = 100, 100
    dx = (x_max - x_min) / (nx - 1) if nx > 1 else 1.0
    dy = (y_max - y_min) / (ny - 1) if ny > 1 else 1.0
    cell_area = dx * dy

    thick_above_woc = woc_input - grid_z
    thick_above_woc[thick_above_woc < 0] = 0
    vol_total_res = np.nansum(thick_above_woc) * cell_area

    thick_above_goc = goc_input - grid_z
    thick_above_goc[thick_above_goc < 0] = 0
    vol_gas_cap = np.nansum(thick_above_goc) * cell_area

    vol_oil_zone = max(0, vol_total_res - vol_gas_cap)

    stoiip = (vol_oil_zone * ntg * porosity * (1 - sw)) / bo
    giip = (vol_gas_cap * ntg * porosity * (1 - sw)) / bg

    # Metrics (bisa di atas tab atau di salah satu tab — saya tampilkan di atas tab1 untuk ringkasan)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🔴 Gross Gas Volume", f"{vol_gas_cap/1e6:.2f} Juta m³")
    col_b.metric("🟢 Gross Oil Volume", f"{vol_oil_zone/1e6:.2f} Juta m³")
    col_c.metric("🔵 Total Reservoir", f"{vol_total_res/1e6:.2f} Juta m³")

    # === TAB 1: 2D ===
    with tab1:
        fig_2d = go.Figure()
        fig_2d.add_trace(go.Contour(
            z=grid_z,
            x=np.linspace(x_min, x_max, grid_z.shape[1]),
            y=np.linspace(y_min, y_max, grid_z.shape[0]),
            colorscale='Greys',
            opacity=0.4,
            contours=dict(
                start=min_z,
                end=max_z,
                size=(max_z - min_z) / 10 if max_z != min_z else 1,
                showlabels=True
            ),
            name='Structure'
        ))

        # point overlay colored by fluid
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
                    marker=dict(size=10, color=colors_map[fluid], line=dict(width=1, color='black')),
                    name=fluid
                ))

        fig_2d.update_layout(height=650, margin=dict(l=20, r=20, t=40, b=20),
                             xaxis_title="X Coordinate", yaxis_title="Y Coordinate")
        st.plotly_chart(fig_2d, use_container_width=True)

        # Export
        try:
            img_2d_png = fig_2d.to_image(format="png", width=1200, height=800)
            st.download_button("🖼 Download PNG", data=img_2d_png,
                               file_name=f"contour_2d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                               mime="image/png")
        except Exception:
            st.info("Export PNG 2D tidak tersedia (butuh orca/kaleido terpasang).")

    # === TAB 2: 3D ===
    # === TAB 2: 3D ===
    with tab2:
        st.subheader("🧊 Model 3D Reservoir & Sumur")
        
        # 1. Inisialisasi Figure
        fig_3d = go.Figure()

        # 2. Plot Permukaan Struktur (Surface)
        fig_3d.add_trace(go.Surface(
            z=grid_z, 
            x=grid_x, 
            y=grid_y, 
            colorscale='Earth_r', 
            opacity=0.9, 
            name='Structure'
        ))

        # 3. Fungsi Helper untuk Bidang Kontak Fluida
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

        # 4. Plot GOC dan WOC
        fig_3d.add_trace(create_plane(goc_input, 'red', 'GOC'))
        fig_3d.add_trace(create_plane(woc_input, 'blue', 'WOC'))

        # 5. --- FITUR BARU: VISUALISASI SUMUR (WELLS) ---
        # Menambahkan checkbox interaktif
        st.markdown("##### 🛤 Kontrol Visualisasi")
        show_wells = st.checkbox("Tampilkan Jalur Sumur (Wells)", value=True)
        
        if show_wells:
            # Loop setiap titik data untuk membuat garis sumur
            for index, row in df.iterrows():
                # Menentukan titik atas sumur. 
                # Kita pakai min_z (titik teratas struktur) agar skala visualnya pas.
                well_top = min_z 
                
                # Gambar Garis Sumur (Pipa)
                fig_3d.add_trace(go.Scatter3d(
                    x=[row['X'], row['X']], 
                    y=[row['Y'], row['Y']], 
                    z=[well_top, row['Z']], # Dari atas struktur ke titik target
                    mode='lines',
                    line=dict(color='grey', width=3), # Warna abu-abu pipa
                    name=f'Well-{index+1}',
                    showlegend=False,
                    hoverinfo='text',
                    text=f"Well-{index+1}<br>X: {row['X']}<br>Y: {row['Y']}<br>Depth: {row['Z']}m"
                ))
                
                # Gambar Marker (Titik Target) di ujung bawah
                fig_3d.add_trace(go.Scatter3d(
                    x=[row['X']], y=[row['Y']], z=[row['Z']],
                    mode='markers',
                    marker=dict(size=5, color='black', symbol='diamond'), # Ikon diamond biar keren
                    showlegend=False,
                    hoverinfo='skip'
                ))
        # -----------------------------------------------

        # 6. Layout & Render
        fig_3d.update_layout(
            scene=dict(
                xaxis_title='X (East)', 
                yaxis_title='Y (North)', 
                zaxis_title='Depth (TVD)', 
                zaxis=dict(autorange="reversed") # Membalik sumbu Z agar kedalaman ke bawah
            ),
            height=650, 
            margin=dict(l=0, r=0, b=0, t=0)
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    # === TAB 3: DATA MENTAH ===
    with tab3:
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv_data,
                           file_name=f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                           mime="text/csv")

    # === TAB 4: CROSS SECTION ===
    with tab4:
        st.markdown("##### ✂ Penampang Melintang (Cross-Section)")
        st.caption("Geser slider untuk memotong peta dari Barat ke Timur pada posisi Y tertentu.")
        slice_y = st.slider("Pilih Posisi Irisan Y", float(y_min), float(y_max), float((y_min + y_max) / 2))
        idx_y = (np.abs(grid_y[:, 0] - slice_y)).argmin()
        z_profile = grid_z[idx_y, :]
        fig_xs = go.Figure()
        fig_xs.add_trace(go.Scatter(x=grid_x[0, :], y=z_profile, mode='lines', fill='tozeroy', name='Top Structure'))
        fig_xs.add_hline(y=goc_input, line_dash="dash", line_color="red", annotation_text="GOC")
        fig_xs.add_hline(y=woc_input, line_dash="dash", line_color="blue", annotation_text="WOC")
        fig_xs.update_yaxes(autorange="reversed", title="Depth (m)")
        fig_xs.update_layout(title=f"Irisan pada Y = {slice_y:.1f}", xaxis_title="X Coordinate", height=500)
        st.plotly_chart(fig_xs, use_container_width=True)

    # === TAB 5: HEATMAP PROPERTY ===
    with tab5:
        st.subheader("🔥 Heatmap Interpolasi Properti")
        st.markdown("Pilih properti yang ingin di-interpolasi (Porosity/Sw/NTG atau custom upload).")

        # use petrophys params per-point (scalar sliders) -> expand to grid by repeating per-point
        df_prop = df.copy()
        # kalau porosity/sw/ntg adalah scalar (slider), buat kolom constant per titik
        df_prop["Porosity"] = porosity
        df_prop["Sw"] = sw
        df_prop["NTG"] = ntg

        option = st.selectbox("Sumber properti:", ["Porosity", "Sw", "NTG", "Depth (Z)", "Upload CSV (kolom VALUE)"])
        if option == "Upload CSV (kolom VALUE)":
            up = st.file_uploader("Upload CSV dengan kolom VALUE", type=["csv"])
            if up is not None:
                prop_df = pd.read_csv(up)
                if "VALUE" in prop_df.columns and len(prop_df) == len(df):
                    prop_values = prop_df["VALUE"].values
                else:
                    st.error("CSV harus memiliki kolom VALUE dan jumlah baris sama dengan titik.")
                    prop_values = None
            else:
                prop_values = None
        else:
            if option == "Depth (Z)":
                prop_values = df_prop["Z"].values
            else:
                prop_values = df_prop[option].values

        if prop_values is None:
            st.info("Belum ada property yang valid untuk di-interpolasi.")
        else:
            try:
                grid_prop = griddata((df["X"], df["Y"]), prop_values, (grid_x, grid_y), method='cubic')
            except Exception:
                grid_prop = griddata((df["X"], df["Y"]), prop_values, (grid_x, grid_y), method='linear')

            fig_heat = go.Figure(data=go.Heatmap(
                x=np.linspace(x_min, x_max, grid_prop.shape[1]),
                y=np.linspace(y_min, y_max, grid_prop.shape[0]),
                z=grid_prop,
                colorscale="Viridis",
                colorbar=dict(title=f"{option}")
            ))
            fig_heat.update_layout(height=650, xaxis_title="X", yaxis_title="Y", title=f"Heatmap {option} (Interpolated)")
            st.plotly_chart(fig_heat, use_container_width=True)

            # export
            heat_df = pd.DataFrame({'X': grid_x.flatten(), 'Y': grid_y.flatten(), option: grid_prop.flatten()})
            st.download_button(label=f"⬇ Download {option} Heatmap CSV",
                               data=heat_df.to_csv(index=False),
                               file_name=f"heatmap_{option.replace(' ','')}{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                               mime="text/csv")
            
      # === TAB 6: PERBANDINGAN 3D BEFORE–AFTER ===
    with tab6:
        st.subheader("⭕ Perbandingan 3D Sebelum–Sesudah")
        st.info("Upload dua dataset untuk melihat perubahan struktur reservoir sebelum dan sesudah.")

        colA, colB = st.columns(2)
        with colA:
            file_before = st.file_uploader("Upload Data Before", type=["csv"])
        with colB:
            file_after = st.file_uploader("Upload Data After", type=["csv"])

    # ===== CEK FILE =====
        if file_before is None or file_after is None:
            st.warning("Silakan upload kedua file (Before & After) terlebih dahulu.")
            st.stop()

    # ===== BACA DATA =====
        df_before = pd.read_csv(file_before)
        df_after = pd.read_csv(file_after)

        required = {"X", "Y", "Z"}
        if not required.issubset(df_before.columns) or not required.issubset(df_after.columns):
            st.error("CSV harus memiliki kolom: X, Y, Z.")
            st.stop()

    # ===== INTERPOLASI BEFORE =====
        dfb = df_before.groupby(["X", "Y"], as_index=False)["Z"].mean()
        xb, yb, zb = dfb["X"].values, dfb["Y"].values, dfb["Z"].values

        gx_b, gy_b = np.meshgrid(
            np.linspace(xb.min(), xb.max(), 100),
            np.linspace(yb.min(), yb.max(), 100)
        )
        gz_b = griddata((xb, yb), zb, (gx_b, gy_b), method="linear")

    # ===== INTERPOLASI AFTER =====
        dfa = df_after.groupby(["X", "Y"], as_index=False)["Z"].mean()
        xa, ya, za = dfa["X"].values, dfa["Y"].values, dfa["Z"].values

        gx_a, gy_a = np.meshgrid(
            np.linspace(xa.min(), xa.max(), 100),
            np.linspace(ya.min(), ya.max(), 100)
        )
        gz_a = griddata((xa, ya), za, (gx_a, gy_a), method="linear")

    # ===== PLOT BEFORE & AFTER =====
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "surface"}, {"type": "surface"}]],
            subplot_titles=("Before", "After")
        )

        fig.add_trace(go.Surface(x=gx_b, y=gy_b, z=gz_b, colorscale="Viridis"), row=1, col=1)
        fig.add_trace(go.Surface(x=gx_a, y=gy_a, z=gz_a, colorscale="Turbo"), row=1, col=2)

        fig.update_layout(height=600, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # ===== SELISIH =====
        st.subheader("📉 Selisih Elevasi (After – Before)")
    try:
            diff = gz_a - gz_b
            fig_diff = go.Figure(go.Surface(
            x=gx_a, y=gy_a, z=diff, colorscale="RdBu"
            ))
            fig_diff.update_layout(height=600, title="Perbedaan Elevasi")
            st.plotly_chart(fig_diff, use_container_width=True)
    except:
            st.warning("Grid Before dan After tidak cocok ukurannya.")

  
# --- jika data TIDAK cukup: tampilkan pesan di masing-masing tab (tab tetap ada) ---
else:
    # small informative content per tab to avoid NameError / empty with-blocks
        with tab1:
            st.warning("Data belum cukup untuk membuat kontur. Masukkan minimal 4 titik yang menyebar.")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.info("Model 3D memerlukan minimal 4 titik. Tambahkan data atau gunakan 'Load Data Demo' pada sidebar.")

        with tab3:
            st.subheader("📋 Data Mentah")
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                    st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="raw_data.csv", mime="text/csv")

        with tab4:
            st.info("Penampang (Cross-section) akan aktif saat data cukup (>=4 titik).")

        with tab5:
            st.info("Heatmap properti akan aktif saat data cukup (>=4 titik). Kamu tetap bisa upload CSV property tapi heatmap tidak akan digenerate tanpa cukup titik.")

        with tab6:
            st.info("Perbandingan 3D Before–After memerlukan dua dataset dengan kolom X,Y,Z.")


# === TAB 5: FITUR EKSTENSI ===
from extra_features import run_extra_features

tab_extra = st.tabs(["🧩 Fitur Ekstensi"])[0]
with tab_extra:
    run_extra_features(df)


# ============================
#  PERHITUNGAN VOLUME RESERVOIR
# ============================

st.subheader("📦 Perhitungan Volume Reservoir")

# Input parameter volumetrik
col_v1, col_v2, col_v3 = st.columns(3)

phi = col_v1.number_input("Porosity (ϕ)", 0.0, 1.0, 0.20)
sw  = col_v2.number_input("Water Saturation (Sw)", 0.0, 1.0, 0.30)
ntg = col_v3.number_input("Net-to-Gross (NTG)", 0.0, 1.0, 0.80)

# ============================
#  AUTO DETECT KOLom X, Y, Z
# ============================

possible_x = ["X", "x", "Easting", "easting", "Long", "long", "Longitude", "longitude"]
possible_y = ["Y", "y", "Northing", "northing", "Lat", "lat", "Latitude", "latitude"]
possible_z = ["Z", "z", "Depth", "depth", "TVD", "tvd", "Elevation", "elevation"]

col_x = next((c for c in possible_x if c in df.columns), None)
col_y = next((c for c in possible_y if c in df.columns), None)
col_z = next((c for c in possible_z if c in df.columns), None)

if col_x is None or col_y is None:
    st.error("❌ Tidak menemukan kolom X/Y di file CSV. Harus ada koordinat X dan Y.")
    st.stop()

# Thickness (Z)
if col_z:
    thickness = df[col_z]
else:
    thickness = st.number_input("Masukkan thickness (jika kolom Z tidak tersedia)", 
                                0.0, 500.0, 50.0)

# ============================
#  PERHITUNGAN AREA
# ============================

xmin, xmax = df[col_x].min(), df[col_x].max()
ymin, ymax = df[col_y].min(), df[col_y].max()
area = (xmax - xmin) * (ymax - ymin)

# Volume bulk reservoir
bulk_volume = area * (thickness.mean() if hasattr(thickness, "mean") else thickness)

# Net reservoir volume
net_volume = bulk_volume * ntg

# Pore volume
pore_volume = net_volume * phi

# Hydrocarbon pore volume
hcpv = pore_volume * (1 - sw)

# ============================
#  DISPLAY HASIL
# ============================

st.write("### 📊 Hasil Perhitungan")

col_r1, col_r2 = st.columns(2)

col_r1.metric("Area (m²)", f"{area:,.2f}")
col_r2.metric("Bulk Volume (m³)", f"{bulk_volume:,.2f}")

col_r1.metric("Net Volume (m³)", f"{net_volume:,.2f}")
col_r2.metric("Pore Volume (m³)", f"{pore_volume:,.2f}")

st.metric("Hydrocarbon Pore Volume (HCPV)", f"{hcpv:,.2f} m³")

