import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import sys

# 1. VERIFICACIÓN DE LIBRERÍAS (Soluciona el error de importación)
try:
    from fpdf import FPDF
except ImportError:
    st.error("❌ Error: La librería 'fpdf2' no se encuentra instalada en el servidor.")
    st.info("Asegúrate de que tu archivo 'requirements.txt' esté en la raíz de GitHub y contenga la línea: fpdf2")
    st.stop()

# 2. CONFIGURACIÓN DE PÁGINA (Debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Auditor de Talento", layout="wide", page_icon="🛡️")

# 3. CONFIGURACIÓN DE API GEMINI
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.warning("⚠️ Falta la clave 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
except Exception as e:
    st.error(f"Error al configurar la IA: {e}")

# --- FUNCIONES DE APOYO ---

def extraer_texto_pdf(archivo):
    """Lee el contenido de un archivo PDF."""
    try:
        reader = PdfReader(archivo)
        texto_completo = ""
        for pagina in reader.pages:
            texto_completo += pagina.extract_text()
        return texto_completo
    except Exception as e:
        return f"Error al leer PDF: {e}"

def crear_pdf_descargable(lista_resultados):
    """Genera el reporte final en PDF usando fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Analisis de Candidatos", ln=True, align='C')
    pdf.ln(10)
    
    for res in lista_resultados:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Candidato: {res['nombre']}", ln=True)
        pdf.set_font("helvetica", size=10)
        # multi_cell permite saltos de línea automáticos
        pdf.multi_cell(0, 8, txt=res['analisis'])
        pdf.ln(5)
        pdf.cell(0, 0, "", "T", ln=True) # Línea horizontal
        pdf.ln(5)
    
    return pdf.output()

# --- INTERFAZ DE USUARIO ---

st.title("🛡️ Auditor de Talento")

# Lógica de ingreso (Session State)
if "acceso_permitido" not in st.session_state:
    st.session_state.acceso_permitido = False

if not st.session_state.acceso_permitido:
    st.info("Bienvenido al Auditor de Talento. Por favor, acepta para continuar.")
    if st.button("Aceptar e Ingresar"):
        st.session_state.acceso_permitido = True
        st.rerun()
else:
    # Sidebar para configuración
    with st.sidebar:
        st.header("Configuración de Vacante")
        descripcion_puesto = st.text_area("Descripción de la Vacante:", height=300, 
                                          placeholder="Pega aquí los requisitos, tecnologías y experiencia buscada...")
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.acceso_permitido = False
            st.rerun()

    # Área de carga de archivos
    archivos = st.file_uploader("Subir CVs de candidatos (PDF)", type="pdf", accept_multiple_files=True)

    if archivos and descripcion_puesto:
        if st.button("🚀 Iniciar Análisis con IA"):
            datos_finales = []
            progreso = st.progress(0)
            
            for idx, cv in enumerate(archivos):
                with st.spinner(f"Analizando {cv.name}..."):
                    # 1. Extraer texto del PDF
                    texto_cv = extraer_texto_pdf(cv)
                    
                    # 2. Consultar a Gemini
                    prompt_ia = f"""
                    Analiza la compatibilidad del siguiente CV con la descripción del puesto.
                    
                    PUESTO:
                    {descripcion_puesto}
                    
                    CV:
                    {texto_cv}
                    
                    PROPORCIONA:
                    1. Porcentaje de compatibilidad (0-100%).
                    2. Breve resumen de fortalezas.
                    3. Breve resumen de debilidades o falta de experiencia.
                    4. Veredicto: (Apto / No Apto / Potencial).
                    """
                    
                    try:
                        respuesta = model.generate_content(prompt_ia)
                        datos_finales.append({
                            "nombre": cv.name,
                            "analisis": respuesta.text
                        })
                    except Exception as e:
                        st.error(f"Error procesando {cv.name}: {e}")
                
                # Actualizar barra
                progreso.progress((idx + 1) / len(archivos))

            st.success("¡Análisis completado con éxito!")
            st.divider()

            # Mostrar resultados en pantalla
            for item in datos_finales:
                with st.expander(f"Ver reporte: {item['nombre']}"):
                    st.markdown(item['analisis'])

            # Botón de descarga de PDF
            try:
                pdf_output = crear_pdf_descargable(datos_finales)
                st.download_button(
                    label="📥 Descargar Reporte Completo (PDF)",
                    data=bytes(pdf_output),
                    file_name="reporte_seleccion.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"No se pudo generar el PDF descargable: {e}")

    elif not descripcion_puesto and archivos:
        st.warning("⚠️ Por favor, ingresa la descripción de la vacante en el panel lateral
