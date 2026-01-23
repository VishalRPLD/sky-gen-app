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

# --- CSS PARA MÓVILES (BOTÓN WHATSAPP) ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .wa-button {
        background-color: #25D366; color: white; padding: 15px;
        text-align: center; border-radius: 10px; text-decoration: none;
        display: block; font-weight: bold; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ Error de enlace: {e}")

# --- FUNCIÓN DE CORREO ---
def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Exitosa Sky Gen AI - {datos['nom']} {datos['ape']}"
        
        cuerpo = f"Estimado(a) {datos['nom']},\n\nSu registro en Sky Gen AI ha sido procesado.\nID: {datos['ced']}\nAdjunto su comprobante."
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Inscripcion_{datos['ced']}.pdf")
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

# --- FORMULARIO ADAPTATIVO ---
st.title("Planilla de Inscripción")

with st.form("sky_form"):
    # En móviles, las columnas se apilan automáticamente
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    
    c3, c4 = st.columns([1, 2])
    with c3: nac = st.selectbox("Nac.", ["V", "E"])
    with c4: ced = st.text_input("Número de Cédula")
    
    st.write("📱 **Contacto WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod = st.selectbox("País", ["+58", "+1", "+57", "+34", "+507"])
    with c6: num = st.text_input("Número (sin el 0)")
    
    mail = st.text_input("Correo Gmail")
    materia = st.text_input("Asignatura que dicta")
    normas = st.text_area("Normas técnicas de apoyo")
    apps = st.multiselect("Google Workspace usado:", ["Drive", "Classroom", "Docs", "Sheets", "Gemini AI"])
    
    btn_reg = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if btn_reg:
    if not mail.endswith("@gmail.com") or not num:
        st.error("❌ Verifique los datos obligatorios.")
    else:
        try:
            full_ced = f"{nac}-{ced}"
            full_ws = f"{cod}{num}"
            
            # 1. GENERAR QR Y PDF
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(f"Instructor: {nom} {ape}\nID: {full_ced}\nMat: {materia}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_io = io.BytesIO()
            qr_img.save(qr_io, format='PNG')
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE - SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.ln(5)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 10, f"Cédula: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(qr_io, x=75, y=60, w=60)
            pdf_bytes = bytes(pdf.output())

            # 2. GUARDAR EN SHEETS (Punto crítico del 404)
            new_row = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, 
                "WhatsApp": full_ws, "Email": mail, "Asignaturas": materia, 
                "Normas": normas, "Apps_Google": ", ".join(apps)
            }])
            
            # Intentamos leer para validar conexión
            df_old = conn.read(worksheet="Sheet1")
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=df_final)
            
            st.success("✅ ¡Inscripción guardada exitosamente!")

            # 3. CORREO
            if enviar_correo(mail, {"nom": nom, "ape": ape, "ced": full_ced}, pdf_bytes):
                st.info(f"📧 Comprobante enviado a {mail}")

            # 4. DESCARGA Y WHATSAPP (Adaptativo)
            st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced}.pdf", mime="application/pdf")
            
            wa_url = f"https://wa.me/584126168188?text=Registro%20Exitoso:%20{nom}%20{ape}%20({full_ced})"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR POR WHATSAPP AL DIRECTOR</a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Falla de sistema: {e}. Revise los permisos de su Hoja de Cálculo.")
