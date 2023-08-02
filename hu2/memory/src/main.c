#include "vmm.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

static void showUsage(FILE *out, const char *myself) {
    /* show some help how to use the program */
    fprintf(out, "Usage: %s [options] --backing <backing store file> [<input file>]\n", myself);
    fprintf(out, "\n");
    fprintf(out, "Simulates virtual memory management using a tlb.\n");
    fprintf(out, "The input file contains one virtual address per line.\n");
    fprintf(out, "The addresses in the input file are used to simulate memory accesses.\n");
    fprintf(out, "If no input file is specified stdin is used.\n");
    fprintf(out, "\n");
    fprintf(out, "Options:\n");
    fprintf(out, "  --help       Show this help.\n");
}

static void usageError(const char *myself, const char *fmt, ...) {
    va_list ap;

    va_start(ap, fmt);
    fprintf(stderr, "Usage: ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);

    showUsage(stderr, myself);
    exit(1);
}

typedef struct command_line_arguments {
    char *addresses_path;
    char *backing_path;
} command_line_arguments;

static command_line_arguments parse_command_line_arguments(int argc, char **argv) {
    command_line_arguments arguments;

    arguments.addresses_path = NULL;
    arguments.backing_path = NULL;
    if (argc < 3 ) {
            showUsage(stdout, argv[0]);
            exit(0);
    }
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0) {
            showUsage(stdout, argv[0]);
            exit(0);
        } else if (strcmp(argv[i], "--backing") == 0) {
            if (arguments.backing_path != NULL) usageError(argv[0], "Only one --backing option is allowed");
            arguments.backing_path = argv[++i];
        } else {
            if (argv[i][0] == '-' && argv[i][1] == '-') usageError(argv[0], "Unknown option '%s'!", argv[i]);
            else if (arguments.addresses_path != NULL) usageError(argv[0], "Only one positional argument is allowed");

            arguments.addresses_path = argv[i];
        }
    }

    return arguments;
}

int main(int argc, char **argv) {
    command_line_arguments arguments = parse_command_line_arguments(argc, argv);

    FILE *fd_addresses = arguments.addresses_path == NULL ? stdin : fopen(arguments.addresses_path, "r");
    FILE *fd_backing = fopen(arguments.backing_path, "r");

    Statistics statistics = simulate_virtual_memory_accesses(fd_addresses, fd_backing);

    printf("page_fault_rate [%.2f%%]\n", (1 - ((float) statistics.pagetable_hits) / (float) statistics.total_memory_accesses) * 100);
    printf("tlb_hit_rate [%.2f%%]\n", (((float) statistics.tlb_hits) / (float) statistics.total_memory_accesses) * 100);

    // Close files
    if (fd_addresses != stdin) fclose(fd_addresses);
    fclose(fd_backing);

    return 0;
}

