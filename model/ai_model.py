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
    df = yf.download(ticker, period="1y")  # Últimos 5 años de datos
    datos_financieros =  df.sort_values(by='Date')
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
    try:
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
    except Exception as e:
        return f"Hubo un error al obtener las noticias de {ticker}: {str(e)}"

class AgenteProcesadorConsulta:
    def __init__(self):
        # Inicializa el LLM de OpenAI con la clave API proporcionada
        self.llm = ChatGroq(temperature=0, model="llama-3.1-8b-instant")
        # Define la plantilla del prompt para extraer el ticker
        self.prompt = PromptTemplate(
            input_variables=["consulta"],
            template=(
                "Eres un asistente financiero. Responde únicamente con el símbolo bursátil no añadas ningun espacio ni nignun /n (ticker) de la siguiente consulta:"
                "Consulta: '{consulta}'"
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
        self.llm = ChatGroq(temperature=0, model="llama3-70b-8192")

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
        mensaje_sistema = f"""
                    You are a financial analyst specializing in historical stock data analysis. You work with datasets already filtered by the corresponding ticker symbol, so there is no need for additional filtering by symbol. 
                    The data is provided in a structured format, typically as a Pandas DataFrame.
                    Context: The dataset comes from Yahoo Finance and contains historical data for the last 5 years of the stock. 
                    The data is structured as a Pandas DataFrame, with each row representing a trading day. The columns include, among others, the date, the opening price, closing price, high price, low price, and trading volume. 
                    The Date column is set as the index of the DataFrame.
                    Your task is:

                    Average Closing Price Over the Last 7 Days:

                    Calculate the average closing price of the stock over the last 7 days based on the provided data.
                    7-Day Price Trend:

                    Analyze the stock's price trend over the last 30 days. Provide insights on whether the trend is upward, downward, or neutral.
                    200-Period Moving Average:

                    Calculate the 200-period moving average to assess the stock's long-term trend.
                    Use only methods from the pandas library to perform these calculations and analyses. 
                    The current date and time are: {fecha_hora_actual}.If you already iterate more than 3 times on the same code just run the other step.
                    """

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
        respuesta = agente.invoke({"input": ["What is the mean average of 200 periods and the price of the last 7 days?", mensaje_sistema]})
        return respuesta["output"]

class AgenteAsesorFinanciero:
    def __init__(self):
        # Inicializa el LLM
        self.llm = ChatGroq(temperature=1, model="mixtral-8x7b-32768")
        # Define la plantilla del prompt para extraer el ticker
        self.prompt = PromptTemplate(
            input_variables=["consulta","respuesta_analisis","noticias","fecha"],
            template=(
                 """
                    Eres un asesor financiero experto y tu tarea es elaborar un informe integral hasta el día de {fecha}, basado en dos fuentes principales que se te proporcionarán:

                    Análisis financiero basado en datos históricos:

                    Recibirás las siguientes métricas generadas por un bot especializado en pandas: {respuesta_analisis}, calculadas a partir de datos históricos:
                    Promedio del precio de cierre en los últimos 7 días.
                    Tendencia del precio en los últimos 7 días (indicando si es alcista, bajista o neutral).
                    Media móvil de 200 períodos para evaluar la tendencia a largo plazo de la acción.
                    Deberás integrar esta información de manera clara y accesible para el usuario.
                    Noticias del mercado:

                    Recibirás un resumen de noticias relevantes relacionadas con el símbolo bursátil: {noticias}.
                    Estas noticias pueden incluir eventos significativos como cambios regulatorios, reportes financieros o situaciones del mercado que hayan impactado en el precio de la acción.
                    Estructura del informe:

                    Introducción
                    Introduce brevemente el símbolo bursátil analizado y el objetivo del informe.
                    Análisis Financiero
                    Presenta de forma clara y accesible las métricas proporcionadas por el bot de Pandas:
                    Media del precio de cierre en los últimos 7 días.
                    Media móvil de 200 periodos y su interpretación.
                    Noticias del Mercado
                    Resume las noticias clave relacionadas con el símbolo.
                    Explica de forma sencilla cómo estas noticias podrían haber influido en el precio o la percepción del mercado.
                    Conclusión
                    Integra las métricas financieras y las noticias para proporcionar una evaluación clara y fundamentada.
                    Responde a la pregunta del usuario considerando tanto el análisis financiero como el contexto de las noticias.
                    Ofrece recomendaciones accionables basadas en los hallazgos.
                    Pregunta del usuario: {consulta}

                    Tu respuesta:
                    Escribe el informe de manera profesional pero accesible, orientado a personas con conocimientos limitados de finanzas. Usa un lenguaje claro, evita tecnicismos innecesarios, y organiza la información de manera lógica y estructurada.
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
    if estado["ticker"][-1]:
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
