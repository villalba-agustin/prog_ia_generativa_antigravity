import os
import sys
import threading
import logging
import time  
from flask import Flask, jsonify, send_from_directory
from mcp.server.mcpserver import MCPServer

# 1. Silenciar por completo los loggers que usan stdout
logging.getLogger('werkzeug').disabled = True
os.environ['WERKZEUG_RUN_MAIN'] = 'true'  # Desactiva el banner ' * Serving Flask app...'

mcp = MCPServer("RobotAspiradora")
app = Flask(__name__)

lock = threading.Lock()

ESTADO = {
    "pos_x": 1,
    "pos_y": 1,
    "bateria": 100,
    "paredes": [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
        (1, 0), (2, 0), (3, 0),
        (1, 4), (2, 4), (3, 4),
        (2, 2)
    ],
    "suciedad": [(1, 2), (2, 3), (3, 1), (3, 2)],
    "ultima_accion": "Robot iniciado en base de carga",
    "historial": [(1, 1)]
}

# -------------------------------------------------------------
# RECURSOS Y HERRAMIENTAS (Los decoradores se mantienen iguales)
# -------------------------------------------------------------

@mcp.resource("casa://mapa")
def obtener_mapa_estatico() -> str:
    """Retorna las dimensiones del entorno y la ubicación de las paredes fijas."""
    with lock:
        return (
            "Plano de la casa (Grilla 5x5):\n"
            "- Límites externos: Paredes en bordes perimetrales (x=0, x=4, y=0, y=4).\n"
            "- Obstáculo interno: Pared en columna 2, fila 2.\n"
            "- Área transitable: Coordenadas interiores (1 a 3)."
        )

@mcp.tool()
def leer_sensores() -> dict:
    """Retorna la posición actual, nivel de batería, si hay suciedad en la celda y si hay paredes adyacentes."""
    with lock:
        x, y = ESTADO["pos_x"], ESTADO["pos_y"]
        return {
            "posicion": (x, y),
            "bateria": f"{ESTADO['bateria']}%",
            "hay_suciedad_aqui": (x, y) in ESTADO["suciedad"],
            "sensores_proximidad": {
                "arriba": (x, y - 1) in ESTADO["paredes"],
                "abajo": (x, y + 1) in ESTADO["paredes"],
                "izquierda": (x - 1, y) in ESTADO["paredes"],
                "derecha": (x + 1, y) in ESTADO["paredes"]
            }
        }

@mcp.tool()
def mover(direccion: str) -> str:
    """Mueve el robot hacia 'arriba', 'abajo', 'izquierda' o 'derecha'."""
    time.sleep(0.5)
    movimientos = {
        "arriba": (0, -1),
        "abajo": (0, 1),
        "izquierda": (-1, 0),
        "derecha": (1, 0)
    }
    
    dir_norm = direccion.strip().lower()
    if dir_norm not in movimientos:
        return f"Error: '{direccion}' no es válida. Usa arriba, abajo, izquierda o derecha."

    with lock:
        if ESTADO["bateria"] <= 0:
            ESTADO["ultima_accion"] = "Batería agotada"
            return "Batería agotada: El robot no puede desplazarse."

        dx, dy = movimientos[dir_norm]
        nueva_x = ESTADO["pos_x"] + dx
        nueva_y = ESTADO["pos_y"] + dy

        if (nueva_x, nueva_y) in ESTADO["paredes"]:
            ESTADO["ultima_accion"] = f"Colisión intentando ir hacia {dir_norm}"
            return f"¡Colisión! Hay un obstáculo en ({nueva_x}, {nueva_y}). Movimiento cancelado."

        ESTADO["pos_x"] = nueva_x
        ESTADO["pos_y"] = nueva_y
        ESTADO["bateria"] = max(0, ESTADO["bateria"] - 2)
        ESTADO["historial"].append((nueva_x, nueva_y))
        ESTADO["ultima_accion"] = f"Movido hacia {dir_norm} -> ({nueva_x}, {nueva_y})"
        
        return f"Movimiento exitoso a ({nueva_x}, {nueva_y}). Batería restante: {ESTADO['bateria']}%"

@mcp.tool()
def aspirar() -> str:
    """Limpia la suciedad de la celda actual donde está ubicado el robot."""
    time.sleep(0.5)
    with lock:
        if ESTADO["bateria"] <= 0:
            return "Batería agotada: No se puede activar la turbina de aspirado."

        pos = (ESTADO["pos_x"], ESTADO["pos_y"])
        if pos in ESTADO["suciedad"]:
            ESTADO["suciedad"].remove(pos)
            ESTADO["bateria"] = max(0, ESTADO["bateria"] - 4)
            ESTADO["ultima_accion"] = f"Suciedad aspirada en ({pos[0]}, {pos[1]})"
            return f"Celda {pos} limpiada con éxito. Batería restante: {ESTADO['bateria']}%"
        
        ESTADO["ultima_accion"] = f"Aspirado en vacío en ({pos[0]}, {pos[1]})"
        return f"La celda {pos} ya se encuentra limpia."

@mcp.tool()
def objetivo_cumplido() -> dict:
    """Verifica si quedan celdas con suciedad en la casa."""
    with lock:
        limpieza_terminada = len(ESTADO["suciedad"]) == 0
        return {
            "limpieza_completada": limpieza_terminada,
            "celdas_sucias_restantes": len(ESTADO["suciedad"]),
            "bateria_actual": f"{ESTADO['bateria']}%"
        }

# -------------------------------------------------------------
# SERVIDOR WEB FLASK
# -------------------------------------------------------------
@app.route("/")
def index():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(directorio_actual, "index.html")

@app.route("/estado")
def consultar_estado():
    with lock:
        response = jsonify(ESTADO)
        # Desactivar caché explícitamente
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

def ejecutar_web():
    from werkzeug.serving import make_server
    server = make_server("127.0.0.1", 5000, app)
    server.serve_forever()

if __name__ == "__main__":
    hilo_web = threading.Thread(target=ejecutar_web, daemon=True)
    hilo_web.start()
    mcp.run()