#ifndef __STRINGBUFFER_H_
#define __STRINGBUFFER_H_

#include <stdlib.h>

/*
 * stringbuffer.h
 *
 * Definition of a simple string type that can grow on demand and is compatible with c-strings.
 * .cstring points to the underlying c-string and has to be freed manually.
 *
 */

typedef struct {
    char *cstring;
    size_t cap;
    size_t len;
} StringBuffer;

/*
 * Returns a new string buffer that can initially hold <initial_capacity> bytes.
 * The new string buffer will hold an empty c-string and therefore always have a
 * initial capacity > 1, regardless of the the argument (to store the null-byte).
 */
StringBuffer string_buffer_new(size_t initial_capacity);

/*
 * Append a formatted string to a StringBuffer. If <output> does not
 * have a large enough capacity to hold the new string, this function
 * will automatically grow it.
 */
void string_buffer_append_formatted(StringBuffer *output, const char *fmt, ...);

size_t string_buffer_ensure_capacity(StringBuffer *str, size_t requested_cap);

void string_buffer_clear(StringBuffer *str);


#endif
