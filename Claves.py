import streamlit as st

class GoogleAiApi:

    @staticmethod
    def obtener_api_google_ai():
        # Lectura de la clave api desde el archivo secrets
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            return api_key
        except Exception:
            st.error("🔑 Falta la API Key. Configúrala en `.streamlit/secrets.toml` o en las preferencias de Streamlit Cloud.")
            st.stop()