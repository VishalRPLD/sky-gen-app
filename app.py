import streamlit as st
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
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

# CSS para adaptabilidad móvil
st.markdown("""
    <style>
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #2E62A1; color: white; }
    .wa-button { display: block; width: 100%; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    input[disabled] { background-color: #f0f2f6 !important; color: #1f77b4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN CON CAJA NEGRA (DIAGNÓSTICO) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ FALLA TÉCNICA EN EL RADAR: {e}")
    st.info("💡 Consejo: Verifique que en los Secrets de Streamlit la 'private_key' tenga comillas y use '\\n' para los saltos de línea.")
    st.stop()

# --- FUNCIONES DE SOPORTE ---
def generar_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def enviar_correo(destinatario, datos, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["gmail"]["user"]
        msg['To'] = destinatario
        msg['Subject'] = f"🛫 Inscripción Exitosa Sky Gen AI - ID: {datos['id']}"
        msg.attach(MIMEText(f"Estimado(a) {datos['nom']},\n\nSu registro fue exitoso.\nID: {datos['id']}\nClave PDF: SkyCrew2026", 'plain'))
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

# --- DATOS DE ADMINISTRACIÓN ---
try:
    config_df = conn.read(worksheet="Config", ttl=0)
    conf = config_df.iloc[0].to_dict()
except:
    conf = {"cliente": "Pendiente", "curso": "Pendiente", "capacitacion": "Pendiente", "fecha": "Pendiente"}

# --- NAVEGACIÓN ---
tab_ins, tab_admin = st.tabs(["📋 Inscripción", "⚙️ Administrador"])

# --- PESTAÑA ADMINISTRADOR ---
with tab_admin:
    st.subheader("🔐 Panel de Control")
    admin_pwd = st.text_input("Clave Administrativa:", type="password")
    if admin_pwd == "Vl071083":
        st.success("Acceso Autorizado")
        with st.form("admin_form"):
            new_cliente = st.text_input("Cliente actual:", value=conf.get("cliente"))
            new_curso = st.text_input("Curso:", value=conf.get("curso"))
            new_cap = st.text_input("Capacitación:", value=conf.get("capacitacion"))
            new_fecha = st.text_input("Fecha:", value=conf.get("fecha"))
            if st.form_submit_button("ACTUALIZAR CONFIGURACIÓN"):
                new_df = pd.DataFrame([{"cliente": new_cliente, "curso": new_curso, "capacitacion": new_cap, "fecha": new_fecha}])
                conn.update(
    spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], 
    worksheet="Config", 
    data=new_df
)

# --- PESTAÑA INSCRIPCIÓN ---
with tab_ins:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        try: st.image("logo.png", width=200)
        except: pass
        st.title("🔐 Acceso Sky Gen AI")
        u_pwd = st.text_input("Contraseña Maestra:", type="password")
        if st.button("Ingresar"):
            if u_pwd == "SkyCrew2026": st.session_state['auth'] = True; st.rerun()
            else: st.error("Clave incorrecta")
        st.stop()

    try: st.image("logo.png", width=300)
    except: pass
    st.title("Planilla de Inscripción")

    with st.form("sky_form", clear_on_submit=False):
        st.info(f"🏢 **Cliente:** {conf['cliente']} | 📖 **Curso:** {conf['curso']}")
        c_f1, c_f2 = st.columns(2)
        with c_f1: st.text_input("Capacitación", value=conf['capacitacion'], disabled=True)
        with c_f2: st.text_input("Fecha de sesión", value=conf['fecha'], disabled=True)
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1: nom = st.text_input("Nombres *")
        with c2: ape = st.text_input("Apellidos *")
        ced = st.text_input("Cédula *")
        whatsapp_n = st.text_input("WhatsApp (con código de país) *")
        mail = st.text_input("Correo Gmail *")
        mat = st.text_input("Asignatura que dicta *")
        normas = st.text_area("Normas técnicas de apoyo")
        apps = st.multiselect("Apps usadas:", ["Drive", "Classroom", "Gemini AI", "Sheets", "Docs", "Forms"])
        uso_gemini = st.text_area("Si usó Gemini, ¿para qué lo utilizó?")
        
        if st.form_submit_button("REGISTRAR INSCRIPCIÓN"):
            if not nom or not ced or not mail:
                st.error("❌ Los campos con * son obligatorios.")
            else:
                id_u = generar_id()
                qr_io = io.BytesIO()
                qrcode.make(f"ID:{id_u}\nCli:{conf['cliente']}\nInst:{nom}").save(qr_io, format='PNG')
                
                pdf = FPDF()
                try: pdf.set_protection(user_pass="SkyCrew2026", owner_pass="SkyCrew2026")
                except: pass
                pdf.add_page()
                try: pdf.image("logo.png", x=85, y=10, w=40)
                except: pass
                pdf.ln(45); pdf.set_font("helvetica", "B", 16)
                pdf.cell(0, 10, "COMPROBANTE OFICIAL - SKY GEN AI", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("helvetica", size=12)
                pdf.cell(0, 10, f"ID: {id_u}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Cliente: {conf['cliente']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Instructor: {nom} {ape}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.image(qr_io, x=75, y=120, w=60)
                pdf_bytes = bytes(pdf.output())

                try:
                    nr = pd.DataFrame([{
                        "Nombres": nom, "Apellidos": ape, "Cedula": ced, "WhatsApp": whatsapp_n, 
                        "Email": mail, "Asignaturas": mat, "Normas": normas, 
                        "Apps_Google": ", ".join(apps), "Uso_Gemini": uso_gemini, "ID_Unico": id_u,
                        "Cliente": conf['cliente'], "Curso": conf['curso']
                    }])
                    df_o = conn.read(worksheet="Sheet1")
                    conn.update(worksheet="Sheet1", data=pd.concat([df_o, nr], ignore_index=True))
                    st.success(f"✅ ¡Éxito! ID: {id_u}")
                    st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"SkyGen_{id_u}.pdf", mime="application/pdf")
                    wa_url = f"https://wa.me/584126168188?text=Registro%20ID:%20{id_u}%0ACliente:%20{conf['cliente']}%0AInst:%20{nom}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 NOTIFICAR AL DIRECTOR</a>', unsafe_allow_html=True)
                    enviar_correo(mail, {"nom": nom, "id": id_u}, pdf_bytes)
                    st.balloons()
                except Exception as e:
                    st.error(f"Error al sincronizar: {e}")
