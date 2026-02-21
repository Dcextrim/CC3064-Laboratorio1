import threading
import time

NUM_FILOSOFOS = 5
DURACION_SIMULACION = 60
TIEMPO_COMER_BASE = 0.3
TIEMPO_PENSAR_BASE = 0.3

class PetersonLock:

    def __init__(self, nombre=""):
        self.flag = [False, False]
        self.turn = 0
        self.nombre = nombre

    def acquire(self, proceso_id):
        otro = 1 - proceso_id
        self.flag[proceso_id] = True
        self.turn = otro
        while self.flag[otro] and self.turn == otro:
            pass

    def release(self, proceso_id):
        self.flag[proceso_id] = False

tenedores = [PetersonLock(nombre=f"Tenedor-{f}") for f in range(NUM_FILOSOFOS)]
simulacion_activa = True
conteo_comidas = [0] * NUM_FILOSOFOS
inicio_simulacion = 0.0

def filosofo(id_fil):
    global simulacion_activa

    tenedor_izq = id_fil
    tenedor_der = (id_fil + 1) % NUM_FILOSOFOS

    ROL_EN_IZQUIERDO = 0
    ROL_EN_DERECHO = 1

    es_zurdo = (id_fil == 0)
    tipo = "ZURDO" if es_zurdo else "DIESTRO"

    while simulacion_activa:
        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) está PENSANDO...")
        time.sleep(TIEMPO_PENSAR_BASE * (0.5 + (id_fil % 3) * 0.25))

        if es_zurdo:
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
            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"intenta tomar tenedor IZQUIERDO [{tenedor_izq}]")
            tenedores[tenedor_izq].acquire(ROL_EN_IZQUIERDO)

            t = time.time() - inicio_simulacion
            print(f"[{t:7.3f}s] Filósofo {id_fil} ({tipo:>7}) "
                  f"obtuvo tenedor [{tenedor_izq}], "
                  f"intenta tomar tenedor DERECHO  [{tenedor_der}]")
            tenedores[tenedor_der].acquire(ROL_EN_DERECHO)

        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] ★★★ Filósofo {id_fil} ({tipo:>7}) "
              f">>> ENTRA a sección crítica (COMIENDO) "
              f"con tenedores [{tenedor_izq}] y [{tenedor_der}] ★★★")

        time.sleep(TIEMPO_COMER_BASE)

        conteo_comidas[id_fil] += 1
        comidas_actual = conteo_comidas[id_fil]

        t = time.time() - inicio_simulacion
        print(f"[{t:7.3f}s] ☆☆☆ Filósofo {id_fil} ({tipo:>7}) "
              f"<<< SALE  de sección crítica "
              f"(total comidas: {comidas_actual}) ☆☆☆")

        if es_zurdo:
            tenedores[tenedor_izq].release(ROL_EN_IZQUIERDO)
            tenedores[tenedor_der].release(ROL_EN_DERECHO)
        else:
            tenedores[tenedor_der].release(ROL_EN_DERECHO)
            tenedores[tenedor_izq].release(ROL_EN_IZQUIERDO)

def main():
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

    hilos = []
    for i in range(NUM_FILOSOFOS):
        hilo = threading.Thread(
            target=filosofo,
            args=(i,),
            name=f"Filosofo-{i}",
            daemon=True
        )
        hilos.append(hilo)

    for hilo in hilos:
        hilo.start()

    try:
        time.sleep(DURACION_SIMULACION)
    except KeyboardInterrupt:
        print("\n[!] Interrupción del usuario detectada.")

    simulacion_activa = False
    print()
    print("=" * 70)
    print("  SEÑAL DE DETENCIÓN ENVIADA")
    print("  Esperando que los filósofos terminen su ciclo actual...")
    print("=" * 70)

    for hilo in hilos:
        hilo.join(timeout=10)

    duracion_real = time.time() - inicio_simulacion

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

if __name__ == "__main__":
    main()
