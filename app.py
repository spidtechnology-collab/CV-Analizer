import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF

# 1. IMPORTANTE: st.set_page_config DEBE ser el primer comando de Streamlit
st.set_page_config(page_title="Analizador", layout="wide")

# Configuración de API con manejo de errores
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración: {e}")

def get_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    # Usamos 'Arial' (fpdf1) o 'helvetica' (fpdf2). 'helvetica' es más estándar.
    pdf.set_font("helvetica", size=12)
    pdf.cell(200, 10, txt="Reporte de Candidatos", ln=1, align='C')
    
    for r in data:
        nombre = str(r.get('nombre', 'N/A'))
        nota = str(r.get('nota', 'N/A'))
        # Añadimos contenido
        pdf.multi_cell(0, 10, txt=f"Nombre: {nombre}\nAnalisis: {nota}\n---")
    
    # Retornamos los bytes del PDF
    return pdf.output(dest='S')

st.title("🛡️ Auditor de Talento")

# Lógica de sesión
if "ok" not in st.session_state:
    st.session_state.ok = False

if not st.session_state.ok:
    st.info("Bienvenido al Auditor de Talento. Por favor, acepta para continuar.")
    if st.button("Aceptar e Ingresar"):
        st.session_state.ok = True
        st.rerun()
else:
    # Interfaz principal una vez aceptado
    with st.sidebar:
        vacante = st.text_area("Descripción del Puesto:")
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.ok = False
            st.rerun()

    archivos = st.file_uploader("Subir CVs", type="pdf", accept_multiple_files=True)

    if archivos and vacante:
        st.success(f"Se han cargado {len(archivos)} archivos. ¡Listo para analizar!")
        # Aquí iría tu lógica para procesar los PDF con PdfReader y Gemini
