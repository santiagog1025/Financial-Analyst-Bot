import streamlit as st
import requests
from streamlit.components.v1 import html

# URLs del backend
import os
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_URL_DATOS = f"http://{BACKEND_HOST}:8000/generar_datos/"
BACKEND_URL_PDF = f"http://{BACKEND_HOST}:8000/descargar_pdf/"

st.title("Generador de Reportes Financieros")

# Variables para almacenar los resultados
reporte_texto = None
ruta_figura = None
reporte_id = None

# Formulario de entrada
with st.form("form_reporte"):
    consulta = st.text_input(
        "Escribe la accion o el fondo del que quieras el reporte", 
        "Google"
    )
    submit_button = st.form_submit_button(label="Generar Reporte")
    
    if submit_button:
        # Obtener datos del reporte y la gráfica
        with st.spinner("Generando datos del reporte..."):
            try:
                datos_response = requests.post(
                    BACKEND_URL_DATOS,
                    data={"consulta": consulta},
                    timeout=60  # Aumentar timeout a 60 segundos
                )
                if datos_response.status_code == 200:
                    response_data = datos_response.json()
                    reporte_texto = response_data["reporte_texto"]
                    ruta_figura = response_data["ruta_figura"]
                    reporte_id = response_data["reporte_id"]
                    st.success("¡Datos cargados con éxito!")
                elif datos_response.status_code == 408:
                    st.error("⏱️ El análisis está tomando más tiempo del esperado. El agente pandas puede estar iterando demasiado. Por favor, intenta nuevamente.")
                elif datos_response.status_code == 500:
                    try:
                        error_data = datos_response.json()
                        st.error(f"Error del servidor: {error_data.get('detail', 'Error interno')}")
                    except:
                        st.error("Error interno del servidor. Por favor, intenta nuevamente.")
                else:
                    st.error(f"Error al cargar los datos del reporte. Status: {datos_response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("🔌 No se puede conectar al backend. Asegúrate de que el servicio FastAPI esté ejecutándose.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout al conectar con el backend. El análisis puede estar tomando más tiempo del esperado debido a múltiples iteraciones del agente pandas.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")

# Función para mostrar el reporte
def generar_report(reporte_texto):
    st.subheader("Contenido del Reporte:")
    st.write(reporte_texto)

def mostrar_grafico(ruta_html):
    st.subheader("Gráfica Financiera Interactiva:")
    try:
        # Leer el archivo HTML con UTF-8
        with open(ruta_html, "r", encoding="UTF8") as f:
            html_content = f.read()
            # Renderizar el contenido HTML
            html(html_content, height=700)
    except Exception as e:
        st.error(f"Error al cargar la gráfica: {e}")

# Mostrar el contenido del reporte
if reporte_texto:
    generar_report(reporte_texto)

# Mostrar la gráfica
if ruta_figura:
    mostrar_grafico(ruta_figura)

# # Botón para descargar el PDF

# if st.button("Descargar Informe PDF"):
#     with st.spinner("Generando PDF..."):
#         try:
#             pdf_response = requests.post(
#                 BACKEND_URL_PDF,
#                 json={"reporte_id": reporte_id},
#                 timeout=10  # Tiempo de espera en segundos
#             )
#             if pdf_response.status_code == 200:
#                 # Verifica que los datos PDF están en el contenido de la respuesta
#                 pdf_content = pdf_response.content
#                 if pdf_content:
#                     # Usa st.download_button para descargar el archivo generado
#                     st.download_button(
#                         label="Descargar Informe PDF",
#                         data=pdf_content,
#                         file_name=f"reporte_financiero_{reporte_id}.pdf",
#                         mime="application/pdf"
#                     )
#                 else:
#                     st.error("El contenido del PDF está vacío.")
#             else:
#                 st.error(f"Error al generar el PDF. Código de estado: {pdf_response.status_code}")
#         except requests.exceptions.RequestException as e:
#             st.error(f"Error de conexión: {str(e)}")
