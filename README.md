# 🩺 Medical Agent — Agente Médico

Agente de inteligencia artificial para la **administración de citas y la consulta de información de un consultorio médico** mediante lenguaje natural.

Este repositorio contiene el servicio de IA desarrollado con **Python, FastAPI y LangGraph**. El Planner utiliza **Ollama** con el modelo local **`qwen3:1.7b`** para clasificar solicitudes y extraer entidades; las operaciones administrativas se delegan a una **API REST independiente desarrollada con NestJS**.

> **Estado del proyecto (octubre de 2026):** el flujo de gestión de citas y la memoria conversacional están implementados en el agente. RAG dispone de componentes de recuperación, pero todavía necesita un proceso de indexación y respuestas fundamentadas. La integración de consultas clínicas y las notificaciones automáticas están pendientes. **n8n es la tecnología elegida para orquestar las notificaciones**, pero aún no está integrado en el código incluido en este repositorio.
>
> **Alcance:** asistente administrativo. No es un sistema de diagnóstico, prescripción ni toma de decisiones clínicas autónomas. NestJS es la fuente de verdad para los registros del consultorio.

---

## Arquitectura

```text
Usuario / cliente HTTP
         │  POST /chat (message, session_id)
         ▼
FastAPI — app/main.py
         │
         ├── session_id → thread_id
         │                   │
         │                   ▼
         │         AsyncSqliteSaver (SQLite)
         │         data/checkpoints.sqlite3
         │                   │
         └───────────────────┘
         ▼
LangGraph (StateGraph)
         │
         ▼
Planner ── Ollama / Qwen3 1.7B
         │    Intención + entidades en JSON
         │    Historial: últimos 3 turnos
         ▼
Router
         │
         ├── patients ───────┐
         ├── appointments ───┼── HTTPX ── NestJS REST API ── MongoDB
         ├── rag ────────────┼── Chroma + nomic-embed-text
         └── sin herramienta│
                            │
         ▼                  │
Responder ◄─────────────────┘
         │
         ├── Respuesta al usuario
         └── Actualización del historial en LangGraph / SQLite
```

**Separación de responsabilidades:**

- **FastAPI:** punto de entrada del agente, identificadores de sesión, inicialización de dependencias y respuesta HTTP.
- **LangGraph:** ejecución del flujo Planner → Router → herramienta/RAG → Responder y persistencia del estado.
- **Ollama / Planner:** interpretación de instrucciones y extracción de entidades. No escribe directamente en MongoDB.
- **Herramientas Python:** validación temprana y consumo de la API del consultorio.
- **NestJS:** acceso a pacientes, médicos y citas, además de la aplicación de reglas de negocio del sistema. El código de NestJS se mantiene en un proyecto separado y no forma parte de este archivo fuente.
- **SQLite:** almacenamiento de checkpoints de conversaciones; no sustituye la base de datos clínica.
- **Chroma:** almacenamiento vectorial utilizado por los componentes RAG.

### Integración de notificaciones prevista con n8n

```text
Cambio confirmado en una cita (NestJS)
                  │
                  ▼
     Evento / solicitud autenticada
                  │
                  ▼
              n8n (previsto)
                  │
          ┌───────┴───────┐
          ▼               ▼
       Correo          WhatsApp / SMS
          │               │
          └───────┬───────┘
                  ▼
        Registro de resultado / reintento
```

**Este flujo es un diseño objetivo, no una integración ya ejecutable.** La decisión de usar n8n no implica que existan actualmente workflows, webhooks, credenciales de proveedores ni envío efectivo de mensajes.

---

## Tecnologías

| Componente | Tecnología / implementación |
|---|---|
| Lenguaje | Python 3.13 (entorno de desarrollo) |
| API del agente | FastAPI, Uvicorn, Pydantic |
| Orquestación | LangGraph (`StateGraph`) |
| Modelo de lenguaje | Ollama, `qwen3:1.7b` mediante `langchain-ollama` |
| Memoria | `langgraph-checkpoint-sqlite`, `AsyncSqliteSaver`, `aiosqlite` |
| Cliente del backend | HTTPX asíncrono con reutilización de conexiones |
| RAG | Chroma, `nomic-embed-text`, LangChain, `PyPDFLoader` |
| Zona horaria | `zoneinfo` / `APP_TIMEZONE` |
| Sistema de consultorio | API REST NestJS y MongoDB (servicio externo al repositorio) |
| Notificaciones futuras | **n8n** para orquestar avisos y recordatorios |

Las dependencias Python declaradas se encuentran en `requirements.txt`.

---

