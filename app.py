import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# 1. CONFIGURATION & PAGE STYLE
# =========================================================
st.set_page_config(
    page_title="Stroke Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk meniru layout Looker Studio (Background grey, Header Biru, Card putih)
st.markdown("""
    <style>
    /* Background utama abu-abu muda ala Looker */
    .stApp { background-color: #E9ECEF; }
    
    /* Header Biru Gelap ala Looker */
    .looker-header {
        background-color: #1a365d; 
        padding: 20px 25px; 
        border-radius: 8px; 
        margin-bottom: 20px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .looker-header h1 { 
        color: #ffffff; font-size: 26px; margin: 0; padding: 0; 
        text-transform: uppercase; letter-spacing: 1px; 
    }
    .looker-header p { color: #cbd5e1; font-size: 14px; margin: 0; padding: 0; margin-top: 5px; }
    
    /* Spacing antar kolom agar rapat */
    div[data-testid="column"] { padding: 0px 8px; }
    
    /* Styling kontainer Tabs agar berbackground putih */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 0px 8px 8px 8px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        margin-top: -10px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. DATA LOADING & PREPROCESSING
# =========================================================
@st.cache_data
def load_data():
    df = pd.read_csv('stroke_data_hanya_cleaning.csv')
    df['Stroke_Label'] = df['Stroke'].map({1: 'Stroke', 0: 'Tidak Stroke'})
    df['Hypertension_Label'] = df['Hypertension'].map({1: 'Hipertensi', 0: 'Normal'})
    df['Heart_Disease_Label'] = df['Heart_Disease'].map({1: 'Penyakit Jantung', 0: 'Normal'})
    df['Diabetes_Label'] = df['Diabetes'].map({1: 'Diabetes', 0: 'Normal'})
    df['Age_Int'] = df['Age'].round().astype(int)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ File 'stroke_data_hanya_cleaning.csv' tidak ditemukan!")
    st.stop()

# =========================================================
# 3. HEADER UTAMA (BANNER LOOKER STYLE)
# =========================================================
st.markdown('''
    <div class="looker-header">
        <h1>Dashboard Analisis Klinis Stroke</h1>
        <p>Eksplorasi Interaktif Faktor Risiko Medis dan Demografi Pasien (10.000 Data Observasi)</p>
    </div>
''', unsafe_allow_html=True)

# =========================================================
# 4. TOP SECTION: FILTER & KPI (SEJAJAR)
# =========================================================
# Membagi kolom: 55% untuk Filter, 45% untuk KPI
col_filter, col_kpi = st.columns([1.3, 1])

with col_filter:
    st.markdown('<div style="font-weight: 800; color: #1a365d; font-size: 15px; margin-bottom: 8px;">FILTER</div>', unsafe_allow_html=True)
    with st.container(border=True):
        f1, f2 = st.columns(2)
        with f1:
            gender_filter = st.multiselect("Berdasarkan Gender:", options=df['Gender'].unique(), default=df['Gender'].unique())
        with f2:
            smoking_filter = st.multiselect("Berdasarkan Status Merokok:", options=df['Smoking_Status'].unique(), default=df['Smoking_Status'].unique())
        
        min_age, max_age = int(df['Age_Int'].min()), int(df['Age_Int'].max())
        age_filter = st.slider("Berdasarkan Rentang Umur (Tahun):", min_value=min_age, max_value=max_age, value=(min_age, max_age))

# Kalkulasi Filter
df_filtered = df[
    (df['Gender'].isin(gender_filter)) &
    (df['Smoking_Status'].isin(smoking_filter)) &
    (df['Age_Int'].between(age_filter[0], age_filter[1]))
]

total_pasien = len(df_filtered)
total_stroke = len(df_filtered[df_filtered['Stroke'] == 1])
total_sehat = len(df_filtered[df_filtered['Stroke'] == 0])
rasio_stroke = (total_stroke / total_pasien * 100) if total_pasien > 0 else 0

with col_kpi:
    st.markdown('<div style="font-weight: 800; color: #1a365d; font-size: 15px; margin-bottom: 8px;">METRIK KINERJA UTAMA</div>', unsafe_allow_html=True)
    
    def make_kpi(title, value, icon, color):
        return f'''
        <div style="background-color: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 12px 15px; text-align: left; margin-bottom: 12px; box-shadow: 0px 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 13px; color: #1a365d; font-weight: 700; margin-bottom: 5px;">{title}</div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="font-size: 26px; font-weight: 900; color: {color};">{value}</div>
                <div style="font-size: 24px;">{icon}</div>
            </div>
        </div>
        '''
        
    k1, k2 = st.columns(2)
    with k1:
        st.markdown(make_kpi("Total Responden", f"{total_pasien:,}", "👤", "#1e40af"), unsafe_allow_html=True)
        st.markdown(make_kpi("Pasien Sehat", f"{total_sehat:,}", "🌿", "#16a34a"), unsafe_allow_html=True)
    with k2:
        st.markdown(make_kpi("Kasus Stroke", f"{total_stroke:,}", "⚠️", "#dc2626"), unsafe_allow_html=True)
        st.markdown(make_kpi("Rerata Kasus (Rasio)", f"{rasio_stroke:.2f}%", "📉", "#ea580c"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# 5. KONTEN VISUALISASI UTAMA
# =========================================================
tab1, tab2, tab3 = st.tabs(["📊 Faktor Umum & Imbalance", "🩺 Analisis Penyakit Penyerta", "📈 Analisis Fisik & Usia"])

# ---------------------------------------------------------
# TAB 1: Proporsi Imbalance
# ---------------------------------------------------------
with tab1:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">1. Faktor Apa Saja yang Memengaruhi Risiko Stroke?</h3>', unsafe_allow_html=True)
    st.info("**Insight Faktor Risiko:** Risiko stroke dipengaruhi oleh kombinasi multi-faktor klinis dan demografi. Kamu dapat berinteraksi langsung menggunakan panel **Filter** di atas untuk menguji pergeseran angka secara *real-time*.")
    
    st.markdown("---")
    
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">5. Apakah Dataset Mengalami Imbalance Sebelum Dilakukan SMOTE?</h3>', unsafe_allow_html=True)
    col_t1_1, col_t1_2 = st.columns([1.2, 1])
    with col_t1_1:
        fig_target = px.pie(
            df_filtered, names='Stroke_Label', color='Stroke_Label',
            color_discrete_map={'Tidak Stroke': '#1E3A8A', 'Stroke': '#DC2626'}, hole=0.4
        )
        fig_target.update_traces(textposition='inside', textinfo='percent+value')
        fig_target.update_layout(margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig_target, use_container_width=True)
        
    with col_t1_2:
        st.warning(f"**Temuan Imbalance Data:**\n\n* **Ya, Sangat Imbalance.** Grafik membuktikan bahwa proporsi pasien sehat mendominasi kelas target (hanya {rasio_stroke:.2f}% kasus stroke).\n* **Solusi Model:** Pipeline backend data science telah berhasil menerapkan teknik **SMOTE** untuk membuat data seimbang artifisial **50:50 (masing-masing 7.022 data per kelas)** agar model Machine Learning tidak bias.")

# ---------------------------------------------------------
# TAB 2: Komorbiditas
# ---------------------------------------------------------
with tab2:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">3. Apakah Hipertensi dan Penyakit Jantung Meningkatkan Risiko Stroke?</h3>', unsafe_allow_html=True)
    col_t2_1, col_t2_2 = st.columns(2)
    with col_t2_1:
        fig_hyper = px.histogram(
            df_filtered, x='Hypertension_Label', color='Stroke_Label', barmode='group',
            color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
            labels={'Hypertension_Label': 'Status Hipertensi', 'Stroke_Label': 'Status'}
        )
        fig_hyper.update_layout(title="Sebaran Berdasarkan Hipertensi", yaxis_title="Jumlah Pasien")
        st.plotly_chart(fig_hyper, use_container_width=True)
        
    with col_t2_2:
        fig_heart = px.histogram(
            df_filtered, x='Heart_Disease_Label', color='Stroke_Label', barmode='group',
            color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
            labels={'Heart_Disease_Label': 'Status Penyakit Jantung', 'Stroke_Label': 'Status'}
        )
        fig_heart.update_layout(title="Sebaran Berdasarkan Penyakit Jantung", yaxis_title="Jumlah Pasien")
        st.plotly_chart(fig_heart, use_container_width=True)
        
    st.success("**Kesimpulan Komorbiditas:** **Ya, sangat meningkatkan risiko.** Rasio perbandingan melonjak tinggi pada pasien penderita Hipertensi maupun Penyakit Jantung.")

# ---------------------------------------------------------
# TAB 3: Analisis Usia & Fisik
# ---------------------------------------------------------
with tab3:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">2. Apakah Usia Memiliki Hubungan Terhadap Kejadian Stroke?</h3>', unsafe_allow_html=True)
    
    # Overlapping Histogram untuk menggantikan Box Plot
    fig_age = px.histogram(
        df_filtered, x='Age', color='Stroke_Label',
        barmode='overlay', 
        nbins=30,
        color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
        labels={'Age': 'Umur Pasien (Tahun)', 'Stroke_Label': 'Status'}
    )
    fig_age.update_traces(opacity=0.75) 
    fig_age.update_layout(yaxis_title="Jumlah Pasien", margin=dict(t=10, b=10))
    st.plotly_chart(fig_age, use_container_width=True)
    
    st.success("**Kesimpulan Usia:** **Ya, sangat berhubungan.** Dari distribusi grafik di atas, terlihat jelas bahwa kasus stroke (merah) mulai muncul dan merangkak naik secara signifikan pada pasien di atas usia 50 tahun.")
    
    st.markdown("---")
    
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">4. Bagaimana Pengaruh BMI dan Kadar Glukosa Terhadap Stroke?</h3>', unsafe_allow_html=True)
    
    # Mengurutkan data agar titik Stroke ada di depan (paling atas) dan yang Sehat jadi transparan
    df_sorted = df_filtered.sort_values(by='Stroke')
    
    fig_scatter = px.scatter(
        df_sorted, x='BMI', y='Avg_Glucose', color='Stroke_Label',
        color_discrete_map={
            'Tidak Stroke': 'rgba(156, 163, 175, 0.25)', 
            'Stroke': '#DC2626'
        }, 
        labels={'Avg_Glucose': 'Rata-rata Kadar Glukosa', 'BMI': 'Indeks Massa Tubuh (BMI)', 'Stroke_Label': 'Status'}
    )
    fig_scatter.update_traces(marker=dict(size=6))
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.warning("**Kesimpulan Karakteristik Fisik:** Pasien dengan **kadar glukosa tinggi** sekaligus **berat badan berlebih (BMI > 25)** berkerumun padat di area rentan (didominasi sebaran titik merah).")

# =========================================================
# 6. FOOTER
# =========================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('''
    <div style="text-align: center; color: #64748b; font-size: 13px; font-weight: 500;">
        Powered by sainsdata@uinsaid.ac.id | Design by Salma Alya Sabila (A&S)
    </div>
''', unsafe_allow_html=True)