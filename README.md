# Visualisasi Reservoir 3D

**Tugas Pemetaan Bawah Permukaan IF-A**

## List Kontributor

-   [Muhammad Luqmaan - 123230070]
-   [Salman Faris - 123230024]
-   [Reza Rasendriya Adi Putra - 123230030]
-   [Valentino Abinata - 123230013]
-   [Rheza Priya Anargya - 123230032]
-   [Gusti Rama - 123230040]
-   [Bintoro - 123230059]
-   [Imam Khusain - 123230018]
-   [Adi Setya N.P - 123230026]
-   [Bintang Jati Kesuma S - 123230075]
-   [Nisrina Salsabila - 123230004]
-   [Muhammad Daffa - 123230203]
-   [Muhammad Diyan Alkautsar - 123230019]

**Peta Struktur Interaktif & Pemodelan Kontak Fluida**

Website ini adalah aplikasi berbasis Streamlit yang dirancang untuk visualisasi 3D model reservoir bawah permukaan. Aplikasi ini memungkinkan pengguna untuk memasukkan data koordinat, memvisualisasikan peta kontur 2D, dan menghasilkan model permukaan 3D dengan bidang kontak fluida interaktif (Gas-Oil Contact dan Water-Oil Contact).

## Fitur

-   **Input Data Fleksibel**: Tambahkan titik manual via sidebar atau **Upload File CSV/Excel** untuk dataset besar.
-   **Kalkulator Volumetrik**: Menghitung estimasi Gross Rock Volume (GRV) untuk zona minyak, gas cap, dan total reservoir secara otomatis.
-   **Pemetaan Kontur 2D**: Visualisasikan struktur reservoir dengan garis kontur 2D dan zona fluida (Gas Cap, Oil Zone, Aquifer).
-   **Pemodelan Permukaan 3D**: Jelajahi reservoir dalam 3D dengan permukaan medan dan bidang GOC/WOC yang dapat disesuaikan.
-   **Kontrol Kontak Fluida**: Sesuaikan level Gas-Oil Contact (GOC) dan Water-Oil Contact (WOC) secara dinamis.
-   **Manajemen Data**: Reset data atau muat dataset demo untuk pengujian cepat.
-   **Ekspor Laporan & Data**:
    -   **Laporan PDF**: Unduh laporan profesional berisi statistik, perhitungan volumetrik, dan snapshot grafik 2D/3D.
    -   **Grid Data**: Unduh hasil interpolasi (X, Y, Z) dalam format `.csv` untuk analisis lanjut di software lain (seperti Petrel/QGIS).
    -   **Ringkasan Teks**: Unduh ringkasan parameter utama dalam format `.txt`.
    
## Instalasi

1.  **Clone repositori** (jika ada):

    ```bash
    git clone <repository-url>
    cd 3d-map
    ```

2.  **Instal dependensi**:
    Pastikan Anda telah menginstal Python, lalu jalankan:
    ```bash
    pip install -r requirements.txt
    ```

## Penggunaan

1.  **Jalankan aplikasi**:

    ```bash
    streamlit run app.py
    ```

2.  **Input Data**:

    - **Opsi A (Manual)**: Gunakan panel **Input Manual** untuk menambahkan titik satu per satu.
    - **Opsi B (Upload)**: Buka panel **Manajemen File**, upload file `.csv` atau `.xlsx` (wajib kolom X, Y, Z), lalu klik "Muat Data".
    - **Opsi C (Demo)**: Buka panel **Reset & Demo** dan klik **Load Data Demo Internal**.

3.  **Eksplorasi**:
    - Pindah antara tab **Peta Kontur 2D**, **Model 3D**, dan **Data Mentah** untuk melihat visualisasi yang berbeda.
    - Sesuaikan slider **Gas-Oil Contact** dan **Water-Oil Contact** di sidebar untuk melihat bagaimana mereka berpotongan dengan struktur reservoir.

## Dependensi

-   [Streamlit](https://streamlit.io/)
-   [Pandas](https://pandas.pydata.org/)
-   [Plotly](https://plotly.com/python/)
-   [NumPy](https://numpy.org/)
-   [SciPy](https://scipy.org/)
-   [FPDF](https://pyfpdf.readthedocs.io/)
-   [Kaleido](https://pypi.org/project/kaleido/)

## Kontribusi

Yang mau ikut kontribusi silakan ikuti langkah-langkah berikut:

1.  **Fork repositori ini**.
2.  **Buat branch fitur baru** (`git checkout -b fitur-baru`).
3.  **Lakukan perubahan** (commit perubahan Anda: `git commit -m 'Menambahkan fitur baru'`).
4.  **Push ke branch** (`git push origin fitur-baru`).
5.  **Buat Pull Request**.
