import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static
from google.cloud import bigquery
from google.oauth2 import service_account

key_path = r"C:\Users\91709\Downloads\cloud-data-mining-452605-a424243a7207.json"
credentials = service_account.Credentials.from_service_account_file(key_path)

client = bigquery.Client(credentials=credentials, project='cloud-data-mining-452605')

@st.cache_data
def load_data():
    query = """
    SELECT * FROM `cloud-data-mining-452605.crash_locations_sj.crash_locations`
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()  

df = load_data()

st.title('San Jose Crash Data Visualization')

if df.empty:
    st.warning("No data loaded. Please check your permissions or table name.")
else:
  
    df['CRASHDATETIME'] = pd.to_datetime(df['CRASHDATETIME'])
    df['CRASH_HOUR'] = df['CRASHDATETIME'].dt.hour

    st.sidebar.header("Filters")

    years_available = sorted(df['YEAR'].dropna().unique())
    selected_year = st.sidebar.selectbox("Select Year", years_available)
    
    hour_filter = st.sidebar.slider('Select Hour Range', 0, 23, (0, 23))

    weather_conditions = df['WEATHER'].dropna().unique()
    selected_weather = st.sidebar.multiselect("Select Weather Conditions", weather_conditions, default=weather_conditions)

    filtered_data = df[
        (df['YEAR'] == selected_year) & 
        (df['CRASH_HOUR'] >= hour_filter[0]) & 
        (df['CRASH_HOUR'] <= hour_filter[1]) & 
        (df['WEATHER'].isin(selected_weather))
    ]

    st.write(f"Filtered Data: {len(filtered_data)} crashes found.")

    st.subheader('Crash Frequency by Hour')
    plt.figure(figsize=(10, 5))
    sns.countplot(x='CRASH_HOUR', data=filtered_data, palette='viridis')
    plt.xlabel('Hour of the Day')
    plt.ylabel('Number of Crashes')
    plt.title('Crashes by Hour')
    st.pyplot(plt)

    st.subheader('Crash Distribution by Severity')
    plt.figure(figsize=(10, 5))
    sns.countplot(x='INJURYSEVERITY', data=filtered_data, palette='magma')
    plt.xlabel('Crash Severity')
    plt.ylabel('Number of Crashes')
    plt.title('Crash Distribution by Severity')
    plt.xticks(rotation=45)
    st.pyplot(plt)

    st.subheader('Weather Impact on Crashes')
    plt.figure(figsize=(10, 5))
    sns.countplot(y='WEATHER', data=filtered_data, palette='coolwarm', order=df['WEATHER'].value_counts().index)
    plt.xlabel('Number of Crashes')
    plt.ylabel('Weather Condition')
    plt.title('Crashes by Weather Condition')
    st.pyplot(plt)

    st.subheader("Crash Locations Heatmap")
    if not filtered_data.empty:
        crash_map = folium.Map(location=[37.3382, -121.8863], zoom_start=12)
        for _, row in filtered_data.iterrows():
            folium.CircleMarker(
                location=[row.get('LATITUDE', 37.3382), row.get('LONGITUDE', -121.8863)], 
                radius=5, color='red', fill=True
            ).add_to(crash_map)
        folium_static(crash_map)
    else:
        st.write("No crash data available for the selected filters.")

    if st.checkbox('Show Raw Data'):
        st.subheader('Raw Data')
        st.write(filtered_data)
