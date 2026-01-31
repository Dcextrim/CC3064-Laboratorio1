# Laboratorio de Sistemas Operativos: Modernización del Kernel Linux

Este repositorio contiene el desarrollo de los ejercicios prácticos del laboratorio de Sistemas Operativos. El enfoque principal es la **modernización y compilación de un Kernel Linux (v6.x)**, adaptando metodologías antiguas (Kernel 2.6) a arquitecturas modernas (Ubuntu 24.04 / x86_64).

## Información del Entorno
* **Sistema Operativo Host:** Ubuntu 24.04 LTS
* **Kernel Base Descargado:** Linux 6.18.7 (Vanilla de kernel.org)
* **Arquitectura:** x86_64
* **Virtualización:** VirtualBox / VMware

---

## Estructura del Repositorio

```text
├── Ejercicio1/          # Scripts y archivos del ejercicio 1
│   ├── HelloWorld.c
│   ├── Fork.c
├── Ejercicio2/          # Scripts y archivos del ejercicio 2
│   ├── files.c
├── Ejercicio3/    # Archivos modificados para el Kernel 6.18.7
│   ├── mycall.c         # Código fuente de la nueva syscall
│   ├── prueba.c         # Programa de usuario para testear la llamada
└── README.md            # Documentación del proyecto
```

---

## El Gran Desafío: Implementación de System Call en Kernel 6.x

El objetivo de este ejercicio fue agregar una llamada al sistema personalizada (`sys_mycall`) en un kernel moderno, superar las protecciones de seguridad actuales y compilarlo exitosamente.

### 1. Modificaciones al Código Fuente

Para lograr la integración, se modificaron los siguientes archivos clave en el árbol del Kernel:

**Tabla de Syscalls** (`arch/x86/entry/syscalls/syscall_64.tbl`):
- Se registró la syscall con el ID 470.
- Entrada: `470 common mycall sys_mycall`

**Header** (`include/linux/syscalls.h`):
- Se añadió el prototipo `asmlinkage long sys_mycall(int i);` antes del `#endif`.

**Makefile Principal** (`Makefile`):
- Se modificó la variable `core-y` para incluir el directorio `mycall/`.

### 2. Implementación de la Syscall

Se utilizó la macro `SYSCALL_DEFINE1` debido a las protecciones modernas (KASLR/Spectre).

**Ubicación:** `mycall/mycall.c`

```c
#include <linux/kernel.h>
#include <linux/syscalls.h>

SYSCALL_DEFINE1(mycall, int, i) {
    // Mensaje personalizado en el log del kernel (dmesg)
    printk(KERN_INFO "Hola desde el PapuKernel!! Recibi: %d\n", i);
    return i + 10;
}
```

### 3. Compilación e Instalación

Se resolvieron conflictos con las claves de confianza de Canonical desactivando las siguientes flags en el `.config`:

- `SYSTEM_TRUSTED_KEYS` (Vaciado)
- `SYSTEM_REVOCATION_KEYS` (Vaciado)
- `CONFIG_DEBUG_INFO_BTF` (Desactivado para evitar errores con pahole)

**Comandos ejecutados:**

```bash
make -j$(nproc)          # Compilación paralela
sudo make modules_install # Instalación de módulos
sudo make install         # Instalación del kernel y update-grub
```

---

## Pruebas y Resultados

Para verificar el funcionamiento, se reinició el sistema con el nuevo Kernel 6.18.7 y se ejecutó un programa en espacio de usuario (`prueba.c`).

**Evidencia de funcionamiento:**
- **Output del programa:** El sistema retornó `60` (Input 50 + 10).
- **Kernel Log (dmesg):** Se registró el mensaje de éxito.

```bash
$ sudo dmesg | tail
[ 1427.35 ] Hola desde el PapuKernel!! Recibi: 50
```

---

## Solución de Problemas

- **Error de Certificados:** Si al compilar aparece un error sobre `debian/canonical-certs.pem`, es necesario editar el archivo `.config` y vaciar las variables de claves confiables.

- **Makefile:** Al editar el Makefile raíz, es crítico no usar `:=` si solo se pone la carpeta propia, ya que esto elimina el resto del kernel de la compilación.

- **Grub:** Para acceder al nuevo kernel, mantener `Shift` durante el arranque y seleccionar "Opciones avanzadas para Ubuntu".

---