import markdown
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from bs4 import BeautifulSoup
from textwrap import wrap
import os

def obtener_ruta_descargas(nombre_archivo):
    """
    Obtiene la ruta a la carpeta de descargas del sistema operativo y construye la ruta del archivo.
    :param nombre_archivo: Nombre del archivo que se guardará en Descargas.
    :return: Ruta completa del archivo en Descargas.
    """
    if os.name == "nt":  # Windows
        from winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        with OpenKey(HKEY_CURRENT_USER, sub_key) as key:
            descargas = QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
    else:  # macOS o Linux
        descargas = str(Path.home() / "Downloads")
    
    return os.path.join(descargas, nombre_archivo)
def guardar_pdf(contenido_markdown, nombre_archivo="archivo.pdf"):
    """
    Convierte contenido Markdown a un archivo PDF respetando el formato básico de Markdown.
    
    :param contenido_markdown: Texto en formato Markdown.
    :param nombre_archivo: Nombre del archivo PDF de salida.
    """
    try:
        # Convertir Markdown a HTML
        contenido_html = markdown(contenido_markdown)
        soup = BeautifulSoup(contenido_html, "html.parser")
        
        # Configurar el PDF con tamaño A4
        archivo_pdf = obtener_ruta_descargas(nombre_archivo)
        pdf = canvas.Canvas(archivo_pdf, pagesize=A4)
        ancho_pagina, alto_pagina = A4
        
        # Configurar márgenes
        margen_izquierdo = 60
        margen_derecho = ancho_pagina + 60
        margen_superior = alto_pagina - 60
        margen_inferior = 60
        y = margen_superior

        pdf.setFont("Helvetica", 10)

        # Ancho del texto
        ancho_texto = margen_derecho - margen_izquierdo

        # Procesar cada elemento del HTML
        for tag in soup.contents:
            if y < margen_inferior:  # Si alcanza el margen inferior, crear nueva página
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = margen_superior

            if isinstance(tag, str):  # Si es solo texto, lo procesamos directamente
                y = escribir_parrafo(pdf, tag, margen_izquierdo, ancho_texto, y, margen_inferior, tipo="p")
            elif tag.name == "h1":
                pdf.setFont("Helvetica-Bold", 14)
                y = escribir_parrafo(pdf, tag, margen_izquierdo, ancho_texto, y, margen_inferior, tipo="h1")
            elif tag.name == "h2":
                pdf.setFont("Helvetica-Bold", 12)
                y = escribir_parrafo(pdf, tag, margen_izquierdo, ancho_texto, y, margen_inferior, tipo="h2")
            elif tag.name == "p":
                pdf.setFont("Helvetica", 10)
                y = escribir_parrafo(pdf, tag, margen_izquierdo, ancho_texto, y, margen_inferior, tipo="p")
            elif tag.name == "ul":
                for li in tag.find_all("li"):
                    texto_lista = f"• {li.text}"
                    y = escribir_parrafo(pdf, texto_lista, margen_izquierdo + 20, ancho_texto - 20, y, margen_inferior, tipo="li")
        
        pdf.save()
        print(f"PDF generado correctamente: {archivo_pdf}")
    
    except Exception as e:
        print(f"Error al convertir el archivo: {e}")