## Funcionalidades y estado real

| Funcionalidad | Estado | Alcance encontrado en el código |
|---|---|---|
| API de chat y salud | ✅ Implementado | `POST /chat`, `GET /health` y documentación OpenAPI |
| Planner | ✅ Implementado | Interpretación con Qwen, salida JSON, alias de intenciones y normalización de entidades |
| Router y Responder | ✅ Implementado | Selección de herramientas y generación determinista de mensajes de salida |
| Búsqueda de pacientes | ✅ Implementado | Por nombre mediante NestJS |
| Identificación de médicos | ✅ Implementado para citas | Búsqueda/resolución de médicos por nombre en NestJS |
| Gestión de citas | ✅ Implementado en el agente | Disponibilidad, agendamiento, consulta, cancelación, reprogramación, confirmación, finalización e inasistencia |
| Validación temporal | ✅ Implementado en el agente | Rechazo de fechas pasadas y de horas vencidas cuando la cita es hoy |
| Conversaciones entre mensajes | ✅ Implementado | `session_id` como `thread_id` de LangGraph |
| Checkpoints persistentes | ✅ Configurado | `AsyncSqliteSaver` y base SQLite local; requiere conservar el mismo archivo para recuperar los hilos |
| Ventana de contexto | ✅ Implementado | El Planner incorpora los últimos `PLANNER_HISTORY_TURNS` turnos (3 por defecto) |
| RAG documental | 🟡 Parcial | Embeddings, base vectorial, retriever y nodo RAG; falta ingesta operativa y respuestas con fuentes |
| Consultas médicas | 🟡 Esqueleto | `ConsultationsTool` hace `GET /consultations`, pero no se conecta al Router ni al grafo |
| Notificaciones | 🟡 Esqueleto | `NotificationsTool` hace `GET /notifications`, pero no está conectado al grafo |
| Automatización de notificaciones con n8n | ⏳ Planificado | Integración por eventos y canales de mensajería aún por desarrollar |
| Contexto estructurado de pacientes/citas activas | ⏳ Pendiente | Actualmente se utiliza el historial textual reciente; no existe un gestor específico de entidades activas |
| Autorización del usuario sobre conversaciones | ⏳ Pendiente de integrar | El endpoint `/chat` recibe `session_id`, pero no se observa autenticación de sesiones en este servicio |

> Los estados de NestJS se describen según las llamadas que realiza el agente. Este repositorio no permite certificar por sí solo todas las validaciones internas, permisos o condiciones de concurrencia de la API NestJS.

---

## Intenciones reconocidas por el Planner

El conjunto de intenciones declaradas en `app/prompts/system_prompt.py` y `app/nodes/planner.py` es:

| Intención | Uso |
|---|---|
| `search_patient` | Buscar pacientes por nombre |
| `check_appointment_availability` | Consultar horarios disponibles de un médico |
| `schedule_appointment` | Agendar una cita |
| `list_appointments` | Consultar citas mediante filtros |
| `cancel_appointment` | Cancelar una cita |
| `reschedule_appointment` | Reprogramar una cita |
| `confirm_appointment` | Confirmar una cita programada |
| `complete_appointment` | Marcar una cita como completada |
| `mark_appointment_no_show` | Registrar que el paciente no se presentó |
| `search_document` | Recuperar contenido del índice RAG |
| `greeting` | Responder saludos |
| `unknown` | Manejar solicitudes no identificadas o no soportadas |

El Planner también normaliza algunos alias de intención, nombres de campos, estados y valores booleanos. El prompt solicita nombres de médicos sin títulos como «Dr.», «Dra.», «doctor» o «doctora» y fechas en formato `YYYY-MM-DD`.

### Gestión de citas

`app/tools/appointments.py` permite:

- Resolver al paciente y al médico mediante la API de NestJS.
- Consultar disponibilidad según médico, fecha y duración.
- Agendar citas solo cuando la información está completa y el horario está disponible.
- Consultar citas por paciente, médico, fecha, estado, pendientes o próximas, según los filtros admitidos por el backend.
- Cancelar y reprogramar citas existentes.
- Confirmar, completar o marcar inasistencia.
- Evitar la selección arbitraria cuando una solicitud coincide con varias citas.
- Rechazar agendamientos y reprogramaciones en fechas pasadas o en horas del día actual que ya transcurrieron.
- Comprobar fechas (`YYYY-MM-DD`), horas (`HH:mm`) y duración permitida (15–240 minutos).

Para agendar, la herramienta resuelve médico y paciente de forma concurrente y consulta la disponibilidad antes de solicitar la creación de la cita a NestJS. La API del consultorio debe conservar la validación definitiva de las reglas de negocio.

