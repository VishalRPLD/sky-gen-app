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
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="wide")

# CSS para adaptabilidad y estética de botones
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    [data-testid="stForm"] { border-radius: 15px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("⚠️ Error de enlace con la base de datos.")

# --- FUNCIONES DE SOPORTE ---
def generar_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Registro Sky Gen AI - ID: {datos['id']}"
        cuerpo = f"Hola {datos['nom']},\n\nSu registro ha sido exitoso.\nID Único: {datos['id']}\nClave del PDF: SkyCrew2026"
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

# --- GESTIÓN DE CONFIGURACIÓN (ADMIN) ---
# Cargamos la configuración desde una hoja llamada "Config" o usamos valores por defecto
try:
    config_df = conn.read(worksheet="Config")
    admin_data = config_df.iloc[0].to_dict()
except:
    admin_data = {"cliente": "Pendiente", "curso": "Pendiente", "capacitacion": "Pendiente", "fecha": "Pendiente"}

# --- NAVEGACIÓN ---
tab_ins, tab_admin = st.tabs(["📋 Inscripción", "⚙️ Administrador"])

# --- PESTAÑA ADMINISTRADOR ---
with tab_admin:
    st.subheader("🔐 Panel de Control")
    admin_pwd = st.text_input("Clave Administrativa:", type="password", key="admin_key")
    
    if admin_pwd == "Vl071083":
        st.success("Acceso Autorizado")
        with st.form("admin_form"):
            new_cliente = st.text_input("Cliente actual:", value=admin_data.get("cliente"))
            new_curso = st.text_input("Curso:", value=admin_data.get("curso"))
            new_cap = st.text_input("Capacitación:", value=admin_data.get("capacitacion"))
            new_fecha = st.text_input("Fecha:", value=admin_data.get("fecha"))
            
            if st.form_submit_button("ACTUALIZAR CONFIGURACIÓN"):
                new_config = pd.DataFrame([{"cliente": new_cliente, "curso": new_curso, "capacitacion": new_cap, "fecha": new_fecha}])
                conn.update(worksheet="Config", data=new_config)
                st.success("✅ Configuración actualizada. Reinicie la app para aplicar cambios.")
                st.rerun()
    elif admin_pwd:
        st.error("Clave incorrecta")

# --- PESTAÑA INSCRIPCIÓN ---
with tab_ins:
    if 'auth_user' not in st.session_state: st.session_state['auth_user'] = False
    
    if not st.session_state['auth_user']:
        try: st.image("logo.png", width=200)
        except: pass
        st.title("🔐 Acceso Sky Gen AI")
        pwd = st.text_input("Contraseña Maestra:", type="password", key="user_key")
        if st.button("Ingresar"):
            if pwd == "SkyCrew2026": st.session_state['auth_user'] = True; st.rerun()
            else: st.error("Clave incorrecta")
        st.stop()

    try: st.image("logo.png", width=300)
    except: pass
    st.title("Planilla de Inscripción")

    with st.form("sky_form", clear_on_submit=False):
        st.info(f"📍 **Cliente:** {admin_data['cliente']} | **Curso:** {admin_data['curso']}")
        
        # Campos No Modificables (Visuales)
        c_a, c_b = st.columns(2)
        with c_a: st.text_input("Capacitación", value=admin_data['capacitacion'], disabled=True)
        with c_b: st.text_input("Fecha", value=admin_data['fecha'], disabled=True)

        st.divider()
        
        # Campos Obligatorios
        c1, c2 = st.columns(2)
        with c1: nom = st.text_input("Nombres *")
        with c2: ape = st.text_input("Apellidos *")
        
        c3, c4 = st.columns([1, 2])
        with c3: nac = st.selectbox("Nac.", ["V", "E"])
        with c4: ced = st.text_input("Cédula *")
        
        st.write("📱 **WhatsApp**")
        c5, c6 = st.columns([1, 2])
        with c5: cod = st.selectbox("País", ["+58", "+1", "+57", "+34", "+507"])
        with c6: num = st.text_input("Número (sin el 0) *")
        
        mail = st.text_input("Correo Gmail *")
        mat = st.text_input("Asignaturas que dicta *")
        normas = st.text_area("Normas técnicas de apoyo")
        apps = st.multiselect("Apps Google usadas:", ["Drive", "Classroom", "Gemini AI", "Sheets", "Docs", "Forms"])
        uso_gemini = st.text_area("Si usó Gemini, ¿para qué lo utilizó?")
        
        btn_reg = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

    if btn_reg:
        if not mail or not nom or not ced or not num:
            st.error("❌ Todos los campos marcados con * son obligatorios.")
        else:
            try:
                id_u = generar_id()
                full_ced = f"{nac}-{ced}"
                full_ws = f"{cod}{num}"
                
                # 1. GENERAR QR Y PDF
                qr_io = io.BytesIO()
                qrcode.make(f"ID: {id_u}\nInst: {nom} {ape}\nMat: {mat}\nCliente: {admin_data['cliente']}").save(qr_io, format='PNG')
                
                pdf = FPDF()
                try: pdf.set_protection(user_pass="SkyCrew2026", owner_pass="SkyCrew2026")
                except: pass
                
                pdf.add_page()
                try: pdf.image("logo.png", x=85, y=10, w=40)
                except: pass
                pdf.ln(45)
                pdf.set_font("helvetica", "B", 18)
                pdf.cell(0, 10, "COMPROBANTE OFICIAL - SKY GEN AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                pdf.ln(5)
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 10, f"ID ÚNICO: {id_u}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("helvetica", size=11)
                pdf.cell(0, 8, f"Cliente: {admin_data['cliente']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 8, f"Curso: {admin_data['curso']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 8, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 8, f"Cédula: {full_ced}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 8, f"Email: {mail}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 8, f"WhatsApp: {full_ws}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.image(qr_io, x=75, y=130, w=60)
                pdf_bytes = bytes(pdf.output())

                # 2. GUARDAR EN GOOGLE SHEETS
                new_row = pd.DataFrame([{
                    "ID": id_u, "Cliente": admin_data['cliente'], "Curso": admin_data['curso'],
                    "Nombres": nom, "Apellidos": ape, "Cedula": full_ced, "WhatsApp": full_ws,
                    "Email": mail, "Materia": mat, "Apps": ", ".join(apps), "Gemini": uso_gemini
                }])
                
                df_old = conn.read(worksheet="Sheet1")
                conn.update(worksheet="Sheet1", data=pd.concat([df_old, new_row], ignore_index=True))
                st.success(f"✅ Inscripción exitosa. ID: {id_u}")

                # 3. ACCIONES
                st.download_button("📥 DESCARGAR COMPROBANTE (Clave: SkyCrew2026)", data=pdf_bytes, file_name=f"SkyGen_{id_u}.pdf", mime="application/pdf")
                
                wa_msg = f"Inscripcion Sky Gen AI%0AID: {id_u}%0ACliente: {admin_data['cliente']}%0AInstructor: {nom} {ape}%0ACedula: {full_ced}%0AMateria: {mat}"
                st.markdown(f'<a href="https://wa.me/584126168188?text={wa_msg}" target="_blank" class="wa-button">📲 NOTIFICAR AL DIRECTOR</a>', unsafe_allow_html=True)
                
                enviar_correo(mail, {"nom": nom, "id": id_u}, pdf_bytes)
                st.balloons()
            except Exception as e:
                st.error(f"⚠️ Error al guardar: {e}. El registro se procesó pero la base de datos no respondió.")
