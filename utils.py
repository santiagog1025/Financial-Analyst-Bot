import markdown
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from bs4 import BeautifulSoup
from textwrap import wrap

def guardar_pdf(contenido_markdown, archivo_pdf):
    """
    Convierte contenido Markdown almacenado en una variable a un archivo PDF,
    interpretando las etiquetas HTML generadas, con márgenes adecuados y texto centrado.

    :param contenido_markdown: Texto en formato Markdown.
    :param archivo_pdf: Ruta del archivo PDF de salida.
    """
    try:
        # Convertir el contenido Markdown a HTML
        contenido_html = markdown.markdown(contenido_markdown)

        # Usar BeautifulSoup para interpretar el HTML
        soup = BeautifulSoup(contenido_html, "html.parser")
        
        # Configurar el PDF con tamaño A4
        pdf = canvas.Canvas(archivo_pdf, pagesize=A4)
        ancho_pagina, alto_pagina = A4
        
        # Configurar márgenes (2.5 cm por cada lado) y centrar contenido verticalmente
        margen_izquierdo = 70
        margen_derecho = ancho_pagina - 70
        margen_superior = alto_pagina - 100  # Mayor espacio superior para centrar
        margen_inferior = 100
        y = margen_superior

        pdf.setFont("Helvetica", 10)

        # Ancho del texto en puntos (para ajustar párrafos largos)
        ancho_texto = margen_derecho - margen_izquierdo

        # Procesar cada elemento del HTML
        for tag in soup.contents:
            if y < margen_inferior:  # Si alcanza el margen inferior, añadir nueva página
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = margen_superior

            if tag.name == "h1":
                pdf.setFont("Helvetica-Bold", 14)
                y = escribir_parrafo_justificado(pdf, tag.text, margen_izquierdo, ancho_texto, y, margen_inferior, espacio_entre_lineas=20)
            elif tag.name == "h2":
                pdf.setFont("Helvetica-Bold", 12)
                y = escribir_parrafo_justificado(pdf, tag.text, margen_izquierdo, ancho_texto, y, margen_inferior, espacio_entre_lineas=18)
            elif tag.name == "p":
                pdf.setFont("Helvetica", 10)
                y = escribir_parrafo_justificado(pdf, tag.text, margen_izquierdo, ancho_texto, y, margen_inferior)
            elif tag.name == "ul":
                for li in tag.find_all("li"):
                    if y < margen_inferior:  # Verificar espacio disponible
                        pdf.showPage()
                        pdf.setFont("Helvetica", 10)
                        y = margen_superior
                    pdf.drawString(margen_izquierdo + 20, y, f"• {li.text}")  # Ajuste del margen
                    y -= 14  # Espacio entre ítems de la lista
            elif tag.name == "strong":
                pdf.setFont("Helvetica-Bold", 10)
                y = escribir_parrafo_justificado(pdf, tag.text, margen_izquierdo, ancho_texto, y, margen_inferior)
            elif tag.name == "em":
                pdf.setFont("Helvetica-Oblique", 10)
                y = escribir_parrafo_justificado(pdf, tag.text, margen_izquierdo, ancho_texto, y, margen_inferior)
            elif tag.name == "a":
                texto_enlace = f"{tag.text} ({tag['href']})"
                pdf.setFont("Helvetica", 10)
                y = escribir_parrafo_justificado(pdf, texto_enlace, margen_izquierdo, ancho_texto, y, margen_inferior)
        
        pdf.save()
        print(f"PDF generado correctamente: {archivo_pdf}")
    
    except Exception as e:
        print(f"Error al convertir el archivo: {e}")

def escribir_parrafo_justificado(pdf, texto, x_inicial, ancho_texto, y, y_minimo, espacio_entre_lineas=14):
    """
    Escribe un párrafo justificado en el PDF respetando los márgenes y los saltos de línea.

    :param pdf: Objeto Canvas de ReportLab.
    :param texto: Texto del párrafo.
    :param x_inicial: Coordenada x inicial (margen izquierdo).
    :param ancho_texto: Ancho disponible para el texto.
    :param y: Coordenada y actual.
    :param y_minimo: Coordenada y mínima antes de un salto de página.
    :param espacio_entre_lineas: Espaciado entre líneas.
    :return: Nueva coordenada y.
    """
    # Dividir el texto en líneas ajustadas al ancho disponible
    lineas = wrap(texto, width=int(ancho_texto / 6))  # Aproximadamente 6 puntos por carácter
    
    for linea in lineas:
        if y < y_minimo:  # Verificar si queda espacio para otra línea
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = A4[1] - 100  # Reiniciar desde el margen superior
        texto = pdf.beginText(x_inicial, y)
        texto.setTextOrigin(x_inicial, y)
        texto.textLine(linea)
        pdf.drawText(texto)
        y -= espacio_entre_lineas

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
    ruta_html = f'{ticker}_analisis_financiero.html'
    fig.write_html(ruta_html)

    return ruta_html