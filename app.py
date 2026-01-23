import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF, XPos, YPos
import qrcode
import io
import smtplib
import secrets
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURACIÓN ADAPTATIVA ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="centered")

# Estilos CSS para botones adaptativos y móviles
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    .stDownloadButton > button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except: pass

# --- FUNCIONES ---
def generar_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Exitosa Sky Gen AI - ID: {datos['id']}"
        cuerpo = f"Estimado(a) {datos['nom']},\n\nSu inscripción fue exitosa.\nID Único: {datos['id']}\nClave del PDF: SkyCrew2026"
        msg.attach(MIMEText(cuerpo, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=SkyGen_{datos['id']}.pdf")
        msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg); server.quit()
        return True
    except: return False

# --- ACCESO ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    try: st.image("logo.png", width=200)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if pwd == "SkyCrew2026": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- FORMULARIO ---
try: st.image("logo.png", width=300)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    ced = st.text_input("Cédula")
    mail = st.text_input("Correo Gmail")
    mat = st.text_input("Asignatura")
    normas = st.text_area("Normas técnicas")
    apps = st.multiselect("Apps Google:", ["Drive", "Classroom", "Gemini AI", "Sheets"])
    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if submit:
    if not mail or not nom:
        st.error("❌ Complete los datos obligatorios.")
    else:
        id_u = generar_id()
        
        # 1. GENERAR PDF Y QR (Con manejo de errores para protección)
        qr_io = io.BytesIO()
        qrcode.make(f"ID: {id_u}\nInstructor: {nom} {ape}\nMat: {mat}").save(qr_io, format='PNG')
        
        pdf = FPDF()
        try:
            # Intentar poner protección si la librería fpdf2 está presente
            pdf.set_protection(user_pass="SkyCrew2026", owner_pass="SkyCrew2026")
        except: pass 
        
        pdf.add_page()
        try: pdf.image("logo.png", x=85, y=10, w=40)
        except: pass
        pdf.ln(45)
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "COMPROBANTE OFICIAL - SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, f"ID INSCRIPCIÓN: {id_u}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Cédula: {ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Materia: {mat}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.image(qr_io, x=75, y=110, w=60)
        pdf_bytes = bytes(pdf.output())

        # 2. MOSTRAR RESULTADOS INMEDIATOS
        st.success(f"✅ ¡Registro Exitoso! ID: {id_u}")
        st.download_button("📥 DESCARGAR PDF (Clave: SkyCrew2026)", data=pdf_bytes, file_name=f"SkyGen_{id_u}.pdf", mime="application/pdf")
        
        # WhatsApp con TODOS los campos
        wa_msg = f"Inscripcion Sky Gen AI%0AID: {id_u}%0AInstructor: {nom} {ape}%0ACedula: {ced}%0AMateria: {mat}%0AApps: {', '.join(apps)}"
        st.markdown(f'<a href="https://wa.me/584126168188?text={wa_msg}" target="_blank" class="wa-button">📲 ENVIAR DATOS AL DIRECTOR</a>', unsafe_allow_html=True)

        # 3. PROCESOS DE FONDO
        try:
            new_row = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": ced, "Email": mail, "Asignaturas": mat, "ID_Unico": id_u}])
            df_old = conn.read(worksheet="Sheet1")
            conn.update(worksheet="Sheet1", data=pd.concat([df_old, new_row], ignore_index=True))
            st.info("☁️ Sincronizado con Base de Datos.")
        except:
            st.warning("⚠️ Base de Datos en mantenimiento (Error 404).")

        enviar_correo(mail, {"nom": nom, "id": id_u}, pdf_bytes)
        st.balloons()
