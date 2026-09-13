# Liga de Barrios y Fincas 🏆

Sistema web completo para la administración del torneo de fútbol amateur **Liga de Barrios y Fincas**. Formato Todos Contra Todos a 1 rueda, con 4 canchas y generación automática de fixture.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic |
| **Base de datos** | PostgreSQL 16 |
| **Autenticación** | JWT (python-jose) · Bcrypt (passlib) |
| **Frontend** | React 18 · TypeScript · Vite 5 · Tailwind CSS 3 |
| **Contenedores** | Docker · Docker Compose |
| **Testing** | Pytest · pytest-asyncio |

---

## Inicio Rápido (Desarrollo Local sin Docker)

### Requisitos Previos
- Python 3.12+
- PostgreSQL 16 corriendo en `localhost:5432`
- Node.js 20+ (en `/home/<user>/.local/node/bin/node` o en PATH)

### 1 – Configurar variables de entorno

```bash
cp .env.example .env
# Editá .env con tus credenciales de PostgreSQL si difieren de los defaults
```

El archivo `.env` ya provee valores funcionales para desarrollo local:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=liga_barrios
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/liga_barrios
```

### 2 – Backend: instalar dependencias, migrar y cargar datos demo

```bash
cd backend

# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE liga_barrios;"

# Aplicar migraciones (crea todas las tablas, constraints y triggers)
alembic upgrade head

# Cargar datos demo realistas (torneo, 8 equipos, jugadores, fixture, resultados)
python -m app.core.seed

# Iniciar el servidor de desarrollo
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

El backend queda disponible en: **http://localhost:8000**

### 3 – Frontend: instalar dependencias e iniciar

```bash
cd frontend

# Instalar dependencias de Node.js
npm install   # o: PATH="/home/$USER/.local/node/bin:$PATH" npm install

# Iniciar el servidor de desarrollo
npm run dev   # o: PATH="/home/$USER/.local/node/bin:$PATH" npm run dev
```

El frontend queda disponible en: **http://localhost:5173**

---

## Inicio Rápido con Docker Compose

> ⚠ Requiere que el usuario `avillalba` esté en el grupo `docker` con sesión reiniciada,
> o bien usar `sudo docker compose`.

```bash
# Desde el directorio raíz del proyecto:
docker compose up --build -d

# Ver logs
docker compose logs -f backend
docker compose logs -f frontend

# Detener servicios
docker compose down
```

Los servicios exponen:
- `http://localhost:8000` → Backend API
- `http://localhost:5173` → Frontend React

---

## Endpoints de API

### Salud / Documentación
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/health` | Health check del sistema |
| `GET` | `/api/docs` | Swagger UI interactivo |
| `GET` | `/api/redoc` | Documentación ReDoc |

### Públicos (sin autenticación)
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/public/summary` | Resumen del torneo activo |
| `GET` | `/api/v1/public/standings` | Tabla de posiciones completa |
| `GET` | `/api/v1/public/fixture` | Fixture completo con partidos |
| `GET` | `/api/v1/public/results` | Resultados de partidos jugados |
| `GET` | `/api/v1/public/scorers` | Ranking de goleadores |
| `GET` | `/api/v1/public/cards` | Tabla de Fair Play (tarjetas) |
| `GET` | `/api/v1/public/teams` | Lista de equipos |

### Autenticación
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Login → devuelve JWT |
| `GET` | `/api/v1/auth/me` | Usuario autenticado actual |

### Administración (rol ADMINISTRADOR requerido)
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/tournaments/{id}/generate-fixture` | Generar fixture automáticamente |
| `POST` | `/api/v1/matches/{id}/result` | Registrar resultado (inmutable) |
| `POST` | `/api/v1/matches/{id}/status` | Suspender / Cancelar partido |
| `POST` | `/api/v1/matches/{id}/reschedule` | Reprogramar automáticamente |
| `POST` | `/api/v1/stats/matches/{id}` | Registrar estadísticas individuales |
| `POST` | `/api/v1/teams/` | Crear equipo |
| `PUT` | `/api/v1/teams/{id}` | Editar equipo |
| `POST` | `/api/v1/players/` | Crear jugador |
| `PATCH` | `/api/v1/players/{id}/toggle-enable` | Habilitar / deshabilitar jugador |

---

## Credenciales de Acceso Demo

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@ligabarrios.com` | `admin1234` |
| Delegado (ej.) | `delegado.bsm@ligabarrios.com` | `delegado123` |

---

## Reglas de Negocio Implementadas

