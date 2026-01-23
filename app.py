import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF, XPos, YPos
import qrcode
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURACIÓN ADAPTATIVA ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="centered")

# CSS para botones adaptativos a pantallas móviles
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .stDownloadButton > button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #F0F2F6; color: black; border: 1px solid #CCC; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN (Modo Silencioso) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    pass

# --- FUNCIÓN DE CORREO ---
def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Registro Sky Gen AI - {datos['nom']}"
        msg.attach(MIMEText(f"Hola {datos['nom']}, adjuntamos su comprobante de inscripción.", 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Comprobante_SkyGen.pdf")
        msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- ACCESO ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if pwd == "SkyCrew2026": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- FORMULARIO ---
st.title("Planilla de Inscripción")
with st.form("sky_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    ced = st.text_input("Cédula")
    mail = st.text_input("Correo Gmail")
    mat = st.text_input("Asignatura")
    btn_reg = st.form_submit_button("GENERAR INSCRIPCIÓN")

if btn_reg:
    if not mail or not nom:
        st.error("❌ Complete los campos básicos.")
    else:
        # --- PASO 1: GENERAR PDF Y QR (Proceso Local, No depende de Google) ---
        qr_io = io.BytesIO()
        qrcode.make(f"SkyGenAI: {nom} {ape}\nID: {ced}").save(qr_io, format='PNG')
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "COMPROBANTE SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.image(qr_io, x=75, y=40, w=60)
        pdf_bytes = bytes(pdf.output())

        # --- PASO 2: MOSTRAR RESULTADOS AL USUARIO INMEDIATAMENTE ---
        st.success("✅ ¡Procesado con éxito!")
        
        # Botón de Descarga
        st.download_button("📥 DESCARGAR COMPROBANTE PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced}.pdf", mime="application/pdf")
        
        # Botón de WhatsApp
        wa_url = f"https://wa.me/584126168188?text=Inscripcion%20Sky%20Gen%20AI:%20{nom}%20{ape}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR AL DIRECTOR POR WHATSAPP</a>', unsafe_allow_html=True)

        # --- PASO 3: INTENTAR PROCESOS DE FONDO (Si fallan, no bloquean la pantalla) ---
        # Guardar en Sheets
        try:
            new_row = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": ced, "Email": mail, "Asignaturas": mat}])
            df_old = conn.read(worksheet="Sheet1")
            conn.update(worksheet="Sheet1", data=pd.concat([df_old, new_row], ignore_index=True))
            st.info("☁️ Sincronizado con la base de datos.")
        except:
            st.warning("⚠️ Nota: Los datos se generaron pero la base de datos está en mantenimiento (Error 404).")

        # Enviar Correo
        enviar_correo(mail, {"nom": nom}, pdf_bytes)
        st.balloons()
