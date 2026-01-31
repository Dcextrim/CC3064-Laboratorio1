#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>

//Poner el número que registraste en syscall_64.tbl
#define __NR_mycall 470 

int main() {
    printf("--- Iniciando prueba de Syscall ---\n");

    // Se le envia un 50.
    // Esperando que nos devuelva 60 (50 + 10)
    long res = syscall(__NR_mycall, 50);

    printf("Resultado devuelto por el kernel: %ld\n", res);

    if (res == 60) {
        printf("Funko el kernel\n");
    } else {
        printf("No funko el kernel\n");
    }

    return 0;
}