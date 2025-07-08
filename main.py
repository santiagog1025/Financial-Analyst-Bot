from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from model.ai_model import correr_modelo
from utils import guardar_pdf, generar_graficos
import uuid
import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

app = FastAPI()
# Diccionario para almacenar los resultados temporalmente
cache = {}

# Configurar un executor para tareas que pueden tomar tiempo
executor = ThreadPoolExecutor(max_workers=4)

def ejecutar_modelo_con_timeout(consulta: str, timeout: int = 45):
    """
    Ejecuta el modelo con un timeout específico.
    """
    try:
        start_time = time.time()
        estado_final = correr_modelo(consulta)
        execution_time = time.time() - start_time

        print(f"Modelo ejecutado en {execution_time:.2f} segundos")
        return estado_final

    except Exception as e:
        print(f"Error en ejecución del modelo: {e}")
        raise e

@app.post("/generar_datos/")
async def generar_datos(consulta: str = Form(...)):
    """
    Genera el contenido del reporte financiero y los datos para la gráfica.
    """
    try:
        # Ejecutar el modelo con timeout usando asyncio
        loop = asyncio.get_event_loop()

        # Ejecutar en un thread separado con timeout
        estado_final = await asyncio.wait_for(
            loop.run_in_executor(executor, ejecutar_modelo_con_timeout, consulta, 45),
            timeout=50.0  # Timeout total de 50 segundos
        )

        # Verificar que tenemos datos válidos
        if not estado_final or not estado_final.get("respuesta_final") or not estado_final.get("datos_financieros"):
            raise HTTPException(
                status_code=500,
                detail="No se pudieron generar datos válidos para el reporte"
            )

        # Preparar datos para la gráfica
        try:
            ruta_figura = generar_graficos(
                estado_final["datos_financieros"][-1],
                estado_final["ticker"][-1]
            )
        except Exception as e:
            print(f"Error generando gráficos: {e}")
            ruta_figura = None

        reporte_texto = estado_final["respuesta_final"][-1]

        # Generar un ID único para esta consulta
        reporte_id = str(uuid.uuid4())

        # Guardar los datos en caché
        cache[reporte_id] = {
            "reporte_texto": reporte_texto,
            "ticker": estado_final["ticker"][-1] if estado_final.get("ticker") else "N/A",
            "ruta_figura": ruta_figura,
            "consulta": consulta
        }

        return JSONResponse({
            "reporte_texto": reporte_texto,
            "ruta_figura": ruta_figura,
            "reporte_id": reporte_id
        })

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="El análisis está tomando más tiempo del esperado. Por favor, intenta nuevamente."
        )
    except Exception as e:
        print(f"Error en generar_datos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
@app.post("/descargar_pdf/")
async def descargar_pdf(reporte_id: str = Form(...)):
    """
    Genera y descarga el informe financiero en formato PDF utilizando datos almacenados.
    """
    # Verificar si el reporte existe en caché
    if reporte_id not in cache:
        return JSONResponse({"error": "Reporte no encontrado"}, status_code=404)
    
    reporte_texto = cache[reporte_id]["reporte_texto"]

    try:
        # Intentar guardar el PDF
        guardar_pdf(reporte_texto)
    except Exception as e:
        return JSONResponse({"error": f"Error al generar el PDF: {str(e)}"}, status_code=500)
