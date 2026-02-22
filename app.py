import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="Auditor de Talento", layout="wide")

# 2. Configuración de API
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Error: Configura 'GOOGLE_API_KEY' en los secrets de Streamlit.")

# Función para extraer texto de PDF
def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Función para generar el PDF de reporte
def create_report_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Análisis de Candidatos", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("helvetica", size=12)
    for r in data:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Candidato: {r['nombre']}", ln=True)
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 8, txt=f"Análisis:\n{r['nota']}")
        pdf.ln(5)
        pdf.cell(0, 0, "", "T", ln=True) # Línea divisoria
        pdf.ln(5)
    
    return pdf.output(dest='S')

# --- INTERFAZ DE USUARIO ---
st.title("🛡️ Auditor de Talento")

if "ok" not in st.session_state:
    st.session_state.ok = False

if not st.session_state.ok:
    st.info("Bienvenido. Por favor, acepta para continuar.")
    if st.button("Aceptar e Ingresar"):
        st.session_state.ok = True
        st.rerun()
else:
    with st.sidebar:
        vacante = st.text_area("Descripción del Puesto (Requerimientos):", height=300)
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.ok = False
            st.rerun()

    archivos = st.file_uploader("Subir CVs (Formatos PDF)", type="pdf", accept_multiple_files=True)

    if archivos and vacante:
        if st.button("🚀 Iniciar Análisis con IA"):
            resultados = []
            progreso = st.progress(0)
            
            for i, archivo in enumerate(archivos):
                with st.spinner(f"Analizando {archivo.name}..."):
                    # Extraer texto del CV
                    texto_cv = extract_text(archivo)
                    
                    # Prompt para Gemini
                    prompt = f"""
                    Actúa como un reclutador experto. Compara el siguiente CV con la descripción de la vacante.
                    
                    VACANTE:
                    {vacante}
                    
                    CV:
                    {texto_cv}
                    
                    PROPORCIONA:
                    1. Un resumen de compatibilidad (0 a 100%).
                    2. Puntos fuertes y debilidades.
                    3. Conclusión de si es apto o no.
                    Se breve y directo.
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        resultados.append({
                            "nombre": archivo.name,
                            "nota": response.text
                        })
                    except Exception as e:
                        st.error(f"Error con {archivo.name}: {e}")
                
                progreso.progress((i + 1) / len(archivos))

            # Mostrar resultados en pantalla
            st.divider()
            st.subheader("Resultados del Análisis")
            
            for res in resultados:
                with st.expander(f"📄 Candidato: {res['nombre']}"):
                    st.markdown(res['nota'])

            # Botón para descargar reporte
            pdf_bytes = create_report_pdf(resultados)
            st.download_button(
                label="📥 Descargar Reporte en PDF",
                data=pdf_bytes,
                file_name="analisis_talento.pdf",
                mime="application/pdf"
            )
