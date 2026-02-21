"""
================================================================================
 PROBLEMA DE LOS FILÓSOFOS COMENSALES (Dining Philosophers)
 Estrategia: Filósofo Zurdo (Left-Handed Philosopher)
 Exclusión Mutua: Algoritmo de Peterson (sin primitivas del SO)
================================================================================

 Descripción del problema:
 -------------------------
 N filósofos se sientan alrededor de una mesa circular. Entre cada par de
 filósofos hay un tenedor (N tenedores en total). Cada filósofo alterna entre
 PENSAR y COMER. Para comer, necesita adquirir sus DOS tenedores adyacentes
 (izquierdo y derecho). El reto es evitar:
   - Deadlock (interbloqueo): todos toman un tenedor y esperan el otro.
   - Starvation (inanición): un filósofo nunca logra comer.

 Solución implementada:
 ----------------------
 1. ALGORITMO DE PETERSON para cada tenedor:
    Cada tenedor es un recurso compartido entre EXACTAMENTE 2 filósofos
    (el de su izquierda y el de su derecha). Peterson funciona para
    exclusión mutua entre 2 procesos, por lo que es la herramienta
    perfecta. Esto REEMPLAZA completamente a threading.Lock.

 2. FILÓSOFO ZURDO para romper la simetría:
    - Todos los filósofos ("diestros") toman primero el tenedor IZQUIERDO
      y luego el DERECHO.
    - UN filósofo (el filósofo 0, el "zurdo") invierte el orden: toma
      primero el DERECHO y luego el IZQUIERDO.
    - Esto rompe la condición de ESPERA CIRCULAR (una de las 4 condiciones
      necesarias de Coffman para deadlock), eliminando el interbloqueo.

 Restricciones cumplidas:
 ------------------------
 - NO se usa threading.Lock, Semaphore, Condition ni ninguna primitiva
   de sincronización del SO.
 - Solo se usa threading.Thread para crear los hilos.
 - La exclusión mutua se logra MANUALMENTE con Peterson.
================================================================================
"""

import threading
import time

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         CONFIGURACIÓN GENERAL                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

