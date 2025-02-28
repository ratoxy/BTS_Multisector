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
    
    # Linha para seleção do tipo de mapa e alcance
    col_mapa, col_alcance = st.columns([2, 1])
    with col_mapa:
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "Híbrido"])
    with col_alcance:
        alcance = st.number_input("Alcance Geral (km)", value=alcance_default, format="%.1f", step=0.1)
    
    # Seleção de até três células
    st.markdown("### Configuração das Células")
    colunas = st.columns(3)
    celulas = []
    for i, col in enumerate(colunas):
        with col:
            ativo = st.checkbox(f"Ativar Célula {i+1}", value=(i == 0))
            if ativo:
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    lat = st.number_input(f"Latitude {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
                with col_lon:
                    lon = st.number_input(f"Longitude {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
                azimute = st.slider(f"Azimute", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")
                celulas.append((lat, lon, azimute, cores[i]))
    
    # Configuração do mapa
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
