import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero)
st.set_page_config(page_title="Auditor de Talento", layout="wide")

# 2. CONFIGURACIÓN DE API
try:
    # Intenta obtener la clave desde los secrets de Streamlit
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Error de configuración: Asegúrate de tener 'GOOGLE_API_KEY' en los Secrets de Streamlit.")

# --- FUNCIONES DE AYUDA ---

def extraer_texto_pdf(archivo_pdf):
    """Extrae todo el texto de un archivo PDF subido."""
    try:
        reader = PdfReader(archivo_pdf)
        texto = ""
        for pagina in reader.pages:
            texto_pag = pagina.extract_text()
            if texto_pag:
                texto += texto_pag
        return texto
    except Exception as e:
        return f"Error al leer el PDF: {e}"

def generar_pdf_reporte(datos_analisis):
    """Crea un PDF con los resultados usando fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    
    # Título del documento
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Auditoria de Talento", ln=True, align='C')
    pdf.ln(10)
    
    for item in datos_analisis:
        # Nombre del candidato
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Candidato: {item['nombre']}", ln=True)
        
        # Resultado del análisis
        pdf.set_font("helvetica", size=10)
        # multi_cell maneja párrafos largos automáticamente
        pdf.multi_cell(0, 8, txt=item['analisis'])
        pdf.ln(5)
        pdf.cell(0, 0, "", "T", ln=True) # Línea divisoria
        pdf.ln(5)
    
    # Retorna los bytes del PDF generado
    return pdf.output()

# --- INTERFAZ DE USUARIO (UI) ---

st.title("🛡️ Auditor de Talento")

# Manejo de sesión (Aceptación de términos)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.info("Bienvenido al sistema de análisis de CVs. Por favor, confirma para entrar.")
    if st.button("Aceptar e Ingresar"):
        st.session_state.autenticado = True
        st.rerun()
else:
    # Barra lateral para la descripción de la vacante
    with st.sidebar:
        st.header("Configuración")
        descripcion_puesto = st.text_area("Descripción de la Vacante:", height=300, 
                                          placeholder="Pega aquí los requisitos del puesto...")
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    # Área principal para subir archivos
    archivos_cvs = st.file_uploader("Sube los CVs de los candidatos (PDF)", 
                                    type="pdf", 
                                    accept_multiple_files=True)

    if archivos_cvs and descripcion_puesto:
        if st.button("🚀 Iniciar Análisis con IA"):
            resultados = []
            barra_progreso = st.progress(0)
            
            for index, cv in enumerate(archivos_cvs):
                with st.spinner(f"Analizando: {cv.name}..."):
                    # 1. Extraer texto
                    texto_cv = extraer_texto_pdf(cv)
                    
                    # 2. Preparar el envío a Gemini
                    prompt = f"""
                    Eres un experto en Recursos Humanos. Analiza la compatibilidad del candidato con la vacante.
                    
                    VACANTE:
                    {descripcion_puesto}
                    
                    CV DEL CANDIDATO:
                    {texto_cv}
                    
                    ENTREGA UN RESUMEN QUE INCLUYA:
                    - % de compatibilidad.
                    - 3 Puntos fuertes.
                    - 3 Áreas de mejora o faltantes.
                    - Veredicto final (Apto / No apto).
                    """
                    
                    try:
                        respuesta = model.generate_content(prompt)
                        resultados.append({
                            "nombre": cv.name,
                            "analisis": respuesta.text
                        })
                    except Exception as e:
                        st.error(f"Error procesando {cv.name}: {e}")
                
                # Actualizar barra de progreso
                barra_progreso.progress((index + 1) / len(archivos_cvs))

            st.success("¡Análisis completado!")
            st.divider()

            # Mostrar resultados en pantalla
            for res in resultados:
                with st.expander(f"Ver análisis de: {res['nombre']}"):
                    st.markdown(res['analisis'])

            # Botón para descargar el reporte final
            try:
                reporte_pdf = generar_pdf_reporte(resultados)
                st.download_button(
                    label="📥 Descargar Reporte Completo (PDF)",
                    data=bytes(reporte_pdf),
                    file_name="analisis_talento_ia.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"No se pudo generar el archivo PDF descargable: {e}")
    
    elif not descripcion_puesto and archivos_cvs:
        st.warning("⚠️ Por favor, ingresa la descripción de la vacante en la barra lateral.")
