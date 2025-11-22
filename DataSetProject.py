import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DataViz Pro Ultra", page_icon="🌞", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .main { background-color: #fdfdfd; }
    .stButton>button { width: 100%; background-color: #2c3e50; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 Pro Kontrol")
    uploaded_file = st.file_uploader("CSV Yükle", type=["csv"])

st.title("🌍 Veri Görselleştirme Uzmanı")

if uploaded_file:
    @st.cache_data
    def load_data(file):
        return pd.read_csv(file)

    df = load_data(uploaded_file)
    df_filtered = df.copy()
    columns = df.columns.tolist()

    # --- TARİH İŞLEME VE FİLTRELEME ---
    with st.expander("🔍 Veri Filtreleme ve Tarih Ayarı", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            date_col = st.selectbox("Tarih Sütunu (Zorunlu)", [None] + columns)
            if date_col:
                # Tarihi datetime formatına çevir
                df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
                df_filtered = df_filtered.dropna(subset=[date_col])
                
                # --- OTOMATİK SÜTUN OLUŞTURMA (Sunburst İçin) ---
                # Tarih sütunundan Yıl ve Ay türetiyoruz
                df_filtered["Yıl"] = df_filtered[date_col].dt.year.astype(str)
                df_filtered["Ay"] = df_filtered[date_col].dt.month_name()
                
                # Listeye yeni türetilen sütunları ekleyelim ki seçebilesin
                columns = df_filtered.columns.tolist()

                if not df_filtered.empty:
                    min_d, max_d = df_filtered[date_col].min().date(), df_filtered[date_col].max().date()
                    dates = st.date_input("Tarih Aralığı", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                    if isinstance(dates, tuple) and len(dates) == 2:
                        df_filtered = df_filtered[(df_filtered[date_col].dt.date >= dates[0]) & (df_filtered[date_col].dt.date <= dates[1])]
        
        with col_f2:
            loc_filter_col = st.selectbox("Konum Filtresi", [None] + columns)
            if loc_filter_col:
                uniques = df[loc_filter_col].unique().tolist()
                sel = st.multiselect("Ülke Seçimi", uniques, default=uniques)
                if sel: df_filtered = df_filtered[df_filtered[loc_filter_col].isin(sel)]

    st.divider()

    # --- GRAFİK AYARLARI ---
    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.subheader("⚙️ Grafik Ayarları")
        
        chart_type = st.selectbox("Grafik Türü", 
            ["Scatter", "Line", "Bar", "Pie", "Histogram", 
             "Heatmap", "Treemap", "Sunburst (Güneş)", 
             "Sankey", "Network", "Geo Map"])

        # Değişkenler
        x_axis, y_axis, color_var = None, None, None
        sb_layer1, sb_layer2, sb_value = None, None, None

        # --- 1. SUNBURST ÖZEL AYARLARI (BURASI YENİLENDİ) ---
        if chart_type == "Sunburst (Güneş)":
            st.info("Katmanları içten dışa doğru seçin.")
            sb_layer1 = st.selectbox("1. Katman (İç Halka - Örn: Ülke)", columns)
            sb_layer2 = st.selectbox("2. Katman (Dış Halka - Örn: Yıl/Ay)", [None] + columns)
            sb_value = st.selectbox("Dilim Büyüklüğü (Örn: Ölüm Sayısı)", columns)
            
            st.caption("İpucu: Tarih sütunu seçtiyseniz listede 'Yıl' ve 'Ay' seçeneklerini görebilirsiniz.")

        # 2. Diğer Grafikler (Kısaltılmış Standart Kodlar)
        elif chart_type == "Heatmap":
            x_axis = st.selectbox("X Ekseni", columns)
            y_axis = st.selectbox("Y Ekseni", columns)
            color_var = st.selectbox("Yoğunluk Değeri", columns) # Z ekseni
        
        elif chart_type in ["Scatter", "Line", "Bar", "Pie", "Histogram"]:
            x_axis = st.selectbox("X Ekseni", columns)
            if chart_type != "Histogram": y_axis = st.selectbox("Y Ekseni", columns)
            color_var = st.selectbox("Renk", [None] + columns)
            
        # (Diğer grafik tiplerinin ayarları burada devam eder...)

    with col_right:
        st.subheader(f"📊 {chart_type} Analizi")

        # --- SUNBURST ÇİZİMİ ---
        if chart_type == "Sunburst (Güneş)" and sb_layer1 and sb_value:
            # Katman listesini oluştur
            path_list = [sb_layer1]
            if sb_layer2:
                path_list.append(sb_layer2)
            
            try:
                fig = px.sunburst(
                    df_filtered,
                    path=path_list, # [Ülke, Yıl] gibi
                    values=sb_value, # Ölüm sayısı
                    title=f"{' > '.join(path_list)} Hiyerarşisine Göre {sb_value} Dağılımı",
                    color=sb_layer1 # Renklendirmeyi ana katmana göre yap
                )
                # Yüzdeleri ve etiketleri göster
                fig.update_traces(textinfo="label+percent entry")
                st.plotly_chart(fig, use_container_width=True)
            except ValueError as e:
                st.error(f"Veri hatası: Seçilen sütunlarda negatif değerler veya bozuk veriler olabilir. Hata: {e}")

        # --- DİĞER GRAFİKLERİN ÇİZİMİ (Kısa Özet) ---
        elif chart_type == "Heatmap" and x_axis and y_axis and color_var:
            fig = px.density_heatmap(df_filtered, x=x_axis, y=y_axis, z=color_var, histfunc="sum", color_continuous_scale="Magma")
            st.plotly_chart(fig, use_container_width=True)
            
        elif x_axis:
            # Basit fallback çizim
            if chart_type == "Bar": fig = px.bar(df_filtered, x=x_axis, y=y_axis, color=color_var)
            elif chart_type == "Pie": fig = px.pie(df_filtered, names=x_axis, values=y_axis)
            elif chart_type == "Scatter": fig = px.scatter(df_filtered, x=x_axis, y=y_axis, color=color_var)
            # ...
            if 'fig' in locals(): st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Lütfen ayarları tamamlayın.")