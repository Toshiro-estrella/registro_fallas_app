import streamlit as st
from PIL import Image
from datetime import datetime
import os
import gspread
from google_utils import cargar_credenciales, subir_imagen_a_drive, guardar_datos_en_sheets
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# ✅ CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Reporte de Fallas", layout="centered")

# ✅ Inicializar bandera de limpieza
if "limpiar" not in st.session_state:
    st.session_state.limpiar = False

# ✅ Mostrar imagen al inicio centrada
image = Image.open("logo_niko.png")
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.write("")
with col2:
    st.image(image, use_container_width=True, caption="Industrias Niko")
with col3:
    st.write("")

# ✅ TÍTULO PRINCIPAL
st.title("📋 Relevancias")

# ✅ Sección: Información de la producción
st.subheader("🛠️ Información de la producción")
operario = st.text_input("Nombre del operario que reporta", value="" if st.session_state.limpiar else None, key="operario")

maquinas = ["MAQ-2", "MAQ-3", "MAQ-4", "MAQ-5", "MAQ-6", "MAQ-7", "MAQ-8", "MAQ-9", "MAQ-10", "MAQ-13", "MAQ-14", "MAQ-15", "MAQ-16-A", "MAQ-16-B", "MAQ-18", "MAQ-19", "MAQ-20", "MAQ-21", "MAQ-22"]
# Si estamos limpiando, usar una clave temporal para forzar reinicio del widget
key_maquina = "maquina_temp" if st.session_state.limpiar else "maquina"
maquina = st.selectbox("Nombre de la máquina", maquinas, key=key_maquina)

producto = st.text_input("Producto que está produciendo", value="" if st.session_state.limpiar else None, key="producto")
orden = st.text_input("Orden de producción", value="" if st.session_state.limpiar else None, key="orden")

# ✅ Sección: Detalles del inconveniente
st.subheader("⚠️ Detalles del inconveniente")
descripcion = st.text_area("Describa la falla o contratiempo", value="" if st.session_state.limpiar else None, key="descripcion")

st.subheader("📷 Foto del inconveniente (opcional)")
foto = st.file_uploader("Subir imagen de la falla", type=["jpg", "jpeg", "png"], key="foto")

# ✅ Botón para enviar
if st.button("Enviar reporte"):
    if not (maquina and producto and orden and descripcion):
        st.warning("Por favor, complete todos los campos.")
    else:
        try:
            creds = cargar_credenciales()

            # Subir imagen si se cargó una
            url_imagen = None
            if foto:
                url_imagen = subir_imagen_a_drive(creds, foto)

            # Preparar los datos
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            datos = [fecha_hora, operario, maquina, producto, orden, descripcion, url_imagen or ""]

            # Guardar en Google Sheets
            guardar_datos_en_sheets(creds, datos)

            st.success("✅ Reporte enviado correctamente")
            if url_imagen:
                st.markdown(f"[🔗 Ver imagen subida]({url_imagen})")

            # ✅ Activar limpieza y reiniciar
            st.session_state.limpiar = True
            st.rerun()

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# ✅ Resetear la bandera después de limpiar
if st.session_state.limpiar:
    st.session_state.limpiar = False

# ---------------------------
# ✅ Historial de reportes
# ---------------------------

st.markdown("---")
st.subheader("📊 Historial de reportes")

try:
    creds = cargar_credenciales()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(os.getenv("SHEET_ID")).sheet1
    registros = sheet.get_all_records()

    if registros:
        import pandas as pd
        import io
        df = pd.DataFrame(registros)

        # Mostrar filtros
        with st.expander("🔍 Filtrar por"):
            col1, col2 = st.columns(2)
            with col1:
                filtro_operario = st.text_input("Filtrar por operario")
            with col2:
                filtro_maquina = st.selectbox("Filtrar por máquina", [""] + sorted(df["Máquina"].unique().tolist()))

            # Aplicar filtros
            if filtro_operario:
                df = df[df["Operario"].str.contains(filtro_operario, case=False, na=False)]
            if filtro_maquina:
                df = df[df["Máquina"] == filtro_maquina]

        st.dataframe(df, use_container_width=True)

        # ✅ Botón para descargar como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Historial')
        processed_data = output.getvalue()

        st.download_button(
            label="📅 Descargar historial en Excel",
            data=processed_data,
            file_name='historial_reportes.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        st.info("No hay reportes registrados todavía.")

except Exception as e:
    st.error(f"Ocurrió un error al cargar el historial: {e}")





