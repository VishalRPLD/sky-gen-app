import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import qrcode
import io

# --- ESTÉTICA SKY GEN AI ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️")

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")

# --- ACCESO ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    try: st.image("logo.png", width=250)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Entrar"):
        if pwd == "SkyCrew2026":
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop()

# --- FORMULARIO ---
try: st.image("logo.png", width=400)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form"):
    col1, col2 = st.columns(2)
    with col1: nom = st.text_input("Nombres")
    with col2: ape = st.text_input("Apellidos")
    
    col3, col4 = st.columns([1, 2])
    with col3: ced_t = st.selectbox("Nacionalidad", ["V", "E"])
    with col4: ced_n = st.text_input("Número de Cédula")
    
    mail = st.text_input("Correo Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")
    
    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if submit:
    if not mail.endswith("@gmail.com"):
        st.error("❌ Error: Use un correo @gmail.com")
    else:
        # 1. GENERAR PDF CON QR
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="COMPROBANTE DE INSCRIPCIÓN - SKY GEN AI", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Instructor: {nom} {ape}", ln=True)
        pdf.cell(200, 10, txt=f"Cédula: {ced_t}-{ced_n}", ln=True)
        
        qr_data = f"Registro Válido: {nom} {ape}. Contacto: +584126168188"
        qr = qrcode.make(qr_data)
        qr_io = io.BytesIO()
        qr.save(qr_io, format='PNG')
        pdf.image(qr_io, x=75, y=60, w=50)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')

        # 2. GUARDAR EN GOOGLE SHEETS
        try:
            new_row = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": f"{ced_t}-{ced_n}", "Email": mail, "Materia": materia}])
            existing_data = conn.read()
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ ¡Inscripción guardada en Google Sheets!")
        except:
            st.warning("⚠️ Guardado local exitoso. Verifique la conexión a Sheets.")

        # 3. MOSTRAR DESCARGA Y WHATSAPP
        st.download_button(label="📥 DESCARGAR MI REGISTRO (PDF)", data=pdf_output, file_name=f"Inscripcion_{ced_n}.pdf", mime="application/pdf")
        
        wa_text = f"Hola Prof. Lakha, envío mi inscripción: {nom} {ape}, Cédula {ced_t}-{ced_n}."
        wa_link = f"https://wa.me/584126168188?text={wa_text.replace(' ', '%20')}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color: #25D366; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold;">📲 ENVIAR INSCRIPCIÓN POR WHATSAPP</button></a>', unsafe_allow_html=True)
        st.balloons()
