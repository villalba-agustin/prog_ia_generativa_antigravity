import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.stream.IntStream;

/**
 * Enumeración que representa los tipos de cliente admitidos.
 */
enum TipoCliente {
    VIP,
    NORMAL;

    public static TipoCliente desdeTexto(String tipo) {
        for (TipoCliente t : values()) {
            if (t.name().equalsIgnoreCase(tipo)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Tipo de cliente no soportado: " + tipo);
    }
}

/**
 * Clase abstracta base que representa la entidad Cliente.
 */
abstract class Cliente {
    private static final double PORCENTAJE_IVA = 0.21;
    private static final double UMBRAL_DESCUENTO_BASE = 1000.0;

    private final String nombre;
    private final List<Double> compras;

    public Cliente(String nombre, List<Double> compras) {
        this.nombre = Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.compras = List.copyOf(compras);
    }

    public String getNombre() {
        return nombre;
    }

    public List<Double> getCompras() {
        return compras;
    }

    public double getSubtotal() {
        return compras.stream()
                .mapToDouble(Double::doubleValue)
                .sum();
    }

    public abstract double calcularDescuento();

    public double calcularTotalConImpuesto() {
        double montoNeto = getSubtotal() - calcularDescuento();
        return montoNeto + (montoNeto * PORCENTAJE_IVA);
    }

    public void mostrarResumen() {
        System.out.println("Cliente: " + nombre);
        System.out.println("Subtotal: " + formatearNumero(getSubtotal()));
        
        double descuento = calcularDescuento();
        System.out.println("Descuento: " + (descuento == 0.0 ? "0" : descuento));
        System.out.println("Total: " + formatearNumero(calcularTotalConImpuesto()));
        System.out.println("--------------------");
    }

    protected boolean superaUmbralBase() {
        return getSubtotal() > UMBRAL_DESCUENTO_BASE;
    }

    private static String formatearNumero(double valor) {
        if (valor == (long) valor) {
            return String.valueOf((long) valor);
        }
        return String.valueOf(valor);
    }
}

/**
 * Representa a un cliente con categoría VIP.
 */
class ClienteVIP extends Cliente {
    private static final double UMBRAL_VIP_ALTO = 2000.0;
    private static final double PORCENTAJE_VIP_ALTO = 0.20;
    private static final double PORCENTAJE_VIP_BASE = 0.10;

    public ClienteVIP(String nombre, List<Double> compras) {
        super(nombre, compras);
    }

    @Override
    public double calcularDescuento() {
        if (!superaUmbralBase()) {
            return 0.0;
        }
        if (getSubtotal() > UMBRAL_VIP_ALTO) {
            return getSubtotal() * PORCENTAJE_VIP_ALTO;
        }
        return getSubtotal() * PORCENTAJE_VIP_BASE;
    }
}

/**
 * Representa a un cliente con categoría Normal.
 */
class ClienteNormal extends Cliente {
    private static final double PORCENTAJE_NORMAL = 0.05;

    public ClienteNormal(String nombre, List<Double> compras) {
        super(nombre, compras);
    }

    @Override
    public double calcularDescuento() {
        if (!superaUmbralBase()) {
            return 0.0;
        }
        return getSubtotal() * PORCENTAJE_NORMAL;
    }
}

/**
 * Fábrica estática para instanciar clientes.
 */
class ClienteFactory {
    public static Cliente crearCliente(String nombre, String tipo, List<Double> compras) {
        TipoCliente tipoEnum = TipoCliente.desdeTexto(tipo);
        return switch (tipoEnum) {
            case VIP -> new ClienteVIP(nombre, compras);
            case NORMAL -> new ClienteNormal(nombre, compras);
        };
    }
}

/**
 * Gestiona la colección de clientes y operaciones sobre el conjunto.
 */
class GestorClientes {
    public static final int POSICION_NO_ENCONTRADA = -1;
    private final List<Cliente> clientes = new ArrayList<>();

    public void agregarCliente(Cliente cliente) {
        clientes.add(Objects.requireNonNull(cliente, "El cliente no puede ser nulo"));
    }

    public List<Cliente> getClientes() {
        return Collections.unmodifiableList(clientes);
    }

    public void procesarTodos() {
        clientes.forEach(Cliente::mostrarResumen);
    }

    public int buscarPosicionPorNombre(String nombreBuscado) {
        return IntStream.range(0, clientes.size())
                .filter(i -> clientes.get(i).getNombre().equalsIgnoreCase(nombreBuscado))
                .findFirst()
                .orElse(POSICION_NO_ENCONTRADA);
    }
}

/**
 * Clase principal de entrada.
 */
public class Main {
    public static void main(String[] args) {
        GestorClientes gestor = new GestorClientes();

        gestor.agregarCliente(ClienteFactory.crearCliente("Ana", "vip", List.of(1200.0, 300.0, 150.0, 80.0)));
        gestor.agregarCliente(ClienteFactory.crearCliente("Luis", "normal", List.of(50.0, 40.0, 20.0)));
        gestor.agregarCliente(ClienteFactory.crearCliente("Marta", "vip", List.of(900.0, 1200.0, 100.0)));
        gestor.agregarCliente(ClienteFactory.crearCliente("Pablo", "normal", List.of(500.0, 200.0, 100.0, 50.0, 25.0)));

        // Procesar todos los clientes registrados
        gestor.procesarTodos();

        // Búsqueda de cliente por nombre
        String nombreBuscado = "Marta";
        int posicionEncontrada = gestor.buscarPosicionPorNombre(nombreBuscado);

        if (posicionEncontrada == GestorClientes.POSICION_NO_ENCONTRADA) {
            System.out.println("No encontrado");
        } else {
            System.out.println("Encontrado en posicion: " + posicionEncontrada);
        }
    }
}
