import streamlit as st
import pandas as pd
from fpdf import FPDF
import qrcode
import io

# --- CONFIGURACIÓN DE ESTÉTICA SKY GEN AI ---
st.set_page_config(page_title="Sky Gen AI - Registro", page_icon="✈️")

# Estilos minimalistas
st.markdown("""
    <style>
    .stButton>button { background-color: #2C5BA3; color: white; border-radius: 10px; }
    h1 { color: #2C5BA3; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS IA (Offline) ---
IA_SUGGESTIONS = {
    "Derecho Aeronáutico": "OACI Anexo 13 y RAV 1, 2, 5.",
    "Navegación Aérea": "OACI Anexo 2, Anexo 11 y RAV 211, 281.",
    "Factores Humanos": "OACI Doc 9683 y RAV 111.",
    "Instrucción": "OACI Doc 9841 y RAV 141."
}

# --- ACCESO CON CLAVE ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Entrar"):
        if pwd == "SkyCrew2026":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Acceso denegado.")
    st.stop()

# --- FORMULARIO ---
st.title("✈️ Inscripción de Instructores")
with st.form("sky_form"):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nombres")
        ced_t = st.selectbox("Cédula", ["V", "E"])
        ws = st.text_input("WhatsApp (+58...)")
    with col2:
        ape = st.text_input("Apellidos")
        ced_n = st.text_input("Número de Cédula")
        mail = st.text_input("Correo Gmail (@gmail.com)")
    
    materia = st.text_input("Materia que dicta")
    
    # IA en tiempo real
    if materia in IA_SUGGESTIONS:
        st.info(f"💡 **Sugerencia IA:** Para esta materia use {IA_SUGGESTIONS[materia]}")
        
    normas = st.text_area("Normas técnicas de apoyo")
    
    st.subheader("🛠️ Google Workspace & Gemini")
    apps = st.multiselect("Apps usadas:", ["Drive", "Classroom", "Docs", "Gemini AI"])
    
    if "Gemini AI" in apps:
        uso_gemini = st.multiselect("¿Para qué ha usado Gemini?", ["Guiones", "Material Didáctico", "Investigación"])

    submit = st.form_submit_button("Registrar Inscripción")

if submit:
    if not mail.endswith("@gmail.com"):
        st.error("Use un correo @gmail.com")
    else:
        st.success("✅ ¡Registro completado!")
        # Botón para enviar por WhatsApp
        msg = f"https://wa.me/584126168188?text=Inscripción%20Sky%20Gen%20AI:%20{nom}%20{ape}"
        st.markdown(f"[📲 Enviar Inscripción]({msg})")
        st.balloons()
