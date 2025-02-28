import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon
import string

def gerar_celula(lat, lon, azimute, alcance, abertura=120):
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))
    return pontos

def main():
    st.set_page_config(layout="wide")

    # CSS para ajustar dinamicamente a largura do mapa quando a sidebar está aberta ou fechada
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            transition: width 0.3s ease-in-out;
        }
        iframe {
            position: fixed;
            top: 0;
            left: 0;
            width: calc(100% - 300px);
            height: 100vh;
            border: none;
            transition: width 0.3s ease-in-out;
        }
        @media (max-width: 768px) {
            iframe {
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.subheader("Configuração do Mapa")
    st.markdown(":blue[**_©2025 NAIIC CTer Santarém_**]")

    cores = ["blue", "red", "green"]
    
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3.0

    col1, col2 = st.sidebar.columns(2)
    with col1:
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "Híbrido"])
    with col2:
        alcance = st.number_input("Alcance (km)", value=alcance_default, format="%.1f", step=0.1)

    st.sidebar.markdown("### Configuração das Células")
    celulas = []

    for i in range(3):
        ativo = st.sidebar.checkbox(f"Célula {i+1}", value=(i == 0))
        if ativo:
            col1, col2, col3 = st.sidebar.columns([1, 1, 1])
            with col1:
                lat = st.number_input(f"Lat {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
            with col2:
                lon = st.number_input(f"Lon {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
            with col3:
                azimute = st.slider(f"Az {i+1}", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")

            celulas.append((lat, lon, azimute, cores[i]))

    tiles = "CartoDB positron" if mapa_tipo == "Padrão" else "Esri WorldImagery"
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=13, tiles=tiles)

    for lat, lon, azimute, cor in celulas:
        folium.Marker([lat, lon], tooltip=f"BTS {lat}, {lon}").add_to(mapa)
        celula_coords = gerar_celula(lat, lon, azimute, alcance)
        folium.Polygon(
            locations=celula_coords,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.3
        ).add_to(mapa)

    st.components.v1.html(mapa._repr_html_(), height=0, scrolling=False)

if __name__ == "__main__":
    main()
