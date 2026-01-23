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

# Estilos CSS para móviles y botones
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; }
    .download-btn { display: block; width: 100%; text-align: center; background-color: #808285; color: white; padding: 10px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    pass

# --- FUNCIONES DE SOPORTE ---
def generar_id():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))

def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Sky Gen AI - ID: {datos['id']}"
        cuerpo = f"Estimado(a) {datos['nom']},\n\nSu ID único es: {datos['id']}\nAdjunto su comprobante PROTEGIDO."
        msg.attach(MIMEText(cuerpo, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Inscripcion_{datos['id']}.pdf")
        msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg); server.quit()
        return True
    except: return False

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
try: st.image("logo.png", width=350)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    
    c3, c4 = st.columns([1, 2])
    with c3: nac = st.selectbox("Nac.", ["V", "E"])
    with c4: ced = st.text_input("Cédula")
    
    st.write("📱 **WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod = st.selectbox("País", ["+58", "+1", "+57", "+34", "+507"])
    with c6: num = st.text_input("Número (sin el 0)")
    
    mail = st.text_input("Correo Gmail")
    mat = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo")
    apps = st.multiselect("Apps Google:", ["Drive", "Classroom", "Gemini AI", "Sheets", "Forms"])
    uso_gemini = st.text_input("Uso de Gemini AI (Opcional)")
    
    submit = st.form_submit_button("GENERAR INSCRIPCIÓN")

if submit:
    if not mail or not nom or not ced:
        st.error("❌ Complete los campos obligatorios.")
    else:
        try:
            id_u = generar_id()
            full_ced = f"{nac}-{ced}"
            full_ws = f"{cod}{num}"
            
            # 1. QR Y PDF PROTEGIDO
            qr_data = f"SKY GEN AI\nID: {id_u}\nInstructor: {nom} {ape}\nCédula: {full_ced}\nMateria: {mat}"
            qr_io = io.BytesIO()
            qrcode.make(qr_data).save(qr_io, format='PNG')
            
            pdf = FPDF()
            # PROTECCIÓN: Requiere la clave para abrir
            pdf.set_protection(user_pass="SkyCrew2026", owner_pass="SkyCrew2026")
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
            pdf.cell(0, 10, f"Cédula: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 10, f"WhatsApp: {full_ws}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 10, f"Materia: {mat}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(qr_io, x=75, y=130, w=60)
            pdf_bytes = bytes(pdf.output())

            # 2. MOSTRAR RESULTADOS
            st.success(f"✅ ¡Inscripción Generada! ID: {id_u}")
            st.download_button("📥 DESCARGAR COMPROBANTE (Clave: SkyCrew2026)", data=pdf_bytes, file_name=f"SkyGen_{id_u}.pdf", mime="application/pdf")
            
            # WhatsApp con TODOS los datos
            wa_text = f"Inscripcion Sky Gen AI%0AID: {id_u}%0AInstructor: {nom} {ape}%0ACedula: {full_ced}%0AMateria: {mat}%0AApps: {', '.join(apps)}"
            wa_url = f"https://wa.me/584126168188?text={wa_text}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR AL DIRECTOR POR WHATSAPP</a>', unsafe_allow_html=True)

            # 3. PROCESOS DE FONDO (Si Sheets falla, no bloquea)
            try:
                new_row = pd.DataFrame([{
                    "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, "WhatsApp": full_ws, 
                    "Email": mail, "Asignaturas": mat, "Normas": normas, 
                    "Apps_Google": ", ".join(apps), "Uso_Gemini": uso_gemini, "ID_Unico": id_u
                }])
                df_old = conn.read(worksheet="Sheet1")
                conn.update(worksheet="Sheet1", data=pd.concat([df_old, new_row], ignore_index=True))
                st.info("☁️ Sincronizado con Base de Datos.")
            except:
                st.warning("⚠️ Nota: Los datos se generaron pero la base de datos está en mantenimiento (Error 404).")

            enviar_correo(mail, {"nom": nom, "ape": ape, "id": id_u}, pdf_bytes)
            st.balloons()
        except Exception as e:
            st.error(f"Falla crítica: {e}")
