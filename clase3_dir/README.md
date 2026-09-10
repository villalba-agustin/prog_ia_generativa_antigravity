# ⚽ Sistema de Gestión de Torneo de Fútbol Web

Una aplicación web **Full-Stack** moderna para la gestión integral de torneos de fútbol en formato **Round Robin (Todos contra Todos)**. Desarrollada con **FastAPI**, **SQLAlchemy**, **SQLite** y una interfaz **Single Page Application (SPA)** responsiva en **HTML5/CSS3/JavaScript** con estética *Glassmorphism* y modo oscuro.

---

## 🌟 Características Principales

- 🛡️ **Gestión de Equipos:**
  - Registro de equipos con nombre y escudo.
  - Subida de archivos locales de imagen (`.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`) con límite estricto de tamaño de **5 MB**.
  - Edición y eliminación de equipos con refresco dinámico de datos.

- 🗓️ **Generador de Fixture Automático:**
  - Algoritmo **Round Robin (Ruleta de Berger / Circle Method)** que asigna localías equitativas y cruces "todos contra todos una sola vez".
  - Manejo automático de fechas libres (**BYE**) cuando el número de equipos es impar.

- 🏆 **Tabla de Posiciones Dinámica:**
  - Actualización en tiempo real conforme se registran los marcadores.
  - Motor automático de desempate con 4 niveles de reglas de negocio stictas.

- 🔐 **Control de Acceso por Roles (Modo Visor vs Modo Admin):**
  - **Modo Visor (Público):** Consulta limpia de tabla de posiciones y fixture. Bloqueo estricto de edición en frontend y backend (`403 Forbidden`).
  - **Modo Administrador:** Autenticación protegida para registrar equipos, subir escudos, editar/eliminar datos, generar/reiniciar torneo e ingresar marcadores.

---

## 📐 Reglas de Posiciones y Desempates

1. **Puntos Obtenidos:** 
   - 🏆 Victoria: **3 Puntos**
   - 🤝 Empate: **1 Punto**
   - ❌ Derrota: **0 Puntos**
2. **Diferencia de Goles (DG):** `Goles a Favor (GF) - Goles en Contra (GC)`.
3. **Goles a Favor (GF):** Mayor cantidad de goles convertidos.
4. **Resultado Entre Sí (Head-to-Head):** Enfrentamiento directo entre los equipos empatados.
5. **Orden Alfabético:** Criterio final de desempate.

---

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic, Python-Multipart.
- **Persistencia de Datos:** SQLite 3 + SQLAlchemy ORM.
- **Frontend:** SPA nativa con Vanilla HTML5, Vanilla CSS3 (Glassmorphism, CSS Variables, Flexbox/Grid), JavaScript ES6+ (Fetch API, Async/Await), FontAwesome 6, Google Fonts (Space Grotesk & Outfit).
- **Entorno:** Entorno virtual Python (`venv`).

---

## 📂 Estructura del Proyecto

```text
clase3_dir/
├── app/
│   ├── __init__.py
│   ├── main.py                   # Entrypoint de FastAPI y montaje de estáticos
│   ├── database.py               # Configuración de SQLite y SQLAlchemy engine
│   ├── models.py                 # Modelos ORM (Team, Match, TournamentState)
│   ├── schemas.py                # Esquemas Pydantic para Request/Response
│   ├── routers/
│   │   ├── auth.py               # Autenticación y dependencia require_admin
│   │   ├── teams.py              # Endpoints CRUD de equipos y carga de imágenes
│   │   ├── tournament.py         # Generación y reinicio de torneo
│   │   └── matches.py            # Consulta y carga de marcadores / tabla
│   ├── services/
│   │   ├── fixture_service.py    # Algoritmo Round Robin (Circle Method)
│   │   └── standings_service.py  # Motor de cálculo y desempate de tabla
│   └── static/
│       ├── index.html            # Interfaz de Usuario SPA
│       ├── styles.css            # Estilos Glassmorphism y Dark Mode
│       ├── app.js                # Lógica del cliente y consumo de API REST
│       └── uploads/              # Carpeta de almacenamiento de escudos
├── venv/                         # Entorno virtual aislado
├── test_tournament.py            # Suite de pruebas unitarias e integración
├── populate_and_verify.py        # Script E2E para poblar datos de prueba
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Documentación principal
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar o Navegar al Proyecto
```bash
cd clase3_dir
```

### 2. Activar el Entorno Virtual
```bash
source venv/bin/activate
```

### 3. Instalar Dependencias (Si aplica)
```bash
pip install -r requirements.txt
```

### 4. Iniciar el Servidor de Desarrollo
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Abrir la Aplicación en el Navegador
Navega a: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

> 🔑 **Contraseña por defecto de Administrador:** `admin`

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye pruebas unitarias e integración completas para validar el fixture, el motor de desempates y las restricciones de seguridad:

```bash
python test_tournament.py
```

---

## 🌐 Endpoints de la API REST

### 🛡️ Equipos (`/api/teams`)
- `GET /api/teams` - Listar todos los equipos.
- `POST /api/teams` - Crear un equipo *(Requiere Admin)*.
- `POST /api/teams/upload-shield` - Subir archivo de imagen de escudo *(Requiere Admin)*.
- `PUT /api/teams/{id}` - Modificar nombre o escudo de un equipo *(Requiere Admin)*.
- `DELETE /api/teams/{id}` - Eliminar equipo *(Requiere Admin)*.

### 🏆 Torneo (`/api/tournament`)
- `GET /api/tournament/status` - Consultar estado del torneo.
- `POST /api/tournament/generate` - Generar fixture todos contra todos *(Requiere Admin)*.
- `POST /api/tournament/reset` - Reiniciar torneo *(Requiere Admin)*.

### 📅 Partidos y Posiciones (`/api`)
- `GET /api/matches` - Obtener todos los partidos agrupados por fecha.
- `GET /api/matches/round/{round_number}` - Obtener partidos de una fecha específica.
- `PUT /api/matches/{id}/score` - Registrar/modificar resultado de un partido *(Requiere Admin)*.
- `DELETE /api/matches/{id}/score` - Limpiar resultado de un partido *(Requiere Admin)*.
- `GET /api/standings` - Consultar la tabla de posiciones calculada.
