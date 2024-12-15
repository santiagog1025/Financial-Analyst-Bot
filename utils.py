import pdfkit
import markdown2

def guardar_pdf(contenido_markdown: str, output_path: str):
    """
    Convierte contenido en formato Markdown a PDF y lo guarda en un archivo.

    Args:
        contenido_markdown (str): Texto en formato Markdown.
        output_path (str): Ruta del archivo PDF de salida.
    """
    # Convierte Markdown a HTML
    contenido_html = markdown2.markdown(contenido_markdown)
    
    # Configuración para pdfkit
    options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'enable-local-file-access': None,  # Permitir acceso local a archivos
        'quiet': ''  # Evita mensajes de salida innecesarios
    }

    try:
        # Generar el archivo PDF
        pdfkit.from_string(contenido_html, output_path, options=options)
        print(f"PDF generado exitosamente: {output_path}")
    except Exception as e:
        print(f"Error al generar el PDF: {e}")

# import markdown
# from fpdf import FPDF, HTMLMixin

# class PDF(FPDF, HTMLMixin):
#     """
#     Extensión de FPDF para soportar contenido HTML.
#     """
#     pass

# def guardar_pdf_desde_markdown(contenido_markdown: str, ruta_salida: str):
#     """
#     Convierte un texto en formato Markdown a un archivo PDF.

#     Args:
#         contenido_markdown (str): Texto en formato Markdown.
#         ruta_salida (str): Ruta donde se guardará el archivo PDF.
#     """
#     # Convertir el contenido de Markdown a HTML
#     contenido_html = markdown.markdown(contenido_markdown)
    
#     # Crear un PDF y agregar el contenido HTML renderizado
#     pdf = PDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.set_font("Arial", size=12)
#     pdf.write_html(contenido_html)

#     # Guardar el PDF
#     pdf.output(ruta_salida)

# # Ejemplo de uso
# contenido_markdown = """
# **Informe Integral sobre el Precio Promedio de Google**

# ### Introducción
# En este informe, nos enfocamos en el análisis del precio promedio de Google, utilizando datos
# históricos y noticias del mercado para proporcionar una visión integral de la situación actual.

# ### Análisis Financiero
# - **Tendencias recientes en los últimos 30 días**: El precio de Google ha experimentado una tendencia positiva.
# - **Media del precio de cierre en los últimos 7 días**: La media es de aproximadamente $2,850.
# - **Media móvil de 200 periodos**: Indica una tendencia a largo plazo positiva.

# ### Conclusión
# Google muestra una tendencia positiva tanto en el corto como en el largo plazo.
# """

# guardar_pdf_desde_markdown(contenido_markdown, "informe_financiero_google.pdf")
