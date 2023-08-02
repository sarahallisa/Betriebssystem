#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void hexDump(char *desc, void *addr, int len, int offset) {
    int i;
    unsigned char buff[17];
    unsigned char *pc = (unsigned char*)addr;

    // Output description if given.
    if (desc != NULL)
        printf ("%s:\n", desc);

    // Process every byte in the data.
    for (i = 0; i < len; i++) {
        // Multiple of 16 means new line (with line offset).

        if ((i % 16) == 0) {
            // Just don't print ASCII for the zeroth line.
            if (i != 0)
                printf("  %s\n", buff);

            // Output the offset.
            printf("0x%lx  %04x ", (long unsigned int) ((char *)addr+i), i);
        }

        // Now the hex code for the specific character.
        printf(" %02x", pc[i+offset]);

        // And store a printable ASCII character for later.
        if ((pc[i+offset] < 0x20) || (pc[i+offset] > 0x7e)) {
            buff[i % 16] = '.';
        } else {
            buff[i % 16] = pc[i+offset];
        }

        buff[(i % 16) + 1] = '\0';
    }

    // Pad out last line if not exactly 16 characters.
    while ((i % 16) != 0) {
        printf("   ");
        i++;
    }

    // And print the final ASCII bit.
    printf("  %s\n", buff);
}


