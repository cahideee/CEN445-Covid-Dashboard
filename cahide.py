import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Cahide Keskin - Covid-19 Analizi", layout="wide", page_icon="🌍")

st.title("🌍 Avrupa Covid-19 Mekansal ve Oransal Analiz Paneli")
st.markdown("""
**Hazırlayan:** Cahide Keskin (2021555039)
**Analiz Kapsamı:**
1.  **Bar Chart:** Seçilen ülkelerin günlük verilerinin karşılaştırması.
2.  **Heatmap (Gelişmiş):** Mart 2020'den itibaren vaka yoğunluğu ve ölüm riski (CFR) analizi.
3.  **Geo Map:** Coğrafi dağılım haritası.
""")

# --- 1. VERİ YÜKLEME ---
FILE_PATH = 'owid-covid-data-europe-final.csv' 

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(FILE_PATH)
        df['date'] = pd.to_datetime(df['date'])
        
        # Sayısal verilerdeki boşlukları 0 ile doldur
        cols = ['new_cases', 'new_deaths', 'total_cases', 'total_deaths']
        for c in cols:
            if c in df.columns:
                df[c] = df[c].fillna(0)
        return df
    except FileNotFoundError:
        st.error(f"Veri dosyası ({FILE_PATH}) bulunamadı. Lütfen klasöre ekleyin.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    
    # --- YAN MENÜ (SIDEBAR) ---
    st.sidebar.header("⚙️ Grafik Ayarları")
    
    # 1. Ülke Seçimi (Bar Chart İçin)
    all_countries = sorted(df['location'].unique())
    selected_countries = st.sidebar.multiselect(
        "Zaman Analizi İçin Ülke Seçin:",
        all_countries,
        default=["Germany", "Italy", "United Kingdom"] # Orijinal varsayılanlar
    )
    
    # 2. Tarih Sınırları
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    # 3. Veri Tipi Seçimi
    data_type = st.sidebar.radio("Analiz Türü:", ["Vakalar (Cases)", "Ölümler (Deaths)"])
    
    # --- AYARLAR ---
    if data_type == "Vakalar (Cases)":
        daily_col = "new_cases"
        total_col = "total_cases"
        color_scale = "Blues"
        
        # Heatmap Ayarları
        hm_z_label = "Yoğunluk (%)"
        hm_colorscale = "Teal"
        
    else: # Ölümler seçiliyse
        daily_col = "new_deaths"
        total_col = "total_deaths"
        color_scale = "Reds"
        
        # Heatmap Ayarları (CFR)
        hm_z_label = "Ölüm Oranı (%)"
        hm_colorscale = "Reds" 

    st.divider()

    # =========================================================
    # 1. BAR CHART (Sütun Grafik) - DEĞİŞTİRİLMEDİ
    # =========================================================
    st.header(f"1. Günlük {data_type} Değişimi (Bar Chart)")
    st.caption("Bu grafik, seçilen ülkelerin günlük verilerini karşılaştırmalı olarak gösterir. Ani artışları (pik noktaları) tespit etmek için idealdir.")

    if selected_countries:
        df_bar = df[df['location'].isin(selected_countries)]
        
        fig_bar = px.bar(
            df_bar,
            x="date",
            y=daily_col,
            color="location",
            title=f"Seçilen Ülkelerde Günlük {data_type}",
            labels={"date": "Tarih", daily_col: "Sayı", "location": "Ülke"},
            barmode="group"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Lütfen sol menüden en az bir ülke seçiniz.")

    st.divider()

    # =========================================================
    # 2. HEATMAP (TARİH ARALIĞI MART 2020'DEN BAŞLATILDI)
    # =========================================================
    # Başlıklar
    if data_type == "Vakalar (Cases)":
        hm_title = "Zaman İçinde Salgın Dalgaları (Normalize Edilmiş)"
    else:
        hm_title = "Zaman İçinde Ölüm Riski / Oranı (Case Fatality Rate)"

    st.header(f"2. {hm_title}")
    
    # Heatmap için en çok vaka görülen 25 ülkeyi alalım
    top_25_countries = df.groupby('location')['total_cases'].max().nlargest(25).index.tolist()
    
    # --- TARİH FİLTRESİ (BURASI GÜNCELLENDİ) ---
    # Sadece 1 Mart 2020 ve sonrasını alıyoruz
    df_heatmap = df[
        (df['location'].isin(top_25_countries)) & 
        (df['date'] >= '2020-03-01')
    ].copy()
    
    # Veri İşleme
    df_heatmap = df_heatmap.sort_values(['location', 'date'])
    
    # 7 Günlük Ortalama (Yumuşatma)
    df_heatmap['smooth_cases'] = df_heatmap.groupby('location')['new_cases'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    df_heatmap['smooth_deaths'] = df_heatmap.groupby('location')['new_deaths'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    
    # HESAPLAMALAR
    if data_type == "Vakalar (Cases)":
        # Normalizasyon (0-100%)
        st.caption("ℹ️ **Not:** Bu harita nüfus farkını ortadan kaldırmak için **normalize** edilmiştir. (Veriler 1 Mart 2020'den başlar)")
        df_heatmap['z_value'] = df_heatmap.groupby('location')['smooth_cases'].transform(lambda x: x / x.max())
        
    else: # Ölümler
        # CFR (Ölüm Oranı) Hesabı
        st.caption("ℹ️ **Not:** Bu harita **Vaka Başına Ölüm Oranını (CFR)** gösterir. (Veriler 1 Mart 2020'den başlar)")
        
        df_heatmap['z_value'] = (df_heatmap['smooth_deaths'] / df_heatmap['smooth_cases']) * 100
        df_heatmap['z_value'] = df_heatmap['z_value'].replace([np.inf, -np.inf], 0).fillna(0)
        df_heatmap['z_value'] = df_heatmap['z_value'].clip(upper=15)

    # ÇİZİM
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=df_heatmap['z_value'],
        x=df_heatmap['date'],
        y=df_heatmap['location'],
        colorscale=hm_colorscale,
        colorbar=dict(title=hm_z_label)
    ))

    fig_heatmap.update_layout(
        xaxis_title="Tarih",
        yaxis_title="Ülke",
        height=700,
        xaxis={'showgrid': False},
        yaxis={'showgrid': False, 'dtick': 1}
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.divider()

    # =========================================================
    # 3. GEO MAP (Coğrafi Harita) - DEĞİŞTİRİLMEDİ
    # =========================================================
    st.header(f"3. Coğrafi Dağılım Haritası")
    
    col_slider, _ = st.columns([2, 1])
    with col_slider:
        selected_date_map = st.slider(
            "Harita Tarihini Seçin:",
            min_value=min_date,
            max_value=max_date,
            value=max_date
        )
    
    st.caption(f"Seçilen tarihteki ({selected_date_map}) toplam {data_type} yoğunluğu.")

    df_day = df[df['date'].dt.date == selected_date_map]
    df_day = df_day[df_day[total_col] > 0]

    fig_map = px.choropleth(
        df_day,
        locations="location",
        locationmode="country names",
        color=total_col,
        hover_name="location",
        scope="europe",
        color_continuous_scale=color_scale,
        title=f"Avrupa Geneli {data_type} Dağılımı",
        labels={total_col: f"Toplam {data_type}"}
    )
    
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=600)
    
    st.plotly_chart(fig_map, use_container_width=True)

    st.info("""
    💡 **Analiz Özeti:**
    * **Bar Chart:** Seçilen ülkelerin günlük sayılarını karşılaştırır.
    * **Heatmap:** Mart 2020'den itibaren salgın dalgalarını ve ölüm oranlarını (başarı/risk) gösterir.
    * **Map:** Virüsün coğrafi yayılımını gösterir.
    """)

else:
    st.warning("Veri yüklenemedi.")