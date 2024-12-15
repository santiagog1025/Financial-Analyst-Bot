import streamlit as st
import requests
from io import BytesIO

# URL del backend
BACKEND_URL = "http://127.0.0.1:8000/generar_reporte/"

st.title("Generador de Reportes Financieros")

# Inicializar una variable para almacenar el PDF generado
pdf_data = None

# Formulario de entrada
with st.form("form_reporte"):
    consulta = st.text_input(
        "Escribe tu consulta financiera", 
        "¿Qué opinas del precio promedio de Google?"
    )
    submit_button = st.form_submit_button(label="Generar Reporte")
    
    if submit_button:
        # Enviar solicitud al backend
        with st.spinner("Generando el informe..."):
            response = requests.post(
                BACKEND_URL,
                data={"consulta": consulta}  # Enviar datos como form-data
            )
            
            if response.status_code == 200:
                # Convertir la respuesta en un archivo PDF en memoria
                pdf_data = BytesIO(response.content)
                st.success("¡Informe generado con éxito!")
            else:
                st.error("Error al generar el informe. Intenta de nuevo.")

# Mostrar el botón de descarga fuera del formulario
if pdf_data:
    st.download_button(
        label="Descargar Informe PDF",
        data=pdf_data,
        file_name="reporte_financiero.pdf",
        mime="application/pdf"
    )