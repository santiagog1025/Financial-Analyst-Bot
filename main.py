from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from model.ai_model import correr_modelo
from utils import guardar_pdf

app = FastAPI()

@app.post("/generar_reporte/")
async def generar_reporte(consulta: str = Form(...)):
    """
    Genera un informe financiero en PDF para un ticker dado y una consulta específica.
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

    # Guardar el informe en PDF
    reporte_pdf_path = f"reporte_financiero_{estado_final["ticker"][-1]}.pdf"
    guardar_pdf(estado_final["respuesta_final"][-1], reporte_pdf_path)

    # Retornar el archivo PDF generado
    return FileResponse(
        path=reporte_pdf_path,
        media_type="application/pdf",
        filename="reporte_financiero.pdf",
    )
