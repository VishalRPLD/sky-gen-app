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
    st.error("⚠️ Error de enlace con Google Sheets.")

# --- FUNCIÓN DE ENVÍO DE CORREO ---
def enviar_correo(destinatario, datos, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Registro Sky Gen AI - {datos['nom']} {datos['ape']}"
        
        cuerpo = f"Estimado(a) {datos['nom']},\n\nSu registro ha sido exitoso.\nID: {datos['ced']}\nWhatsApp: {datos['telf']}\n\nAdjunto su comprobante."
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Comprobante_SkyGen.pdf")
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
    with c3: ced_t = st.selectbox("Nac.", ["V", "E"])
    with c4: ced_n = st.text_input("Cédula")
    
    st.write("📱 **WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod_p = st.selectbox("País", ["+58", "+1", "+57"])
    with c6: num_t = st.text_input("Número (sin el 0)")
    
    mail = st.text_input("Correo Gmail")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo")
    apps = st.multiselect("Apps:", ["Drive", "Classroom", "Gemini AI"])
    
    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if submit:
    if not mail.endswith("@gmail.com") or not num_t:
        st.error("❌ Datos incompletos.")
    else:
        try:
            full_telf = f"{cod_p}{num_t}"
            full_ced = f"{ced_t}-{ced_n}"
            
            # 1. QR CON DATOS (Corregido)
            qr_data = f"Instructor: {nom} {ape}\nID: {full_ced}\nMat: {materia}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill='black', back_color='white')
            qr_io = io.BytesIO()
            qr_img.save(qr_io, format='PNG')
            
            # 2. PDF (Corregido para Download Button)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 10, f"ID: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(qr_io, x=75, y=60, w=60)
            
            # Convertir a bytes reales
            pdf_bytes = bytes(pdf.output())

            # 3. GUARDAR EN GOOGLE SHEETS (Sincronización total)
            new_row = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, 
                "WhatsApp": full_telf, "Email": mail, "Asignaturas": materia, 
                "Normas": normas, "Apps_Google": str(apps)
            }])
            
            df_old = conn.read(worksheet="Sheet1")
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=df_final)
            st.success("✅ Datos registrados en la nube.")

            # 4. CORREO Y WHATSAPP
            if enviar_correo(mail, {"nom": nom, "ape": ape, "ced": full_ced, "telf": full_telf}, pdf_bytes):
                st.success(f"📧 Comprobante enviado a {mail}")
            
            st.download_button("📥 Descargar Comprobante PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced_n}.pdf", mime="application/pdf")
            
            wa_url = f"https://wa.me/584126168188?text=Inscripción:%20{nom}%20{ape}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; width: 100%; cursor: pointer;">📲 ENVIAR POR WHATSAPP AL DIRECTOR</button></a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Falla: {e}")
