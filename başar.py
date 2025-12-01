import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Covid-19 Avrupa Analizi", layout="wide", page_icon="🇪🇺")

st.title("🇪🇺 Avrupa Covid-19 Analiz Paneli")
st.markdown("""
**Analiz Kapsamı:**
1.  **Sankey:** Top 15 ülkenin hastalık seyri ve sonuç akışı.
2.  **Scatter:** Top 30 ülkenin vaka-ölüm-yaşlı nüfus korelasyonu (Çizim Özellikli).
3.  **Pie Chart:** Avrupa genelindeki vaka veya ölüm yükünün ülkelere göre dağılımı.
""")

# --- 1. VERİ YÜKLEME ---
FILE_PATH = 'owid-covid-data-europe-final.csv'

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(FILE_PATH)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("Veri dosyası bulunamadı.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    
    # --- GENEL VERİ HAZIRLIĞI ---
    df_latest = df.sort_values("date").groupby("location").tail(1)
    df_latest = df_latest[~df_latest['location'].isin(['Europe', 'International', 'World'])]
    
    # LİSTELER
    top_15_list = df_latest.nlargest(15, 'total_cases')['location'].tolist()
    top_30_list = df_latest.nlargest(30, 'total_cases')['location'].tolist()
    
    # VERİ SETLERİ
    df_sankey = df_latest[df_latest['location'].isin(top_15_list)]
    df_top30 = df_latest[df_latest['location'].isin(top_30_list)]

    st.divider()

    # =========================================================
    # 1. SANKEY GRAFİĞİ (Top 15)
    # =========================================================
    st.header("1. Sankey Diyagramı: Sonuç Analizi (İlk 15)")
    st.caption("ℹ️ **Görsel Not:** Kırmızı 'Vefat' çizgileri, sunumda daha net görülebilmesi için orantısal olarak **5 kat kalınlaştırılmıştır**.")
    
    country_labels = df_sankey['location'].tolist()
    outcome_labels = ["İYİLEŞEN / DİĞER", "VEFAT (ÖLÜM)"]
    all_labels = country_labels + outcome_labels
    idx_recovered = len(country_labels)
    idx_death = len(country_labels) + 1
    
    sources, targets, values, colors, custom_data = [], [], [], [], []
    DEATH_SCALE = 5 
    
    for i, (idx, row) in enumerate(df_sankey.iterrows()):
        cases = row['total_cases']
        deaths = row['total_deaths']
        recovered = cases - deaths
        sources.append(i); targets.append(idx_recovered); values.append(recovered); custom_data.append(recovered); colors.append("rgba(46, 204, 64, 0.4)")
        sources.append(i); targets.append(idx_death); values.append(deaths * DEATH_SCALE); custom_data.append(deaths); colors.append("rgba(255, 65, 54, 0.8)")

    fig_sankey = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_labels, color=["#1f77b4"]*len(country_labels) + ["#2ECC40", "#FF4136"]),
        link = dict(source=sources, target=targets, value=values, color=colors, customdata=custom_data, hovertemplate='Kaynak: %{source.label}<br>Hedef: %{target.label}<br>Gerçek Sayı: %{customdata:,.0f}<extra></extra>')
    )])
    fig_sankey.update_layout(height=600, font_size=12, title_text="Hastalık Seyri (Kırmızı Hatlar Vurgulanmıştır)")
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.divider()

    # =========================================================
    # 2. SCATTER PLOT (MANUEL ÇİZİM ÖZELLİKLİ)
    # =========================================================
    st.header("2. Scatter Plot: Vaka vs Ölüm (İlk 30)")
    
    col_scatter_opts, _ = st.columns([1, 3])
    with col_scatter_opts:
        show_trend = st.checkbox("📉 Otomatik Trend Çizgisini Göster (Mavi)")

    color_col = 'aged_65_older' if 'aged_65_older' in df.columns else None
    
    # Temel Grafik
    fig_scatter = px.scatter(
        df_top30, x="total_cases", y="total_deaths", color=color_col, size="total_deaths", hover_name="location", log_x=True, log_y=True,
        labels={"aged_65_older": "65+ Yaş Oranı (%)", "total_cases": "Toplam Vaka", "total_deaths": "Toplam Ölüm"},
        title="Vaka, Ölüm ve Yaşlı Nüfus İlişkisi", color_continuous_scale="Reds"
    )
    fig_scatter.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    
    # --- 1. OTOMATİK TREND ÇİZGİSİ (Seçilirse) ---
    if show_trend:
        df_trend = df_top30[(df_top30['total_cases'] > 0) & (df_top30['total_deaths'] > 0)]
        x_log = np.log10(df_trend['total_cases'])
        y_log = np.log10(df_trend['total_deaths'])
        m, b = np.polyfit(x_log, y_log, 1)
        x_range = np.linspace(x_log.min(), x_log.max(), 100)
        y_range = m * x_range + b
        x_line = 10**x_range
        y_line = 10**y_range
        
        fig_scatter.add_trace(
            go.Scatter(
                x=x_line, y=y_line, mode='lines', 
                name='Genel Trend',
                line=dict(color='blue', dash='dash', width=3) # Mavi ve daha kalın
            )
        )

    # --- 2. MANUEL ÇİZİM AYARLARI ---
    # Grafiğin üzerine çizilecek şekillerin rengini kırmızı yapıyoruz
    fig_scatter.update_layout(
        newshape=dict(line=dict(color='red', width=4)), # Çizgi Rengi: KIRMIZI
        dragmode=False # Varsayılan olarak çizim kapalı, menüden seçilecek
    )
    
    # Menüye "Çizgi Çiz" butonunu ekle
    config = {
        'modeBarButtonsToAdd': ['drawline', 'eraseshape'], # Çizgi çizme ve silme butonu
        'displaylogo': False
    }

    st.plotly_chart(fig_scatter, use_container_width=True, config=config)
    
    st.info("💡 **Nasıl Çizilir?** Grafiğin sağ üst köşesindeki menüde **'Çizgi (Draw Line)'** ikonuna tıklayın. Sonra mouse ile grafiğin üzerine basılı tutup kendi kırmızı trend çizginizi çekebilirsiniz! (Silmek için 'Erase Shape' ikonunu kullanın)")

    st.divider()

    # =========================================================
    # 3. PIE CHART (SEÇENEKLİ: VAKA veya ÖLÜM)
    # =========================================================
    st.header("3. Pie Chart: Avrupa Genel Dağılımı")
    st.caption("Aşağıdaki seçenekten grafiğin neyi göstereceğini değiştirebilirsiniz.")

    pie_option = st.radio(
        "Analiz Kriterini Seçiniz:",
        ["Toplam Vaka Dağılımı", "Toplam Ölüm Dağılımı"],
        horizontal=True
    )

    if pie_option == "Toplam Vaka Dağılımı":
        metric_col = "total_cases"
        chart_title = "Avrupa Toplam Vaka Pastası (Top 10 vs Diğerleri)"
        legend_title = "Ülkeler (Vaka Payı)"
    else:
        metric_col = "total_deaths"
        chart_title = "Avrupa Toplam Ölüm Pastası (Top 10 vs Diğerleri)"
        legend_title = "Ülkeler (Ölüm Payı)"

    df_sorted = df_latest.sort_values(by=metric_col, ascending=False)
    top_10_pie = df_sorted.head(10).copy()
    others_value = df_sorted.iloc[10:][metric_col].sum()
    others_df = pd.DataFrame([{'location': 'Diğer Ülkeler (Others)', metric_col: others_value}])
    df_pie_final = pd.concat([top_10_pie[['location', metric_col]], others_df], ignore_index=True)

    fig_pie = px.pie(
        df_pie_final,
        values=metric_col,
        names='location',
        title=chart_title,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=700, legend_title=legend_title)
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    if pie_option == "Toplam Vaka Dağılımı":
        st.info("💡 **Yorum:** Vaka dağılımında genellikle Rusya, İngiltere ve Fransa en büyük dilimleri alır.")
    else:
        st.info("💡 **Yorum:** Ölüm dağılımına geçtiğinizde dilimlerin boyutlarının değiştiğine dikkat edin.")

else:
    st.warning("Veri yüklenemedi.")