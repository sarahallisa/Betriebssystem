#ifndef VMM_OUTPUT_UTILITY_H
#define VMM_OUTPUT_UTILITY_H

#include <stdbool.h>

/**
 * Outputs the results of a read operation.
 *
 * @param virtual_address The virtual address supplied by the input
 * @param physical_address The physical address calculated after doing TLB and page table operations
 * @param value The value read at the physical address
 * @param tlb_hit Whether the tlb contained the page number
 * @param pt_hit Whether the pagetable contained an entry for the page number. Ignored if tlb_hit is true.
 */
void print_access_results(int virtual_address, int physical_address, unsigned char value, bool tlb_hit, bool pt_hit);

#endif //VMM_OUTPUT_UTILITY_H
