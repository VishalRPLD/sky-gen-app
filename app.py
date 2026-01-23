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
    st.error("⚠️ Error de enlace inicial con la base de datos.")

# --- FUNCIÓN DE ENVÍO DE CORREO ---
def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Registro Exitoso Sky Gen AI - {datos['nom']} {datos['ape']}"
        
        cuerpo = f"""
        Estimado(a) {datos['nom']} {datos['ape']},
        
        Su registro en el programa Sky Gen AI ha sido procesado con los siguientes datos:
        - Cédula: {datos['ced']}
        - WhatsApp: {datos['telf']}
        - Asignatura: {datos['materia']}
        
        Adjunto encontrará su comprobante oficial con código QR.
        
        Atentamente,
        Prof. Lakha.
        """
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Comprobante_SkyGen_{datos['ced']}.pdf")
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

# --- FORMULARIO COMPLETO ---
try: st.image("logo.png", width=350)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    
    c3, c4 = st.columns([1, 2])
    with c3: ced_t = st.selectbox("Nac.", ["V", "E"])
    with c4: ced_n = st.text_input("Cédula (Solo números)")
    
    st.write("📱 **WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod_p = st.selectbox("Código", ["+58", "+1", "+57", "+34", "+507"])
    with c6: num_t = st.text_input("Número (sin el 0)")
    
    mail = st.text_input("Correo Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo")

    st.subheader("🛠️ Diagnóstico Google Workspace")
    apps = st.multiselect("Apps utilizadas (últimos 3 meses):", ["Drive", "Classroom", "Docs", "Sheets", "Forms", "Meet", "Gemini AI"])
    
    btn_submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if btn_submit:
    if not mail.endswith("@gmail.com") or not num_t:
        st.error("❌ Verifique su correo Gmail y número de teléfono.")
    else:
        full_telf = f"{cod_p}{num_t}"
        full_ced = f"{ced_t}-{ced_n}"
        dict_datos = {"nom": nom, "ape": ape, "ced": full_ced, "telf": full_telf, "materia": materia}
        
        # 1. GENERAR PDF CON TODOS LOS DATOS
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "COMPROBANTE OFICIAL - SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Cédula: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"WhatsApp: {full_telf}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Email: {mail}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Materia: {materia}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # QR con datos completos
        qr = qrcode.make(f"SkyGenAI: {nom} {ape}\nID: {full_ced}\nMat: {materia}")
        qr_buf = io.BytesIO()
        qr.save(qr_buf, format='PNG')
        pdf.image(qr_buf, x=75, y=100, w=60)
        
        # IMPORTANTE: Convertir a bytes para evitar el error de Streamlit
        pdf_bytes = pdf.output()

        # 2. GUARDAR EN SHEETS
        try:
            df_old = conn.read()
            new_row = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, 
                "WhatsApp": full_telf, "Email": mail, "Asignaturas": materia, 
                "Normas": normas, "Apps_Google": ", ".join(apps)
            }])
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Registro guardado en la base de datos.")
        except Exception as e:
            st.warning(f"⚠️ Error en Sheets: Verifique que las columnas coincidan y tenga permiso de Editor.")

        # 3. ENVIAR CORREO
        if enviar_correo(mail, dict_datos, pdf_bytes):
            st.success(f"📧 Comprobante enviado a {mail}")
        else:
            st.error("❌ Error al enviar el correo. Revise su configuración de Gmail.")

        # 4. BOTONES DE ACCIÓN
        st.download_button(label="📥 Descargar Comprobante PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced_n}.pdf", mime="application/pdf")
        
        wa_link = f"https://wa.me/584126168188?text=Inscripción%20Sky%20Gen%20AI:%20{nom}%20{ape}%20({full_ced})"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 ENVIAR POR WHATSAPP AL DIRECTOR</button></a>', unsafe_allow_html=True)
        st.balloons()