| # | Regla | Backend | PostgreSQL |
|---|---|---|---|
| 1 | Un solo torneo activo | Validación en servicio | `UNIQUE INDEX` parcial |
| 2 | DNI único en torneo | Validación antes de insertar | `UNIQUE (tournament_id, dni)` |
| 3 | Camiseta única por equipo | Validación en endpoint | `UNIQUE (team_id, jersey_number)` |
| 4 | Equipos no duplicados | Nombres normalizados | `UNIQUE (tournament_id, name)` |
| 5 | Sin solapamiento en canchas | Algoritmo de slots | Trigger de validación |
| 6 | Equipo max 1 partido por fecha | FixtureEngine | Trigger `tg_prevent_team_double_booking` |
| 7 | **Inmutabilidad del resultado** | HTTP 409 si `status=JUGADO` | Trigger `tg_enforce_match_immutability` |
| 8 | Equipo no juega contra sí mismo | Pydantic validator | `CHECK (home_team_id <> away_team_id)` |
| 9 | Marcadores positivos | `conint(ge=0)` | `CHECK (home_score >= 0)` |

---

## Algoritmo del Fixture (Round-Robin de Berger)

- Formato: Todos Contra Todos a **1 sola rueda**.
- Con N equipos (par): **N-1 fechas**, **N/2 partidos por fecha**.
- Si N es impar, se añade un equipo "LIBRE" para equilibrar.
- Slots por cancha: 6 (horarios 11:00–18:00, duración 70 min).
- Capacidad total: 4 canchas × 6 slots = **24 partidos/día**.
- Asignación balanceada: los partidos se distribuyen equitativamente entre canchas.
- Bloqueo: `fixture_generated = True` impide regeneración.

### Criterios de Desempate en la Tabla
1. Puntos (PTS)
2. Diferencia de Gol (DG)
3. Goles a Favor (GF)
4. Resultado Directo entre empatados (Head-to-Head)
5. Fair Play: menos tarjetas (Amarilla=1pt, Roja=3pts)
6. Sorteo determinista

---

## Estructura del Proyecto

```
primer_parcial/
├── .env                    # Variables de entorno (desarrollo)
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
├── docker-compose.yml
├── README.md
├── backend/
│   ├── .venv/              # Entorno virtual Python
│   ├── alembic/
│   │   └── versions/       # Migraciones de base de datos
│   ├── app/
│   │   ├── api/v1/         # Endpoints REST (auth, teams, players, matches, stats, public)
│   │   ├── core/           # Config, DB, seguridad, seed
│   │   ├── models/         # Modelos SQLAlchemy (ORM)
│   │   ├── schemas/        # Schemas Pydantic (validación / serialización)
│   │   └── services/       # Lógica de dominio (fixture, standings, reschedule, match)
│   ├── tests/              # Suite de tests (14 tests, 100% passing)
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.tsx          # Componente raíz + gestión de estado global
        ├── main.tsx         # Entry point React
        ├── api.ts           # Cliente HTTP para el backend
        ├── types.ts         # Tipos TypeScript
        └── components/      # Componentes (Navbar, StandingsTable, FixtureView, AdminPanel, ...)
```

---

## Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

**14 tests pasando**, divididos en:
- `test_fixture_rules.py` — Round-robin, slots de tiempo, integridad del fixture
- `test_integrity_and_immutability.py` — Inmutabilidad de resultados, constraints únicos
- `test_standings_rules.py` — Puntos, fair play, jerarquía de desempates
- `test_auth_and_permissions.py` — JWT, RBAC, endpoints públicos/privados

---

## Vistas del Frontend

| Vista | Tab | Acceso |
|---|---|---|
| Tabla de Posiciones | `standings` | Público |
| Fixture Completo | `fixture` | Público |
| Resultados | `results` | Público |
| Goleadores | `scorers` | Público |
| Fair Play (Tarjetas) | `fairplay` | Público |
| Equipos y Planteles | `teams` | Público |
| Panel de Administración | `admin` | Solo ADMINISTRADOR |
| Panel del Delegado | `delegate` | Solo DELEGADO |

---

## Notas de Arquitectura

- **Backend**: Clean Architecture → `api` → `services` → `repositories` → `models`
- **Seguridad Doble**: Toda regla crítica tiene validación en FastAPI **Y** en PostgreSQL (triggers/constraints)
- **Async**: SQLAlchemy 2.0 con `asyncpg` para operaciones no bloqueantes
- **Fixture Inmutable**: Una vez generado, el fixture queda bloqueado (`fixture_generated=True`)
- **Resultados Inmutables**: El trigger `tg_enforce_match_immutability` en PostgreSQL impide cualquier modificación de marcadores ya registrados, incluso con acceso directo a la BD
- **Motor de Posiciones Determinista**: Idempotente, se recalcula completamente desde cero en cada partido jugado

