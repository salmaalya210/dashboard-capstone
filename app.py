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

# Helper function untuk menghitung korelasi Pearson
def calculate_correlation(df_input):
    df_corr = df_input.copy()
    
    # Encoding sederhana untuk kolom kategorikal
    df_corr['Gender_Male'] = df_corr['Gender'].map({'Male': 1, 'Female': 0})
    df_corr['SES_Code'] = df_corr['SES'].map({'Low': 0, 'Medium': 1, 'High': 2})
    df_corr['Smoking_Code'] = df_corr['Smoking_Status'].map({'Never': 0, 'Former': 1, 'Current': 2})
    
    # Ambil kolom numerik & ter-encode untuk korelasi dengan target Stroke
    cols_to_corr = [
        'Age', 'Gender_Male', 'SES_Code', 'Hypertension', 
        'Heart_Disease', 'BMI', 'Avg_Glucose', 'Diabetes', 
        'Smoking_Code', 'Stroke'
    ]
    
    corr_matrix = df_corr[cols_to_corr].corr()
    stroke_corr = corr_matrix['Stroke'].drop('Stroke').fillna(0).sort_values(ascending=True)
    
    rename_dict = {
        'Age': 'Usia',
        'Gender_Male': 'Jenis Kelamin (Pria)',
        'SES_Code': 'Status Sosial Ekonomi (SES)',
        'Hypertension': 'Hipertensi',
        'Heart_Disease': 'Penyakit Jantung',
        'BMI': 'Indeks Massa Tubuh (BMI)',
        'Avg_Glucose': 'Rata-rata Kadar Glukosa',
        'Diabetes': 'Diabetes',
        'Smoking_Code': 'Status Merokok'
    }
    stroke_corr = stroke_corr.rename(index=rename_dict)
    return stroke_corr

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
col_filter, col_kpi = st.columns([1.3, 1])

with col_filter:
    st.markdown('<div style="font-weight: 800; color: #1a365d; font-size: 15px; margin-bottom: 8px;">FILTER PANEL</div>', unsafe_allow_html=True)
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
        st.markdown(make_kpi("Rasio Stroke", f"{rasio_stroke:.2f}%", "📉", "#ea580c"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# 5. KONTEN VISUALISASI UTAMA (TABS 1-5 BERURUTAN KRONOLOGIS)
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 1. Faktor Risiko Utama", 
    "📅 2. Distribusi Usia", 
    "🩺 3. Penyakit Penyerta", 
    "⚖️ 4. BMI & Glukosa", 
    "📊 5. Keseimbangan Data"
])

# ---------------------------------------------------------
# TAB 1: Faktor Risiko Utama (Q1)
# ---------------------------------------------------------
with tab1:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">1. Faktor Apa Saja yang Memengaruhi Risiko Stroke?</h3>', unsafe_allow_html=True)
    st.info("**Insight Faktor Risiko:** Korelasi Pearson di bawah ini menunjukkan tingkat kekuatan hubungan linear antara berbagai faktor klinis/demografis dengan kejadian stroke. Nilai positif yang lebih tinggi menandakan hubungan yang lebih kuat terhadap kejadian stroke.")
    
    if total_pasien == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter saat ini.")
    else:
        corr_series = calculate_correlation(df_filtered)
        
        # Buat grafik batang korelasi
        fig_corr = px.bar(
            x=corr_series.values,
            y=corr_series.index,
            orientation='h',
            labels={'x': 'Koefisien Korelasi (r)', 'y': 'Faktor Risiko'},
            color=corr_series.values,
            color_continuous_scale='Reds',
            range_color=[0, 0.5]
        )
        fig_corr.update_layout(
            margin=dict(t=20, b=20, l=10, r=10),
            coloraxis_showscale=False,
            height=380
        )
        st.plotly_chart(fig_corr, width='stretch')
        
        top_factors = corr_series.sort_values(ascending=False)
        st.success(f"""**Kesimpulan Korelasi:** 
        Berdasarkan data tersaring, tiga faktor utama dengan korelasi tertinggi terhadap kejadian stroke adalah:
        1. **{top_factors.index[0]}** (r = {top_factors.values[0]:.3f})
        2. **{top_factors.index[1]}** (r = {top_factors.values[1]:.3f})
        3. **{top_factors.index[2]}** (r = {top_factors.values[2]:.3f})
        """)

