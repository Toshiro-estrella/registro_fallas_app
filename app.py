import streamlit as st
from PIL import Image
from datetime import datetime
import pandas as pd
import gspread
import os
import io
from dotenv import load_dotenv
from google_utils import cargar_credenciales, subir_imagen_a_drive, guardar_datos_en_sheets

load_dotenv()

# Cargar credenciales una sola vez
try:
    creds = cargar_credenciales()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(os.getenv("SHEET_ID")).sheet1
except Exception as e:
    st.error(f"Error al cargar credenciales: {e}")
    st.stop()

# Logo cacheado
@st.cache_resource
def cargar_logo():
    return Image.open("logo_niko.png")

# Mostrar imagen al inicio centrada
image = cargar_logo()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(image, caption="Industrias Niko")

st.title("📋 Relevancias")

# Formulario de reporte
with st.form("formulario_reporte", clear_on_submit=True):
    st.subheader("🛠️ Información de la producción")
    operario = st.text_input("Nombre del operario que reporta")
    maquinas = ["MAQ-2", "MAQ-3", "MAQ-4", "MAQ-5", "MAQ-6", "MAQ-7", "MAQ-8", "MAQ-9", "MAQ-10", "MAQ-13", "MAQ-14", "MAQ-15", "MAQ-16-A", "MAQ-16-B", "MAQ-18", "MAQ-19", "MAQ-20", "MAQ-21", "MAQ-22"]
    maquina = st.selectbox("Nombre de la máquina", maquinas)
    producto = st.text_input("Producto que está produciendo")
    orden = st.text_input("Orden de producción")

    st.subheader("⚠️ Detalles del inconveniente")
    descripcion = st.text_area("Describa la falla o contratiempo")

    st.subheader("📷 Foto del inconveniente (opcional)")
    foto = st.file_uploader("Subir imagen de la falla", type=["jpg", "jpeg", "png"])

    enviado = st.form_submit_button("Enviar reporte")

if enviado:
    if not all([operario, maquina, producto, orden, descripcion]):
        st.warning("Por favor, complete todos los campos.")
    else:
        with st.spinner("Enviando reporte..."):
            try:
                # Subir imagen si se cargó una
                url_imagen = None
                if foto:
                    url_imagen = subir_imagen_a_drive(creds, foto)

                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                datos = [fecha_hora, operario, maquina, producto, orden, descripcion, url_imagen or ""]
                guardar_datos_en_sheets(creds, datos)

                st.success("✅ Reporte enviado correctamente")
                if url_imagen:
                    st.markdown(f"[🔗 Ver imagen subida]({url_imagen})")

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

# Historial de reportes diferido
st.markdown("---")
with st.expander("📊 Historial de reportes"):
    if st.checkbox("Mostrar historial"):
        with st.spinner("Cargando historial..."):
            try:
                registros = sheet.get_all_records()[-200:]  # Últimos 200 registros
                if registros:
                    df = pd.DataFrame(registros)
                    col1, col2 = st.columns(2)
                    with col1:
                        filtro_operario = st.text_input("Filtrar por operario")
                    with col2:
                        filtro_maquina = st.selectbox("Filtrar por máquina", [""] + sorted(df["Máquina"].unique().tolist()))

                    if filtro_operario:
                        df = df[df["Operario"].str.contains(filtro_operario, case=False, na=False)]
                    if filtro_maquina:
                        df = df[df["Máquina"] == filtro_maquina]

                    st.dataframe(df, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Historial')
                    processed_data = output.getvalue()

                    st.download_button(
                        label="🗕️ Descargar historial en Excel",
                        data=processed_data,
                        file_name='historial_reportes.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                else:
                    st.info("No hay reportes registrados todavía.")
            except Exception as e:
                st.error(f"Ocurrió un error al cargar el historial: {e}")

