import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import qrcode
import io

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ACCESO ---
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
            st.error("Clave incorrecta.")
    st.stop()

# --- FORMULARIO ---
st.title("✈️ Registro de Instructores - Sky Gen AI")
with st.form("sky_form"):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nombres")
        ced_n = st.text_input("Cédula")
        ws = st.text_input("WhatsApp")
    with col2:
        ape = st.text_input("Apellidos")
        mail = st.text_input("Email (@gmail.com)")
        materia = st.text_input("Materia")

    normas = st.text_area("Normas técnicas")
    apps = st.multiselect("Apps Google:", ["Drive", "Classroom", "Gemini AI"])
    
    submit = st.form_submit_button("Enviar Inscripción")

if submit:
    # Crear nueva fila de datos
    new_data = pd.DataFrame([{
        "Nombres": nom, "Apellidos": ape, "Cedula": ced_n, 
        "WhatsApp": ws, "Email": mail, "Materia": materia, 
        "Normas": normas, "Apps_Google": str(apps)
    }])
    
    # Obtener datos existentes y agregar el nuevo
    try:
        existing_data = conn.read(worksheet="Sheet1", usecols=list(range(8)))
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ ¡Datos guardados en la nube!")
        st.balloons()
    except Exception as e:
        st.error("Error al conectar con la base de datos. Verifique el link en Secrets.")
