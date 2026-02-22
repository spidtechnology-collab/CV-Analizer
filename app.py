import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import json
from fpdf import FPDF

Configuración técnica
try:
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
st.error(f"Error: {e}")

st.set_page_config(page_title="Analizador", layout="wide")

def get_pdf(data):
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Reporte de Candidatos", ln=1, align='C')
for r in data:
nombre = str(r.get('nombre', 'N/A'))
nota = str(r.get('nota', 'N/A'))
pdf.multi_cell(0, 10, txt=f"Nombre: {nombre}\nAnalisis: {nota}\n---")
return pdf.output(dest='S').encode('latin-1', 'replace')

st.title("🛡️ Auditor de Talento")

if "ok" not in st.session_state:
st.session_state.ok = False

if not st.session_state.ok:
st.warning("Debe aceptar los terminos para continuar.")
if st.button("Aceptar Terminos y Entrar"):
st.session_state.ok = True
st.rerun()
else:
vacante = st.sidebar.text_area("Describa el puesto buscado:")
archivos = st.file_uploader("Subir CVs (PDF)", type="pdf", accept_multiple_files=True)
