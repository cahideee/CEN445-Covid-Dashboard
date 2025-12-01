import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
# Altair ve Numpy importları kaldırılmıştır.

# --- PAGE SETTINGS ---
st.set_page_config(page_title="COVID-19 Europe Data Dashboard", page_icon="📈", layout="wide")

# --- CSS (Minimalist and Simplified) ---
st.markdown("""
<style>
    .main { background-color: #f8f8f8; }
    .block-container { padding-top: 1rem; }
    h2 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- MAIN HEADER ---
st.title("COVID-19 Europe Data Visualization & Analysis")
st.caption("Dashboard for Presentation by Mehmet Şah Zengin")
st.divider()

# --- SIDEBAR (Data Loading) ---
with st.sidebar:
    st.title("Data Control")
    uploaded_file = st.file_uploader("Upload CSV Data", type=["csv"])
    
    DATE_COL_NAME = "date"
    COUNTRY_COL_NAME = "location"

df = pd.DataFrame()
df_filtered = pd.DataFrame()
columns = []

if uploaded_file:
    @st.cache_data
    def load_data(file):
        try:
            temp_df = pd.read_csv(file)
            required_cols = [DATE_COL_NAME, COUNTRY_COL_NAME, 'total_cases', 'total_deaths', 'new_cases', 'new_deaths']
            for col in required_cols:
                if col not in temp_df.columns:
                    st.error(f"Error: Missing required column '{col}'. Please ensure your CSV file contains these exact columns.")
                    return None
            
            # Fill NaN values with 0 (Clean data)
            temp_df['new_cases'] = temp_df['new_cases'].fillna(0)
            temp_df['new_deaths'] = temp_df['new_deaths'].fillna(0)
            temp_df['total_cases'] = temp_df['total_cases'].fillna(0)
            temp_df['total_deaths'] = temp_df['total_deaths'].fillna(0)

            return temp_df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None

    df_base = load_data(uploaded_file)

    if df_base is not None:
        df = df_base.copy()
        
        # --- DATE PROCESSING AND NEW METRIC CALCULATION ---
        try:
            df[DATE_COL_NAME] = pd.to_datetime(df[DATE_COL_NAME], errors='coerce')
            df = df.dropna(subset=[DATE_COL_NAME])
            
            # CFR Calculation: Case Fatality Ratio
            df['CFR'] = (df['total_deaths'] / df['total_cases']) * 100
            df['CFR'] = df['CFR'].fillna(0) 

        except Exception as e:
            st.error(f"Date column ('{DATE_COL_NAME}') or CFR calculation could not be processed.")
            df = pd.DataFrame() 

    if not df.empty:
        # --- AUTOMATIC COLUMN CREATION (For Hierarchy) ---
        df["Yıl"] = df[DATE_COL_NAME].dt.year.astype(str)
        df["Ay"] = df[DATE_COL_NAME].dt.month_name(locale='en_US.utf8') 
        
        # New Column: Week of the Month
        df['Ayın Haftası'] = ((df[DATE_COL_NAME].dt.day - 1) // 7 + 1).astype(str) + '. Week'
        
        columns = df.columns.tolist()
        df_filtered = df.copy()

        # --- FILTER PANELS ---
        st.sidebar.subheader("Filter Data")
        
        # 1. Date Range Filter
        with st.sidebar:
            min_d, max_d = df[DATE_COL_NAME].min().date(), df[DATE_COL_NAME].max().date()
            dates = st.date_input(
                "Date Range Filter (All Charts)", 
                value=(min_d, max_d), 
                min_value=min_d, 
                max_value=max_d
            )
            if isinstance(dates, tuple) and len(dates) == 2:
                df_filtered = df_filtered[
                    (df_filtered[DATE_COL_NAME].dt.date >= dates[0]) & 
                    (df_filtered[DATE_COL_NAME].dt.date <= dates[1])
                ]
            
        # 2. Country/Location Filter 
        with st.sidebar:
            uniques = df[COUNTRY_COL_NAME].unique().tolist()
            
            # Default list: Spain removed as requested
            default_countries = ['Turkey', 'Germany', 'Italy', 'France', 'United Kingdom']
            
            valid_defaults = [c for c in default_countries if c in uniques]
            
            sel_countries = st.multiselect(
                "Select Countries", 
                uniques, 
                default=valid_defaults if valid_defaults else uniques[:5] 
            )
            if sel_countries: 
                df_filtered = df_filtered[df_filtered[COUNTRY_COL_NAME].isin(sel_countries)]

        st.divider()

        # --- CHART AREA ---
        st.header("Presentation Charts")

        # =========================================================================
        # 1. LINE CHART (CFR) - PLOTLY
        # =========================================================================
        st.subheader("1. Case Fatality Ratio (CFR) Over Time")
        
        if not df_filtered.empty:
            fig_line = px.line(
                df_filtered,
                x=DATE_COL_NAME, 
                y='CFR', 
                color=COUNTRY_COL_NAME,
                title="Cumulative Case Fatality Ratio (%) by Country"
            )
            fig_line.update_layout(
                xaxis_title="Date", 
                yaxis_title="Case Fatality Ratio (%)",
                yaxis_tickformat=".2f" 
            )
            fig_line.update_traces(hovertemplate='%{y:.2f}%')

            st.plotly_chart(fig_line, use_container_width=True)
            
            # ANALYTICAL INTERPRETATION
            st.markdown("### 🔍 Key Takeaways: CFR Line Chart")
            st.markdown(r"""
                * **Severity Trend:** The CFR trend indicates how the proportion of total cases resulting in death has evolved. A **falling CFR** over time often suggests improvements in medical treatment, better patient management, or increased testing (catching milder cases).
                * **Cross-Country Comparison:** **Significant gaps** between country lines highlight differences in national health strategies, testing regimes, demographic structures (e.g., population age), or the point at which severe waves hit.
                * **Initial Shock:** Expect the CFR to be **highest at the beginning** of the pandemic period due to low testing rates (only severe cases were confirmed).
            """)
            
        else:
            st.info("Please adjust sidebar filters to display data for the CFR Line Chart.")
            
        st.divider()

        # =========================================================================
        # 2. INTERACTIVE TREEMAP (Country -> Daily Cases) - PLOTLY
        # =========================================================================
        st.subheader("2. Interactive Treemap: Weekly Case Load and Daily Breakdown")
        
        # --- Weekly Treemap Data Preparation ---
        if not df_filtered.empty:
            
            # Weekly analysis start date selection
            available_dates = df_filtered[DATE_COL_NAME].dt.date.unique()
            max_date_treemap = df_filtered[DATE_COL_NAME].max().date()
            
            # Date Picker
            col_t1, col_t2 = st.columns([1, 4])
            with col_t1:
                selected_start_date = st.date_input(
                    "Analysis Start Date (for Treemap Week)", 
                    value=max_date_treemap - pd.Timedelta(days=6), 
                    min_value=df_filtered[DATE_COL_NAME].min().date(),
                    max_value=max_date_treemap
                )
            
            # Filter for the 7-day period
            end_date = selected_start_date + pd.Timedelta(days=6)
            
            df_week = df_filtered[
                (df_filtered[DATE_COL_NAME].dt.date >= selected_start_date) & 
                (df_filtered[DATE_COL_NAME].dt.date <= end_date)
            ].copy()
            
            with col_t2:
                st.info(f"Treemap analysis period: **{selected_start_date}** to **{end_date}**.")

            # Hierarchy column creation (Country -> Day)
            df_week['Day_of_Week'] = df_week[DATE_COL_NAME].dt.strftime('%a, %Y-%m-%d')
            
            # Treemap uses new_cases
            df_treemap = df_week[[COUNTRY_COL_NAME, 'Day_of_Week', 'new_cases']].copy()
            
            if not df_treemap.empty and df_treemap['new_cases'].sum() > 0:
                
                fig_treemap = px.treemap(
                    df_treemap,
                    # Hierarchy Path: Starts directly with Country
                    path=[COUNTRY_COL_NAME, 'Day_of_Week'], 
                    values='new_cases', 
                    color=COUNTRY_COL_NAME, 
                    title=f"Weekly Case Load Distribution: {selected_start_date} - {end_date}"
                )
                
                # Display absolute value and percent parent
                fig_treemap.update_traces(textinfo="label+value+percent parent") 

                fig_treemap.update_layout(margin = dict(t=50, l=25, r=25, b=25))
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.info(f"No sufficient 'new_cases' data found for the selected weekly period ({selected_start_date} - {end_date}) in the Treemap.")

            # ANALYTICAL INTERPRETATION
            st.markdown("### 🔍 Key Takeaways: Treemap")
            st.markdown(r"""
                * **Weekly Burden:** The size of the largest country tiles indicates where the pandemic's **case growth** was most concentrated during the selected week. This identifies immediate areas of concern.
                * **Daily Volatility (Drill-Down):** Clicking a country tile shows the **daily distribution of cases** within that week. Volatility in these daily figures (e.g., a huge spike on one day) may indicate data reporting delays or a specific local event that caused a temporary surge.
                * **Week-to-Week Consistency:** Comparing the size of the top countries across different weeks helps determine if the pandemic burden is shifting or consistently impacting the same regions.
            """)
        else:
            st.info("Please adjust sidebar filters to display data for the Treemap.")

        st.divider()


        # =========================================================================
        # 3. SUNBURST CHART (Country → Month → Week) - PLOTLY
        # =========================================================================
        st.subheader("3. Sunburst Chart: Death Hierarchy (Country -> Month -> Week of Month)")
        
        if not df_filtered.empty:
            df_sunburst = df_filtered[df_filtered['new_deaths'] > 0].dropna(subset=['new_deaths'])

            if not df_sunburst.empty:
                try:
                    fig_sunburst = px.sunburst(
                        df_sunburst,
                        # Hierarchy Path: Country -> Month -> Week of Month
                        path=[COUNTRY_COL_NAME, "Ay", "Ayın Haftası"], 
                        values='new_deaths', 
                        color=COUNTRY_COL_NAME, 
                        title="Daily Death Hierarchy: Country > Month > Week of Month"
                    )
                    fig_sunburst.update_traces(textinfo="label+percent entry")
                    st.plotly_chart(fig_sunburst, use_container_width=True)
                    
                    # ANALYTICAL INTERPRETATION
                    st.markdown("### 🔍 Key Takeaways: Sunburst Chart")
                    st.markdown(r"""
                        * **Overall Contribution:** The size of the outermost ring segments (Countries) immediately highlights the nations responsible for the largest portion of the **total deaths** over the filtered period.
                        * **Monthly Surges (Drill-Down):** Clicking on a country reveals the **monthly breakdown**. Large monthly segments pinpoint the specific time periods (months) when a country experienced its highest death rates.
                        * **Intra-Month Dynamics:** The final inner ring (**Week of Month**) reveals whether death peaks were confined to a single intense week or were sustained throughout the month, which is crucial for assessing the success of mid-month interventions.
                    """)
                    
                except ValueError as e:
                    st.error(f"Sunburst Chart Data Error: Check for negative or non-numeric values in 'new_deaths' column. Error: {e}")
            else:
                st.info("No daily death data found in the current selection for the Sunburst Chart (filtered for new_deaths > 0).")

else:
    st.info("Please upload your COVID-19 European data CSV file to start the analysis.")