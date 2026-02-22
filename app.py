import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import plotly.graph_objects as go
import json

# --- CONFIGURACIÓN INICIAL ---
genai.configure(api_key="TU_API_KEY_AQUI")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Auditor de Talento IA", layout="wide")

# --- INTERFAZ: FASE 1 (AUTORIZACIÓN) ---
st.title("🛡️ Plataforma de Evaluación de Candidatos")

if "autorizado" not in st.session_state:
    st.session_state.autorizado = False

if not st.session_state.autorizado:
    st.warning("### Aviso de Privacidad y Deslinde de Responsabilidad")
    st.write("""
    Al continuar, usted autoriza el procesamiento de datos personales contenidos en los CVs. 
    Este programa es una herramienta de apoyo y no sustituye el juicio humano. 
    El desarrollador se deslinda de cualquier conflicto de intereses o decisiones de contratación.
    """)
    if st.button("Acepto los términos y deseo cargar CVs"):
        st.session_state.autorizado = True
        st.rerun()
else:
    # --- FASE 2: CARGA DE ARCHIVOS ---
    st.sidebar.header("Configuración de Vacante")
    jd_text = st.sidebar.text_area("Descripción del Puesto (Requerimientos):", height=200)
    
    uploaded_files = st.file_uploader("Cargar CVs (Formato PDF)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and jd_text:
        if st.button("🚀 Analizar CVs"):
            resultados_batch = []
            
            for file in uploaded_files:
                # Extracción de texto
                reader = PdfReader(file)
                cv_content = "".join([page.extract_text() for page in reader.pages])
                
                # Prompt estructurado para obtener JSON
                prompt = f"""
                Analiza el CV adjunto contra la Descripción de Puesto (JD). 
                JD: {jd_text}
                CV: {cv_content}
                
                Devuelve estrictamente un objeto JSON con:
                - nombre_candidato: str
                - experiencia: int (0-100)
                - educacion: int (0-100)
                - habilidades: int (0-100)
                - fiabilidad: int (0-100)
                - resumen_reservas: str (máximo 2 líneas)
                """
                
                response = model.generate_content(prompt)
                # Limpiamos la respuesta para asegurar que sea JSON puro
                json_data = response.text.replace('```json', '').replace('```', '')
                resultados_batch.append(json.loads(json_data))
            
            st.session_state.resultados = resultados_batch

    # --- FASE 3: VISUALIZACIÓN DE RESULTADOS ---
    if "resultados" in st.session_state:
        st.divider()
        st.header("📊 Resultados del Análisis")
        
        for res in st.session_state.resultados:
            # Cálculo del Promedio
            promedio = (res['experiencia'] + res['educacion'] + res['habilidades'] + res['fiabilidad']) / 4
            
            # Lógica de Estatus
            if promedio >= 86:
                status = "✅ APROBADO"
                color = "green"
            elif promedio >= 70:
                status = "⚠️ APROBADO CON RESERVAS"
                color = "orange"
            else:
                status = "🚨 SUJETO A VALIDACIÓN (BAJO)"
                color = "red"
            
            with st.expander(f"Candidato: {res['nombre_candidato']} - Score: {promedio}%"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Gráfica de Pay (Pie) para mostrar el peso de los pilares
                    fig = go.Figure(data=[go.Pie(
                        labels=['Experiencia', 'Educación', 'Habilidades', 'Fiabilidad'],
                        values=[res['experiencia'], res['educacion'], res['habilidades'], res['fiabilidad']],
                        hole=.3
                    )])
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown(f"### Estatus: :{color}[{status}]")
                    st.write(f"**Promedio General:** {promedio}%")
                    st.write(f"**Nota de la IA:** {res['resumen_reservas']}")
                    
                    # Tabla de detalles
                    st.table({
                        "Pilar": ["Experiencia", "Educación", "Habilidades", "Fiabilidad"],
                        "Calificación": [res['experiencia'], res['educacion'], res['habilidades'], res['fiabilidad']]
                    })