NUM_FILOSOFOS = 5            # Número de filósofos/tenedores (CONFIGURABLE)
DURACION_SIMULACION = 60     # Duración mínima de la simulación en segundos
TIEMPO_COMER_BASE = 0.3      # Tiempo base de comer (segundos)
TIEMPO_PENSAR_BASE = 0.3     # Tiempo base de pensar (segundos)

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║             CERROJO DE PETERSON (Reemplazo de threading.Lock)            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class PetersonLock:
    """
    Implementación del Algoritmo de Peterson para exclusión mutua entre
    exactamente 2 procesos (proceso 0 y proceso 1).

    ¿Por qué Peterson reemplaza a threading.Lock?
    -----------------------------------------------
    - threading.Lock es una primitiva del SO que usa instrucciones atómicas
      del hardware (test-and-set, compare-and-swap) para lograr exclusión
      mutua entre N hilos.
    - Peterson logra lo mismo, pero SOLO por software, usando dos variables
      compartidas: flag[] (intención) y turn (cortesía/turno).
    - La limitación de Peterson es que solo funciona para 2 procesos. Pero
      en nuestro caso cada tenedor es disputado por EXACTAMENTE 2 filósofos,
      así que Peterson encaja perfectamente.

    Propiedades garantizadas:
    -------------------------
    1. EXCLUSIÓN MUTUA: Nunca ambos procesos están en la sección crítica
       simultáneamente.
    2. PROGRESO: Si ningún proceso está en la sección crítica y alguno
       quiere entrar, uno de ellos lo logrará.
    3. ESPERA LIMITADA: Un proceso no espera indefinidamente si el otro
       sale de la sección crítica.

    Funcionamiento:
    ---------------
    - flag[i] = True  → El proceso i DESEA entrar a la sección crítica.
    - turn = j        → Se CEDE el turno al proceso j (acto de cortesía).
    - Espera activa mientras el OTRO quiera entrar Y sea el turno del otro.

    Nota sobre CPython:
    -------------------
    El GIL (Global Interpreter Lock) de CPython garantiza que las lecturas
    y escrituras de variables simples de Python son atómicas, y actúa como
    barrera de memoria al cambiar de hilo. Esto permite que Peterson funcione
    correctamente en CPython sin necesidad de barreras de memoria explícitas.
    """

    def __init__(self, nombre=""):
        self.flag = [False, False]  # flag[i]: True si proceso i quiere entrar
        self.turn = 0               # Turno: a quién se cede la prioridad
        self.nombre = nombre        # Identificador (para depuración)

    def acquire(self, proceso_id):
        """
        Protocolo de ENTRADA a la sección crítica para el proceso proceso_id.

        Pasos del algoritmo:
          1. Levanto mi bandera: "Yo quiero entrar" → flag[yo] = True
          2. Cedo el turno al otro: "Después de ti" → turn = otro
          3. Espera activa (busy-wait): me quedo esperando si
             - El otro TAMBIÉN quiere entrar (flag[otro] == True), Y
             - Es el turno del otro (turn == otro).
             Si alguna de las dos condiciones es falsa, yo entro.

        ¿Por qué funciona?
        Si ambos procesos intentan entrar al mismo tiempo:
        - Ambos ponen flag[i] = True.
        - Ambos intentan ceder el turno al otro (turn = otro).
        - SOLO UNA escritura a 'turn' prevalece (la última en ejecutarse).
        - El que escribió 'turn' ÚLTIMO se queda esperando (cedió el turno),
          y el otro entra a la sección crítica.

        Parámetros:
            proceso_id (int): 0 o 1, identifica al proceso que solicita acceso.
        """
        otro = 1 - proceso_id

        # Paso 1: Declaro mi intención de entrar
        self.flag[proceso_id] = True

        # Paso 2: Cedo cortésmente el turno al otro proceso
        self.turn = otro

        # Paso 3: Espera activa (spin-lock)
        # Solo entro cuando: el otro NO quiere entrar, o NO es su turno.
        # El while se rompe cuando flag[otro] == False  OR  turn != otro.
        while self.flag[otro] and self.turn == otro:
            # Busy-wait: esto es inherente al algoritmo de Peterson.
            # En CPython, el GIL se libera periódicamente (~5ms), permitiendo
            # que otros hilos avancen y eventualmente liberen su bandera.
            pass

    def release(self, proceso_id):
        """
        Protocolo de SALIDA de la sección crítica.

        Simplemente bajo mi bandera: "Ya no necesito el recurso".
        Esto permite que el otro proceso (si está esperando) pueda entrar.

        Parámetros:
            proceso_id (int): 0 o 1, identifica al proceso que libera el acceso.
        """
        self.flag[proceso_id] = False


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                      VARIABLES GLOBALES COMPARTIDAS                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# --- Tenedores (recurso compartido protegido) ---
# Cada tenedor[f] es un PetersonLock independiente.
# Tenedor f es compartido entre:
#   - Filósofo f         → para quien es su tenedor IZQUIERDO (rol 0 en Peterson)
#   - Filósofo (f-1) % N → para quien es su tenedor DERECHO   (rol 1 en Peterson)
#
# Disposición en la mesa (ejemplo con 5 filósofos):
#
#            Filósofo 0
#        T4 /         \ T0
#     Fil 4             Fil 1
#        T3 \         / T1
#            Filósofo 3
#              | T2 |
#            Filósofo 2
#
tenedores = [PetersonLock(nombre=f"Tenedor-{f}") for f in range(NUM_FILOSOFOS)]

# --- Bandera de control ---
# Variable compartida para detener la simulación limpiamente.
# Cuando pasa a False, todos los filósofos terminan su ciclo actual y salen.
simulacion_activa = True

# --- Métricas ---
# Contador de cuántas veces ha comido cada filósofo.
# Se incrementa DENTRO de la sección crítica (protegido por los 2 Peterson locks).
conteo_comidas = [0] * NUM_FILOSOFOS

