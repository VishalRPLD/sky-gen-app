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

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️", layout="wide")

# Intentar obtener la URL de la hoja desde secrets de forma segura
try:
    URL_SHEET = st.secrets["connections"]["gsheets"]["spreadsheet"]
except KeyError:
    st.error("❌ ERROR: No se encontró la URL de la hoja en los Secrets.")
    st.stop()

# CSS para adaptabilidad móvil y diseño
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    input[disabled] { background-color: #f0f2f6 !important; color: #1f77b4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ FALLA TÉCNICA EN EL RADAR: {e}")
    st.stop()

# --- 3. FUNCIONES DE APOYO ---
def generar_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Exitosa Sky Gen AI - ID: {datos['id']}"
        
        cuerpo = f"Estimado(a) {datos['nom']},\n\nSu registro en Sky Gen AI fue exitoso.\n\nID Único: {datos['id']}\nClave del PDF: SkyCrew2026\n\nAdjunto encontrará su comprobante."
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=SkyGen_{datos['id']}.pdf")
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- 4. CARGA DE CONFIGURACIÓN ADMINISTRATIVA ---
try:
    config_df = conn.read(worksheet="Config", ttl=0)
    conf = config_df.iloc[0].to_dict()
except:
    conf = {"cliente": "Pendiente", "curso": "Pendiente", "capacitacion": "Pendiente", "fecha": "Pendiente"}

# --- 5. NAVEGACIÓN POR PESTAÑAS ---
tab_ins, tab_admin = st.tabs(["📋 Inscripción", "⚙️ Administrador"])

# --- PESTAÑA ADMINISTRADOR ---
with tab_admin:
    st.subheader("🔐 Panel de Control Administrativo")
    admin_pwd = st.text_input("Clave de Acceso:", type="password", key="admin_pwd_key")
    if admin_pwd == "Vl071083":
        st.success("Acceso Autorizado")
        with st.form("admin_form"):
            new_cliente = st.text_input("Cliente actual:", value=conf.get("cliente"))
            new_curso = st.text_input("Curso:", value=conf.get("curso"))
            new_cap = st.text_input("Capacitación:", value=conf.get("capacitacion"))
            new_fecha = st.text_input("Fecha:", value=conf.get("fecha"))
            
            if st.form_submit_button("ACTUALIZAR SISTEMA"):
                new_df = pd.DataFrame([{"cliente": new_cliente, "curso": new_curso, "capacitacion": new_cap, "fecha": new_fecha}])
                conn.update(spreadsheet=URL_SHEET, worksheet="Config", data=new_df)
                st.success("✅ Configuración Global Actualizada")
                st.rerun()

# --- PESTAÑA INSCRIPCIÓN ---
with tab_ins:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    
    if not st.session_state['auth']:
        st.title("🔐 Acceso Sky Gen AI")
        u_pwd = st.text_input("Contraseña de Acceso:", type="password")
        if st.button("Ingresar"):
            if u_pwd == "SkyCrew2026": 
                st.session_state['auth'] = True
                st.rerun()
            else: 
                st.error("Clave incorrecta")
        st.stop()

    st.title("Planilla de Inscripción Digital")

    with st.form("sky_form", clear_on_submit=False):
        st.info(f"🏢 **Entidad:** {conf['cliente']} | 📖 **Programa:** {conf['curso']}")
        c_f1, c_f2 = st.columns(2)
        with c_f1: st.text_input("Tipo de Capacitación", value=conf['capacitacion'], disabled=True)
        with c_f2: st.text_input("Fecha Programada", value=conf['fecha'], disabled=True)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1: nom = st.text_input("Nombres *")
        with c2: ape = st.text_input("Apellidos *")
        ced = st.text_input("Cédula de Identidad *")
        whatsapp_n = st.text_input("WhatsApp (Ej: 58412...) *")
        mail = st.text_input("Correo Gmail *")
        mat = st.text_input("Asignatura / Especialidad *")
        normas = st.text_area("Normas Técnicas (RAV, OACI, etc.)")
        apps = st.multiselect("Herramientas Workspace:", ["Drive", "Classroom", "Gemini AI", "Sheets", "Docs", "Forms"])
        uso_gemini = st.text_area("Experiencia previa con IA")
        
        if st.form_submit_button("ENVIAR REGISTRO"):
            if not nom or not ced or not mail:
                st.error("❌ Por favor complete los campos obligatorios (*)")
            else:
                id_u = generar_id()
                
                # Generación de QR
                qr_io = io.BytesIO()
                qrcode.make(f"ID:{id_u}\nCli:{conf['cliente']}\nInstructor:{nom}").save(qr_io, format='PNG')
                
                # Generación de PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("helvetica", "B", 16)
                pdf.cell(0, 10, "COMPROBANTE DE INSCRIPCION - SKY GEN AI", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(10)
                pdf.set_font("helvetica", size=12)
                pdf.cell(0, 10, f"ID de Registro: {id_u}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Participante: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Entidad: {conf['cliente']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.image(qr_io, x=75, y=100, w=60)
                pdf_bytes = bytes(pdf.output())

                try:
                    # Sincronización con Base de Datos
                    df_actual = conn.read(worksheet="Sheet1")
                    nuevo_registro = pd.DataFrame([{
                        "Nombres": nom, "Apellidos": ape, "Cedula": ced, "WhatsApp": whatsapp_n, 
                        "Email": mail, "Asignaturas": mat, "Normas": normas, 
                        "Apps_Google": ", ".join(apps), "Uso_Gemini": uso_gemini, "ID_Unico": id_u,
                        "Cliente": conf['cliente'], "Curso": conf['curso']
                    }])
                    
                    # Actualizar la hoja principal
                    conn.update(
                        spreadsheet=URL_SHEET, 
                        worksheet="Sheet1", 
                        data=pd.concat([df_actual, nuevo_registro], ignore_index=True)
                    )
                    
                    st.success(f"✅ ¡Registro Exitoso! Su ID es: {id_u}")
                    st.download_button("📥 DESCARGAR COMPROBANTE PDF", data=pdf_bytes, file_name=f"SkyGen_{id_u}.pdf", mime="application/pdf")
                    
                    # WhatsApp y Correo
                    wa_url = f"https://wa.me/584126168188?text=Nuevo%20Registro%20ID:%20{id_u}%0ACliente:%20{conf['cliente']}%0AInstructor:%20{nom}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR REGISTRO AL DIRECTOR</a>', unsafe_allow_html=True)
                    
                    if enviar_correo(mail, {"nom": nom, "id": id_u}, pdf_bytes):
                        st.info("📩 Se ha enviado una copia a su correo Gmail.")
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"Falla de comunicación con la base de datos: {e}")
