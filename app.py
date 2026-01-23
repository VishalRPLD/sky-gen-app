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

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error de conexión inicial: {e}")

# --- FUNCIÓN: ENVÍO DE CORREO ---
def enviar_correo(destinatario, datos, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Exitosa Sky Gen AI - {datos['nom']} {datos['ape']}"
        
        cuerpo = f"""
        Estimado(a) Instructor(a) {datos['nom']} {datos['ape']},
        
        Su registro ha sido procesado con éxito.
        - Cédula: {datos['ced']}
        - Asignatura: {datos['materia']}
        - WhatsApp: {datos['telf']}
        
        Adjunto encontrará su comprobante oficial con código QR.
        
        Atentamente,
        Prof. Lakha.
        """
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Comprobante_SkyGen_{datos['ced']}.pdf")
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Error enviando correo: {e}")
        return False

# --- CONTROL DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    try: st.image("logo.png", width=250)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Ingresar"):
        if pwd == "SkyCrew2026":
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop()

# --- FORMULARIO COMPLETO ---
try: st.image("logo.png", width=350)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1: nom = st.text_input("Nombres")
    with col2: ape = st.text_input("Apellidos")
    
    col3, col4 = st.columns([1, 2])
    with col3: nac = st.selectbox("Nac.", ["V", "E"])
    with col4: ced_num = st.text_input("Cédula (Solo números)")
    
    st.write("📱 **Contacto WhatsApp**")
    col5, col6 = st.columns([1, 2])
    with col5: cod_p = st.selectbox("País", ["+58", "+1", "+57", "+34", "+507"])
    with col6: telf_num = st.text_input("Número (sin el 0)", placeholder="4121234567")
    
    mail = st.text_input("Correo Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")
    
    apps = st.multiselect("Apps de Google (últimos 3 meses):", 
                         ["Drive", "Classroom", "Docs", "Sheets", "Forms", "Meet", "Gemini AI"])
    
    uso_gemini = st.text_input("Si usó Gemini, ¿para qué lo utilizó? (Opcional)")

    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

# --- PROCESAMIENTO ---
if submit:
    if not mail.endswith("@gmail.com") or not telf_num or not nom:
        st.error("❌ Por favor complete los campos obligatorios y use un correo @gmail.com.")
    else:
        try:
            full_ced = f"{nac}-{ced_num}"
            full_ws = f"{cod_p}{telf_num}"
            
            # 1. GENERAR QR CON DATOS REALES
            qr_content = f"SKY GEN AI\nInstructor: {nom} {ape}\nID: {full_ced}\nMat: {materia}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_content)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_io = io.BytesIO()
            qr_img.save(qr_io, format='PNG')
            qr_io.seek(0)

            # 2. GENERAR PDF (Formato de Bytes compatible)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE OFICIAL - SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.ln(10)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 8, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 8, f"Cédula: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 8, f"WhatsApp: {full_ws}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 8, f"Email: {mail}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(0, 8, f"Materia: {materia}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(qr_io, x=75, y=100, w=60)
            
            # Convertir PDF a bytes de forma segura
            pdf_bytes = pdf.output() 

            # 3. GUARDAR EN GOOGLE SHEETS
            new_data = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, 
                "WhatsApp": full_ws, "Email": mail, "Asignaturas": materia, 
                "Normas": normas, "Apps_Google": ", ".join(apps), "Uso_Gemini": uso_gemini
            }])
            
            existing_df = conn.read(worksheet="Sheet1")
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("✅ ¡Inscripción guardada en la base de datos!")

            # 4. ENVÍO DE CORREO
            datos_msg = {"nom": nom, "ape": ape, "ced": full_ced, "telf": full_ws, "materia": materia}
            if enviar_correo(mail, datos_msg, pdf_bytes):
                st.info(f"📧 Comprobante enviado a {mail}")

            # 5. BOTONES DE ACCIÓN
            st.download_button(
                label="📥 Descargar Comprobante PDF",
                data=pdf_bytes,
                file_name=f"Inscripcion_{ced_num}.pdf",
                mime="application/pdf"
            )
            
            wa_text = f"Hola Prof. Lakha, registro mi inscripción en Sky Gen AI. Instructor: {nom} {ape}, Cédula: {full_ced}."
            wa_url = f"https://wa.me/584126168188?text={wa_text.replace(' ', '%20')}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 NOTIFICAR AL DIRECTOR POR WHATSAPP</button></a>', unsafe_allow_html=True)
            
            st.balloons()

        except Exception as e:
            st.error(f"Falla técnica: {e}")
