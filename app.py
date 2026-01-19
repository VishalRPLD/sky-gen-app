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
    st.error("⚠️ Error de conexión a la base de datos. Verifique sus 'Secrets'.")

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

with st.form("sky_form", clear_on_submit=False):
    col_n, col_a = st.columns(2)
    with col_n: nom = st.text_input("Nombres")
    with col_a: ape = st.text_input("Apellidos")
    
    col_ct, col_cn = st.columns([1, 2])
    with col_ct: ced_t = st.selectbox("Nacionalidad", ["V", "E"])
    with col_cn: ced_n = st.text_input("Número de Cédula")
    
    # NUEVA SECCIÓN: TELÉFONO WHATSAPP
    st.write("📞 **Contacto WhatsApp**")
    col_code, col_phone = st.columns([1, 2])
    with col_code: 
        cod_pais = st.selectbox("Código", ["+58", "+1", "+57", "+507", "+34"], index=0)
    with col_phone: 
        num_telf = st.text_input("Número (sin el 0 inicial)", placeholder="4121234567")
    
    mail = st.text_input("Correo electrónico Gmail (@gmail.com)")
    materia = st.text_input("Asignaturas que dicta")
    normas = st.text_area("Normas técnicas de apoyo a su asignatura")
    
    submit = st.form_submit_button("REGISTRAR INSCRIPCIÓN")

# --- PROCESAMIENTO ---
if submit:
    if not mail.endswith("@gmail.com"):
        st.error("❌ Error: Use un correo @gmail.com")
    elif not nom or not num_telf:
        st.warning("⚠️ Complete los campos obligatorios.")
    else:
        try:
            full_phone = f"{cod_pais}{num_telf}"
            
            # 1. GENERAR QR Y PDF
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"Inscrito: {nom} {ape} | Telf: {full_phone}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            img_byte_arr = io.BytesIO()
            qr_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "COMPROBANTE DE INSCRIPCIÓN - SKY GEN AI", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, f"Instructor: {nom} {ape}", ln=True)
            pdf.cell(0, 10, f"WhatsApp: {full_phone}", ln=True)
            pdf.image(img_byte_arr, x=75, y=60, w=60)
            
            pdf_bytes = pdf.output()

            # 2. GUARDAR EN GOOGLE SHEETS
            new_row = pd.DataFrame([{"Nombres": nom, "Apellidos": ape, "Cedula": f"{ced_t}-{ced_n}", "WhatsApp": full_phone, "Email": mail, "Asignaturas": materia}])
            
            # Verificación de conexión para evitar 404
            data_existing = conn.read()
            updated_df = pd.concat([data_existing, new_row], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("✅ ¡Registro exitoso en la nube!")
            
            # 3. ACCIONES
            st.download_button(label="📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Inscripcion_{ced_n}.pdf", mime="application/pdf")
            
            wa_link = f"https://wa.me/584126168188?text=Nueva%20Inscripción:%20{nom}%20{ape}%20({full_phone})"
            st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer;">📲 ENVIAR POR WHATSAPP AL DIRECTOR</button></a>', unsafe_allow_html=True)
            st.balloons()
            
        except Exception as e:
            st.error(f"Falla de sistema: {e}. Verifique el enlace de su Hoja de Cálculo.")
