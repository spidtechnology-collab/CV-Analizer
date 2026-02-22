import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import plotly.graph_objects as go
import json
from fpdf import FPDF
from docx import Document
from io import BytesIO

1. CONFIGURACIÓN DE SEGURIDAD Y API
try:
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel(
model_name='gemini-1.5-flash',
generation_config={"response_mime_type": "application/json"}
)
except Exception as e:
st.error(f"Revisa tu configuración de API en Streamlit: {e}")

st.set_page_config(page_title="Auditor de Talento IA", layout="wide")

2. FUNCIONES PARA DESCARGAR REPORTES
def generar_pdf(resultados):
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(190, 10, "Reporte de Analisis de Candidatos", ln=True, align='C')
for res in resultados:
pdf.ln(10)
pdf.set_font("Arial", "B", 12)
pdf.cell(190, 10, f"Candidato: {res.get('nombre_candidato', 'N/A')}", ln=True)
pdf.set_font("Arial", "", 10)
pdf.multi_cell(190, 7, f"Resumen: {res.get('resumen_reservas', '')}")
pdf.cell(190, 7, f"Puntajes - Exp: {res.get('experiencia')}% | Hab: {res.get('habilidades')}%", ln=True)
return pdf.output(dest='S').encode('latin-1', errors='replace')

def generar_docx(resultados):
doc = Document()
doc.add_heading('Reporte de Evaluación IA', 0)
for res in resultados:
doc.add_heading(f"Candidato: {res.get('nombre_candidato', 'N/A')}", level=1)
doc.add_paragraph(f"Nota de la IA: {res.get('resumen_reservas', '')}")
doc.add_paragraph(f"Puntajes: Exp: {res.get('experiencia')}% | Edu: {res.get('educacion')}% | Hab: {res.get('habilidades')}%")
bio = BytesIO()
doc.save(bio)
return bio.getvalue()

3. INTERFAZ DE USUARIO
st.title("🛡️ Plataforma de Evaluación de Candidatos")

if "autorizado" not in st.session_state:
st.session_state.autorizado = False

if not st.session_state.autorizado:
st.warning("### Aviso de Privacidad")
st.write("Al continuar, autoriza el procesamiento de datos personales en los CVs.")
if st.button("Acepto los términos"):
st.session_state.autorizado = True
st.rerun()
else:
# PANEL LATERAL
st.sidebar.header("Datos de la Vacante")
jd_text = st.sidebar.text_area("¿Qué buscas en el puesto?", height=200)
uploaded_files = st.file_uploader("Sube los CVs (en PDF)", type="pdf", accept_multiple_files=True)
