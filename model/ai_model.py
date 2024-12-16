from langgraph.graph import StateGraph, END, START
from langchain import PromptTemplate, LLMChain
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.schema import SystemMessage
from typing import List, TypedDict, Annotated
import pandas as pd
import operator
import yfinance as yf
import pandas as pd
import pandas as pd

from typing import Dict
from datetime import datetime
# Obtener la clave de API desde las variables de entorno
load_dotenv()
@tool
def ObtenerDatosFinancieros(ticker: str) -> pd.DataFrame:
    """
    Obtiene datos financieros históricos para el ticker proporcionado.

    Args:
        ticker (str): Símbolo del ticker de la empresa.

    Returns:
        pd.DataFrame: DataFrame con los datos financieros históricos.
    """
    df = yf.download(ticker, period="5y")  # Últimos 5 años de datos
    datos_financieros =  df.sort_values(by='Date', ascending=False)
    return datos_financieros

@tool
def ObtenerNoticias(ticker: str) -> str:
    """
    Obtiene noticias financieras relevantes para el ticker proporcionado.

    Args:
        ticker (str): Símbolo del ticker de la empresa.

    Returns:
        str: Noticias obtenidas en formato de texto.
    """
    # Inicializar la herramienta de búsqueda
    wrapper = DuckDuckGoSearchAPIWrapper(region="de-de", time="d", max_results=2)

    news_tool = DuckDuckGoSearchResults(api_wrapper=wrapper, source="news")
    
    # Ejecutar la búsqueda
    resultados = news_tool.invoke({"query": ticker})
    
    # Verificar tipo de `resultados`
    if isinstance(resultados, str):
        # Si es una cadena, simplemente devuélvela
        return resultados
    elif isinstance(resultados, list):
        # Procesar como lista de diccionarios
        noticias = []
        for resultado in resultados:
            if isinstance(resultado, dict):  # Asegurarse de que cada elemento sea un diccionario
                titulo = resultado.get('title', 'Sin título')
                enlace = resultado.get('link', '#')
                snippet = resultado.get('snippet', 'Sin descripción')
                noticias.append(f"{titulo}\n{snippet}\n{enlace}")
        return "\n\n".join(noticias)
    else:
        return "No se encontraron resultados válidos."
class AgenteProcesadorConsulta:
    def __init__(self):
        # Inicializa el LLM de OpenAI con la clave API proporcionada
        self.llm = ChatGroq(temperature=0, model="gemma-7b-it")
        # Define la plantilla del prompt para extraer el ticker
        self.prompt = PromptTemplate(
            input_variables=["consulta"],
            template=(
                "Eres un asistente financiero. Responde únicamente con el símbolo bursátil (ticker) de la siguiente consulta:\n"
                "Consulta: '{consulta}'\n"
                "Ticker:"
            )
        )
        # Crea una cadena LLM con el LLM y el prompt
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    def extraer_ticker(self, consulta: str) -> str:
        return self.chain.run(consulta)


class AgenteAnalizarDatos:
    def __init__(self):
        """
        Inicializa el agente de análisis de datos financieros.
        """
        # Inicializar el modelo de lenguaje con la clave de API
        self.llm = ChatGroq(temperature=0, model="llama-3.3-70b-versatile")

    def ejecutar(self, datos_financieros: pd.DataFrame, consulta: str) -> str:
        """
        Analiza los datos financieros y extrae información relevante según la consulta.

        Args:
            datos_financieros (pd.DataFrame): DataFrame con los datos financieros.
            consulta (str): Pregunta o consulta específica para el análisis.

        Returns:
            str: Respuesta generada por el agente basada en la consulta.
        """
        # Obtener la fecha y hora actuales
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Crear el mensaje de sistema con la fecha y hora actuales
        mensaje_sistema = SystemMessage(
            content=f"""
                    Eres un analista financiero que utiliza datos históricos de acciones obtenidos de Yahoo Finance para responder a las consultas de los usuarios. Los datos que analizarás ya están filtrados por el ticker correspondiente, por lo que no es necesario realizar consultas adicionales para filtrar por símbolo.
                    
                    Tu tarea es:
                    
                    1. **Promedio del Precio de Cierre en los Últimos 7 Días**:
                       - Calcula el promedio del precio de cierre de la acción en los últimos 7 días.
                    
                    2. **Tendencia en los Últimos 30 Días**:
                       - Analiza la tendencia del precio de la acción en los últimos 30 días.
                    
                    3. **Media Móvil de 200 Períodos**:
                       - Calcula la media móvil de 200 períodos para evaluar la tendencia a largo plazo de la acción.
                    
                    Utiliza exclusivamente métodos de la biblioteca `pandas` para realizar estos cálculos y análisis. La fecha y hora actuales son: {fecha_hora_actual}. Emplea esta información para contextualizar tus respuestas y asegurarte de que los análisis reflejen el estado más reciente de los datos disponibles.
                    """

                    )

        # Crear el agente de Pandas
        agente = create_pandas_dataframe_agent(
            llm=self.llm,
            df=datos_financieros,
            verbose=True,
            allow_dangerous_code=True,
            agent_executor_kwargs={
                "handle_parsing_errors": True  # Manejar errores de análisis
            }
        )

        # Ejecutar la consulta utilizando el agente con el mensaje de sistema
        respuesta = agente.invoke({"input": [consulta], "messages": [mensaje_sistema]})
        return respuesta["output"]

