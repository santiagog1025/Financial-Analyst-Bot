import streamlit as st
import requests

# Título de la aplicación
st.title("Aplicación de Reporte de Consulta")

# Formulario para ingresar nombre y consulta
nombre = st.text_input("Ingresa tu nombre:")
consulta = st.text_input("Ingresa tu consulta:")

# Botón para enviar la consulta
if st.button("Enviar Consulta"):
    # Envía la consulta al backend
    response = requests.post("http://localhost:8000/reporte", json={"nombre": nombre, "consulta": consulta})

    # Verifica si la respuesta es exitosa
    if response.status_code == 200:
        # Obtiene el reporte en formato Markdown
        reporte_markdown = response.json().get("reporte")

        # Muestra el reporte en la aplicación
        st.markdown(reporte_markdown)
    else:
        st.error("Error al obtener el reporte.")