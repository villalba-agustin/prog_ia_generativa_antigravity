"""Módulo que modela el dominio del sistema comercial mediante Programación Orientada a Objetos."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union


class Cliente(ABC):
    """Clase base abstracta que representa la entidad Cliente en el sistema."""

    PORCENTAJE_IVA: float = 0.21
    UMBRAL_DESCUENTO_BASE: float = 1000.0

    def __init__(self, nombre: str, compras: List[Union[int, float]]) -> None:
        self.nombre: str = nombre
        self.compras: List[Union[int, float]] = compras

    @property
    def subtotal(self) -> Union[int, float]:
        """Calcula el subtotal acumulado de todas las compras del cliente."""
        return sum(self.compras)

    @abstractmethod
    def calcular_descuento(self) -> Union[int, float]:
        """Calcula el monto del descuento aplicable según las reglas de la categoría."""
        pass

    def calcular_total_con_impuesto(self) -> float:
        """Calcula el total final aplicando impuestos sobre el monto neto."""
        monto_neto: float = self.subtotal - self.calcular_descuento()
        return monto_neto + (monto_neto * self.PORCENTAJE_IVA)

    def mostrar_resumen(self) -> None:
        """Imprime en consola el resumen financiero del cliente."""
        print("Cliente:", self.nombre)
        print("Subtotal:", self.subtotal)
        print("Descuento:", self.calcular_descuento())
        print("Total:", self.calcular_total_con_impuesto())
        print("--------------------")


class ClienteVIP(Cliente):
    """Representa a un cliente de categoría VIP con descuentos preferenciales."""

    UMBRAL_VIP_ALTO: float = 2000.0
    PORCENTAJE_VIP_ALTO: float = 0.2
    PORCENTAJE_VIP_BASE: float = 0.1

    def calcular_descuento(self) -> Union[int, float]:
        if self.subtotal <= self.UMBRAL_DESCUENTO_BASE:
            return 0
        if self.subtotal > self.UMBRAL_VIP_ALTO:
            return self.subtotal * self.PORCENTAJE_VIP_ALTO
        return self.subtotal * self.PORCENTAJE_VIP_BASE


class ClienteNormal(Cliente):
    """Representa a un cliente de categoría Normal."""

    PORCENTAJE_NORMAL: float = 0.05

    def calcular_descuento(self) -> Union[int, float]:
        if self.subtotal <= self.UMBRAL_DESCUENTO_BASE:
            return 0
        return self.subtotal * self.PORCENTAJE_NORMAL


class ClienteFactory:
    """Fábrica para instanciar subclases de Cliente según la categoría."""

    @staticmethod
    def crear_cliente(nombre: str, tipo: str, compras: List[Union[int, float]]) -> Cliente:
        """Crea y retorna una instancia concreta de Cliente."""
        if tipo.lower() == "vip":
            return ClienteVIP(nombre, compras)
        elif tipo.lower() == "normal":
            return ClienteNormal(nombre, compras)
        else:
            raise ValueError(f"Tipo de cliente no soportado: '{tipo}'")


class GestorClientes:
    """Gestiona una colección de clientes y permite realizar búsquedas y reportes."""

    POSICION_NO_ENCONTRADA: int = -1

    def __init__(self, lista_clientes: Optional[List[Cliente]] = None) -> None:
        self.clientes: List[Cliente] = lista_clientes if lista_clientes is not None else []

    def agregar_cliente(self, cliente: Cliente) -> None:
        """Agrega un nuevo cliente al gestor."""
        self.clientes.append(cliente)

    def procesar_todos(self) -> None:
        """Muestra el resumen financiero de todos los clientes registrados."""
        for cliente in self.clientes:
            cliente.mostrar_resumen()

    def buscar_posicion_por_nombre(self, nombre_buscado: str) -> int:
        """Busca el índice de un cliente por su nombre (-1 si no existe)."""
        for posicion, cliente in enumerate(self.clientes):
            if cliente.nombre == nombre_buscado:
                return posicion
        return self.POSICION_NO_ENCONTRADA


if __name__ == "__main__":
    datos_iniciales = [
        {"nombre": "Ana", "tipo": "vip", "compras": [1200, 300, 150, 80]},
        {"nombre": "Luis", "tipo": "normal", "compras": [50, 40, 20]},
        {"nombre": "Marta", "tipo": "vip", "compras": [900, 1200, 100]},
        {"nombre": "Pablo", "tipo": "normal", "compras": [500, 200, 100, 50, 25]},
    ]

    # Instanciación mediante Factory y registro en el gestor
    gestor = GestorClientes()
    for datos in datos_iniciales:
        nuevo_cliente = ClienteFactory.crear_cliente(
            nombre=datos["nombre"],
            tipo=datos["tipo"],
            compras=datos["compras"],
        )
        gestor.agregar_cliente(nuevo_cliente)

    # Procesar todos los clientes registrados
    gestor.procesar_todos()

    # Búsqueda de cliente
    nombre_buscado: str = "Marta"
    posicion_encontrada: int = gestor.buscar_posicion_por_nombre(nombre_buscado)

    if posicion_encontrada == GestorClientes.POSICION_NO_ENCONTRADA:
        print("No encontrado")
    else:
        print("Encontrado en posicion:", posicion_encontrada)