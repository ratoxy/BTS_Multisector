import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon, MultiPolygon
import string
from streamlit_folium import folium_static

def gerar_celula(lat, lon, azimute, alcance, abertura):
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))
    return pontos

def gerar_rotulo_coluna(indice):
    letras = string.ascii_uppercase
    if indice < 26:
        return letras[indice]
    else:
        primeiro = letras[(indice // 26) - 1]
        segundo = letras[indice % 26]
        return primeiro + segundo

def gerar_grelha(area_coberta, tamanho_quadricula):
    if area_coberta is None:
        return [], [], []

    min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
    linhas = []
    etiquetas = []
    
    delta_lat = tamanho_quadricula / 111000
    
    lat_range = np.arange(max_lat, min_lat, -delta_lat)
    
    lon_range = []
    if lat_range.size > 0:
        delta_lon = tamanho_quadricula / (111000 * np.cos(np.radians((max_lat + min_lat) / 2)))
        lon_range = np.arange(min_lon, max_lon, delta_lon)
    
    for lat in lat_range:
        linhas.append([(lat, min_lon), (lat, max_lon)])
    
    for lon in lon_range:
        linhas.append([(min_lat, lon), (max_lat, lon)])

    perimetro = [(min_lat, min_lon), (min_lat, max_lon), (max_lat, max_lon), (max_lat, min_lon), (min_lat, min_lon)]

    for row_index, lat in enumerate(lat_range[:-1]):
        if lon_range.size > 0:
            delta_lon = tamanho_quadricula / (111000 * np.cos(np.radians(lat)))
            for col_index, lon in enumerate(lon_range[:-1]):
                coluna_label = gerar_rotulo_coluna(col_index)
                etiqueta = f"{coluna_label}{row_index + 1}"
                etiquetas.append(((lat - delta_lat / 2, lon + delta_lon / 2), etiqueta))

    return linhas, etiquetas, perimetro

def gerar_kml(celulas, grelha, etiquetas, perimetro, alcance, cor_grelha):
    kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
    kml += '<Document>\n'

    # Pasta Células
    kml += '<Folder><name>Células</name>\n'
    for lat, lon, azimute, cor in celulas:
        celula_coords = gerar_celula(lat, lon, azimute, alcance)
        kml += f'<Placemark><name>Célula {lat}, {lon}</name><styleUrl>#{cor}</styleUrl><Polygon><outerBoundaryIs><LinearRing><coordinates>'
        for lat, lon in celula_coords:
            kml += f'{lon},{lat},0 '
        kml += '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>\n'
        kml += f'<Style id="{cor}"><PolyStyle><color>7f{cor[5:7]}{cor[3:5]}{cor[1:3]}</color><fill>1</fill><outline>1</outline></PolyStyle></Style>\n' # Adiciona estilo para a cor com opacidade de 50%
    kml += '</Folder>\n'

    # Pasta Grelha
    kml += '<Folder><name>Grelha</name>\n'
    if grelha:
        kml += f'<Style id="grelha_style"><LineStyle><color>7f{cor_grelha[5:7]}{cor_grelha[3:5]}{cor_grelha[1:3]}</color></LineStyle><IconStyle><scale>0.1</scale></IconStyle></Style>\n'
        for linha in grelha:
            kml += f'<Placemark><name>Linha Grelha</name><styleUrl>#grelha_style</styleUrl><LineString><coordinates>'
            for lat, lon in linha:
                kml += f'{lon},{lat},0 '
            kml += '</coordinates></LineString></Placemark>\n'

        for (lat, lon), label in etiquetas:
            kml += f'<Placemark><name>{label}</name><styleUrl>#grelha_style</styleUrl><Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>\n' # Remove "Etiqueta Grelha"

        kml += f'<Placemark><name>Perímetro Grelha</name><styleUrl>#grelha_style</styleUrl><LineString><coordinates>'
        for lat, lon in perimetro:
            kml += f'{lon},{lat},0 '
        kml += '</coordinates></LineString></Placemark>\n'
    kml += '</Folder>\n'

    kml += '</Document>\n</kml>'
    return kml

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("_Multi Cell View_")
    st.sidebar.markdown(":blue[**_©2025 NAIIC CTer Santarém_**]")
    
    cores = ["blue", "red", "green"]
    
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3
    abertura_default = 120
    tamanho_quadricula_default = 500

    with st.sidebar.expander("Configuração Geral", expanded=True):
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "OpenStreetMap", "Terreno"])
        mostrar_grelha = st.toggle("Mostrar Grelha")
        tamanho_quadricula = st.slider("Tamanho da Quadricula (m)", 200, 1000, tamanho_quadricula_default, step=50)
        cor_grelha = st.color_picker("Cor da Grelha e Rótulos", "#FFA500")
    
    with st.sidebar.expander("Configuração das Células", expanded=True):
        alcance = st.slider("Alcance Geral (km)", 1, 20, alcance_default)
        abertura = st.slider("Abertura (graus)", 1, 360, abertura_default)
    
    celulas = []
    area_coberta = None

    for i in range(3):
        with st.sidebar.expander(f"Célula {i+1}", expanded=(i == 0)):
            ativo = st.checkbox(f"Ativar Célula {i+1}", value=(i == 0))
            if ativo:
                col1, col2 = st.columns(2)
                with col1:
                    lat = st.number_input(f"Lat {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
                with col2:
                    lon = st.number_input(f"Lon {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
                azimute = st.slider(f"Azimute {i+1}", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")
                celulas.append((lat, lon, azimute, cores[i]))
                poligono = Polygon(gerar_celula(lat, lon, azimute, alcance, abertura))
                area_coberta = poligono if area_coberta is None else area_coberta.union(poligono)

    tiles_dict = {
        "Padrão": "CartoDB positron",
        "Satélite": "Esri WorldImagery",
        "OpenStreetMap": "OpenStreetMap",
        "Terreno": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
    }

    # Recria o mapa a cada alteração
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=13, tiles=tiles_dict[mapa_tipo], attr="Esri WorldTopoMap")

    for lat, lon, azimute, cor in celulas:
        folium.Marker([lat, lon], tooltip=f"BTS {lat}, {lon}").add_to(mapa)
        celula_coords = gerar_celula(lat, lon, azimute, alcance, abertura)
        folium.Polygon(locations=celula_coords, color=cor, fill=True, fill_color=cor, fill_opacity=0.3).add_to(mapa)

    # Centraliza o mapa na área da grade (mesmo se a grade não estiver ativa)
    if area_coberta is not None:
        min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
        mapa.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    elif celulas:
        lats = [lat for lat, _, _, _ in celulas]
        lons = [lon for _, lon, _, _ in celulas]
        mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    if mostrar_grelha and area_coberta is not None:
        grelha, etiquetas, perimetro = gerar_grelha(area_coberta, tamanho_quadricula)
        for linha in grelha:
            folium.PolyLine(linha, color=cor_grelha, weight=2, opacity=0.9).add_to(mapa)
        for (pos, label) in etiquetas:
            folium.Marker(pos, icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: {cor_grelha};">{label}</div>')).add_to(mapa)
        folium.PolyLine(perimetro, color=cor_grelha, weight=4, opacity=1).add_to(mapa)

    folium.LayerControl().add_to(mapa)

    st.markdown(
        """
        <style>
            iframe {
                width: 100% !important;
                height: calc(100vh - 20px) !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    folium_static(mapa)

    # Botão de Exportação KML no final da barra lateral
    with st.sidebar:
        if st.button("Exportar para KML"):
            if celulas:
                if mostrar_grelha and area_coberta is not None:
                    grelha, etiquetas, perimetro = gerar_grelha(area_coberta, tamanho_quadricula)
                else:
                    grelha, etiquetas, perimetro = [], [], []

                kml_data = gerar_kml(celulas, grelha, etiquetas, perimetro, alcance, cor_grelha)
                st.download_button(
                    label="Download KML",
                    data=kml_data,
                    file_name="celulas_grelha.kml",
                    mime="application/vnd.google-earth.kml+xml"
                )

if __name__ == "__main__":
    main()
