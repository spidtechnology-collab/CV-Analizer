import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import json
from fpdf import FPDF
from docx import Document
from io import BytesIO

try:
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')
except:
st.error("Error de API Key")

st.set_page_config(page_title="Analizador", layout="wide")

def get_pdf(data):
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Reporte de Candidatos", ln=1, align='C')
for r in data:
pdf.multi_cell(0, 10, txt=f"Nombre: {r.get('nombre', 'N/A')}\nAnalisis: {r.get('nota', 'N/A')}\n")
return pdf.output(dest='S').encode('latin-1', 'replace')

st.title("🛡️ Auditor de Talento")

if "ok" not in st.session_state:
st.session_state.ok = False

if not st.session_state.ok:
if st.button("Aceptar Terminos y Entrar"):
st.session_state.ok = True
st.rerun()
else:
vacante = st.sidebar.text_area("Puesto:")
archivos = st.file_uploader("Subir CVs", type="pdf", accept_multiple_files=True)
if archivos and vacante and st.button("Analizar"):
res = []
for a in archivos:
reader = PdfReader(a)
texto = "".join([p.extract_text() for p in reader.pages])
p = f"Analiza este CV: {texto} para el puesto: {vacante}. Responde solo JSON: {{'nombre': '...', 'nota': '...', 'puntos': 0}}"
try:
out = model.generate_content(p)
res.append(json.loads(out.text.replace('json', '').replace('', '')))
except:
st.error("Error en un archivo")
st.session_state.res = res
