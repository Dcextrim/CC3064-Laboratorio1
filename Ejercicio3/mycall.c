#include <linux/kernel.h>
#include <linux/syscalls.h>

SYSCALL_DEFINE1(mycall, int, i) {
    printk(KERN_INFO "Hola desde el PapuKernel!! Recibi: %d\n", i);
    return i + 10;
}