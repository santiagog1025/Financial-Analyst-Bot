from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from ddgs import DDGS
from typing import List, TypedDict, Annotated
import operator
import yfinance as yf
import pandas as pd
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
    try:
        # Descargar datos - usar group_by='ticker' para evitar MultiIndex cuando sea un solo ticker
        df = yf.download(ticker, period="1y", auto_adjust=False, group_by='ticker')

        # Debug: Imprimir información sobre las columnas
        print(f"Columnas descargadas para {ticker}: {list(df.columns)}")
        print(f"Tipo de columnas: {type(df.columns)}")
        print(f"Shape del DataFrame: {df.shape}")

        # Si el DataFrame está vacío, intentar con auto_adjust=True
        if df.empty:
            print(f"Datos vacíos con auto_adjust=False, intentando con auto_adjust=True")
            df = yf.download(ticker, period="1y", auto_adjust=True, group_by='ticker')
            print(f"Columnas con auto_adjust=True: {list(df.columns)}")

        # Manejar MultiIndex si existe
        if isinstance(df.columns, pd.MultiIndex):
            print(f"MultiIndex detectado con {df.columns.nlevels} niveles")
            if df.columns.nlevels == 2:
                # Para un solo ticker, el primer nivel será el ticker y el segundo los nombres de columnas
                # Usar solo el segundo nivel (nombres de columnas)
                df.columns = df.columns.get_level_values(1)
                print(f"Columnas después de aplanar MultiIndex: {list(df.columns)}")

        # Verificar si el índice es 'Date' y resetear si es necesario
        if df.index.name == 'Date':
            df = df.reset_index()
            datos_financieros = df.sort_values(by='Date').set_index('Date')
        else:
            # Si el índice ya es datetime, solo ordenar
            datos_financieros = df.sort_index()

        print(f"Datos financieros finales para {ticker}: {datos_financieros.shape}")
        print(f"Columnas finales: {list(datos_financieros.columns)}")

        return datos_financieros

    except Exception as e:
        print(f"Error al obtener datos financieros para {ticker}: {e}")
        # Retornar DataFrame vacío en caso de error
        return pd.DataFrame()

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
        with DDGS() as ddgs:
            # Usamos el ticker como parte de la búsqueda
            query = f"{ticker} stock news"
            max_results = 2
            results = ddgs.text(query, max_results=max_results)
            noticias = []
            for r in results:
                titulo = r.get("title", "Sin título")
                enlace = r.get("href", "#")
                snippet = r.get("body", "Sin descripción")
                noticias.append(f"{titulo}\n{snippet}\n{enlace}")
            return "\n\n".join(noticias) if noticias else "No se encontraron noticias relevantes."
    except Exception as e:
        return f"Hubo un error al obtener las noticias de {ticker}: {str(e)}"

class AgenteProcesadorConsulta:
    def __init__(self):
        # Inicializa el LLM de OpenAI con la clave API proporcionada
        self.llm = ChatGroq(temperature=0, model="meta-llama/llama-4-maverick-17b-128e-instruct")
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
        self.chain = self.prompt | self.llm | StrOutputParser()
    def extraer_ticker(self, consulta: str) -> str:
        return self.chain.invoke(consulta)