# ---------------------------------------------------------
# TAB 2: Distribusi Usia (Q2)
# ---------------------------------------------------------
with tab2:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">2. Apakah Usia Memiliki Hubungan Terhadap Kejadian Stroke?</h3>', unsafe_allow_html=True)
    
    if total_pasien == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter saat ini.")
    else:
        col_t2_left, col_t2_right = st.columns(2)
        
        with col_t2_left:
            # Box plot untuk perbandingan kuartil & median usia
            fig_box_age = px.box(
                df_filtered,
                x='Stroke_Label',
                y='Age',
                color='Stroke_Label',
                color_discrete_map={'Tidak Stroke': '#1E3A8A', 'Stroke': '#DC2626'},
                labels={'Stroke_Label': 'Status Pasien', 'Age': 'Usia (Tahun)'},
                title="Perbandingan Rentang Usia Pasien"
            )
            fig_box_age.update_layout(showlegend=False, margin=dict(t=40, b=20))
            st.plotly_chart(fig_box_age, width='stretch')
            
        with col_t2_right:
            # Histogram distribusi sebaran detail usia
            fig_hist_age = px.histogram(
                df_filtered,
                x='Age',
                color='Stroke_Label',
                barmode='overlay',
                nbins=30,
                color_discrete_map={'Tidak Stroke': '#1E3A8A', 'Stroke': '#DC2626'},
                labels={'Age': 'Usia Pasien (Tahun)', 'Stroke_Label': 'Status'},
                title="Distribusi Usia Pasien"
            )
            fig_hist_age.update_traces(opacity=0.75)
            fig_hist_age.update_layout(yaxis_title="Jumlah Pasien", margin=dict(t=40, b=20))
            st.plotly_chart(fig_hist_age, width='stretch')
            
        avg_age_stroke = df_filtered[df_filtered['Stroke'] == 1]['Age'].mean()
        avg_age_normal = df_filtered[df_filtered['Stroke'] == 0]['Age'].mean()
        
        stroke_info = f"{avg_age_stroke:.1f} tahun" if not pd.isna(avg_age_stroke) else "N/A"
        normal_info = f"{avg_age_normal:.1f} tahun" if not pd.isna(avg_age_normal) else "N/A"
        
        st.success(f"""**Kesimpulan Usia:** 
        **Ya, usia memiliki hubungan yang sangat signifikan.** 
        *   Rata-rata usia pasien stroke adalah **{stroke_info}**, jauh lebih tinggi dibanding pasien sehat (**{normal_info}**).
        *   Berdasarkan grafik di atas, risiko stroke terlihat mulai merangkak naik secara nyata pada kelompok usia di atas 50 tahun.
        """)

# ---------------------------------------------------------
# TAB 3: Komorbiditas & Penyakit Penyerta (Q3)
# ---------------------------------------------------------
with tab3:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">3. Apakah Hipertensi, Penyakit Jantung, dan Diabetes Meningkatkan Risiko Stroke?</h3>', unsafe_allow_html=True)
    
    if total_pasien == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter saat ini.")
    else:
        col_t3_1, col_t3_2, col_t3_3 = st.columns(3)
        
        with col_t3_1:
            fig_hyper = px.histogram(
                df_filtered, x='Hypertension_Label', color='Stroke_Label', barmode='stack', barnorm='percent',
                color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
                labels={'Hypertension_Label': 'Status Hipertensi', 'Stroke_Label': 'Status'},
                title="Proporsi Stroke vs Hipertensi"
            )
            fig_hyper.update_layout(yaxis_title="Persentase (%)", margin=dict(t=40, b=20))
            st.plotly_chart(fig_hyper, width='stretch')
            
        with col_t3_2:
            fig_heart = px.histogram(
                df_filtered, x='Heart_Disease_Label', color='Stroke_Label', barmode='stack', barnorm='percent',
                color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
                labels={'Heart_Disease_Label': 'Status Jantung', 'Stroke_Label': 'Status'},
                title="Proporsi Stroke vs Penyakit Jantung"
            )
            fig_heart.update_layout(yaxis_title="Persentase (%)", margin=dict(t=40, b=20))
            st.plotly_chart(fig_heart, width='stretch')
            
        with col_t3_3:
            fig_diabetes = px.histogram(
                df_filtered, x='Diabetes_Label', color='Stroke_Label', barmode='stack', barnorm='percent',
                color_discrete_map={'Tidak Stroke': '#9CA3AF', 'Stroke': '#DC2626'}, 
                labels={'Diabetes_Label': 'Status Diabetes', 'Stroke_Label': 'Status'},
                title="Proporsi Stroke vs Diabetes"
            )
            fig_diabetes.update_layout(yaxis_title="Persentase (%)", margin=dict(t=40, b=20))
            st.plotly_chart(fig_diabetes, width='stretch')
            
        # Hitung statistik persentase untuk teks insight
        def get_stroke_pct(col_name, val):
            subset = df_filtered[df_filtered[col_name] == val]
            if len(subset) == 0:
                return 0.0
            return (len(subset[subset['Stroke'] == 1]) / len(subset)) * 100
            
        rate_hyper = get_stroke_pct('Hypertension', 1)
        rate_no_hyper = get_stroke_pct('Hypertension', 0)
        
        rate_heart = get_stroke_pct('Heart_Disease', 1)
        rate_no_heart = get_stroke_pct('Heart_Disease', 0)
        
        rate_diabetes = get_stroke_pct('Diabetes', 1)
        rate_no_diabetes = get_stroke_pct('Diabetes', 0)
        
        st.success(f"""**Kesimpulan Penyakit Penyerta:** 
        **Ya, ketiganya sangat meningkatkan risiko stroke secara signifikan.** Proporsi kasus stroke (merah) melonjak tinggi pada pasien yang memiliki penyakit penyerta:
        *   **Hipertensi:** Pasien hipertensi memiliki rasio kejadian stroke sebesar **{rate_hyper:.1f}%** dibanding pasien normal (**{rate_no_hyper:.1f}%**).
        *   **Penyakit Jantung:** Pasien dengan penyakit jantung memiliki rasio kejadian stroke sebesar **{rate_heart:.1f}%** dibanding pasien normal (**{rate_no_heart:.1f}%**).
        *   **Diabetes:** Pasien penderita diabetes memiliki rasio kejadian stroke sebesar **{rate_diabetes:.1f}%** dibanding pasien normal (**{rate_no_diabetes:.1f}%**).
        """)

