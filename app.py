import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import qrcode
import io

# --- ESTÉTICA SKY GEN AI ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("⚠️ Error de enlace inicial con la base de datos.")

# --- ACCESO ---
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
        else: st.error("Acceso denegado.")
    st.stop()

# --- FORMULARIO DE INSCRIPCIÓN ---
try: st.image("logo.png", width=350)
except: pass
st.title("Planilla de Inscripción")

with st.form("sky_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1: nom = st.text_input("Nombres")
    with c2: ape = st.text_input("Apellidos")
    
    c3, c4 = st.columns([1, 2])
    with c3: ced_t = st.selectbox("Nacionalidad", ["V", "E"])
    with c4: ced_n = st.text_input("Número de Cédula")
    
    st.write("📱 **Contacto WhatsApp**")
    c5, c6 = st.columns([1, 2])
    with c5: cod_p = st.selectbox("País", ["+58", "+1", "+57", "+34", "+507"])
    with c6: num_t = st.text_input("Número (sin el 0)", placeholder="4121234567")
    
    mail = st.text_input("Correo Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")

    st.subheader("🛠️ Diagnóstico Tecnológico")
    apps = st.multiselect(
        "¿Qué aplicaciones de Google Workspace ha utilizado en los últimos 3 meses?",
        ["Drive", "Classroom", "Docs", "Sheets", "Forms", "Meet", "Google Gemini AI"]
    )
    
    uso_gemini = ""
    if "Google Gemini AI" in apps:
        uso_gemini = st.multiselect(
            "¿Para qué ha utilizado Gemini AI?",
            ["Guiones de clase", "Generación de imágenes", "Investigación", "Material didáctico"]
        )
    
    btn_submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

if btn_submit:
    if not mail.endswith("@gmail.com") or not num_t:
        st.error("❌ Verifique su correo Gmail y su número de teléfono.")
    else:
        try:
            full_telf = f"{cod_p}{num_t}"
            
            # 1. GENERAR QR Y PDF
            qr = qrcode.make(f"Registro: {nom} {ape} | ID: {ced_t}-{ced_n}")
            buf = io.BytesIO()
            qr.save(buf, format='PNG')
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE - SKY GEN AI", ln=True, align="C")
            pdf.set_font("helvetica", size=12)
            pdf.ln(10)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", ln=True)
            pdf.cell(0, 10, f"WhatsApp: {full_telf}", ln=True)
            pdf.image(buf, x=75, y=70, w=60)
            pdf_out = pdf.output()

            # 2. GUARDAR EN GOOGLE SHEETS
            new_row = pd.DataFrame([{
                "Nombres": nom, "Apellidos": ape, "Cedula": f"{ced_t}-{ced_n}", 
                "WhatsApp": full_telf, "Email": mail, "Asignaturas": materia, 
                "Normas": normas, "Apps_Google": ", ".join(apps), "Uso_Gemini": ", ".join(uso_gemini)
            }])
            
            df_old = conn.read()
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(data=df_final)
            
            st.success("✅ ¡Inscripción guardada en la nube!")
            st.download_button("📥 DESCARGAR REGISTRO (PDF)", data=pdf_out, file_name=f"Inscripcion_{ced_n}.pdf")
            
            link_wa = f"https://wa.me/584126168188?text=Inscripción%20Exitosa:%20{nom}%20{ape}%20({full_telf})"
            st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 ENVIAR POR WHATSAPP AL DIRECTOR</button></a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Falla de sistema: {e}. Revise los permisos de su Hoja de Cálculo.")
