import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. VERIFICACIÓN DE LIBRERÍAS
try:
    from fpdf import FPDF
except ImportError:
    st.error("❌ Error: La librería 'fpdf2' no está instalada.")
    st.info("Revisa que tu archivo 'requirements.txt' incluya 'fpdf2' y haz un Reboot de la app.")
    st.stop()

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Auditor de Talento", layout="wide", page_icon="🛡️")

# 3. CONFIGURACIÓN DE API
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    else:
        st.warning("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
except Exception as e:
    st.error(f"Error de IA: {e}")

# --- FUNCIONES ---
def extraer_texto_pdf(archivo):
    try:
        reader = PdfReader(archivo)
        texto = ""
        for pagina in reader.pages:
            t = pagina.extract_text()
            if t: texto += t
        return texto
    except Exception as e:
        return f"Error: {e}"

def crear_pdf_reporte(resultados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Analisis de Candidatos", ln=True, align='C')
    pdf.ln(10)
    for r in resultados:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Candidato: {r['nombre']}", ln=True)
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 8, txt=r['analisis'])
        pdf.ln(5)
        pdf.cell(0, 0, "", "T", ln=True)
        pdf.ln(5)
    return pdf.output()

# --- INTERFAZ ---
st.title("🛡️ Auditor de Talento")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.info("Bienvenido. Haz clic para ingresar.")
    if st.button("Ingresar"):
        st.session_state.auth = True
        st.rerun()
else:
    with st.sidebar:
        st.header("Configuración")
        vacante = st.text_area("Descripción de la Vacante:", height=300)
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    archivos = st.file_uploader("Subir CVs (PDF)", type="pdf", accept_multiple_files=True)

    if archivos and vacante:
        if st.button("🚀 Analizar"):
            lista_res = []
            barra = st.progress(0)
            for i, cv in enumerate(archivos):
                with st.spinner(f"Analizando {cv.name}..."):
                    texto = extraer_texto_pdf(cv)
                    prompt = f"Analiza este CV:\n{texto}\nPara esta vacante:\n{vacante}\nDa un % de match y resumen de fortalezas/debilidades."
                    try:
                        res = model.generate_content(prompt)
                        lista_res.append({"nombre": cv.name, "analisis": res.text})
                    except Exception as e:
                        st.error(f"Error en {cv.name}: {e}")
                barra.progress((i + 1) / len(archivos))

            for item in lista_res:
                with st.expander(f"Candidato: {item['nombre']}"):
                    st.markdown(item['analisis'])

            if lista_res:
                try:
                    pdf_out = crear_pdf_reporte(lista_res)
                    st.download_button("📥 Descargar Reporte", data=bytes(pdf_out), file_name="reporte.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Error al generar PDF: {e}")
    
    elif archivos and not vacante:
        st.warning("⚠️ Por favor, ingresa la descripción de la vacante.")

