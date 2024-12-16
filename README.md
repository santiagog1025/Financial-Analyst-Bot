# Generador de Reportes Financieros

Este proyecto es una aplicación avanzada que genera reportes financieros interactivos utilizando datos históricos de Yahoo Finance y noticias relevantes del mercado. Integra múltiples tecnologías de inteligencia artificial, incluyendo LangChain, agentes multi-modalidades y gráficos interactivos para proporcionar análisis financiero detallado, tendencias de mercado y la capacidad de descargar informes profesionales en formato PDF.

## Características

- **Análisis Financiero Automatizado:** Obtiene y analiza datos históricos de precios, volúmenes y tendencias de acciones utilizando Yahoo Finance.
- **Multi-Agentes de IA:** Implementa agentes especializados para extracción de datos financieros, análisis de datos y generación de reportes, coordinados mediante LangChain y StateGraph.
- **Noticias del Mercado:** Integra noticias relevantes relacionadas con las acciones mediante DuckDuckGo Search API para enriquecer el análisis.
- **Gráficos Interactivos:** Genera gráficos avanzados con Plotly, incluyendo velas financieras, medias móviles y volúmenes.
- **Reportes en PDF:** Convierte los análisis y gráficos en documentos PDF descargables, estructurados y fáciles de interpretar.
- **Respuestas Contextualizadas:** El sistema utiliza modelos de lenguaje para personalizar las respuestas basadas en la consulta específica del usuario.

## Requisitos

Asegúrate de tener Python 3.8 o superior instalado. Instala las dependencias requeridas ejecutando:

```bash
pip install -r requirements.txt
```

## Instalación

1. Clona este repositorio:

```bash
git clone (https://github.com/santiagog1025/Bot_financiero)
cd Bot_financiero
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno en un archivo `.env`:

```env
GROQ_API_KEY=<TU_CLAVE_API_GROQ>
```

## Uso

### Backend

1. Inicia el servidor FastAPI:

```bash
uvicorn main:app --reload
```


### Frontend

1. Ejecuta la aplicación Streamlit:

```bash
streamlit run app.py
```

2. Ingresa tu consulta financiera en la interfaz de usuario.
3. Visualiza el análisis y los gráficos interactivos generados.
4. Descarga el informe en formato PDF si es necesario.

## Estructura del Proyecto

```plaintext
.
├── app.py                   # Código del frontend en Streamlit
├── main.py                  # Backend en FastAPI
├── model/
│   └── ai_model.py          # Lógica de los agentes de IA
├── utils/
│   ├── pdf_generator.py     # Función para generar PDFs
│   └── graph_generator.py   # Función para generar gráficos interactivos
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación del proyecto
└── .env                     # Variables de entorno (no incluido por defecto)
```

## Funcionalidades Clave

### Generar Datos y Gráficos
Endpoint del backend:

- **URL:** `/generar_datos/`
- **Método:** POST
- **Parámetros:**
  - `consulta`: Consulta financiera del usuario.
- **Respuesta:**
  - `reporte_texto`: Texto del reporte generado.
  - `ruta_figura`: Ruta del gráfico HTML generado.
  - `reporte_id`: ID único del reporte.

### Descargar Reporte en PDF
Endpoint del backend:

- **URL:** `/descargar_pdf/`
- **Método:** POST
- **Parámetros:**
  - `reporte_id`: ID único del reporte.
- **Respuesta:**
  - Archivo PDF generado.

## Tecnologías Utilizadas

- **FastAPI:** Backend para la generación de datos y reportes.
- **Streamlit:** Frontend para la visualización interactiva.
- **Plotly:** Gráficos interactivos.
- **ReportLab:** Generación de PDFs.
- **DuckDuckGo Search API:** Para obtener noticias relevantes.
- **Yahoo Finance:** Para datos financieros históricos.


## Licencia

Este proyecto está bajo la licencia MIT. 

---

¡Gracias por utilizar el Generador de Reportes Financieros! 🎉
