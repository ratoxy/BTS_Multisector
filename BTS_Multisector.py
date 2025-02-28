import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon, box
import string

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

def gerar_grelha(area_coberta, espaco=0.0045):
    """
    Gera uma grelha quadriculada de 500 metros sobre a área exata coberta pelos setores ativos, com rótulos alfanuméricos.
    """
    min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
    linhas = []
    etiquetas = []
    letras = string.ascii_uppercase
    
    lon_range = np.arange(min_lon, max_lon, espaco)
    lat_range = np.arange(max_lat, min_lat, -espaco)  # Invertendo para iniciar no canto superior esquerdo
    
    for lon in lon_range:
        linhas.append([(min_lat, lon), (max_lat, lon)])
    for lat in lat_range:
        linhas.append([(lat, min_lon), (lat, max_lon)])
    
    perimetro = [
        (min_lat, min_lon), (min_lat, max_lon),
        (max_lat, max_lon), (max_lat, min_lon),
        (min_lat, min_lon)
    ]
    
    for row_index, lat in enumerate(lat_range[:-1]):  # Evitar etiquetas fora dos limites
        for col_index, lon in enumerate(lon_range[:-1]):
            etiqueta = f"{letras[col_index % len(letras)]}{row_index + 1}"
            etiquetas.append(((lat - espaco / 2, lon + espaco / 2), etiqueta))
    
    return linhas, etiquetas, perimetro

def main():
    st.set_page_config(layout="wide")
    st.subheader("GSM Cell View")
    st.markdown(":blue[**_©2025   NAIIC CTer Santarém_**]")
    
    cores = ["blue", "red", "green"]
    
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3.0
    
    col_mapa, col_alcance, col_grelha = st.columns([1, 1, 1])
    with col_mapa:
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "Híbrido"])
    with col_alcance:
        alcance = st.number_input("Alcance Geral (km)", value=alcance_default, format="%.1f", step=0.1)
    with col_grelha:
        mostrar_grelha = st.checkbox("Mostrar Grelha", value=False)
    
    st.markdown("### Configuração das Células")
    colunas = st.columns(3)
    celulas = []
    area_coberta = None
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
                
                poligono = Polygon(gerar_celula(lat, lon, azimute, alcance))
                area_coberta = poligono if area_coberta is None else area_coberta.union(poligono)
    
    tiles = "CartoDB positron" if mapa_tipo == "Padrão" else "Esri WorldImagery"
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=14, tiles=tiles)
    
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
    
    if mostrar_grelha and area_coberta is not None:
        grelha, etiquetas, perimetro = gerar_grelha(area_coberta)
        for linha in grelha:
            folium.PolyLine(linha, color="orange", weight=2, opacity=0.9).add_to(mapa)
        for (pos, label) in etiquetas:
            folium.Marker(pos, icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: orange;">{label}</div>')).add_to(mapa)
        folium.PolyLine(perimetro, color="orange", weight=4, opacity=1).add_to(mapa)  # Contorno mais grosso
    
    mapa.fit_bounds(area_coberta.bounds)
    
    if mapa_tipo == "Híbrido":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Labels",
            overlay=True
        ).add_to(mapa)
    
    folium.LayerControl().add_to(mapa)
    st.components.v1.html(mapa._repr_html_(), height=700)

if __name__ == "__main__":
    main()
