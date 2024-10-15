import sys

def leer_gramatica_validando(archivo):
    reglas = {}
    terminales = set()  # Usamos sets para evitar duplicados en terminales
    no_terminales = []  # Usamos una lista para mantener el orden de aparición de los no terminales

    try:
        with open(archivo, 'r') as f:
            lineas_validas = 0
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith('#'):
                    continue  # Ignorar líneas vacías o comentarios
                if linea.count('->') != 1:
                    print(f"Error: La línea '{linea}' tiene más de un '->' o está malformada.")
                    continue

                lado_izq, _ = linea.split('->')
                lado_izq = lado_izq.strip()

                # Añadir al conjunto de no terminales solo si no está presente
                if lado_izq not in no_terminales:
                    no_terminales.append(lado_izq)

            # Segunda pasada para procesar las reglas
            f.seek(0)  # Reiniciar el puntero del archivo al principio
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith('#'):
                    continue  # Ignorar líneas vacías o comentarios

                lado_izq, lado_der = linea.split('->')
                lado_izq = lado_izq.strip()
                producciones = lado_der.strip().split('|')  # Separar las alternativas con '|'

                if lado_izq not in reglas:
                    reglas[lado_izq] = []

                for produccion in producciones:
                    simbolos = produccion.strip().split()

                    reglas[lado_izq].append(simbolos)

                    # Clasificar terminales: todos los símbolos que no son no terminales ni epsilon
                    for simbolo in simbolos:
                        if simbolo not in no_terminales and simbolo != 'ε':
                            terminales.add(simbolo)

                lineas_validas += 1

            if lineas_validas == 0:
                print(f"Error: El archivo '{archivo}' no contiene reglas gramaticales válidas.")
                sys.exit(1)

    except FileNotFoundError:
        print(f"Error: El archivo '{archivo}' no se encontró.")
        sys.exit(1)

    return reglas, sorted(terminales), no_terminales  # No ordenar no_terminales


def calcular_conjunto_primeros(reglas, terminales, no_terminales):
    primeros = {nt: set() for nt in no_terminales}  # Inicializar conjuntos de primeros vacíos para cada no terminal

    def primeros_de(simbolo):
        if simbolo in terminales:
            return {simbolo}
        elif simbolo == 'ε':
            return {'ε'}
        return primeros[simbolo]

    cambios = True
    while cambios:
        cambios = False
        for lado_izq, producciones in reglas.items():
            for produccion in producciones:
                antes_cambio = len(primeros[lado_izq])
                incluye_epsilon = True  # Asumimos que toda la producción puede derivar en epsilon inicialmente
                for simbolo in produccion:
                    primeros_actuales = primeros_de(simbolo)

                    # Agregar todos los símbolos de primeros de "simbolo" excepto epsilon
                    primeros[lado_izq].update(primeros_actuales - {'ε'})

                    # Si "simbolo" no puede generar epsilon, no seguimos evaluando más símbolos de esta producción
                    if 'ε' not in primeros_actuales:
                        incluye_epsilon = False
                        break  # Terminar la evaluación de esta producción
                if incluye_epsilon:
                    primeros[lado_izq].add('ε')
                despues_cambio = len(primeros[lado_izq])
                if despues_cambio > antes_cambio:
                    cambios = True
    return primeros

def calcular_conjunto_siguientes(reglas, terminales, no_terminales, primeros):
    siguentes = {nt: set() for nt in no_terminales}  # Inicializar conjuntos FOLLOW vacíos

    # Asumimos que el primer símbolo es el símbolo de inicio
    inicio = list(no_terminales)[0]
    siguentes[inicio].add('$')  # Agregar $ al FOLLOW del símbolo de inicio

    cambios = True
    while cambios:
        cambios = False
        for lado_izq, producciones in reglas.items():
            for produccion in producciones:
                for i, simbolo in enumerate(produccion):
                    if simbolo in no_terminales:
                        # Obtener los símbolos que siguen a 'simbolo' en la producción
                        siguientes_simbolos = produccion[i+1:]
                        if siguientes_simbolos:
                            # Calcular FIRST de los siguientes símbolos
                            primeros_siguientes = set()
                            for s in siguientes_simbolos:
                                primeros_siguientes.update(primeros[s] - {'ε'})
                                if 'ε' not in primeros[s]:
                                    break
                            else:
                                # Si todos los siguientes símbolos pueden derivar en ε
                                primeros_siguientes.add('ε')

                            antes_cambio = len(siguentes[simbolo])
                            siguentes[simbolo].update(primeros_siguientes - {'ε'})
                            if 'ε' in primeros_siguientes:
                                siguentes[simbolo].update(siguentes[lado_izq])

                            if len(siguentes[simbolo]) > antes_cambio:
                                cambios = True
                        else:
                            # Si 'simbolo' es el último símbolo, agregar FOLLOW de 'lado_izq'
                            antes_cambio = len(siguentes[simbolo])
                            siguentes[simbolo].update(siguentes[lado_izq])
                            if len(siguentes[simbolo]) > antes_cambio:
                                cambios = True

    return siguentes

def calcular_conjunto_prediccion(reglas, primeros, siguentes):
    prediccion = {}

    for lado_izq, producciones in reglas.items():
        prediccion[lado_izq] = []
        for produccion in producciones:
            conjunto_prediccion = set()
            incluye_epsilon = True

            for simbolo in produccion:
                primeros_simbolo = primeros[simbolo] if simbolo in primeros else {simbolo}
                conjunto_prediccion.update(primeros_simbolo - {'ε'})
                
                if 'ε' not in primeros_simbolo:
                    incluye_epsilon = False
                    break

            if incluye_epsilon:
                conjunto_prediccion.update(siguentes[lado_izq])

            prediccion[lado_izq].append((produccion, conjunto_prediccion))

    return prediccion


def imprimir_resultados(primeros, siguientes, prediccion):
    # Imprimir conjuntos de PRIMEROS
    print("---------------------")
    for nt, conjunto in primeros.items():
        print(f"PRIM({nt})={{" + ", ".join(conjunto) + "}}")
    print("---------------------")

    # Imprimir conjuntos de SIGUIENTES
    for nt, conjunto in siguientes.items():
        print(f"SIG({nt})={{" + ", ".join(conjunto) + "}}")
    print("---------------------")

    # Imprimir conjuntos de PREDICCIÓN
    for nt, producciones in prediccion.items():
        for produccion, conjunto_pred in producciones:
            produccion_str = " ".join(produccion)
            conjunto_pred_str = ", ".join(conjunto_pred)
            print(f"PRED({nt})={produccion_str} -> {conjunto_pred_str}")
    print("---------------------")


                    
def main():
    archivo_gramatica = 'gramatica.txt'  # Archivo por defecto
    if len(sys.argv) > 1:
        archivo_gramatica = sys.argv[1]
    
    try:
        reglas, terminales, no_terminales = leer_gramatica_validando(archivo_gramatica)
        primeros = calcular_conjunto_primeros(reglas, terminales, no_terminales)
        siguientes = calcular_conjunto_siguientes(reglas, terminales, no_terminales, primeros)
        prediccion = calcular_conjunto_prediccion(reglas, primeros, siguientes)
    except FileNotFoundError:
        print(f"Error: El archivo '{archivo_gramatica}' no se encontró.")
        sys.exit(1)

    imprimir_resultados(primeros, siguientes, prediccion)


if __name__ == "__main__":  
    main()
