clientes = [
    {"nombre": "Ana", "tipo": "vip", "compras": [1200, 300, 150, 80]},
    {"nombre": "Luis", "tipo": "normal", "compras": [50, 40, 20]},
    {"nombre": "Marta", "tipo": "vip", "compras": [900, 1200, 100]},
    {"nombre": "Pablo", "tipo": "normal", "compras": [500, 200, 100, 50, 25]}
]

# Procesar cliente 1
subtotal_cliente_1 = 0
indice_compra_cliente_1 = 0
while indice_compra_cliente_1 < len(clientes[0]["compras"]):
    subtotal_cliente_1 = subtotal_cliente_1 + clientes[0]["compras"][indice_compra_cliente_1]
    indice_compra_cliente_1 = indice_compra_cliente_1 + 1

descuento_cliente_1 = 0
if clientes[0]["tipo"] == "vip":
    if subtotal_cliente_1 > 2000:
        descuento_cliente_1 = subtotal_cliente_1 * 0.2
    else:
        if subtotal_cliente_1 > 1000:
            descuento_cliente_1 = subtotal_cliente_1 * 0.1
        else:
            descuento_cliente_1 = 0
else:
    if subtotal_cliente_1 > 1000:
        descuento_cliente_1 = subtotal_cliente_1 * 0.05
    else:
        descuento_cliente_1 = 0

total_final_cliente_1 = subtotal_cliente_1 - descuento_cliente_1 + (subtotal_cliente_1 - descuento_cliente_1) * 0.21
print("Cliente:", clientes[0]["nombre"])
print("Subtotal:", subtotal_cliente_1)
print("Descuento:", descuento_cliente_1)
print("Total:", total_final_cliente_1)
print("--------------------")

# Procesar cliente 2 (código repetido)
subtotal_cliente_2 = 0
indice_compra_cliente_2 = 0
while indice_compra_cliente_2 < len(clientes[1]["compras"]):
    subtotal_cliente_2 = subtotal_cliente_2 + clientes[1]["compras"][indice_compra_cliente_2]
    indice_compra_cliente_2 = indice_compra_cliente_2 + 1

descuento_cliente_2 = 0
if clientes[1]["tipo"] == "vip":
    if subtotal_cliente_2 > 2000:
        descuento_cliente_2 = subtotal_cliente_2 * 0.2
    else:
        if subtotal_cliente_2 > 1000:
            descuento_cliente_2 = subtotal_cliente_2 * 0.1
        else:
            descuento_cliente_2 = 0
else:
    if subtotal_cliente_2 > 1000:
        descuento_cliente_2 = subtotal_cliente_2 * 0.05
    else:
        descuento_cliente_2 = 0

total_final_cliente_2 = subtotal_cliente_2 - descuento_cliente_2 + (subtotal_cliente_2 - descuento_cliente_2) * 0.21
print("Cliente:", clientes[1]["nombre"])
print("Subtotal:", subtotal_cliente_2)
print("Descuento:", descuento_cliente_2)
print("Total:", total_final_cliente_2)
print("--------------------")

# Procesar cliente 3 (más repetición)
subtotal_cliente_3 = 0
indice_compra_cliente_3 = 0
while indice_compra_cliente_3 < len(clientes[2]["compras"]):
    subtotal_cliente_3 = subtotal_cliente_3 + clientes[2]["compras"][indice_compra_cliente_3]
    indice_compra_cliente_3 = indice_compra_cliente_3 + 1

descuento_cliente_3 = 0
if clientes[2]["tipo"] == "vip":
    if subtotal_cliente_3 > 2000:
        descuento_cliente_3 = subtotal_cliente_3 * 0.2
    else:
        if subtotal_cliente_3 > 1000:
            descuento_cliente_3 = subtotal_cliente_3 * 0.1
        else:
            descuento_cliente_3 = 0
else:
    if subtotal_cliente_3 > 1000:
        descuento_cliente_3 = subtotal_cliente_3 * 0.05
    else:
        descuento_cliente_3 = 0

total_final_cliente_3 = subtotal_cliente_3 - descuento_cliente_3 + (subtotal_cliente_3 - descuento_cliente_3) * 0.21
print("Cliente:", clientes[2]["nombre"])
print("Subtotal:", subtotal_cliente_3)
print("Descuento:", descuento_cliente_3)
print("Total:", total_final_cliente_3)
print("--------------------")

# Procesar cliente 4 (todavía más repetición)
subtotal_cliente_4 = 0
indice_compra_cliente_4 = 0
while indice_compra_cliente_4 < len(clientes[3]["compras"]):
    subtotal_cliente_4 = subtotal_cliente_4 + clientes[3]["compras"][indice_compra_cliente_4]
    indice_compra_cliente_4 = indice_compra_cliente_4 + 1

descuento_cliente_4 = 0
if clientes[3]["tipo"] == "vip":
    if subtotal_cliente_4 > 2000:
        descuento_cliente_4 = subtotal_cliente_4 * 0.2
    else:
        if subtotal_cliente_4 > 1000:
            descuento_cliente_4 = subtotal_cliente_4 * 0.1
        else:
            descuento_cliente_4 = 0
else:
    if subtotal_cliente_4 > 1000:
        descuento_cliente_4 = subtotal_cliente_4 * 0.05
    else:
        descuento_cliente_4 = 0

total_final_cliente_4 = subtotal_cliente_4 - descuento_cliente_4 + (subtotal_cliente_4 - descuento_cliente_4) * 0.21
print("Cliente:", clientes[3]["nombre"])
print("Subtotal:", subtotal_cliente_4)
print("Descuento:", descuento_cliente_4)
print("Total:", total_final_cliente_4)
print("--------------------")

# Búsqueda ineficiente y poco clara
nombre_buscado = "Marta"
posicion_encontrada = -1
indice_busqueda = 0
while indice_busqueda < len(clientes):
    if clientes[indice_busqueda]["nombre"] == nombre_buscado:
        posicion_encontrada = indice_busqueda
    indice_busqueda = indice_busqueda + 1

if posicion_encontrada == -1:
    print("No encontrado")
else:
    print("Encontrado en posicion:", posicion_encontrada)