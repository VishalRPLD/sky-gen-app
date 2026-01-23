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

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("⚠️ Error de base de datos.")

# --- FUNCIÓN DE ENVÍO DE CORREO ---
def enviar_correo(destinatario, nombre_instructor, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Bienvenido a Sky Gen AI - {nombre_instructor}"
        
        cuerpo = f"Estimado(a) {nombre_instructor},\n\nSu registro en el programa Sky Gen AI ha sido exitoso. Adjunto encontrará su comprobante oficial.\n\nAtentamente,\nProf. Lakha."
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= Comprobante_SkyGen.pdf")
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- ACCESO ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    try: st.image("logo.png", width=250)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Ingresar"):
        if pwd == "SkyCrew2026": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- FORMULARIO ---
st.title("Planilla de Inscripción")
with st.form("sky_form"):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    ced = st.text_input("Cédula")
    mail = st.text_input("Correo Gmail")
    btn = st.form_submit_button("REGISTRAR")

if btn:
    if "@" not in mail: st.error("Email inválido")
    else:
        # 1. PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "REGISTRO SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        qr = qrcode.make(f"SkyGen: {nom}")
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        pdf.image(buf, x=75, y=50, w=50)
        pdf_out = pdf.output()

        # 2. SHEETS
        try:
            df = conn.read()
            new_data = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": ced, "Email": mail}])
            conn.update(data=pd.concat([df, new_data], ignore_index=True))
            st.success("✅ Datos en la nube.")
        except: st.warning("⚠️ Error en Sheets.")

        # 3. ENVIAR CORREO
        if enviar_correo(mail, nom, pdf_out):
            st.success(f"📧 Comprobante enviado a {mail}")
        else:
            st.error("❌ No se pudo enviar el correo.")

        st.download_button("📥 Descargar PDF", data=pdf_out, file_name="comprobante.pdf")
        st.balloons()
