import streamlit as st
import markdown
import time
import os
import tempfile
from google import genai

# Configuración básica de la página
st.set_page_config(page_title="Analizador de Audio y Video", page_icon="📚")

# --- LA MAGIA: INICIALIZAR LA MEMORIA DE LA APP ---
if "resumen_generado" not in st.session_state:
    st.session_state.resumen_generado = None

# Título en HTML para que el link de la web quede limpio y corto
st.markdown("<h1 style='text-align: left;'>📚 Analizador de Audio y Video</h1>", unsafe_allow_html=True)
st.markdown("Subí el audio/video de lo que quieras y obtené un breve resumen.")
st.markdown("---")

# 1. El "Peaje" de la API Key
api_key_usuario = st.text_input(
    "🔑 Pegá tu API Key de Google acá:", 
    type="password", 
    help="Es gratis. Se usa solo durante esta sesión para generar tu análisis."
)

# Desplegable sutil para la ayuda
st.markdown("""
<details style="margin-bottom: 15px; margin-top: -5px;">
    <summary style="font-size: 13px; color: #a0aab2; cursor: pointer;">❓ ¿No tenés una API Key? Tocá acá para ver cómo crearla gratis</summary>
    <div style="font-size: 13.5px; padding-top: 8px; padding-left: 15px; color: #d1d5db;">
        1. Entrá a <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #60a5fa; text-decoration: none;">Google AI Studio</a>.<br>
        2. Iniciá sesión con tu cuenta de Google (no pide tarjeta de crédito).<br>
        3. Hacé clic en el botón azul <b>'Create API key'</b>.<br>
        4. Copiá esa clave larga y pegala en el recuadro de arriba.
    </div>
</details>
""", unsafe_allow_html=True)

# 2. Datos del tema
materia = st.text_input("📝 ¿De qué tema es el video o el audio?")

# 3. Instrucciones personalizables
prompt_por_defecto = """Generá un resumen detallado, claro y estructurado en formato Markdown con las siguientes secciones:
1. **Tema Principal**: Un párrafo resumen general.
2. **Puntos Clave**: Los conceptos más importantes explicados de forma sencilla.
3. **Avisos o Fechas**: Mencioná si se habló de tareas, entregas o bibliografía.
4. **Conclusión**: Un cierre breve."""

instrucciones = st.text_area(
    "✍️ ¿Qué querés que haga el agente? (Podés dejar este texto o escribir el tuyo):", 
    value=prompt_por_defecto, 
    height=150
)

st.caption("💡 **Aclaración:** Podés cambiar este recuadro para que genere lo que desees. Otro ejemplo podría ser pedirle que solo te haga un resumen de fórmulas, etc.  \n📝 **Tip de formato:** Utilizá `** **` para destacar los títulos o palabras clave (Ej: **Título**).")
st.markdown("---")

# --- 4. Opciones de entrada (Pestañas con el nuevo aviso de duración) ---
tab_subir, tab_grabar = st.tabs(["📁 Subir Archivo", "🎙️ Grabar en Vivo"])

with tab_subir:
    # Único cartel de aviso, claro y al grano
    st.markdown("""
    <div style="background-color: transparent; padding: 12px; font-size: 14px; border-left: 4px solid #ffc107; margin-bottom: 15px;">
        ⚠️ <b>¡Atención con las clases largas!</b><br>
        Si tu video dura <b>más de 1 hora</b>, por favor convertilo a MP3 antes de subirlo. Los videos pesados saturan el sistema y pueden dar error.
        <br><a href="https://cloudconvert.com/mp4-to-mp3" target="_blank" style="color: #60a5fa; text-decoration: none;">🔗 Clic acá para convertir video a MP3 gratis</a>
    </div>
    <div style="background-color: transparent; padding: 12px; font-size: 13px; border-left: 4px solid #17a2b8; margin-bottom: 15px; color: #a0aab2;">
        💡 <b>Tip:</b> Para grabar clases enteras, lo más seguro es usar la grabadora de voz de tu celu y subir el audio directamente acá.
    </div>
    """, unsafe_allow_html=True)
    
    archivo_subido = st.file_uploader("📂 Subí un archivo desde tu equipo", type=["mp3", "mp4", "m4a", "wav"])

with tab_grabar:
    st.markdown("""
    <div style="background-color: transparent; padding: 12px; font-size: 14px; border-left: 4px solid #f8d7da; margin-bottom: 15px;">
        ⚠️ <b>Aviso importante:</b> Usá esta opción solo para audios CORTOS. Si apagás la pantalla del celu o cambiás de app, la grabación se cortará.
    </div>
    """, unsafe_allow_html=True)
    
    audio_grabado = st.audio_input("🔴 Tocá para grabar")

# Lógica para saber qué archivo vamos a usar
archivo_final = audio_grabado if audio_grabado else archivo_subido

st.markdown("---")

# 5. El motor de la app
if st.button("🚀 Procesar Archivo"):
    if not api_key_usuario:
        st.warning("⚠️ Necesitás ingresar una API Key para continuar.")
    elif not materia:
        st.warning("⚠️ Por favor ingresá de qué tema trata el archivo.")
    elif not instrucciones:
        st.warning("⚠️ Las instrucciones para la IA no pueden estar vacías.")
    elif not archivo_final:
        st.warning("⚠️ Por favor subí un archivo o grabá un audio.")
    else:
        try:
            client = genai.Client(api_key=api_key_usuario)
            
            with st.spinner("Preparando archivo..."):
                extension = archivo_final.name.split('.')[-1] if hasattr(archivo_final, 'name') else 'wav'
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp_file:
                    tmp_file.write(archivo_final.getvalue())
                    ruta_temp = tmp_file.name

            with st.spinner("☁️ Subiendo a Google (clases largas pueden tardar unos minutos)..."):
                archivo_gemini = client.files.upload(file=ruta_temp)
                while archivo_gemini.state.name == 'PROCESSING':
                    time.sleep(5)
                    archivo_gemini = client.files.get(name=archivo_gemini.name)

            with st.spinner("🧠 Analizando contenido..."):
                prompt_final = f"Tema: {materia}.\n\nInstrucciones:\n{instrucciones}"
                response = client.models.generate_content(model='gemini-2.5-flash', contents=[archivo_gemini, prompt_final])
                
            st.success("¡Análisis listo!")
            st.session_state.resumen_generado = response.text
            client.files.delete(name=archivo_gemini.name)
            os.remove(ruta_temp)
            
        except Exception as e:
            st.error(f"Error: El archivo es muy pesado o la clave es incorrecta. Intentá con un MP3 más liviano. (Detalle: {e})")

# --- MOSTRAR EL RESUMEN Y EL BOTÓN ---
if st.session_state.resumen_generado:
    st.markdown("### 📋 Tu Resultado:")
    st.markdown(st.session_state.resumen_generado)
    st.markdown("---")
    
    texto_html = markdown.markdown(st.session_state.resumen_generado)
    plantilla_html = f"<html><body style='font-family: Arial; padding: 40px; line-height: 1.6;'>{texto_html}</body></html>"
    
    st.download_button(
        label="⬇️ Descargar Archivo",
        data=plantilla_html,
        file_name=f"Analisis_{materia.replace(' ', '_')}.html",
        mime="text/html"
    )
    st.caption("💡 **Tip:** Abrí el archivo descargado y apretá `Ctrl + P` para guardarlo como un PDF perfecto.")
