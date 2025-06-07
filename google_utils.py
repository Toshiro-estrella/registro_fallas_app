import os
import json
import io
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

def cargar_credenciales():
    from dotenv import load_dotenv
    load_dotenv()
    service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return creds

def subir_imagen_a_drive(creds, archivo):
    drive_service = build("drive", "v3", credentials=creds)
    nombre_archivo = archivo.name
    file_metadata = {
        "name": nombre_archivo,
        "parents": [os.getenv("FOLDER_ID_DRIVE")]
    }
    media = MediaIoBaseUpload(archivo, mimetype=archivo.type)
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    file_id = file.get("id")
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    return f"https://drive.google.com/uc?id={file_id}"

def guardar_datos_en_sheets(creds, datos):
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(os.getenv("SHEET_ID")).sheet1
    sheet.append_row(datos)