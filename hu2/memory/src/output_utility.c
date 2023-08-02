#include "output_utility.h"

#include <stdio.h>

#define FORMAT_BOOL(v) (v) ? "true" : "false"

void print_access_results(int virtual_address, int physical_address, unsigned char value, bool tlb_hit, bool pt_hit) {
    printf("Virtual: %*d, ", 5, virtual_address);
    printf("Physical: %*d, ", 5, physical_address);
    //printf("Value: 0x%02x, ", value); // Output value as hex
    printf("Value: %*d, ", 3, value); // Output value as decimal
    printf("TLB hit: %s", FORMAT_BOOL(tlb_hit));
    if (!tlb_hit) printf(", PT hit: %s ", FORMAT_BOOL(pt_hit));
    printf("\n");

    fflush(stdout);
}
