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
