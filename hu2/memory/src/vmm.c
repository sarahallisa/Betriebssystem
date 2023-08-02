#include "vmm.h"
#include "output_utility.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>

#define PAGETABLE_ENTRIES 256
#define PAGE_SIZE 256
#define TLB_ENTRIES 16
#define FRAME_SIZE 256
#define FRAMES 64
#define PHYSICALMEMORY_SIZE 16384

typedef struct {
    int page_number;
    int frame_number;
} TLB_Entry;

typedef struct PageTableEntry{
    int page_number;
} PageTable_Entry;

typedef struct {
    TLB_Entry tlb[TLB_ENTRIES];
    PageTable_Entry page_table[PAGETABLE_ENTRIES];
} VM;

VM vm;
int **pm;
bool tlb_hit;
bool pt_hit;
int frame_number;
int tlbcounter = 0;
int framecounter = 0;
unsigned char value;

int** allocate_physical_memory(int frames, int frame_size) {
    int** temp;

    temp = malloc(frames * sizeof(int *));

    for(int i = 0; i < frames; i++) {
        temp[i] = (int*) malloc(sizeof(int) * frame_size);

        for(int j = 0; j < frame_size; j++) {
            temp[i][j] = 0;
        }
    }

    return temp;
}

void page_fault(int page_number, FILE *fd_backing) {

    for(int i = 0; i < TLB_ENTRIES; i++) {
        if(frame_number == vm.tlb[i].frame_number) {
            vm.tlb[i].frame_number = -1;
            vm.tlb[i].page_number = -1;
        }
    }

    unsigned char buffer[FRAME_SIZE];

    fseek(fd_backing, page_number * FRAME_SIZE, SEEK_SET);
    fread(buffer, 1, FRAME_SIZE, fd_backing);

    for(int i = 0; i < FRAME_SIZE; i++) {
        pm[frame_number][i] = buffer[i];
    }

    vm.page_table[page_number].page_number = frame_number;

    vm.tlb[tlbcounter].page_number = page_number;
    vm.tlb[tlbcounter].frame_number = frame_number;
    tlbcounter++;
    tlbcounter %= TLB_ENTRIES;
}


int get_physical_address(int logical_address, FILE *fd_backing) {
    int page_number = (logical_address & 0x0000FF00) >> 8;
    int offset = (logical_address & 0x000000FF);
    int current_frame = -1;
    int physical_address;

    if(vm.tlb == NULL) {
        current_frame = 0;
    } else {
        // Check TLB entries
        for (int i = 0; i < TLB_ENTRIES; i++) {
            if (vm.tlb[i].page_number == page_number) {
                tlb_hit = true;
                current_frame = vm.tlb[i].frame_number;
                break;
            } else {
                tlb_hit = false;
                current_frame = 0;
            }
        }
    }

    if (tlb_hit) {
        physical_address = (current_frame << 8) | offset;
        value = pm[current_frame][offset];
        return physical_address;
    } else {
        // Search page number in page table
        if (vm.page_table[page_number].page_number != -1) {
            pt_hit = true;
            current_frame = vm.page_table[page_number].page_number;

            vm.tlb[tlbcounter].page_number = page_number;
            vm.tlb[tlbcounter].frame_number = current_frame;
            tlbcounter++;
            tlbcounter %= TLB_ENTRIES;

            physical_address = (current_frame << 8) | offset;
            value = pm[current_frame][offset];
            return physical_address;
        } else {
            // Page number not found in page table (page fault)

            for(int i = 0; i < 256; i++) {
                if(vm.page_table[i].page_number == frame_number) {
                    vm.page_table[i].page_number = -1;
                    break;
                }
            }
            
            page_fault(page_number, fd_backing);

            current_frame = frame_number;
            frame_number = (frame_number + 1) % FRAMES;
            
            physical_address = (current_frame << 8) | offset;
            value = pm[current_frame][offset];
            return physical_address;
        }
    }
}

/**
 * Initialized a statistics object to zero.
 * @param stats A pointer to an uninitialized statistics object.
 */
static void statistics_initialize(Statistics *stats) {
    stats->tlb_hits = 0;
    stats->pagetable_hits = 0;
    stats->total_memory_accesses = 0;
}

Statistics simulate_virtual_memory_accesses(FILE *fd_addresses, FILE *fd_backing) {
    // Initialize statistics
    Statistics stats;
    statistics_initialize(&stats);

    char *line = NULL;
    size_t line_length;

    // Allocate space for frames and page table
    pm = allocate_physical_memory(FRAMES, FRAME_SIZE);

    // Initialize TLB entries and page table
    for (int i = 0; i < TLB_ENTRIES; i++) {
        vm.tlb[i].page_number = -1;
        vm.tlb[i].frame_number = -1;
    }

    for (int i = 0; i < PAGETABLE_ENTRIES; i++) {
        vm.page_table[i].page_number = -1;
    }

    int logical_address;
    int physical_address;
    int count = 1;

    // Read every line from data and change to int
    while(getline(&line, &line_length, fd_addresses) != -1) {
        tlb_hit = false;
        pt_hit = false;

        logical_address = atoi(line);
        physical_address = get_physical_address(logical_address, fd_backing);

        if(tlb_hit) {
            stats.tlb_hits++;
            stats.pagetable_hits++;
        }

        if(pt_hit) {
            stats.pagetable_hits++;
        }

        stats.total_memory_accesses++;
        
        print_access_results(logical_address, physical_address, value, tlb_hit, pt_hit);

        count++;
    }

    free(pm);

    return stats;
}
