import streamlit as st
import markdown
import time
import os
import tempfile
import requests
import yt_dlp
from google import genai

# Configuración de la página
st.set_page_config(page_title="Analizador de Audio y Video", page_icon="📚")

if "resumen_generado" not in st.session_state:
    st.session_state.resumen_generado = None

# Título limpio para evitar anclas raras en el link
st.markdown("<h1 style='text-align: left;'>📚 Analizador de Audio y Video</h1>", unsafe_allow_html=True)
st.markdown("Subí el audio/video/link de lo que quieras y obtené un breve resumen.")
st.markdown("---")

# 1. API Key
api_key_usuario = st.text_input("🔑 Pegá tu API Key de Google acá:", type="password")

st.markdown("""
<details style="margin-bottom: 15px; margin-top: -5px;">
    <summary style="font-size: 13px; color: #a0aab2; cursor: pointer;">❓ ¿No tenés una API Key? Clic acá para ver cómo crearla gratis</summary>
    <div style="font-size: 13.5px; padding-top: 8px; padding-left: 15px; color: #d1d5db;">
        1. Entrá a <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #60a5fa; text-decoration: none;">Google AI Studio</a>.<br>
        2. Iniciá sesión y hacé clic en <b>'Create API key'</b>.<br>
        3. Copiá la clave y pegala arriba.
    </div>
</details>
""", unsafe_allow_html=True)

# 2. Datos del tema e Instrucciones
materia = st.text_input("📝 ¿De qué tema trata el contenido?")

prompt_por_defecto = """Generá un resumen detallado y estructurado:
1. **Tema Principal**: Resumen general.
2. **Puntos Clave**: Conceptos más importantes.
3. **Avisos o Fechas**: Tareas o bibliografía mencionada.
4. **Conclusión**: Cierre breve."""

instrucciones = st.text_area("✍️ Instrucciones para la IA:", value=prompt_por_defecto, height=120)
st.caption("💡 Podés pedirle cosas específicas como: 'Solo haceme un resumen de las fórmulas matemáticas'.")

st.markdown("---")

# 3. Pestañas de entrada
tab_link, tab_subir, tab_grabar = st.tabs(["🔗 Pegar Link", "📁 Subir Archivo", "🎙️ Grabar"])

archivo_a_procesar = None

with tab_link:
    st.markdown("""
    <div style="background-color: transparent; padding: 12px; font-size: 14px; border-left: 4px solid #60a5fa; margin-bottom: 15px;">
        ✅ <b>Opción recomendada para clases largas:</b> Pegá el link de YouTube o de Google Drive (asegurante de que el archivo de Drive sea público).
    </div>
    """, unsafe_allow_html=True)
    url_usuario = st.text_input("🔗 Link del video o audio:")

with tab_subir:
    st.markdown("""
    <div style="background-color: transparent; padding: 12px; font-size: 13px; border-left: 4px solid #ffc107; margin-bottom: 15px;">
        ⚠️ <b>Aviso:</b> Si el video dura más de 1 hora, mejor pasalo a MP3 antes de subirlo.
    </div>
    """, unsafe_allow_html=True)
    archivo_subido = st.file_uploader("📂 Elegí un archivo", type=["mp3", "mp4", "m4a", "wav"], key="uploader")

with tab_grabar:
    st.markdown("<div style='font-size: 13px; color: #a0aab2; margin-bottom: 10px;'>Ideal para notas rápidas de voz.</div>", unsafe_allow_html=True)
    audio_grabado = st.audio_input("🔴 Grabar ahora")

st.markdown("---")

# 4. Función mágica para descargar desde links
def descargar_desde_url(url):
    try:
        # Si es YouTube
        if "youtube.com" in url or "youtu.be" in url:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': tempfile.mktemp() + '.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info).replace(info['ext'], 'mp3')
        
        # Si es Google Drive (convertimos link de compartir a link de descarga directa)
        elif "drive.google.com" in url:
            file_id = url.split('/')[-2] if '/d/' in url else url.split('=')[-1]
            direct_link = f'https://drive.google.com/uc?export=download&id={file_id}'
            r = requests.get(direct_link, allow_redirects=True)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(r.content)
            return tmp.name
        
        return None
    except Exception as e:
        st.error(f"Error al bajar el link: {e}")
        return None

# 5. Lógica del Botón
if st.button("🚀 Iniciar Análisis"):
    path_final = None
    
    if url_usuario:
        with st.spinner("📥 Descargando contenido desde el link..."):
            path_final = descargar_desde_url(url_usuario)
    elif audio_grabado:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_grabado.getvalue())
            path_final = tmp.name
    elif archivo_subido:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{archivo_subido.name.split('.')[-1]}") as tmp:
            tmp.write(archivo_subido.getvalue())
            path_final = tmp.name

    if not path_final or not api_key_usuario:
        st.warning("⚠️ Falta la API Key o el contenido para analizar.")
    else:
        try:
            client = genai.Client(api_key=api_key_usuario)
            
            with st.spinner("☁️ Subiendo a la inteligencia artificial..."):
                archivo_gemini = client.files.upload(file=path_final)
                while archivo_gemini.state.name == 'PROCESSING':
                    time.sleep(4)
                    archivo_gemini = client.files.get(name=archivo_gemini.name)

            with st.spinner("🧠 Redactando tus notas..."):
                prompt_final = f"Materia: {materia}\n\nInstrucciones: {instrucciones}"
                response = client.models.generate_content(model='gemini-2.5-flash', contents=[archivo_gemini, prompt_final])
                st.session_state.resumen_generado = response.text
            
            st.success("¡Análisis completado!")
            client.files.delete(name=archivo_gemini.name)
            if os.path.exists(path_final): os.remove(path_final)
            
        except Exception as e:
            st.error(f"Error: {e}")

# 6. Resultados
if st.session_state.resumen_generado:
    st.markdown("### 📋 Resultado:")
    st.markdown(st.session_state.resumen_generado)
    
    # Botón de PDF/HTML
    texto_html = markdown.markdown(st.session_state.resumen_generado)
    plantilla = f"<html><body style='font-family: Arial; padding: 30px;'>{texto_html}</body></html>"
    st.download_button("⬇️ Descargar Resumen", data=plantilla, file_name=f"Notas_{materia}.html", mime="text/html")
