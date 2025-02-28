import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon

def gerar_setor(lat, lon, azimute, alcance, abertura=120):
    """
    Gera os pontos do setor da célula GSM.
    """
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))  # Fechar o setor
    return pontos

def main():
    st.set_page_config(layout="wide")
    st.subheader("GSM Sector View")
    st.markdown(":blue[**_©2025   NAIIC CTer Santarém_**]")
    
    # Coordenadas padrão
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3.0
    
    # Definição de cores para os setores
    cores = ["blue", "red", "green"]
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        lat = st.number_input("Latitude da BTS", value=lat_default, format="%.6f")
    with col2:
        lon = st.number_input("Longitude da BTS", value=lon_default, format="%.6f")
    with col4:
        alcance = st.number_input("Alcance (km)", value=alcance_default, format="%.1f", step=0.1)
    with col5:
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "Híbrido"])
    
    # Seleção de até três setores
    setores = []
    for i in range(3):
        with st.expander(f"Configuração do Setor {i+1}"):
            ativo = st.checkbox(f"Ativar Setor {i+1}", value=(i == 0))
            if ativo:
                azimute = st.slider(f"Azimute Setor {i+1}", 0, 360, azimute_default + i * 120)
                setores.append((azimute, cores[i]))
    
    # Definição do tipo de mapa
    tiles = "CartoDB positron" if mapa_tipo == "Padrão" else "Esri WorldImagery"
    mapa = folium.Map(location=[lat, lon], zoom_start=14, tiles=tiles)
    folium.Marker([lat, lon], tooltip="BTS").add_to(mapa)
    
    # Adicionar setores ao mapa
    for azimute, cor in setores:
        setor_coords = gerar_setor(lat, lon, azimute, alcance)
        folium.Polygon(
            locations=setor_coords,
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
