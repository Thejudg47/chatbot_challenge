import streamlit as st
from google import genai
from google.genai import types
from Claves import *
from Roles import *
import json

# Configuracion de la pagina web
st.set_page_config(
    page_title="",
    page_icon="",
    layout="centered"
)



api_key = GoogleAiApi.obtener_api_google_ai()

client = genai.Client(api_key=api_key)

# Inicializacion segura del estado de la sesion
if "fase" not in st.session_state:
    st.session_state.fase = "configuracion" # Estados: configuracion, entrevista, evaluacion
if "rol_seleccionado" not in st.session_state:
    st.session_state.rol_seleccionado = None
if "pregunta_actual" not in st.session_state:
    st.session_state.pregunta_actual = 1
if "historial" not in st.session_state:
    st.session_state.historial = [] # Estructura: [{"pregunta": "...", "respuesta": "..."}]
if "pregunta_activa" not in st.session_state:
    st.session_state.pregunta_activa = ""
if "reporte_evaluacion" not in st.session_state:
    st.session_state.reporte_evaluacion = None

# Sidebar con boton de reinicio
with st.sidebar:
    st.header("Opciones")
    if st.button("Reiniciar entrevista", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("")
st.caption("")

if st.session_state.fase == "configuracion":

    # Seleccion de rol
    roles_disponibles = Roles.obtener_roles()

    rol = st.selectbox(
        "Selecciona el rol al que postulas:",
        options=roles_disponibles,
        index=0
    )

    if st.button("Comenzar Entrevista", type="primary"):
        st.session_state.rol_seleccionado = rol
        st.session_state.fase = "entrevista"
        st.session_state.pregunta_actual = 1
        st.session_state.historial = []

        # Generar primera pregunta
        prompt_inicial = f"""
        Eres un Líder Técnico entrevistando a un candidato para el puesto de '{rol}'.
        Genera únicamente la PRIMERA pregunta técnica para evaluar sus conocimientos base.
        Sé directo, profesional y conciso. No agregues saludos ni texto introductorio.
        """ 

        with st.spinner("El lider tecnico esta preparando tu primera pregunta..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_inicial
            )
            st.session_state.pregunta_activa = response.strip()
        st.rerun()

# Logica conversacional y control de preguntas
elif st.session_state.fase == "entrevista":
    num_p = st.session_state.pregunta_actual
    rol = st.session_state.rol_seleccionado

    st.info(f"**puesto** {rol}")
    st.progress(num_p / 3, text=f"Pregunta {num_p} de 3")

    # mostrar historial de preguntas y respuestas anteriores
    for idx, item in enumerate(st.session_state.historial, 1):
        st.markdown(f"**Pregunta {idx}:** {item['pregunta']}")
        st.markdown(f"**Tu respuesta:** {item['respuesta']}")
        st.markdown("---")

    # Mostrar la pregunta actual activa
    st.markdown(f"### Pregunta {num_p}:")
    st.write(st.session_state.pregunta_activa)

    # Formulario para capturar la respuesta
    with st.form(key=f"form_pregunta_{num_p}"):
        respuesta_usuario = st.text_area("Escribe tu respuesta técnica aquí:", height=120)
        btn_enviar = st.form_submit_button("Enviar Respuesta")

    if btn_enviar:
        if not respuesta_usuario.strip():
            st.warning("Por favor redacta una respuesta antes de enviar.")
        else:
            # 1. Guarda pregunta y respuesta en el historial
            st.session_state.historial.append({
                "pregunta": st.session_state.pregunta_activa,
                "respuesta": respuesta_usuario.strip()
            })

            # Control de limite de preguntas (3)
            if num_p < 3:
                st.session_state.pregunta_actual += 1

                # prompt adaptativo: Gemini considera la última respuesta dada
                prompt_adaptativo = f"""
                Eres un Líder Técnico evaluando a un aspirante para el puesto de '{rol}'.
                
                Historial completo de la entrevista hasta el momento:
                {st.session_state.historial}
                
                Formula la PREGUNTA #{st.session_state.pregunta_actual} de 3 de forma adaptativa:
                - Si la respuesta previa fue vaga, superficial o errónea, haz una pregunta de aclaración o sobre un concepto fundamental.
                - Si la respuesta previa fue sólida y completa, eleva la dificultad hacia un escenario de arquitectura, optimización o caso de borde.
                
                Entrega ÚNICAMENTE el texto de la nueva pregunta sin saludos ni metatexto.
                """

                with st.spinner("El lider tecnico esta analizando tu respuesta..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_adaptativo
                    )
                    st.session_state.pregunta_activa = response.text.strip()

                st.rerun()

            else:
                # 3. Transicion de estado inmediata a la fase de evaluacion
                st.session_state.fase = "evaluacion"
                st.rerun()

# Pantalla de evaluacion
elif st.session_state.fase == "evaluacion":
    st.subheader("📊 Reporte Final de Evaluación Técnica")
    rol = st.session_state.rol_seleccionado

    # si aun no hemos generado la evaluzacion en esta sesion, la solicitamos a Gemini
    if st.session_state.reporte_evaluacion is None:
        with st.spinner("Construyendo el reporte de evaluación en Markdown..."):
            prompt_reporte_md = f"""
            Actúa como un Líder Técnico Senior realizando la evaluación final del candidato para el rol de '{rol}'.
            
            Historial completo de la entrevista (3 preguntas y respuestas):
            {json.dumps(st.session_state.historial, ensure_ascii=False)}

            Genera una evaluación que retorne un JSON estricto para estructurar el reporte final según estas reglas:
            1. "calificacion_global": Número entero del 1 al 10.
            2. "fortalezas": Lista con AL MENOS 2 aspectos técnicos positivos.
            3. "areas_mejora": Lista con AL MENOS 2 conceptos que el aspirante debe reforzar.
            4. "dictamen": Únicamente 'APROBADO' o 'NO APROBADO'.
            5. "reporte_markdown": Un texto formateado en Markdown que integre exactamente estos 4 puntos con encabezados claros y listas con viñetas.

            Estructura del JSON:
            {{
                "calificacion_global": 8,
                "fortalezas": ["Punto 1", "Punto 2"],
                "areas_mejora": ["Punto 1", "Punto 2"],
                "dictamen": "APROBADO",
                "reporte_markdown": "## Reporte de Evaluación\\n..."
            }}
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_reporte_md,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            st.session_state.reporte_evaluacion = json.loads(response.text)

    eval_data = st.session_state.reporte_evaluacion

    # Renderizado del reporte visual
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="Calificacion Global", value=f"{eval_data['calificacion_global']} / 10")

        dictamen = eval_data["dictamen"]
        if dictamen == "APROBADO":
            st.success(f"### Dictamen: {dictamen}")
        else:
            st.error(f"### Dictamen: {dictamen}")

    with col2:
        st.markdown("### Resumen del reporte")
        st.write(eval_data["reporte_markdown"])

    st.markdown("---")

    # --- 2 Y 3. FORTALEZAS Y ÁREAS DE MEJORA EN COLUMNAS ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 2. Fortalezas Detectadas")
        for f in eval_data["fortalezas"]:
            st.markdown(f"- {f}")

    with col_b:
        st.markdown("### 3. Áreas de Mejora")
        for m in eval_data["areas_mejora"]:
            st.markdown(f"- {m}")

    st.markdown("---")


    # Desplegable para revisar la entrevista completa
    with st.expander("🔍 Ver transcripción de las 3 preguntas y respuestas"):
        for idx, item in enumerate(st.session_state.historial, 1):
            st.markdown(f"**P{idx}:** {item['pregunta']}")
            st.markdown(f"**R:** {item['respuesta']}")
            st.markdown("---")

    if st.button("Iniciar nueva entrevista", type="primary"):
        st.session_state.clear()
        st.rerun()