class AgenteAsesorFinanciero:
    def __init__(self):
        # Inicializa el LLM de OpenAI con la clave API proporcionada
        self.llm = ChatGroq(temperature=1, model="llama-3.3-70b-versatile")
        # Define la plantilla del prompt para extraer el ticker
        self.prompt = PromptTemplate(
            input_variables=["consulta","respuesta_analisis","noticias","fecha"],
            template=(
                 """
                    Eres un asesor financiero experto y tu tarea es elaborar un informe integral hasta el dia de {fecha} basado en dos fuentes principales:
                    
                    1. **Análisis financiero basado en datos históricos**:
                       - Utiliza los datos procesados por el bot de Pandas para extraer información clave.
                       - Esto incluye tendencias de corto y largo plazo, medias móviles, y otras métricas relevantes.
                    
                    2. **Noticias del mercado**:
                       - Proporciona un resumen de las noticias más recientes y relevantes relacionadas con el símbolo bursátil.
                       - Destaca cualquier evento que pueda haber influido en la acción, como cambios regulatorios, resultados financieros, o movimientos de mercado.
                    
                    **Estructura del informe**:
                    
                    ### Introducción
                    - Introduce brevemente el símbolo bursátil analizado y el objetivo del informe.
                    
                    ### Análisis Financiero
                    - Resumen del análisis del bot de Pandas:
                        - Tendencias recientes en los últimos 30 días (subidas, bajadas).
                        - Media del precio de cierre en los últimos 7 días.
                        - Media móvil de 200 periodos para identificar la tendencia a largo plazo.
                    
                    ### Noticias del Mercado
                    - Resumen de noticias clave relacionadas con el símbolo.
                    - Resalta cualquier noticia que pueda haber impactado significativamente en los precios o la percepción del mercado.
                    
                    ### Conclusión
                    - Integra los datos financieros y las noticias para proporcionar una evaluación clara y fundamentada.
                    - Responde a la pregunta del usuario considerando tanto el análisis financiero como el contexto de las noticias.
                    - Ofrece recomendaciones accionables basadas en los hallazgos.
                    
                    **Pregunta del usuario**: {consulta}
                    
                    **Tu respuesta**:
                    Escribe el informe de manera profesional, pero accesible para personas con conocimientos limitados de finanzas. Usa un lenguaje claro, evita tecnicismos innecesarios, y proporciona un análisis lógico y estructurado.
                    """)

        )
        # Crea una cadena LLM con el LLM y el prompt
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    def responder(self, consulta: str, respuesta_analisis:str, noticias: str, fecha:str) -> str:
         # Empaquetar las variables como un diccionario
        inputs = {
            "consulta": consulta,
            "respuesta_analisis": respuesta_analisis,
            "noticias": noticias,
            "fecha": fecha
        }
        return self.chain.run(inputs)
    
class Estado(TypedDict):
    consulta: Annotated[List[str], operator.add]   # Consulta proporcionada por el usuario
    ticker: Annotated[List[str], operator.add]  # Ticker extraído de la consulta
    datos_financieros: Annotated[List[pd.DataFrame], operator.add]  # Datos financieros del ticker
    respuesta_analisis: Annotated[List[str], operator.add]  # Respuesta generada por el análisis de datos
    ruta_html: Annotated[List[str], operator.add]  # Ruta del archivo HTML generado para los gráficos
    noticias: Annotated[List[str], operator.add]  # Lista de noticias relacionadas
    respuesta_final: Annotated[List[str], operator.add]  # Respuesta final generada por el analista financiero
grafico = StateGraph(Estado)

def extraer_ticker(estado: Estado) -> Estado:
    agente = AgenteProcesadorConsulta()
    ticker = agente.extraer_ticker(estado["consulta"][-1])
    estado["ticker"].append(ticker)
    return estado
def obtener_datos_financieros(estado: Estado) -> Estado:
    if estado["ticker"]:
        df = ObtenerDatosFinancieros(estado["ticker"][-1])
        estado["datos_financieros"].append(df)
    return estado
def analizar_datos(estado: Estado) -> Estado:
    if estado["datos_financieros"] is not None:
        agente_analizar = AgenteAnalizarDatos()
        respuesta = agente_analizar.ejecutar(
            datos_financieros=estado["datos_financieros"][-1],
            consulta=estado["consulta"]
        )
        estado["respuesta_analisis"].append(respuesta)
    return estado
def obtener_noticias(estado: Estado) -> Estado:
    if estado["ticker"]:
        ticker = estado["ticker"][-1]
        noticias = ObtenerNoticias(ticker)
        estado["noticias"].append(noticias)
    return estado

def analista_financiero(estado: Estado) -> Estado:
    fecha_hora_actual = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    agente = AgenteAsesorFinanciero()
    respuesta = agente.responder(consulta=estado["consulta"], respuesta_analisis=estado["respuesta_analisis"],noticias = estado["noticias"],fecha=fecha_hora_actual)
    estado["respuesta_final"].append(respuesta)
    return estado

grafico.add_node("extraer_ticker", extraer_ticker)
grafico.add_node("obtener_datos_financieros", obtener_datos_financieros)
grafico.add_node("analizar_datos", analizar_datos)
grafico.add_node("obtener_noticias", obtener_noticias)
grafico.add_node("analista_financiero", analista_financiero)
grafico.add_edge(START, "extraer_ticker")
grafico.add_edge("extraer_ticker", "obtener_datos_financieros")
grafico.add_edge("extraer_ticker", "obtener_noticias")
grafico.add_edge("obtener_datos_financieros", "analizar_datos")
grafico.add_edge("analizar_datos", "analista_financiero")
grafico.add_edge("obtener_noticias", "analista_financiero")
grafico.add_edge("analista_financiero", END)

app = grafico.compile()

def correr_modelo(consulta: str):
    estado_inicial = {
    "consulta": [consulta],
    "ticker": [],
    "datos_financieros": [],
    "respuesta_analisis": [],
    "ruta_html": [],
    "noticias": [],
    "respuesta_final": []
}
    estado_final = app.invoke(estado_inicial)

    return estado_final
