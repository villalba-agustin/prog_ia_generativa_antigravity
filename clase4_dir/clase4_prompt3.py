clientes = [
    {"nombre": "Ana", "tipo": "vip", "compras": [1200, 300, 150, 80]},
    {"nombre": "Luis", "tipo": "normal", "compras": [50, 40, 20]},
    {"nombre": "Marta", "tipo": "vip", "compras": [900, 1200, 100]},
    {"nombre": "Pablo", "tipo": "normal", "compras": [500, 200, 100, 50, 25]}
]

PORCENTAJE_IVA = 0.21


def calcular_descuento(subtotal: float, tipo_cliente: str) -> float:
    """Calcula el descuento aplicable según el subtotal y el tipo de cliente usando cláusulas de guarda."""
    # Cláusula de guarda: sin descuento para montos iguales o inferiores a 1000
    if subtotal <= 1000:
        return 0

    # Retornos tempranos para cliente VIP
    if tipo_cliente == "vip":
        if subtotal > 2000:
            return subtotal * 0.2
        return subtotal * 0.1

    # Retorno directo para cliente normal (subtotal > 1000)
    return subtotal * 0.05


def calcular_total_con_impuesto(subtotal: float, descuento: float) -> float:
    """Calcula el total final aplicando el impuesto (IVA)."""
    monto_base = subtotal - descuento
    return monto_base + (monto_base * PORCENTAJE_IVA)


def procesar_cliente(cliente: dict) -> None:
    """Procesa y muestra el resumen financiero de un cliente."""
    subtotal = sum(cliente["compras"])
    descuento = calcular_descuento(subtotal, cliente["tipo"])
    total_final = calcular_total_con_impuesto(subtotal, descuento)

    print("Cliente:", cliente["nombre"])
    print("Subtotal:", subtotal)
    print("Descuento:", descuento)
    print("Total:", total_final)
    print("--------------------")


def buscar_posicion_cliente(lista_clientes: list, nombre_buscado: str) -> int:
    """Busca un cliente por nombre y retorna su posición (-1 si no se encuentra)."""
    for posicion, cliente in enumerate(lista_clientes):
        if cliente["nombre"] == nombre_buscado:
            return posicion
    return -1


# Procesar todos los clientes
for cliente in clientes:
    procesar_cliente(cliente)

# Búsqueda de cliente
nombre_buscado = "Marta"
posicion_encontrada = buscar_posicion_cliente(clientes, nombre_buscado)

if posicion_encontrada == -1:
    print("No encontrado")
else:
    print("Encontrado en posicion:", posicion_encontrada)