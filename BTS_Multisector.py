import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon

def gerar_celula(lat, lon, azimute, alcance, abertura=120):
    """
    Gera os pontos da célula GSM.
    """
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))  # Fechar a célula
    return pontos

def main():
    st.set_page_config(layout="wide")
    st.subheader("GSM Cell View")
    st.markdown(":blue[**_©2025   NAIIC CTer Santarém_**]")
    
    # Definição de cores para as células
    cores = ["blue", "red", "green"]
    
    # Definição do ponto inicial
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3.0
    
    # Campo de alcance geral
    alcance = st.number_input("Alcance Geral (km)", value=alcance_default, format="%.1f", step=0.1)
    
    # Seleção de até três células
    celulas = []
    for i in range(3):
        with st.expander(f"Configuração da Célula {i+1}"):
            ativo = st.checkbox(f"Ativar Célula {i+1}", value=(i == 0))
            if ativo:
                lat = st.number_input(f"Latitude Célula {i+1}", value=lat_default, format="%.6f")
                lon = st.number_input(f"Longitude Célula {i+1}", value=lon_default, format="%.6f")
                azimute = st.slider(f"Azimute Célula {i+1}", 0, 360, azimute_default + i * 120)
                celulas.append((lat, lon, azimute, cores[i]))
    
    # Definição do tipo de mapa
    mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "Híbrido"])
    tiles = "CartoDB positron" if mapa_tipo == "Padrão" else "Esri WorldImagery"
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=14, tiles=tiles)
    
    # Adicionar células ao mapa
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
    
    # Adicionar camadas extras se for híbrido
    if mapa_tipo == "Híbrido":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Labels",
            overlay=True
        ).add_to(mapa)
    
    folium.LayerControl().add_to(mapa)
    st.components.v1.html(mapa._repr_html_(), height=900)

if __name__ == "__main__":
    main()
