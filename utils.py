import markdown
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from bs4 import BeautifulSoup


def guardar_pdf(contenido_markdown, archivo_pdf):
    """
    Convierte contenido Markdown almacenado en una variable a un archivo PDF,
    interpretando las etiquetas HTML generadas.

    :param contenido_markdown: Texto en formato Markdown.
    :param archivo_pdf: Ruta del archivo PDF de salida.
    """
    try:
        # Convertir el contenido Markdown a HTML
        contenido_html = markdown.markdown(contenido_markdown)

        
        # Usar BeautifulSoup para interpretar el HTML
        soup = BeautifulSoup(contenido_html, "html.parser")
        
        # Configurar el PDF
        pdf = canvas.Canvas(archivo_pdf, pagesize=letter)
        ancho_pagina, alto_pagina = letter
        y = alto_pagina - 40  # Margen superior
        pdf.setFont("Helvetica", 10)
        
        # Procesar cada elemento del HTML
        for tag in soup.contents:
            if y < 40:  # Si el texto alcanza el margen inferior, añadir una página nueva
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = alto_pagina - 40
            
            if tag.name == "h1":
                pdf.setFont("Helvetica-Bold", 14)
                pdf.drawString(40, y, tag.text)
                y -= 20
            elif tag.name == "p":
                pdf.setFont("Helvetica", 10)
                pdf.drawString(40, y, tag.text)
                y -= 15
            elif tag.name == "ul":
                for li in tag.find_all("li"):
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(60, y, f"- {li.text}")
                    y -= 12
            elif tag.name == "strong":
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(40, y, tag.text)
                y -= 12
            elif tag.name == "em":
                pdf.setFont("Helvetica-Oblique", 10)
                pdf.drawString(40, y, tag.text)
                y -= 12
            elif tag.name == "a":
                texto_enlace = f"{tag.text} ({tag['href']})"
                pdf.setFont("Helvetica", 10)
                pdf.drawString(40, y, texto_enlace)
                y -= 15
        
        pdf.save()
        print(f"PDF generado correctamente: {archivo_pdf}")
    
    except Exception as e:
        print(f"Error al convertir el archivo: {e}")

