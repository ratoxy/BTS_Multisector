import folium
import numpy as np
import streamlit as st
from streamlit_folium import folium_static
from shapely.geometry import Polygon
import string

def gerar_celula(lat, lon, azimute, alcance, abertura=120):
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))  # Fechar a célula
    return pontos

def gerar_grelha(area_coberta, espaco):
    min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
    linhas = []
    etiquetas = []
    letras = string.ascii_uppercase
    
    lon_range = np.arange(min_lon, max_lon, espaco)
    lat_range = np.arange(max_lat, min_lat, -espaco)

    for lon in lon_range:
        linhas.append([(min_lat, lon), (max_lat, lon)])
    for lat in lat_range:
        linhas.append([(lat, min_lon), (lat, max_lon)])

    perimetro = [
        (min_lat, min_lon), (min_lat, max_lon),
        (max_lat, max_lon), (max_lat, min_lon),
        (min_lat, min_lon)
    ]
    
    for row_index, lat in enumerate(lat_range[:-1]):  
        for col_index, lon in enumerate(lon_range[:-1]):
            col_label = letras[col_index % len(letras)]
            if col_index >= len(letras):
                col_label = letras[col_index // len(letras) - 1] + col_label
            etiqueta = f"{col_label}{row_index + 1}"
            etiquetas.append(((lat - espaco / 2, lon + espaco / 2), etiqueta))
    
    return linhas, etiquetas, perimetro

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("_Multi Cell View_")
    st.sidebar.markdown(":blue[**_©2025 NAIIC CTer Santarém_**]")
    st.sidebar.subheader("Configuração do Mapa")

    cores = ["blue", "red", "green"]
    
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3.0

    mapa_tipo = st.sidebar.selectbox("Tipo de mapa", ["Padrão", "Satélite", "OpenStreetMap"])
    mostrar_grelha = st.sidebar.checkbox("Mostrar Grelha", value=False)
    
    col_g1, col_g2, col_g3 = st.sidebar.columns([1, 1, 1])
    with col_g1:
        tamanho_quadricula = st.number_input("Tamanho (m)", value=500, step=100)
    with col_g2:
        cor_grelha = st.color_picker("Cor", "#FFA500")
    
    st.sidebar.subheader("Configuração das Células")
    alcance = st.sidebar.slider("Alcance Geral (km)", 1, 20, alcance_default)
    celulas = []
    area_coberta = None

    for i in range(3):
        ativo = st.sidebar.checkbox(f"Ativar Célula {i+1}", value=(i == 0))
        if ativo:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                lat = st.number_input(f"Lat {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
            with col2:
                lon = st.number_input(f"Lon {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
            
            azimute = st.sidebar.slider(f"Azimute {i+1}", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")
            celulas.append((lat, lon, azimute, cores[i]))

            poligono = Polygon(gerar_celula(lat, lon, azimute, alcance))
            area_coberta = poligono if area_coberta is None else area_coberta.union(poligono)

    tiles_dict = {
        "Padrão": "CartoDB positron",
        "Satélite": "Esri WorldImagery",
        "OpenStreetMap": "OpenStreetMap"
    }
    
    tiles = tiles_dict[mapa_tipo]
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

    if mostrar_grelha and area_coberta is not None:
        grelha, etiquetas, perimetro = gerar_grelha(area_coberta, tamanho_quadricula / 111000)
        for linha in grelha:
            folium.PolyLine(linha, color=cor_grelha, weight=2, opacity=0.9).add_to(mapa)
        for (pos, label) in etiquetas:
            folium.Marker(pos, icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: {cor_grelha};">{label}</div>')).add_to(mapa)
        folium.PolyLine(perimetro, color=cor_grelha, weight=4, opacity=1).add_to(mapa)

    if area_coberta:
        mapa.fit_bounds(area_coberta.bounds)

    folium.LayerControl().add_to(mapa)
    st.components.v1.html(mapa._repr_html_(), height=900)

if __name__ == "__main__":
    main()