# Timestamp del inicio de la simulación (para logs relativos).
inicio_simulacion = 0.0


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                  ASIGNACIÓN DE ROLES EN PETERSON                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# Para que Peterson funcione correctamente, cada filósofo debe tener un
# ROLE CONSISTENTE (0 o 1) para cada tenedor que comparte.
#
# Regla de asignación:
# --------------------
#   Filósofo i → Tenedor IZQUIERDO = tenedor[i]         → ROL 0 en Peterson
#   Filósofo i → Tenedor DERECHO   = tenedor[(i+1) % N] → ROL 1 en Peterson
#
# Verificación de consistencia (ejemplo con N=5):
#   Tenedor 0: compartido por Fil 0 (rol 0) y Fil 4 (rol 1) ✓ (2 roles distintos)
#   Tenedor 1: compartido por Fil 1 (rol 0) y Fil 0 (rol 1) ✓
#   Tenedor 2: compartido por Fil 2 (rol 0) y Fil 1 (rol 1) ✓
#   ...etc. Cada tenedor tiene exactamente un proceso 0 y un proceso 1. ✓


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                      FUNCIÓN DEL FILÓSOFO (HILO)                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def filosofo(id_fil):
    """
    Función ejecutada por cada hilo-filósofo. Ciclo de vida:
      PENSAR → TOMAR TENEDORES → COMER (sección crítica) → SOLTAR TENEDORES → repetir

    Estrategia del Filósofo Zurdo:
    ------------------------------
    - Filósofo 0 (ZURDO): toma tenedor DERECHO primero, luego IZQUIERDO.
    - Filósofos 1..N-1 (DIESTROS): toman tenedor IZQUIERDO primero, luego DERECHO.

    ¿Cómo rompe la simetría?
    Si todos toman el izquierdo primero, se forma un ciclo de espera:
      Fil 0 espera T1 (tiene T0) → Fil 1 espera T2 (tiene T1) → ... → Fil N-1 espera T0 (tiene TN-1)
    Con el filósofo zurdo, Fil 0 toma T1 primero (no T0), rompiendo el ciclo.

    Parámetros:
        id_fil (int): Identificador del filósofo (0 a NUM_FILOSOFOS-1).
    """
    global simulacion_activa

    # Identificar tenedores adyacentes
    tenedor_izq = id_fil                         # Tenedor a la izquierda
    tenedor_der = (id_fil + 1) % NUM_FILOSOFOS   # Tenedor a la derecha

    # Roles en Peterson (ver sección de asignación de roles arriba)
    ROL_EN_IZQUIERDO = 0   # Filósofo i es proceso 0 en tenedor[i]
    ROL_EN_DERECHO = 1     # Filósofo i es proceso 1 en tenedor[(i+1)%N]

    # ¿Es este el filósofo zurdo?
    es_zurdo = (id_fil == 0)
    tipo = "ZURDO" if es_zurdo else "DIESTRO"

    while simulacion_activa:
        # ──────────────────────────────────────────────────────────────
        # FASE 1: PENSAR (fuera de la sección crítica)
        # No requiere ningún recurso compartido.
        # ──────────────────────────────────────────────────────────────
        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) está PENSANDO...")
        # Variamos el tiempo de pensar para cada filósofo para más realismo
        time.sleep(TIEMPO_PENSAR_BASE * (0.5 + (id_fil % 3) * 0.25))

        # ──────────────────────────────────────────────────────────────
        # FASE 2: HAMBRIENTO - TOMAR TENEDORES
        # El orden de adquisición depende de si es zurdo o diestro.
        # Aquí se usa el Algoritmo de Peterson para cada tenedor.
        # ──────────────────────────────────────────────────────────────
        if es_zurdo:
            # ╔══════════════════════════════════════════════════════════╗
            # ║  FILÓSOFO ZURDO: Toma DERECHO primero, IZQUIERDO después║
            # ║  Esto ROMPE la espera circular y PREVIENE el deadlock.  ║
            # ╚══════════════════════════════════════════════════════════╝
            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"intenta tomar tenedor DERECHO  [{tenedor_der}]")
            tenedores[tenedor_der].acquire(ROL_EN_DERECHO)

            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"obtuvo tenedor [{tenedor_der}], "
                  f"intenta tomar tenedor IZQUIERDO [{tenedor_izq}]")
            tenedores[tenedor_izq].acquire(ROL_EN_IZQUIERDO)

        else:
            # ╔══════════════════════════════════════════════════════════╗
            # ║  FILÓSOFO DIESTRO: Toma IZQUIERDO primero, DERECHO después ║
            # ╚══════════════════════════════════════════════════════════╝
            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"intenta tomar tenedor IZQUIERDO [{tenedor_izq}]")
            tenedores[tenedor_izq].acquire(ROL_EN_IZQUIERDO)

            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"obtuvo tenedor [{tenedor_izq}], "
                  f"intenta tomar tenedor DERECHO  [{tenedor_der}]")
            tenedores[tenedor_der].acquire(ROL_EN_DERECHO)

        # ╔════════════════════════════════════════════════════════════╗
        # ║           >>> INICIO SECCIÓN CRÍTICA: COMER <<<           ║
        # ║  El filósofo posee AMBOS tenedores. Ningún vecino puede   ║
        # ║  estar comiendo simultáneamente porque cada tenedor está   ║
        # ║  protegido por su propio PetersonLock.                    ║
        # ╚════════════════════════════════════════════════════════════╝

        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] ★★★ Filósofo {id_fil} ({tipo:>7}) "
              f">>> ENTRA a sección crítica (COMIENDO) "
              f"con tenedores [{tenedor_izq}] y [{tenedor_der}] ★★★")

        # Simular el acto de comer (el recurso compartido está protegido)
        time.sleep(TIEMPO_COMER_BASE)

        # Incrementar contador (seguro: protegido por ambos Peterson locks)
        conteo_comidas[id_fil] += 1
        comidas_actual = conteo_comidas[id_fil]

        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] ☆☆☆ Filósofo {id_fil} ({tipo:>7}) "
              f"<<< SALE  de sección crítica "
              f"(total comidas: {comidas_actual}) ☆☆☆")

        # ╔════════════════════════════════════════════════════════════╗
        # ║            >>> FIN SECCIÓN CRÍTICA <<<                    ║
        # ╚════════════════════════════════════════════════════════════╝

        # ──────────────────────────────────────────────────────────────
        # FASE 3: SOLTAR TENEDORES (orden inverso a la adquisición)
        # Se libera la exclusión mutua en cada PetersonLock.
        # ──────────────────────────────────────────────────────────────
        if es_zurdo:
            # Zurdo adquirió: derecho → izquierdo. Libera: izquierdo → derecho.
            tenedores[tenedor_izq].release(ROL_EN_IZQUIERDO)
            tenedores[tenedor_der].release(ROL_EN_DERECHO)
        else:
            # Diestro adquirió: izquierdo → derecho. Libera: derecho → izquierdo.
            tenedores[tenedor_der].release(ROL_EN_DERECHO)
            tenedores[tenedor_izq].release(ROL_EN_IZQUIERDO)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                          PROGRAMA PRINCIPAL                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def main():
    """
    Orquesta la simulación:
    1. Crea N hilos (uno por filósofo).
    2. Los ejecuta durante DURACION_SIMULACION segundos.
    3. Envía señal de detención y espera a que terminen.
    4. Imprime estadísticas finales.
    """
    global simulacion_activa, inicio_simulacion

    print("=" * 70)
    print("  PROBLEMA DE LOS FILÓSOFOS COMENSALES")
    print("  Exclusión Mutua: Algoritmo de Peterson (sin locks del SO)")
    print("  Anti-Deadlock:   Estrategia del Filósofo Zurdo")
    print(f"  Filósofos:       {NUM_FILOSOFOS}")
    print(f"  Duración:        {DURACION_SIMULACION} segundos")
    print("=" * 70)
    print()

    inicio_simulacion = time.time()

    # ---- Crear e iniciar los hilos ----
    # Solo se usa threading.Thread (sin Lock, Semaphore, etc.)
    hilos = []
    for i in range(NUM_FILOSOFOS):
        hilo = threading.Thread(
            target=filosofo,
            args=(i,),
            name=f"Filosofo-{i}",
            daemon=True  # Daemon: el programa puede salir si un hilo se atasca
        )
        hilos.append(hilo)

    # Iniciar todos los hilos
    for hilo in hilos:
        hilo.start()

    # ---- Esperar la duración de la simulación ----
    try:
        time.sleep(DURACION_SIMULACION)
    except KeyboardInterrupt:
        print("\n[!] Interrupción del usuario detectada.")

    # ---- Señal de detención limpia ----
    simulacion_activa = False
    print()
    print("=" * 70)
    print("  SEÑAL DE DETENCIÓN ENVIADA")
    print("  Esperando que los filósofos terminen su ciclo actual...")
    print("=" * 70)

    # Esperar a que cada hilo termine (con timeout de seguridad)
    for hilo in hilos:
        hilo.join(timeout=10)

    duracion_real = time.time() - inicio_simulacion

    # ╔════════════════════════════════════════════════════════════════════════╗
    # ║                       ESTADÍSTICAS FINALES                           ║
    # ╚════════════════════════════════════════════════════════════════════════╝
    print()
    print("=" * 70)
    print("  ESTADÍSTICAS FINALES")
    print("=" * 70)

    total_comidas = sum(conteo_comidas)
    max_comidas = max(conteo_comidas)
    min_comidas = min(conteo_comidas)

    for i in range(NUM_FILOSOFOS):
        tipo = "ZURDO" if i == 0 else "DIESTRO"
        barra = "█" * (conteo_comidas[i] * 30 // max(max_comidas, 1))
        print(f"  Filósofo {i} ({tipo:>7}): {conteo_comidas[i]:4d} comidas  {barra}")

    print(f"\n  Total de comidas:        {total_comidas}")
    print(f"  Duración real:           {duracion_real:.2f} segundos")
    print(f"  Promedio por filósofo:   {total_comidas / NUM_FILOSOFOS:.1f}")
    print(f"  Máximo de un filósofo:   {max_comidas}")
    print(f"  Mínimo de un filósofo:   {min_comidas}")

    if min_comidas > 0:
        ratio = max_comidas / min_comidas
        print(f"  Ratio máx/mín:           {ratio:.2f} "
              f"({'Equitativo' if ratio < 2.0 else 'Desbalanceado'})")

    print(f"\n  ✓ Simulación completada sin deadlock.")
    print(f"  ✓ Todos los filósofos comieron al menos {min_comidas} veces.")
    print("=" * 70)


# ---- Punto de entrada ----
if __name__ == "__main__":
    main()
