#include "stringbuffer.h"

#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>

StringBuffer string_buffer_new(size_t initial_capacity) {
    if (initial_capacity < 1) {
        initial_capacity = 1;
    }
    StringBuffer result = {.cap = initial_capacity, .len = 1, .cstring = malloc(initial_capacity * sizeof(char))};
    result.len = 1;
    *result.cstring = 0;

    return result;
}

size_t string_buffer_ensure_capacity(StringBuffer *str, size_t requested_cap) {
    size_t new_buffer_size = 0;

    if (requested_cap > str->cap) {

        // try cap * 1.75
        new_buffer_size = str->cap * 1.75f;
        if (new_buffer_size < str->cap) {
            // theoretically this could happen (overflow)...
            new_buffer_size = SIZE_MAX;
        }

        // if cap * 1.75 is not big enough, we get exactly as much as requested
        if (requested_cap > new_buffer_size) {
            new_buffer_size = requested_cap;
        }

        char *tmp_data = realloc(str->cstring, new_buffer_size * sizeof(char));

        if (tmp_data == NULL) {
            return str->cap;
        }

        str->cstring = tmp_data;
        str->cap = new_buffer_size;

        return new_buffer_size;
    }

    return str->cap;
}

void string_buffer_clear(StringBuffer *str) {
    if (str && str->cap > 0) {
        str->len = 1;
        *str->cstring = 0;
    }
}

void string_buffer_append_formatted(StringBuffer *output, const char *fmt, ...) {
    va_list args;

    va_start(args, fmt);
    size_t space_needed = vsnprintf(NULL, 0, fmt, args);
    va_end(args);

    size_t cap_needed = output->len + space_needed;

    size_t new_cap = string_buffer_ensure_capacity(output, cap_needed);

    if (new_cap < cap_needed) {
        fprintf(stderr, "Error: StringBuffer: not enough memory to print into string buffer\n");
        return;
    }

    va_start(args, fmt);
    vsnprintf(output->cstring + output->len - 1, space_needed + 1, fmt, args);
    va_end(args);

    output->len += space_needed;
}