def escribir_parrafo(pdf, tag, x_inicial, ancho_texto, y, y_minimo, tipo="p", espacio_entre_lineas=14):
    """
    Escribe un párrafo en el PDF respetando los márgenes y saltos de línea según el tipo de contenido Markdown,
    incluyendo negritas y otros estilos.
    
    :param pdf: Objeto Canvas de ReportLab.
    :param tag: Tag HTML a procesar (puede ser un párrafo, lista, etc.).
    :param x_inicial: Coordenada x inicial (margen izquierdo).
    :param ancho_texto: Ancho disponible para el texto.
    :param y: Coordenada y actual.
    :param y_minimo: Coordenada y mínima antes de un salto de página.
    :param tipo: Tipo de elemento Markdown (párrafo, lista, etc.).
    :param espacio_entre_lineas: Espaciado entre líneas.
    :return: Nueva coordenada y.
    """
    # Si el tag es un objeto BeautifulSoup (un elemento HTML)
    if isinstance(tag, str):
        texto = tag
    else:
        # Manejar texto en negrita (strong, b)
        if tag.name in ['strong', 'b']:
            texto = f"**{tag.get_text()}**"
            estilo = "Helvetica-Bold"
        else:
            texto = tag.get_text()
            estilo = "Helvetica"
    
    lineas = wrap(texto, width=int(ancho_texto / 6))  # Aproximadamente 6 puntos por carácter
    
    for linea in lineas:
        if y < y_minimo:  # Si no hay espacio suficiente, crear nueva página
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = A4[1] - 100  # Reiniciar coordenada y en la nueva página
        
        # Ajustar el tipo de formato basado en el tipo de tag Markdown
        if tipo == "h1":
            x_inicial = (A4[0] - pdf.stringWidth(linea, "Helvetica-Bold", 14)) / 2  # Centrar título h1
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(x_inicial, y, linea)
        elif tipo == "h2":
            x_inicial = (A4[0] - pdf.stringWidth(linea, "Helvetica-Bold", 12)) / 2  # Centrar título h2
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x_inicial, y, linea)
        elif tipo == "li":
            pdf.setFont("Helvetica", 10)
            pdf.drawString(x_inicial, y, linea)  # Para las listas, ajustamos el margen izquierdo
        else:
            pdf.setFont(estilo, 10)
            pdf.drawString(x_inicial, y, linea)

        y -= espacio_entre_lineas  # Moverse a la siguiente línea

    return y
def generar_graficos(datos_financieros: pd.DataFrame, ticker: str) -> str:
    """
    Genera gráficos financieros interactivos utilizando Plotly.

    Args:
        datos_financieros (pd.DataFrame): DataFrame con los datos financieros.
        ticker (str): Símbolo del ticker de la empresa.

    Returns:
        str: Ruta del archivo HTML generado con los gráficos.
    """
    # Verificar si el DataFrame contiene las columnas necesarias
    columnas_requeridas = ['Open', 'High', 'Low', 'Close', 'Volume']
    for columna in columnas_requeridas:
        if columna not in datos_financieros.columns:
            raise ValueError(f"El DataFrame no contiene la columna '{columna}'.")

    # Calcular medias móviles
    datos_financieros['MA20'] = datos_financieros['Close'].rolling(window=20).mean()
    datos_financieros['MA50'] = datos_financieros['Close'].rolling(window=50).mean()

    # Crear subplots: 2 filas (Gráfico de velas y volumen)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, subplot_titles=(f'Gráfico de Velas de {ticker}',
                                                               'Volumen de Transacciones'),
                        row_heights=[0.7, 0.3])

    # Gráfico de velas
    fig.add_trace(go.Candlestick(x=datos_financieros.index,
                                 open=datos_financieros['Open'],
                                 high=datos_financieros['High'],
                                 low=datos_financieros['Low'],
                                 close=datos_financieros['Close'],
                                 name='Velas'),
                  row=1, col=1)

    # Agregar medias móviles al gráfico de velas
    fig.add_trace(go.Scatter(x=datos_financieros.index, y=datos_financieros['MA20'],
                             mode='lines', name='MA 20 días'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=datos_financieros.index, y=datos_financieros['MA50'],
                             mode='lines', name='MA 50 días'),
                  row=1, col=1)

    # Gráfico de volumen
    fig.add_trace(go.Bar(x=datos_financieros.index, y=datos_financieros['Volume'],
                         showlegend=False),
                  row=2, col=1)

    # Actualizar el diseño
    fig.update_layout(title=f'Análisis Financiero de {ticker}',
                      yaxis_title='Precio',
                      xaxis_title='Fecha',
                      xaxis_rangeslider_visible=False)

    # Guardar el gráfico como archivo HTML
    ruta_html = f'C:\\Users\\nitro\Desktop\\Trabajos_genAi\\LangGraph\\rutas\\{ticker}_analisis_financiero.html'
    fig.write_html(ruta_html)

    return ruta_html