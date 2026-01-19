import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import qrcode
from PIL import Image
import io

# --- ESTÉTICA SKY GEN AI ---
st.set_page_config(page_title="Sky Gen AI", page_icon="✈️")

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error de conexión: {e}")

# --- ACCESO ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    try: st.image("logo.png", width=250)
    except: pass
    st.title("🔐 Acceso Sky Gen AI")
    pwd = st.text_input("Contraseña Maestra:", type="password")
    if st.button("Entrar"):
        if pwd == "SkyCrew2026":
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Clave incorrecta.")
    st.stop()

# --- FORMULARIO DE INSCRIPCIÓN ---
try: st.image("logo.png", width=400)
except: pass
st.title("Planilla de Inscripción")

# Iniciamos el formulario
with st.form("sky_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1: nom = st.text_input("Nombres")
    with col2: ape = st.text_input("Apellidos")
    
    col3, col4 = st.columns([1, 2])
    with col3: ced_t = st.selectbox("Nacionalidad", ["V", "E"])
    with col4: ced_n = st.text_input("Número de Cédula")
    
    mail = st.text_input("Correo electrónico Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")
    
    # El botón debe estar DENTRO del bloque 'with st.form'
    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

# --- PROCESAMIENTO FUERA DEL FORMULARIO ---
if submit:
    if not mail.endswith("@gmail.com"):
        st.error("❌ Error: Debe utilizar estrictamente una cuenta @gmail.com.")
    elif not nom or not ape or not ced_n:
        st.warning("⚠️ Por favor, complete los campos obligatorios.")
    else:
        try:
            # 1. GENERAR QR CORRECTAMENTE
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"Registro: {nom} {ape} | ID: {ced_t}-{ced_n}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir QR a formato que FPDF entienda
            img_byte_arr = io.BytesIO()
            qr_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # 2. GENERAR PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE DE INSCRIPCIÓN - SKY GEN AI", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", ln=True)
            pdf.cell(0, 10, f"Identificación: {ced_t}-{ced_n}", ln=True)
            pdf.cell(0, 10, f"Asignatura: {materia}", ln=True)
            
            # Insertar QR usando el flujo de bytes
            pdf.image(img_byte_arr, x=75, y=80, w=60)
            
            pdf_bytes = pdf.output()

            # 3. GUARDAR EN GOOGLE SHEETS
            new_row = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": f"{ced_t}-{ced_n}", "Email": mail, "Asignaturas": materia}])
            existing_data = conn.read()
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("✅ ¡Inscripción procesada y guardada con éxito!")
            
            # 4. BOTONES DE ACCIÓN
            st.download_button(label="📥 DESCARGAR COMPROBANTE (PDF)", data=pdf_bytes, file_name=f"Inscripcion_{ced_n}.pdf", mime="application/pdf")
            
            wa_text = f"Hola Prof. Lakha, envío mi inscripción de Sky Gen AI: {nom} {ape}, Cédula {ced_t}-{ced_n}."
            wa_link = f"https://wa.me/584126168188?text={wa_text.replace(' ', '%20')}"
            st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color: #25D366; color: white; padding: 15px; border: none; border-radius: 10px; width: 100%; cursor: pointer; font-weight: bold;">📲 ENVIAR POR WHATSAPP AL DIRECTOR</button></a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Se produjo un error durante el procesamiento: {e}")
