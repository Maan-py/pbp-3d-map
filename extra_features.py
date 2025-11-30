# extra_features.py

import streamlit as st
import pandas as pd

def run_extra_features(df):
    st.header("🧩 Fitur Ekstensi")
    st.caption("Fitur tambahan yang berdiri di luar kode utama (modular & non-intrusif).")

    if df.empty:
        st.info("Data belum tersedia.")
        return

    st.subheader("📈 Statistik Dasar")
    st.dataframe(df.describe(), use_container_width=True)

    st.subheader("🧭 Cek Sebaran Koordinat")
    st.write(f"Rentang X: {df['X'].min()} — {df['X'].max()}")
    st.write(f"Rentang Y: {df['Y'].min()} — {df['Y'].max()}")
    st.write(f"Rentang Z: {df['Z'].min()} — {df['Z'].max()}")

    st.subheader("🗂 Download Summary")
    summary_csv = df.describe().to_csv().encode("utf-8")
    st.download_button(
        "📥 Download CSV Statistik",
        data=summary_csv,
        file_name="summary_stats.csv",
        mime="text/csv"
    )
        
