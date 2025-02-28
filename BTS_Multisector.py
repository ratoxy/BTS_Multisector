import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon
from streamlit_folium import folium_static
import string

def gerar_celula(lat, lon, azimute, alcance, abertura=120, pontos=40):
    """Gera a área de cobertura da célula com mais pontos para suavidade."""
    pontos_lista = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=pontos):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos_lista.append((lat + dlat, lon + dlon))
    pontos_lista.append((lat, lon))  # Fechar a célula
    return pontos_lista

def col_label(n):
    """Gera rótulos de coluna estilo Excel (A, B, ..., Z, AA, AB, ...)."""
    label = ""
    while n >= 0:
        label = chr(n % 26 + ord('A')) + label
        n = n // 26 - 1
    return label

def gerar_grelha(area_coberta, espaco_m, cor_grelha):
    """Gera a grade fixa com rótulos contínuos e cor personalizável."""
    espaco = espaco_m / 111000  # Converter metros para graus aproximadamente
    min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
    
    linhas, etiquetas = [], []
    lon_range = np.arange(min_lon, max_lon + espaco, espaco)
    lat_range = np.arange(max_lat, min_lat - espaco, -espaco)
    
    for lon in lon_range:
        linhas.append([(min_lat, lon), (max_lat, lon)])
    for lat in lat_range:
        linhas.append([(lat, min_lon), (lat, max_lon)])
    
    for row_index, lat in enumerate(lat_range[:-1]):  
        for col_index, lon in enumerate(lon_range[:-1]):
            etiqueta = f"{col_label(col_index)}{row_index + 1}"
            etiquetas.append(((lat - espaco / 2, lon + espaco / 2), etiqueta))
    
    perimetro = [
        (min_lat, min_lon), (min_lat, max_lon),
        (max_lat, max_lon), (max_lat, min_lon),
        (min_lat, min_lon)
    ]
    
    return linhas, etiquetas, perimetro, cor_grelha

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("_Multi Cell View_")
    st.sidebar.markdown(":blue[**_©2025 NAIIC CTer Santarém_**]")
    
    cores = ["blue", "red", "green"]
    lat_default, lon_default = 39.2369, -8.6807
    azimute_default, alcance_default = 40, 3.0
    
    mapa_tipo = st.sidebar.selectbox("Tipo de mapa", ["Padrão", "Satélite", "OSM"])
    alcance = st.sidebar.number_input("Alcance (km)", value=alcance_default, format="%.1f", step=0.1)
    
    with st.sidebar.expander("Grelha"):
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            mostrar_grelha = st.checkbox("Mostrar", value=False)
        with col2:
            tamanho_grelha = st.number_input("Tamanho (m)", value=500, step=100, min_value=100, label_visibility="collapsed")
        with col3:
            cor_grelha = st.color_picker("Cor", "#FFA500", label_visibility="collapsed")
    
    st.sidebar.markdown("### Células")
    celulas = []
    area_coberta = None
    
    for i in range(3):
        ativo = st.sidebar.checkbox(f"Célula {i+1}", value=(i == 0))
        if ativo:
            lat = st.sidebar.number_input(f"Lat {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
            lon = st.sidebar.number_input(f"Lon {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
            azimute = st.sidebar.slider(f"Azimute {i+1}", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")
            celulas.append((lat, lon, azimute, cores[i]))
            poligono = Polygon(gerar_celula(lat, lon, azimute, alcance))
            area_coberta = poligono if area_coberta is None else area_coberta.union(poligono)
    
    tiles_dict = {"Padrão": "CartoDB positron", "Satélite": "Esri WorldImagery", "OSM": "OpenStreetMap"}
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=13, tiles=tiles_dict[mapa_tipo])
    
    for lat, lon, azimute, cor in celulas:
        folium.Marker([lat, lon], tooltip=f"BTS {lat}, {lon}").add_to(mapa)
        folium.Polygon(
            locations=gerar_celula(lat, lon, azimute, alcance),
            color=cor, fill=True, fill_color=cor, fill_opacity=0.3
        ).add_to(mapa)
    
    if mostrar_grelha and area_coberta is not None:
        grelha, etiquetas, perimetro, cor_grelha = gerar_grelha(area_coberta, tamanho_grelha, cor_grelha)
        for linha in grelha:
            folium.PolyLine(linha, color=cor_grelha, weight=2, opacity=0.9).add_to(mapa)
        for (pos, label) in etiquetas:
            folium.Marker(pos, icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: {cor_grelha};">{label}</div>')).add_to(mapa)
        folium.PolyLine(perimetro, color=cor_grelha, weight=4, opacity=1).add_to(mapa)
    
    st.markdown("<style>.stApp { height: 100vh; }</style>", unsafe_allow_html=True)
    folium_static(mapa, width=1400, height=800)

if __name__ == "__main__":
    main()
