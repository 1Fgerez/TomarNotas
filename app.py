import streamlit as st
import markdown
import time
import os
import tempfile
from google import genai

# Configuración básica de la página
st.set_page_config(page_title="Resumidor de Clases", page_icon="📚")

# --- LA MAGIA: INICIALIZAR LA MEMORIA DE LA APP ---
if "resumen_generado" not in st.session_state:
    st.session_state.resumen_generado = None

st.title("📚 Resumidor de Clases con IA")
st.markdown("Subí el audio o video de tu clase y obtené los apuntes clave en segundos.")
st.markdown("---")

# 1. El "Peaje" de la API Key
api_key_usuario = st.text_input(
    "🔑 Pegá tu API Key de Google acá:", 
    type="password", 
    help="Es gratis. Se usa solo durante esta sesión para generar tu resumen."
)

with st.expander("❓ ¿Cómo encontrar o crear tu API Key gratuita?"):
    st.markdown("""
    1. Entrá a [Google AI Studio](https://aistudio.google.com/app/apikey).
    2. Iniciá sesión con tu cuenta de Google (no pide tarjeta de crédito).
    3. Hacé clic en el botón azul **'Create API key'**.
    4. Copiá esa clave larga y pegala en el recuadro de arriba. 
    """)

# 2. Datos de la materia
materia = st.text_input("📝 ¿De qué materia es la clase? (Ej: Paradigmas, SSL, Análisis 2)")

# 3. El botón para subir el archivo
st.info("💡 Consejo: Para clases largas (ej: 3 horas), te recomendamos subir el archivo en formato AUDIO (.mp3 o .m4a). Pesa muchísimo menos que un video y la IA lo procesa más rápido.")
archivo_subido = st.file_uploader("📂 Subí el audio o video de la clase", type=["mp3", "mp4", "m4a", "wav"])

st.markdown("---")

# 4. El motor de la app
if st.button("🚀 Generar Resumen"):
    if not api_key_usuario:
        st.warning("⚠️ Necesitás ingresar una API Key para continuar.")
    elif not materia:
        st.warning("⚠️ Por favor ingresá el nombre de la materia.")
    elif not archivo_subido:
        st.warning("⚠️ Por favor subí un archivo de la clase.")
    else:
        try:
            client = genai.Client(api_key=api_key_usuario)
            
            with st.spinner("Preparando archivo..."):
                extension = archivo_subido.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp_file:
                    tmp_file.write(archivo_subido.getvalue())
                    ruta_temp = tmp_file.name

            with st.spinner("☁️ Subiendo a la nube de Google (puede tardar un ratito)..."):
                archivo_gemini = client.files.upload(file=ruta_temp)

                while archivo_gemini.state.name == 'PROCESSING':
                    time.sleep(5)
                    archivo_gemini = client.files.get(name=archivo_gemini.name)

                if archivo_gemini.state.name == 'FAILED':
                    st.error("Hubo un error al procesar el archivo en Google.")
                    st.stop()

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
            
            # --- GUARDAMOS EL TEXTO EN LA MEMORIA DE LA PÁGINA ---
            st.session_state.resumen_generado = response.text
            
            client.files.delete(name=archivo_gemini.name)
            os.remove(ruta_temp)
            
        except Exception as e:
            st.error(f"Ups, ocurrió un error. Asegurate de que tu API Key sea correcta. (Detalle: {e})")

# --- MOSTRAR EL RESUMEN Y EL BOTÓN ---
if st.session_state.resumen_generado:
    st.markdown("### 📋 Tu Resumen:")
    
    # Cambiamos st.info por st.markdown para que se vea mucho mejor en la pantalla de la página
    st.markdown(st.session_state.resumen_generado)
    
    st.markdown("---")
    
    # --- LA MAGIA DEL HTML PARA EL PDF ---
    # 1. Traducimos los ## y ** a formato web real
    texto_html = markdown.markdown(st.session_state.resumen_generado)
    
    # 2. Le ponemos un poco de diseño (letra Arial, márgenes prolijos)
    plantilla_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px auto; max-width: 800px; padding: 20px; color: #333; }}
            h1, h2, h3 {{ color: #1a73e8; }}
        </style>
    </head>
    <body>
        {texto_html}
    </body>
    </html>
    """
    
    # 3. El nuevo botón de descarga
    st.download_button(
        label="⬇️ Descargar Resumen",
        data=plantilla_html,
        file_name=f"Resumen_{materia.replace(' ', '_')}.html",
        mime="text/html"
    )
    
    st.caption("💡 **Para guardarlo como PDF:** Hacé clic en descargar, abrí el archivo que se baja y ahí apretá `Ctrl + P` para 'Guardar como PDF'.")
