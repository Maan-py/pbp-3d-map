import streamlit as st

def setup_page_config():
    """Konfigurasi halaman utama aplikasi"""
    st.set_page_config(page_title="GeoViz Pro", layout="wide", page_icon="🌍")

def apply_custom_css():
    """Menerapkan CSS custom"""
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
