package pe.halcondorado.allpashift.calculos;

import java.util.Map;

/**
 * Nombre visible de cada cultivo del catálogo (agro.cultivos guarda el nombre sin tildes y solo en español):
 * español con tildes e inglés. Si un cultivo nuevo no está aquí, se muestra el nombre de la base tal cual.
 * El código interno (CatalogoCalculos.codigo) NO cambia: se sigue calculando desde el nombre de la base.
 */
public final class NombresCultivo {

    private NombresCultivo() {}

    /** nombre en la base → {es, en} */
    static final Map<String, String[]> NOMBRES = Map.ofEntries(
            Map.entry("Quinua", new String[] {"Quinua", "Quinoa"}),
            Map.entry("Cebada", new String[] {"Cebada", "Barley"}),
            Map.entry("Trigo", new String[] {"Trigo", "Wheat"}),
            Map.entry("Maiz amilaceo", new String[] {"Maíz amiláceo", "Starchy maize"}),
            Map.entry("Maiz amarillo duro", new String[] {"Maíz amarillo duro", "Yellow hard maize"}),
            Map.entry("Arroz", new String[] {"Arroz", "Rice"}),
            Map.entry("Zarandaja", new String[] {"Zarandaja", "Lablab bean"}),
            Map.entry("Arveja grano seco", new String[] {"Arveja grano seco", "Dry pea"}),
            Map.entry("Frijol grano seco", new String[] {"Frijol grano seco", "Dry bean"}),
            Map.entry("Frijol caupi", new String[] {"Frijol caupí", "Cowpea"}),
            Map.entry("Granadilla", new String[] {"Granadilla", "Sweet granadilla"}),
            Map.entry("Papaya", new String[] {"Papaya", "Papaya"}),
            Map.entry("Maracuya", new String[] {"Maracuyá", "Passion fruit"}),
            Map.entry("Arandano", new String[] {"Arándano", "Blueberry"}),
            Map.entry("Palta", new String[] {"Palta", "Avocado"}),
            Map.entry("Mandarina", new String[] {"Mandarina", "Mandarin"}),
            Map.entry("Platano", new String[] {"Plátano", "Plantain"}),
            Map.entry("Banano organico", new String[] {"Banano orgánico", "Organic banana"}),
            Map.entry("Uva de mesa", new String[] {"Uva de mesa", "Table grape"}),
            Map.entry("Limon", new String[] {"Limón", "Lime"}),
            Map.entry("Mango", new String[] {"Mango", "Mango"}),
            Map.entry("Esparrago", new String[] {"Espárrago", "Asparagus"}),
            Map.entry("Alcachofa", new String[] {"Alcachofa", "Artichoke"}),
            Map.entry("Zanahoria", new String[] {"Zanahoria", "Carrot"}),
            Map.entry("Tomate", new String[] {"Tomate", "Tomato"}),
            Map.entry("Aji paprika", new String[] {"Ají páprika", "Paprika pepper"}),
            Map.entry("Cebolla", new String[] {"Cebolla", "Onion"}),
            Map.entry("Melon", new String[] {"Melón", "Melon"}),
            Map.entry("Sandia", new String[] {"Sandía", "Watermelon"}),
            Map.entry("Olluco", new String[] {"Olluco", "Ulluco"}),
            Map.entry("Yuca", new String[] {"Yuca", "Cassava"}),
            Map.entry("Camote", new String[] {"Camote", "Sweet potato"}),
            Map.entry("Papa", new String[] {"Papa", "Potato"}),
            Map.entry("Cacao", new String[] {"Cacao", "Cocoa"}),
            Map.entry("Cafe", new String[] {"Café", "Coffee"}),
            Map.entry("Cana de azucar", new String[] {"Caña de azúcar", "Sugarcane"}),
            Map.entry("Algodon Pima", new String[] {"Algodón Pima", "Pima cotton"}));

    /** Nombre en español con tildes (o el de la base si no está en la lista). */
    public static String es(String nombreBd) {
        String[] n = NOMBRES.get(nombreBd);
        return n == null ? nombreBd : n[0];
    }

    /** Nombre en inglés (o el de la base si no está en la lista). */
    public static String en(String nombreBd) {
        String[] n = NOMBRES.get(nombreBd);
        return n == null ? nombreBd : n[1];
    }
}
