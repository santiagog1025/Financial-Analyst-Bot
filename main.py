from fastapi import FastAPI
from model.ai_model import generar_graficos, correr_modelo
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir CORS para que Streamlit pueda comunicarse con FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # Cambia esto a la URL de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/reporte")
def reporte(nombre: str, consulta: str):

    estado_final = correr_modelo(consulta)
    # Genera un reporte en formato Markdown
    reporte_markdown = f"# Reporte de Consulta\n\n"
    reporte_markdown += f"**Nombre:** {nombre}\n\n"
    reporte_markdown += f"**Consulta:** {estado_final['consulta'][-1]}\n\n"
    reporte_markdown += "## Resultados\n\n"
    reporte_markdown += "{estado_final['respuesta_final'][-1]}.\n"
    # Crea la gráfica
    html = generar_graficos(estado_final["datos_financieros"][-1], estado_final["ticker"][-1])

    # Agrega la gráfica al reporte
    reporte_markdown += f"### Gráfica de {estado_final['ticker'][-1]}\n\n"
    reporte_markdown += html

    return {"reporte": reporte_markdown}