class AgenteAnalizarDatos:
    def __init__(self):
        """
        Inicializa el agente de análisis de datos financieros.
        """
        # Inicializar el modelo de lenguaje con la clave de API
        self.llm = ChatGroq(temperature=0, model="meta-llama/llama-4-maverick-17b-128e-instruct")

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
                    Context: The dataset comes from Yahoo Finance and contains historical data for the last year of the stock.
                    The data is structured as a Pandas DataFrame, with each row representing a trading day. The columns include: Date (index), Open, High, Low, Close, Adj Close, Volume.

                    Your task is to calculate these 3 specific metrics ONLY:

                    1. Average Closing Price Over the Last 7 Days: df['Close'].tail(7).mean()
                    2. 200-Period Moving Average: df['Close'].rolling(window=200).mean().iloc[-1]
                    3. 30-Day Price Trend: Compare current price with price 30 days ago to determine if trend is upward, downward, or neutral.

                    CRITICAL INSTRUCTIONS:
                    - Use ONLY simple pandas operations as shown above
                    - Do NOT use complex analysis or additional calculations
                    - Do NOT iterate more than 2 times
                    - If any calculation fails, skip it and continue with the others
                    - Provide results in a simple format: "7-day average: $X, 200-day MA: $Y, 30-day trend: direction"

                    The current date and time are: {fecha_hora_actual}.
                    """

        # Crear el agente de Pandas con límites estrictos
        agente = create_pandas_dataframe_agent(
            llm=self.llm,
            df=datos_financieros,
            verbose=False,  # Reducir verbosidad para mejorar rendimiento
            allow_dangerous_code=True,
            max_iterations=2,  # Límite máximo de iteraciones
            max_execution_time=20  # Límite de tiempo en segundos
        )

        try:
            # Ejecutar la consulta utilizando el agente con el mensaje de sistema
            respuesta = agente.invoke({
                "input": "Calculate: 1) df['Close'].tail(7).mean() 2) df['Close'].rolling(200).mean().iloc[-1] 3) Compare current vs 30-day ago price. " + mensaje_sistema
            })
            return respuesta["output"]
        except Exception as e:
            # Si hay un error o timeout, devolver un análisis básico
            print(f"Error en análisis pandas: {e}")
            return self._analisis_basico(datos_financieros)

    def _analisis_basico(self, df: pd.DataFrame) -> str:
        """
        Realiza un análisis básico si el agente pandas falla.
        """
        try:
            # Análisis básico usando pandas directamente
            if 'Close' in df.columns and len(df) > 0:
                # Últimos 7 días promedio
                avg_7_days = df['Close'].tail(7).mean()

                # Media móvil de 200 períodos
                if len(df) >= 200:
                    ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
                else:
                    ma_200 = df['Close'].mean()  # Usar promedio total si no hay suficientes datos

                # Tendencia de 30 días
                if len(df) >= 30:
                    price_30_days_ago = df['Close'].iloc[-30]
                    current_price = df['Close'].iloc[-1]
                    trend_pct = ((current_price - price_30_days_ago) / price_30_days_ago) * 100

                    if trend_pct > 2:
                        trend = f"alcista (+{trend_pct:.1f}%)"
                    elif trend_pct < -2:
                        trend = f"bajista ({trend_pct:.1f}%)"
                    else:
                        trend = f"neutral ({trend_pct:.1f}%)"
                else:
                    current_price = df['Close'].iloc[-1]
                    trend = "datos insuficientes para tendencia"

                return f"""
                Análisis Financiero (Análisis Directo):

                Métricas Calculadas:
                - Promedio de precio de cierre últimos 7 días: ${avg_7_days:.2f}
                - Media móvil de 200 períodos: ${ma_200:.2f}
                - Tendencia de 30 días: {trend}
                - Precio actual: ${current_price:.2f}

                Nota: Este análisis fue generado directamente debido a limitaciones de tiempo en el procesamiento del agente pandas.
                """
            else:
                return "No se pudieron analizar los datos financieros - datos insuficientes o columna 'Close' no encontrada."
        except Exception as e:
            return f"Error en análisis básico: {str(e)}"

class AgenteAsesorFinanciero:
    def __init__(self):
        # Inicializa el LLM
        self.llm = ChatGroq(temperature=1, model="llama-3.3-70b-versatile")
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
        self.chain = self.prompt | self.llm | StrOutputParser()
    def responder(self, consulta: str, respuesta_analisis:str, noticias: str, fecha:str) -> str:
         # Empaquetar las variables como un diccionario
        inputs = {
            "consulta": consulta,
            "respuesta_analisis": respuesta_analisis,
            "noticias": noticias,
            "fecha": fecha
        }
        return self.chain.invoke(inputs)
    
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
        df = ObtenerDatosFinancieros.invoke(estado["ticker"][-1])
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
        noticias = ObtenerNoticias.invoke(ticker)
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
grafico.add_node("esperar_ambos", lambda x: x)  # Nodo de sincronización
grafico.add_edge("analizar_datos", "esperar_ambos")
grafico.add_edge("obtener_noticias", "esperar_ambos")
grafico.add_edge("esperar_ambos", "analista_financiero")
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
    print(estado_final)
    return estado_final