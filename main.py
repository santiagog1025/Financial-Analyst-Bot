from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from model.ai_model import correr_modelo
from utils import guardar_pdf, generar_graficos
import uuid
import os

app = FastAPI()
# Diccionario para almacenar los resultados temporalmente
cache = {}

@app.post("/generar_datos/")
async def generar_datos(consulta: str = Form(...)):
    """
    Genera el contenido del reporte financiero y los datos para la gráfica.
    """
    # Ejecutar el modelo y obtener los datos
    estado_inicial = {
        "consulta": [consulta],
        "ticker": [],
        "datos_financieros": [],
        "respuesta_analisis": [],
        "ruta_html": [],
        "noticias": [],
        "respuesta_final": None,
    }
    estado_final = correr_modelo(estado_inicial)

    # Preparar datos para la gráfica
    ruta_figura = generar_graficos(estado_final["datos_financieros"][-1], estado_final["ticker"][-1])  # Retorna la ruta del archivo gráfico
    reporte_texto = estado_final["respuesta_final"][-1]
    # Generar un ID único para esta consulta
    reporte_id = str(uuid.uuid4())

    # Guardar los datos en caché
    cache[reporte_id] = {
        "reporte_texto": reporte_texto,
        "ruta_figura": ruta_figura,
        "consulta": consulta
    }

    return JSONResponse({
        "reporte_texto": reporte_texto,
        "ruta_figura": ruta_figura,
        "reporte_id": reporte_id
    })
@app.post("/descargar_pdf/")
async def descargar_pdf(reporte_id: str = Form(...)):
    """
    Genera y descarga el informe financiero en formato PDF utilizando datos almacenados.
    """
    # Verificar si el reporte existe en caché (o la ubicación donde se guarda el archivo)
    if reporte_id not in cache:
        return {"error": "Reporte no encontrado"}, 404
    else:
        reporte_texto = cache[reporte_id]["reporte_texto"]
        reporte_pdf_path = f"reporte_financiero_{reporte_id}.pdf"

    try:
        guardar_pdf(reporte_texto, reporte_pdf_path)
    except Exception as e:
        return {"error": f"Error al generar el PDF: {str(e)}"}, 500

    # Verifica que el archivo existe antes de enviarlo
    if os.path.exists(reporte_pdf_path):
        return FileResponse(
            path=reporte_pdf_path,
            media_type="application/pdf",
            filename=f"reporte_financiero_{reporte_id}.pdf",
        )
    else:
        return {"error": "Archivo PDF no encontrado"}, 404