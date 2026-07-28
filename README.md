# 🩺 Medical Agent

Agente de Inteligencia Artificial para la administración de un consultorio médico.

Este proyecto implementa un agente basado en **LangGraph** y **FastAPI** que utiliza un modelo local de **Ollama** para comprender las solicitudes del usuario, clasificarlas y ejecutar herramientas del sistema del consultorio mediante APIs.

---

# Arquitectura

```
                Usuario
                    │
                    ▼
              FastAPI (/chat)
                    │
                    ▼
               LangGraph Agent
                    │
     ┌──────────────┴──────────────┐
     │                             │
 Planner                    Tool Router
     │                             │
     └──────────────┬──────────────┘
                    ▼
             Medical Tools
                    │
                    ▼
        Backend del Consultorio
           (NestJS REST API)
```

---

# Tecnologías

- Python 3.13
- FastAPI
- Uvicorn
- LangGraph
- LangChain
- Ollama
- Qwen3 8B
- Pydantic
- HTTPX

---

# Estructura del proyecto

```
medical-agent/
│
├── app/
│   ├── graph/
│   │     builder.py
│   │
│   ├── nodes/
│   │     planner.py
│   │     router.py
│   │     responder.py
│   │
│   ├── prompts/
│   │     system_prompt.py
│   │
│   ├── schemas/
│   │     request.py
│   │     state.py
│   │
│   ├── tools/
│   │
│   ├── main.py
│   │
│   └── config.py
│
├── requirements.txt
├── .env
└── README.md
```

---

# Instalación

## Clonar el repositorio

```bash
git clone https://github.com/usuario/medical-agent.git

cd medical-agent
```

---

## Crear entorno virtual

Windows

```powershell
py -3.13 -m venv .venv
```

Linux / Mac

```bash
python3.13 -m venv .venv
```

---

## Activar entorno virtual

Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux

```bash
source .venv/bin/activate
```

---

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Ollama

Instalar Ollama

https://ollama.com

Descargar el modelo

```bash
ollama pull qwen3:8b
```

Verificar modelos instalados

```bash
ollama list
```

---

# Ejecutar el proyecto

```bash
python -m uvicorn app.main:app --reload
```

Swagger(Endpoints test)

```
http://127.0.0.1:8000/docs
```

# Flujo del agente

1. Usuario envía un mensaje.
2. FastAPI recibe la petición.
3. LangGraph ejecuta el grafo.
4. Planner identifica la intención.
5. Router selecciona la herramienta.
6. La herramienta consulta el backend.
7. Se genera la respuesta.
8. FastAPI devuelve el resultado.

---

# Ejemplo

Petición

```json
{
    "message":"Quiero agendar una cita para mañana"
}
```

Respuesta

```json
{
    "intent":"appointment",
    "tool":"appointment_tool",
    "response":"He encontrado disponibilidad para mañana a las 10:00."
}
```

---

# Roadmap

## Sprint 1

- [x] FastAPI
- [x] LangGraph
- [x] Planner
- [x] Parser JSON
- [x] Integración con Ollama

---

## Sprint 2

- [ ] Router
- [ ] Medical Tools
- [ ] Response Generator

---

## Sprint 3

- [ ] Memoria conversacional
- [ ] Persistencia
- [ ] Checkpoints LangGraph

---

## Sprint 4

Integración con el sistema del consultorio

- [ ] Pacientes
- [ ] Médicos
- [ ] Consultas
- [ ] Agenda
- [ ] Recetas
- [ ] Historial clínico

---

# Próximas funcionalidades

- Agendar citas
- Cancelar citas
- Reprogramar citas
- Consultar pacientes
- Buscar historial clínico
- Registrar consultas
- Registrar diagnósticos
- Registrar tratamientos
- Consultar medicamentos
- Enviar recordatorios

---

# Licencia

Proyecto desarrollado con fines educativos y de investigación.

---

# Autor

**Benjamín Carreón**

Proyecto desarrollado como parte del sistema **Agente Médico**, una plataforma de inteligencia artificial para la administración de consultorios médicos basada en FastAPI, LangGraph y Ollama.