Consulta también [`APPOINTMENTS_IMPLEMENTATION.md`](APPOINTMENTS_IMPLEMENTATION.md) para los detalles de las operaciones ampliadas.

---

## Memoria y contexto conversacional

La memoria utiliza `AsyncSqliteSaver`, inicializado durante el ciclo de vida de FastAPI en `app/memory/memory.py`. El grafo se compila mediante `build_graph(checkpointer)` y se invoca con:

```python
config={
    "configurable": {
        "thread_id": session_id,
    },
}
```

La ruta por defecto del almacenamiento es `data/checkpoints.sqlite3`, configurable con `CHECKPOINT_DB_PATH`.

**Cómo se comporta:**

1. En la primera solicitud, FastAPI utiliza el `session_id` proporcionado o genera uno nuevo.
2. LangGraph busca los checkpoints asociados con ese `thread_id`.
3. El Planner construye el prompt con el mensaje actual y los **últimos 3 turnos** del campo `history` (valor configurable).
4. El Responder incorpora el intercambio usuario/asistente a `history` y LangGraph guarda el nuevo estado.
5. Una solicitud posterior con el mismo `session_id` puede recuperar los turnos previos. La continuidad tras reinicios depende de reutilizar el mismo archivo SQLite.

**Persistencia no significa contexto ilimitado:** los checkpoints pueden conservar más turnos y otros campos del estado, pero el Planner solo incorpora al prompt los últimos `PLANNER_HISTORY_TURNS` intercambios. No hay todavía resumen automático de conversaciones largas ni recuperación selectiva de entidades antiguas.

**Consideración de rendimiento:** cuando una respuesta enumera muchas citas, su texto completo se incorpora al historial. Esto puede incrementar la cantidad de tokens enviados a Ollama y, con ello, la latencia de mensajes posteriores.

**Consideración de privacidad:** los checkpoints pueden contener respuestas y datos de pacientes; el archivo SQLite debe protegerse y no publicarse. El `session_id` por sí mismo aún no acredita la identidad ni los permisos de un usuario.

---

## RAG documental: alcance actual

El proyecto incluye la infraestructura básica para recuperar fragmentos relevantes:

```text
Documentos PDF
     │
     ▼
PyPDFLoader (loader.py)
     │
     ▼
RecursiveCharacterTextSplitter (splitter.py)
     │
     ▼
OllamaEmbeddings / nomic-embed-text
     │
     ▼
Chroma: colección "medical"
     │
     ▼
Retriever (k=4)
     │
     ▼
RagTool → rag_node → Responder
```

**Limitaciones actuales:** el código contiene cargador, splitter, índice y recuperador, pero no se encontró un proceso completo que cargue documentos, cree fragmentos y los inserte en Chroma de forma reproducible. Tampoco se encontró una colección de documentos PDF en `app/documents/` dentro del proyecto entregado. `RagTool` devuelve el texto concatenado de documentos recuperados; aún no genera una respuesta sintetizada con referencias verificables a las fuentes.

RAG es independiente del historial conversacional persistido en SQLite: Chroma se utiliza para fragmentos documentales; SQLite conserva el estado de LangGraph.

---

## Notificaciones con n8n — diseño elegido y trabajo pendiente

La estrategia seleccionada para las notificaciones es **n8n como orquestador de workflows**. El objetivo es desacoplar la entrega de mensajes de las herramientas de IA y de las reglas de negocio de NestJS.

### Responsabilidades propuestas

| Componente | Responsabilidad prevista |
|---|---|
| NestJS | Confirmar operaciones de citas, registrar el evento correspondiente y determinar destinatarios autorizados |
| n8n | Recibir eventos, decidir el flujo, enviar el mensaje por un proveedor y gestionar errores/reintentos |
| Proveedores externos | Entregar correos, mensajes de WhatsApp o SMS según el canal contratado |
| Agente FastAPI | Atender solicitudes conversacionales y consultar el resultado a través de NestJS si se habilita esa capacidad |

### Eventos candidatos

- `appointment.created`: confirmación inicial al registrar una cita.
- `appointment.confirmed`: aviso de cita confirmada.
- `appointment.rescheduled`: comunicación de nueva fecha y hora.
- `appointment.cancelled`: aviso de cancelación.
- `appointment.reminder`: recordatorio previo a la cita, programado según las reglas del consultorio.

*Estos nombres representan una propuesta de contrato de eventos, no eventos ya implementados en el backend.*

### Criterios para la integración

