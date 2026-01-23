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

# --- CONFIGURACIÓN ESTÉTICA ADAPTATIVA ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="centered")

# Estilo CSS para que los botones ocupen el ancho total en móviles
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    .download-btn { display: block; width: 100%; text-align: center; background-color: #F0F2F6; padding: 10px; border-radius: 10px; text-decoration: none; color: black; font-weight: bold; margin-bottom: 10px; border: 1px solid #CCC; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ Error de enlace de datos: {e}")

# --- FUNCIÓN DE CORREO ---
def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Sky Gen AI - {datos['nom']} {datos['ape']}"
        
        cuerpo = f"Estimado(a) {datos['nom']},\n\nConfirmamos su inscripción.\nID: {datos['ced']}\nAdjunto su comprobante PDF.\n\nAtentamente,\nProf. Lakha."
        msg.attach(MIMEText(cuerpo, 'plain'))
        
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
    try: st.image("logo.png", width=200)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if pwd == "SkyCrew2026": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- FORMULARIO ---
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    # Layout que se adapta a columnas en desktop y filas en móvil
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    
    c3, c4 = st.columns([1, 2])
    with c3: nac = st.selectbox("Nac.", ["V", "E"])
    with c4: ced = st.text_input("Cédula")
    
    st.write("📱 **WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod = st.selectbox("País", ["+58", "+1", "+57"])
    with c6: num = st.text_input("Número (sin el 0)")
    
    mail = st.text_input("Correo Gmail")
    materia = st.text_input("Asignatura")
    normas = st.text_area("Normas de apoyo")
    
    btn_reg = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if btn_reg:
    if not mail.endswith("@gmail.com") or not num or not nom:
        st.error("❌ Complete los campos obligatorios.")
    else:
        try:
            full_ced = f"{nac}-{ced}"
            full_ws = f"{cod}{num}"
            
            # 1. QR Y PDF
            qr_content = f"SKY GEN AI\nInstructor: {nom} {ape}\nID: {full_ced}\nMat: {materia}"
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(qr_content)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_io = io.BytesIO()
            qr_img.save(qr_io, format='PNG')
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.ln(5)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 10, f"ID: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(qr_io, x=75, y=60, w=60)
            pdf_bytes = bytes(pdf.output())

            # 2. GUARDAR EN GOOGLE SHEETS (Lógica flexible)
            new_row = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, 
                "WhatsApp": full_ws, "Email": mail, "Asignaturas": materia, "Normas": normas
            }])
            
            # Intentar leer la primera hoja disponible sin importar el nombre
            df_old = conn.read() 
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(data=df_final)
            
            st.success("✅ ¡Inscripción guardada!")

            # 3. CORREO
            enviar_correo(mail, {"nom": nom, "ape": ape, "ced": full_ced}, pdf_bytes)

            # 4. ACCIONES (Adaptativo)
            st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced}.pdf", mime="application/pdf")
            
            wa_url = f"https://wa.me/584126168188?text=Inscripcion%20Exitosa:%20{nom}%20{ape}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR POR WHATSAPP</a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Falla de sistema: {e}. Verifique que la hoja de Google esté compartida como EDITOR.")
