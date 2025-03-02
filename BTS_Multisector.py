import streamlit as st
import folium
from streamlit_folium import folium_static

def main():
    mapa = folium.Map(location=[39.2369, -8.6807], zoom_start=13)
    folium_static(mapa)

if __name__ == "__main__":
    main()
