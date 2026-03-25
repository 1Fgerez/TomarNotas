import streamlit as st
import time
import os
import tempfile
from google import genai

# Configuración básica de la página
st.set_page_config(page_title="Resumidor de Clases", page_icon="📚")

st.title("📚 Resumidor de Clases con IA")
st.markdown("Subí el audio o video de tu clase y obtené los apuntes clave en segundos.")

st.markdown("---")

# 1. El "Peaje" de la API Key (Traé tu propia llave)
api_key_usuario = st.text_input(
    "🔑 Pegá tu API Key de Google acá:", 
    type="password", 
    help="Es gratis. Se usa solo durante esta sesión para generar tu resumen."
)

# 2. Datos de la materia
materia = st.text_input("📝 ¿De qué tema es el video o la grabacion de audio?")

# 3. El botón para subir el archivo
archivo_subido = st.file_uploader("📂 Subí el audio o video de la clase", type=["mp3", "mp4", "m4a", "wav"])

st.markdown("---")

# 4. El motor de la app
if st.button("🚀 Generar Resumen"):
    # Validaciones antes de arrancar
    if not api_key_usuario:
        st.warning("⚠️ Necesitás ingresar una API Key para continuar.")
    elif not materia:
        st.warning("⚠️ Por favor ingresá el nombre de la materia.")
    elif not archivo_subido:
        st.warning("⚠️ Por favor subí un archivo de la clase.")
    else:
        try:
            # Inicializar Gemini con la llave que puso tu amigo/a
            client = genai.Client(api_key=api_key_usuario)
            
            # MAGIA TÉCNICA: Streamlit guarda los archivos subidos en la memoria RAM.
            # Como Gemini necesita leer un archivo físico, creamos un archivo temporal oculto.
            with st.spinner("Preparando archivo..."):
                extension = archivo_subido.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp_file:
                    tmp_file.write(archivo_subido.getvalue())
                    ruta_temp = tmp_file.name

            # Subir a Google
            with st.spinner("☁️ Subiendo a la nube de Google (puede tardar un poquito)..."):
                archivo_gemini = client.files.upload(file=ruta_temp)

                while archivo_gemini.state.name == 'PROCESSING':
                    time.sleep(5)
                    archivo_gemini = client.files.get(name=archivo_gemini.name)

                if archivo_gemini.state.name == 'FAILED':
                    st.error("Hubo un error al procesar el archivo en Google.")
                    st.stop()

            # Generar el resumen
            with st.spinner("🧠 El agente está escuchando y redactando los apuntes..."):
                prompt = f"""
                Sos un asistente de estudio universitario experto. Analizá esta grabación de la clase de la materia {materia}.
                Generá un resumen detallado, claro y estructurado en formato Markdown con las siguientes secciones:
                
                1. **Tema Principal**: Un párrafo resumen de qué trató la clase.
                2. **Conceptos Clave**: Los puntos teóricos más importantes.
                3. **Avisos, Tareas o Bibliografía**: Detallá si el profesor mencionó fechas, libros o entregas. Si no, omití esto.
                4. **Foco de atención**: Mencioná si se hizo énfasis en algo particular para los exámenes.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[archivo_gemini, prompt]
                )
                
            st.success("¡Resumen listo!")
            
            # Mostrar el resultado final en la página web
            st.markdown("### 📋 Tu Resumen:")
            st.info(response.text)
            
            # Limpieza: Borrar rastros para no ocupar espacio
            client.files.delete(name=archivo_gemini.name)
            os.remove(ruta_temp)
            
        except Exception as e:
            # Si el usuario pone una API key falsa o hay un error, le avisamos sin que se rompa la app
            st.error(f"Ups, ocurrió un error: {e}")