- Disparar notificaciones **después** de confirmar la operación en NestJS; no asumir que una intención del Planner equivale a una cita guardada.
- Autenticar la comunicación con n8n y evitar exponer webhooks sin protección.
- Minimizar los datos personales enviados a proveedores de mensajería.
- Establecer consentimiento, horarios permitidos y preferencias del destinatario.
- Registrar resultados, reintentos e idempotencia para evitar mensajes duplicados.
- Mantener las fallas de mensajería separadas de la transacción que crea o modifica una cita.
- Centralizar reglas de fechas y zonas horarias en el sistema del consultorio.

**Estado actual del repositorio:** `app/tools/notifications.py` contiene un cliente mínimo que consulta `/notifications`; no hay rutas, nodos ni workflows n8n conectados a la ejecución del grafo. La elección de n8n está documentada como dirección de desarrollo, no como funcionalidad disponible.

---

## Estructura del proyecto

```text
AgenteMedico/
├── app/
│   ├── config/
│   │   └── settings.py
│   ├── graph/
│   │   ├── builder.py
│   │   └── state.py
│   ├── memory/
│   │   └── memory.py
│   ├── nodes/
│   │   ├── planner.py
│   │   ├── router.py
│   │   ├── rag_node.py
│   │   └── responder.py
│   ├── prompts/
│   │   └── system_prompt.py
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── loader.py
│   │   ├── rag_tool.py
│   │   ├── retriever.py
│   │   ├── splitter.py
│   │   └── vectordb.py
│   ├── schemas/
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── llm.py
│   │   └── nest_api.py
│   ├── tools/
│   │   ├── appointments.py
│   │   ├── consultations.py
│   │   ├── notifications.py
│   │   └── patients.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── text_normalizer.py
│   └── main.py
├── .env.example
├── requirements.txt
├── APPOINTMENTS_IMPLEMENTATION.md
├── README.md
└── README-actualizado.md
```

`app/schemas/response.py` existe, pero está vacío en la versión revisada. `consultations.py` y `notifications.py` contienen implementaciones mínimas todavía no utilizadas por el Router.

---

## Instalación y ejecución local

### Requisitos

- Python 3.13 (versión utilizada para el desarrollo del agente).
- Ollama instalado y accesible mediante `OLLAMA_BASE_URL`.
- Backend NestJS del consultorio disponible y configurado mediante `NEST_API`.

### Descargar el proyecto y preparar Python

```powershell
git clone https://github.com/BCarreonC/AgenteMedico.git
cd AgenteMedico

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux/macOS puedes crear el entorno con `python3.13 -m venv .venv` y activarlo mediante `source .venv/bin/activate`.

### Instalar los modelos de Ollama

Instala Ollama desde <https://ollama.com> y ejecuta:

```powershell
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```

El modelo `qwen3:1.7b` se emplea para el Planner. `nomic-embed-text` se utiliza para embeddings documentales.

### Configurar variables de entorno

```powershell
Copy-Item .env.example .env
```

Ejemplo alineado con `app/config/settings.py`:

```dotenv
# API de negocio
NEST_API=http://127.0.0.1:3000/api
NEST_TIMEOUT_SECONDS=15.0

# Aplicación
APP_TIMEZONE=America/Mexico_City

# Ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:1.7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_KEEP_ALIVE=30m
OLLAMA_NUM_PREDICT=128

# Memoria y contexto
CHECKPOINT_DB_PATH=data/checkpoints.sqlite3
PLANNER_HISTORY_TURNS=3

# Registro de eventos
LOG_LEVEL=INFO
```

### Ejecutar FastAPI

Con NestJS y Ollama accesibles:

```powershell
python -m uvicorn app.main:app --reload
```

| Ruta | Método | Propósito |
|---|---|---|
| `http://127.0.0.1:8000/health` | GET | Estado básico del agente |
| `http://127.0.0.1:8000/chat` | POST | Conversación con el agente |
| `http://127.0.0.1:8000/docs` | GET | Documentación interactiva OpenAPI |

Durante el arranque, FastAPI prepara el checkpointer, verifica la conectividad de NestJS/Ollama y realiza un *warm-up* de Qwen. La función de comprobación informa los errores de conectividad en los logs; no debe interpretarse como una garantía de que todas las dependencias estén disponibles.

---

## API de chat

### Solicitud

```http
POST /chat
Content-Type: application/json
```

```json
{
  "session_id": "consultorio-001",
  "message": "Muéstrame las citas de Juan Pérez García"
}
```

