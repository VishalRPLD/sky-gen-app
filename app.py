import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import qrcode
import io

# --- CONFIGURACIÓN ESTÉTICA SKY GEN AI ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="centered")

# Estilos minimalistas
st.markdown("""
    <style>
    .stButton>button { background-color: #2C5BA3; color: white; border-radius: 10px; width: 100%; }
    h1 { color: #2C5BA3; text-align: center; }
    .stTextInput>div>div>input { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.warning("⚠️ Conexión a base de datos pendiente de configurar en Secrets.")

# --- ACCESO ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    # Mostrar Logo en pantalla de acceso
    try:
        st.image("logo.png", width=300)
    except:
        pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Entrar"):
        if pwd == "SkyCrew2026":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Clave incorrecta. Contacte al Prof. Lakha.")
    st.stop()

# --- FORMULARIO DE INSCRIPCIÓN ---
# Mostrar Logo arriba del formulario
st.image("logo.png", use_container_width=True)
st.title("Planilla de Inscripción")

with st.form("sky_form"):
    # Fila 1: Nombres y Apellidos
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nombres")
    with col2:
        ape = st.text_input("Apellidos")

    # Fila 2: Cédula y WhatsApp
    col3, col4 = st.columns([1, 2])
    with col3:
        ced_t = st.selectbox("Nacionalidad", ["V", "E"])
    with col4:
        ced_n = st.text_input("Número de Cédula")

    # Fila 3: Teléfono y Correo
    col5, col6 = st.columns(2)
    with col5:
        ws = st.text_input("Número teléfono móvil con WhatsApp")
    with col6:
        mail = st.text_input("Correo electrónico Gmail (estrictamente)")

    # Campos de Asignatura y Normas
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")
    
    st.subheader("🛠️ Google Workspace & Gemini")
    apps = st.multiselect("¿Qué aplicaciones de Google ha utilizado en los últimos 3 meses?", 
                         ["Drive", "Classroom", "Docs", "Sheets", "Forms", "Meet", "Google Gemini AI"])
    
    if "Google Gemini AI" in apps:
        uso_gemini = st.multiselect("¿Qué material ha generado con Gemini?", 
                                   ["Guiones", "Imágenes", "Vídeos", "Investigaciones Profundas", "Material Didáctico"])

    submit = st.form_submit_button("Enviar Inscripción")

if submit:
    if not mail.endswith("@gmail.com"):
        st.error("❌ Error: Debe utilizar estrictamente una cuenta @gmail.com.")
    else:
        # Preparar datos para Google Sheets
        new_data = pd.DataFrame([{
            "Nombres": nom, "Apellidos": ape, "Cedula": f"{ced_t}-{ced_n}", 
            "WhatsApp": ws, "Email": mail, "Asignaturas": materia, 
            "Normas": normas, "Apps_Google": str(apps)
        }])
        
        try:
            # Guardado en Google Sheets
            existing_data = conn.read(worksheet="Sheet1")
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("✅ ¡Inscripción registrada en la base de datos!")
            
            # Generar link de WhatsApp para aviso al Director
            wa_link = f"https://wa.me/584126168188?text=Enviar%20Inscripción:%20{nom}%20{ape}%20({ced_t}-{ced_n})"
            st.markdown(f'[📲 Enviar Inscripción al Director]({wa_link})')
            st.balloons()
        except:
            st.warning("✅ Inscripción procesada localmente. (Conexión a Sheets no detectada).")
            st.markdown(f'[📲 Enviar Inscripción vía WhatsApp](https://wa.me/584126168188?text=Inscripción:%20{nom}%20{ape})')