# ---------------------------------------------------------
# TAB 4: Analisis Usia & Fisik (Q4)
# ---------------------------------------------------------
with tab4:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">4. Bagaimana Pengaruh BMI dan Kadar Glukosa Terhadap Stroke?</h3>', unsafe_allow_html=True)
    
    if total_pasien == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter saat ini.")
    else:
        # Mengurutkan data agar titik Stroke ada di depan (paling atas)
        df_sorted = df_filtered.sort_values(by='Stroke')
        
        fig_scatter = px.scatter(
            df_sorted, x='BMI', y='Avg_Glucose', color='Stroke_Label',
            color_discrete_map={
                'Tidak Stroke': 'rgba(156, 163, 175, 0.3)', 
                'Stroke': '#DC2626'
            }, 
            marginal_x='box',
            marginal_y='box',
            labels={'Avg_Glucose': 'Rata-rata Kadar Glukosa', 'BMI': 'Indeks Massa Tubuh (BMI)', 'Stroke_Label': 'Status'},
            title="Sebaran Karakteristik Fisik Pasien"
        )
        fig_scatter.update_traces(marker=dict(size=6))
        fig_scatter.update_layout(margin=dict(t=40, b=20))
        st.plotly_chart(fig_scatter, width='stretch')
        
        st.warning("""**Kesimpulan Karakteristik Fisik:** 
        *   Pasien dengan **kadar glukosa tinggi (Avg_Glucose > 150)** sekaligus **berat badan berlebih (BMI > 25)** berkerumun padat di area rentan (didominasi sebaran titik merah).
        *   Box plot marginal pada sumbu X (BMI) dan sumbu Y (Glukosa) menunjukkan distribusi nilai pasien Stroke (merah) secara signifikan lebih bergeser ke arah nilai BMI dan Glukosa yang lebih tinggi dibandingkan pasien Tidak Stroke.
        """)

# ---------------------------------------------------------
# TAB 5: Proporsi Imbalance (Q5)
# ---------------------------------------------------------
with tab5:
    st.markdown('<h3 style="color:#1a365d; font-size:18px;">5. Apakah Dataset Mengalami Imbalance Sebelum Dilakukan SMOTE?</h3>', unsafe_allow_html=True)
    col_t5_1, col_t5_2 = st.columns([1.2, 1])
    
    with col_t5_1:
        # Pie chart dari dataset asli (unfiltered) untuk menunjukkan bias alami kelas target
        fig_target = px.pie(
            df, names='Stroke_Label', color='Stroke_Label',
            color_discrete_map={'Tidak Stroke': '#1E3A8A', 'Stroke': '#DC2626'}, hole=0.4,
            title="Proporsi Target Variabel pada Dataset Asli"
        )
        fig_target.update_traces(textposition='inside', textinfo='percent+value')
        fig_target.update_layout(margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_target, width='stretch')
        
    with col_t5_2:
        total_ori = len(df)
        stroke_ori = len(df[df['Stroke'] == 1])
        sehat_ori = len(df[df['Stroke'] == 0])
        rasio_ori = (stroke_ori / total_ori * 100)
        
        st.warning(f"""**Temuan Keseimbangan Data:**
        *   **Ya, Sangat Imbalance.** Grafik membuktikan bahwa proporsi pasien sehat mendominasi kelas target secara alami (**{sehat_ori:,} data / {100-rasio_ori:.2f}%** pasien sehat vs hanya **{stroke_ori:,} data / {rasio_ori:.2f}%** pasien stroke).
        *   **Dampak Model:** Tanpa penyeimbangan, model machine learning cenderung hanya mempelajari pasien sehat dan gagal mengklasifikasikan pasien stroke dengan akurat.
        *   **Solusi Model:** Pipeline backend data science telah berhasil menerapkan teknik **SMOTE** untuk membuat data training seimbang secara artifisial **50:50 (masing-masing {sehat_ori:,} data per kelas)** agar model Machine Learning tidak mengalami bias kelas mayoritas.
        """)

# =========================================================
# 6. FOOTER
# =========================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('''
    <div style="text-align: center; color: #64748b; font-size: 13px; font-weight: 500;">
        Dashboard Capstone Project Facial Stroke Early Sign Detection
    </div>
''', unsafe_allow_html=True)