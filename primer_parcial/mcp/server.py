"""
Servidor MCP Oficial para 'Liga de Barrios y Fincas'.
Implementado con el SDK oficial de MCP para Python (mcp>=2.0.0).

Expone herramientas de solo lectura para consultar información estructurada
del torneo amateur, fixture, estadísticas y validación de reglas de negocio.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure mcp folder is on python path for relative tool imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from mcp.server.mcpserver import MCPServer
from db import get_safe_db_info, test_connection

# Import individual tools
from tools.schema import get_database_schema
from tools.teams import list_teams, list_players
from tools.tournament import get_tournament_summary, get_standings
from tools.fixture import get_matchday, validate_fixture
from tools.stats import get_top_scorers, get_card_statistics

# Initialize MCP Server
server = MCPServer(
    name="liga-barrios-mcp",
    instructions=(
        "Servidor MCP oficial de la Liga de Barrios y Fincas. "
        "Permite consultar información en tiempo real sobre equipos, jugadores, "
        "fixture, tabla de posiciones, estadísticas disciplinarias y de goleo, "
        "así como realizar validaciones automatizadas del fixture. "
        "Todas las herramientas son de solo lectura y seguras."
    )
)

# Register the 9 requested tools with explicit names and documentation
server.tool(name="get_database_schema")(get_database_schema)
server.tool(name="list_teams")(list_teams)
server.tool(name="list_players")(list_players)
server.tool(name="get_tournament_summary")(get_tournament_summary)
server.tool(name="get_standings")(get_standings)
server.tool(name="get_matchday")(get_matchday)
server.tool(name="validate_fixture")(validate_fixture)
server.tool(name="get_top_scorers")(get_top_scorers)
server.tool(name="get_card_statistics")(get_card_statistics)


def main():
    parser = argparse.ArgumentParser(description="Servidor MCP para Liga de Barrios y Fincas")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Tipo de transporte MCP (por defecto: stdio para clientes locales como Antigravity)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Verifica la conexión a PostgreSQL y lista las herramientas registradas sin iniciar el bucle stdio"
    )

    args = parser.parse_args()

    if args.test:
        import asyncio
        db_ok = asyncio.run(test_connection())
        db_info = get_safe_db_info()
        print("=== Test de Servidor MCP: Liga de Barrios y Fincas ===")
        print(f"Estado DB: {'CONECTADO' if db_ok else 'FALLO'}")
        print(f"Info DB: {db_info}")
        tools = server._tool_manager.list_tools()
        print(f"Herramientas registradas ({len(tools)}):")
        for t in tools:
            print(f"  - {t.name}")
        return

    # Run the server using selected transport (stdio is default for Antigravity / Claude / Cursor)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
