import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Teste de Mapa")

mapa = folium.Map(location=[39.2369, -8.6807], zoom_start=13)
st_folium(mapa, use_container_width=True, height=700)