`message` es obligatorio. `session_id` es opcional; si se omite, el backend del agente genera un UUID. Para continuar una conversación, el cliente debe conservar el `session_id` de la respuesta y enviarlo de nuevo.

### Estructura de respuesta

```json
{
  "session_id": "consultorio-001",
  "intent": "list_appointments",
  "confidence": 0.99,
  "tool": "appointments",
  "entities": {
    "patient_name": "Juan Pérez García"
  },
  "response": "Encontré citas para el paciente solicitado...",
  "errors": []
}
```

*Ejemplo ilustrativo de formato, no un resultado garantizado:* el contenido, la intención, la confianza y las entidades dependen de la solicitud, del Planner y de lo que devuelva NestJS.

### Continuación del contexto

```json
{
  "session_id": "consultorio-001",
  "message": "¿Y cuáles son sus próximas citas?"
}
```

El Planner puede interpretar referencias como «sus citas» utilizando los últimos turnos del historial. Esto no sustituye la confirmación de identidades y registros cuando una acción podría afectar datos de varios pacientes.

---

## Configuración y rendimiento

La instancia de `ChatOllama` usa `temperature=0`, `reasoning=False`, `format="json"`, `num_predict` y `keep_alive` configurables. La aplicación intenta cargar el modelo al iniciar para disminuir la latencia de las primeras solicitudes.

`NestAPIClient` utiliza un `httpx.AsyncClient` compartido, con límites de conexiones y *keep-alive*. El agente registra tiempos del Planner, solicitudes a Ollama, llamadas HTTP, ejecución de herramientas y duración total de cada petición.

El tamaño del contexto conversacional influye en el costo de evaluación del prompt. El valor inicial `PLANNER_HISTORY_TURNS=3` controla **cuántos turnos se incluyen en el prompt**, no cuántos conserva la base SQLite.

**Precaución:** el modo de logs detallados puede registrar mensajes y respuestas que contengan información personal de pacientes. Es necesario aplicar controles de acceso y minimización de datos antes de utilizar el sistema con información real.

---

## Roadmap priorizado

### Prioridad alta: completar el agente administrativo

- [x] FastAPI y grafo LangGraph operativo.
- [x] Planner con Qwen local, normalización de entidades y Router.
- [x] Gestión conversacional de citas y búsqueda de pacientes.
- [x] Validaciones tempranas de fechas y horas vencidas en el agente.
- [x] Checkpointer persistente SQLite y ventana configurable del historial.
- [ ] Agregar contexto estructurado de `current_patient_id`, `current_doctor_id` y referencias a citas; confirmar entidades ambiguas antes de modificar registros.
- [ ] Vincular las sesiones a una identidad autenticada y aplicar autorización por usuario/rol.
- [ ] Reducir el tamaño del historial enviado al Planner cuando contiene listados extensos.
- [ ] Verificar y reforzar en NestJS las reglas críticas de agenda y la protección ante operaciones concurrentes.

### Prioridad media: extender las operaciones del consultorio

- [ ] Integrar `ConsultationsTool` con Planner, Router y Responder para operaciones permitidas sobre consultas.
- [ ] Ampliar la gestión de pacientes y médicos mediante herramientas de negocio autorizadas.
- [ ] Completar el flujo de indexación documental de RAG y mostrar fuentes de información recuperada.
- [ ] Implementar una estrategia de contexto resumido o recuperación selectiva para conversaciones largas.

### Notificaciones con n8n

- [ ] Definir el contrato de eventos de citas desde NestJS.
- [ ] Crear y asegurar el endpoint o mecanismo de entrega a n8n.
- [ ] Construir workflows de confirmación, cancelación, reprogramación y recordatorios.
- [ ] Configurar el proveedor de correo y, posteriormente, WhatsApp o SMS según necesidades.
- [ ] Manejar consentimiento, idempotencia, reintentos, preferencias y estado de entrega.
- [ ] Conectar la consulta de notificaciones al agente solo cuando la API y los permisos estén preparados.

### Antes de un uso real con pacientes

- [ ] Definir controles de acceso, retención, eliminación y respaldo de checkpoints e historiales.
- [ ] Minimizar datos clínicos/personales en logs, prompts y plataformas externas.
- [ ] Auditar cambios de agenda y accesos a información sensible.
- [ ] Revisar requisitos legales y organizativos aplicables al tratamiento de datos de salud.

---

## Licencia y autoría

Proyecto desarrollado como parte de **Agente Médico**, una plataforma orientada a la administración asistida de consultorios.

**Autor:** Benjamín Carreón Cadenas.

Para las condiciones de uso y distribución, consulta el archivo [`LICENSE`](LICENSE) del repositorio.