---

## Servidor MCP (Model Context Protocol) 🤖

El proyecto incluye un servidor MCP oficial construido con el **SDK oficial de MCP para Python** (`mcp>=2.0.0`), ubicado en la carpeta independiente `mcp/`.

Permite que agentes de Inteligencia Artificial (como **Antigravity IDE**) consulten información en tiempo real de la base de datos PostgreSQL de forma controlada, segura y tipada.

### Principios de Seguridad
1. **Solo Lectura**: Ninguna herramienta permite operaciones destructivas ni de escritura (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
2. **Sin Ejecución de SQL Arbitrario**: No existe ninguna herramienta genérica para ejecutar código SQL.
3. **Consultas Parametrizadas**: Todas las consultas utilizan parámetros vinculados (`:param`) con SQLAlchemy `text()`.
4. **Validación de Parámetros**: Tipado estricto y validaciones de rango en cada función.
5. **Cero Exposición de Secretos**: La base de datos y esquemas excluyen credenciales, contraseñas, hashes y tablas de auditoría interna.

### Catálogo de Herramientas Disponibles

| # | Herramienta | Parámetros | Descripción |
|---|---|---|---|
| 1 | `get_database_schema` | *Ninguno* | Retorna la estructura relacional de las tablas del dominio (`tournaments`, `teams`, `players`, `rounds`, `pitches`, `matches`, `match_stats`, `standings`), sus columnas, tipos, claves primarias y foráneas. |
| 2 | `list_teams` | `include_inactive: bool = False` | Lista los equipos registrados en el torneo activo y la cantidad de jugadores de cada uno. |
| 3 | `list_players` | `team_id: Optional[str]`, `team_name: Optional[str]`, `only_enabled: bool = True` | Lista los jugadores registrados, su DNI, número de camiseta y equipo al que pertenecen. |
| 4 | `get_tournament_summary` | *Ninguno* | Resumen métrico del torneo: cantidad de equipos, jugadores, fechas, partidos jugados, pendientes, suspendidos y cancelados. |
| 5 | `get_standings` | *Ninguno* | Tabla actual de posiciones oficial con PJ, PG, PE, PP, GF, GC, DG, PTS y puntaje Fair Play. |
| 6 | `get_matchday` | `round_number: int` | Partidos programados para la fecha indicada, con horarios, canchas asignadas, equipos y estados. |
| 7 | `validate_fixture` | *Ninguno* | **Auditoría profunda del fixture**: detecta enfrentamientos duplicados, equipos con doble partido en una fecha, superposiciones horarias, conflictos de asignación de canchas e inconsistencias. |
| 8 | `get_top_scorers` | `limit: int = 10` | Ranking de los máximos goleadores del torneo activo. |
| 9 | `get_card_statistics` | `group_by: str = "team"` | Estadísticas disciplinarias de tarjetas amarillas y rojas (por equipo `'team'`, por jugador `'player'`, o `'all'`). |

### Instalación y Ejecución del Servidor MCP

```bash
cd mcp

# 1. Crear entorno virtual e instalar dependencias del SDK oficial MCP
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Test rápido de conexión y verificación de herramientas registradas
python server.py --test

# 3. Iniciar el servidor en modo transporte stdio (estándar para agentes IA)
python server.py --transport stdio
```

### Ejecución de Pruebas Automatizadas del MCP

```bash
cd mcp
source .venv/bin/activate
pytest tests/ -v
```

La suite ejecuta 15 pruebas cubriendo cada herramienta, validaciones de errores y llamadas a través del protocolo oficial de `MCPServer`.

---

## Conexión con Antigravity IDE 🚀

Para vincular este servidor MCP con Antigravity, se incluye la configuración lista para usar en `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "liga-barrios": {
      "command": "/home/avillalba/Documentos/prog_ia_generativa_antigravity/primer_parcial/mcp/.venv/bin/python",
      "args": [
        "/home/avillalba/Documentos/prog_ia_generativa_antigravity/primer_parcial/mcp/server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/liga_barrios"
      }
    }
  }
}
```

### Opciones de Ubicación del Archivo de Configuración:
1. **Local en el Workspace (Recomendada)**:
   `.agents/mcp_config.json` en la raíz del repositorio de trabajo.
2. **Global de Antigravity**:
   `~/.gemini/config/mcp_config.json` (ya configurado automáticamente).

Una vez configurado, Antigravity detectará automáticamente el servidor `liga-barrios` y el agente podrá invocar cualquiera de las 9 herramientas de consulta y auditoría de la base de datos de la liga.

