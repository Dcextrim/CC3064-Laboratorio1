#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#define BUFFER_SIZE 1024 // Tamaño del bloque que se va a leer

int main(int argc, char* argv[]) {

    if (argc != 3) {
        printf("Uso correcto: %s <archivo_origen> <archivo_destino>\n", argv[0]);
        exit(1);
    }

    char *source_file = argv[1];
    char *dest_file = argv[2];
    char buffer[BUFFER_SIZE];
    ssize_t bytes_read, bytes_written;

    int fd_src = open(source_file, O_RDONLY);
    if (fd_src == -1) {
        perror("Error al abrir archivo origen");
        exit(1);
    }

    int fd_dest = open(dest_file, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd_dest == -1) {
        perror("Error al crear archivo destino");
        close(fd_src);
        exit(1);
    }

    while ((bytes_read = read(fd_src, buffer, BUFFER_SIZE)) > 0) {
        bytes_written = write(fd_dest, buffer, bytes_read);
        
        if (bytes_written != bytes_read) {
            perror("Error al escribir");
            close(fd_src);
            close(fd_dest);
            exit(1);
        }
    }

    if (bytes_read == -1) {
        perror("Error al leer");
    }

    close(fd_src);
    close(fd_dest);

    printf("Copia completada exitosamente.\n");
    return 0;
}