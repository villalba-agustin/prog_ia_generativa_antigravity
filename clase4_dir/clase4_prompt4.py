"""Módulo para el procesamiento financiero y búsqueda de clientes."""

from typing import Any, Dict, List, Union

# --- Constantes (Números Mágicos Extraídos) ---
PORCENTAJE_IVA: float = 0.21

UMBRAL_DESCUENTO_BASE: float = 1000.0
UMBRAL_DESCUENTO_ALTO: float = 2000.0

PORCENTAJE_DESCUENTO_VIP_ALTO: float = 0.2
PORCENTAJE_DESCUENTO_VIP_BASE: float = 0.1
PORCENTAJE_DESCUENTO_NORMAL: float = 0.05

TIPO_CLIENTE_VIP: str = "vip"
POSICION_NO_ENCONTRADA: int = -1

# --- Datos ---
clientes: List[Dict[str, Any]] = [
    {"nombre": "Ana", "tipo": "vip", "compras": [1200, 300, 150, 80]},
    {"nombre": "Luis", "tipo": "normal", "compras": [50, 40, 20]},
    {"nombre": "Marta", "tipo": "vip", "compras": [900, 1200, 100]},
    {"nombre": "Pablo", "tipo": "normal", "compras": [500, 200, 100, 50, 25]},
]


def calcular_descuento(subtotal: Union[int, float], tipo_cliente: str) -> Union[int, float]:
    """Calcula el descuento aplicable según el subtotal y el tipo de cliente.

    Args:
        subtotal (Union[int, float]): Suma total de las compras del cliente.
        tipo_cliente (str): Categoría del cliente ('vip' o 'normal').

    Returns:
        Union[int, float]: Monto del descuento a aplicar.
    """
    if subtotal <= UMBRAL_DESCUENTO_BASE:
        return 0

    if tipo_cliente == TIPO_CLIENTE_VIP:
        if subtotal > UMBRAL_DESCUENTO_ALTO:
            return subtotal * PORCENTAJE_DESCUENTO_VIP_ALTO
        return subtotal * PORCENTAJE_DESCUENTO_VIP_BASE

    return subtotal * PORCENTAJE_DESCUENTO_NORMAL


def calcular_total_con_impuesto(subtotal: Union[int, float], descuento: Union[int, float]) -> float:
    """Calcula el monto total final incluyendo el IVA.

    Args:
        subtotal (Union[int, float]): Subtotal acumulado de las compras.
        descuento (Union[int, float]): Descuento aplicado al cliente.

    Returns:
        float: Total final con impuestos aplicados.
    """
    monto_base: float = subtotal - descuento
    return monto_base + (monto_base * PORCENTAJE_IVA)


def procesar_cliente(cliente: Dict[str, Any]) -> None:
    """Calcula y muestra por pantalla el resumen financiero de un cliente.

    Args:
        cliente (Dict[str, Any]): Diccionario con datos del cliente.
    """
    subtotal: Union[int, float] = sum(cliente["compras"])
    descuento: Union[int, float] = calcular_descuento(subtotal, cliente["tipo"])
    total_final: float = calcular_total_con_impuesto(subtotal, descuento)

    print("Cliente:", cliente["nombre"])
    print("Subtotal:", subtotal)
    print("Descuento:", descuento)
    print("Total:", total_final)
    print("--------------------")


def buscar_posicion_cliente(lista_clientes: List[Dict[str, Any]], nombre_buscado: str) -> int:
    """Busca un cliente por su nombre y devuelve su índice en la lista.

    Args:
        lista_clientes (List[Dict[str, Any]]): Lista de clientes a consultar.
        nombre_buscado (str): Nombre del cliente a localizar.

    Returns:
        int: Índice base 0 donde reside el cliente, o POSICION_NO_ENCONTRADA (-1).
    """
    for posicion, cliente in enumerate(lista_clientes):
        if cliente["nombre"] == nombre_buscado:
            return posicion
    return POSICION_NO_ENCONTRADA


if __name__ == "__main__":
    # Procesar todos los clientes
    for cliente in clientes:
        procesar_cliente(cliente)

    # Búsqueda de cliente
    nombre_buscado: str = "Marta"
    posicion_encontrada: int = buscar_posicion_cliente(clientes, nombre_buscado)

    if posicion_encontrada == POSICION_NO_ENCONTRADA:
        print("No encontrado")
    else:
        print("Encontrado en posicion:", posicion_encontrada)