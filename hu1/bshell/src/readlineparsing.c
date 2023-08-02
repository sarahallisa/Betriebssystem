#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include "shell.h"
#include "types.h"
#include "command.h"
#include "list.h"
#include "debug.h"
#include "helper.h"

#ifndef NOLIBREADLINE
#include <readline/readline.h>

/* Call this to get the next character of input. */
char *current_readline_prompt = (char *)NULL;
char *current_readline_line = (char *)NULL;
int current_readline_line_index = 0;


/*
 * This code is mainly copied from BASH
 */
static int
yy_readline_get (){
    int line_len;
    unsigned char c;
    if (current_readline_line == 0){
        /* our prompt comes directly from the shell and not frome here!*/
        current_readline_line = readline (current_readline_prompt);

        /* after the prompt is used for the first time, we can reset it here to a different value for multiline input! */
        sprintf(current_readline_prompt, ">| ");
        if (current_readline_line == 0){
            return(EOF);
        }
        current_readline_line_index = 0;
        line_len = strlen (current_readline_line);
        /* we need two additional bytes for \n\0*/
        current_readline_line = (char *)realloc (current_readline_line, 2 + line_len);
        /* readline does not add \n to a line!*/
        current_readline_line[line_len++] = '\n';
        /*terminate the current string!*/
        current_readline_line[line_len] = '\0';
    }

    if (current_readline_line[current_readline_line_index] == 0)
    {
        free (current_readline_line);
        current_readline_line = (char *)NULL;
        return (yy_readline_get ());
    }
    else
    {
        c = current_readline_line[current_readline_line_index++];

        return (c);
    }
}

#if 0
static int
yy_readline_unget (c)
    int c;
{
    if (current_readline_line_index && current_readline_line)
        current_readline_line[--current_readline_line_index] = c;
    return (c);
}
#endif /* 0 */
#endif /* NOLIBREADLINE */

int yy_getc () {
#ifndef NOLIBREADLINE
    return (*(yy_readline_get)) ();
#else
    return (*(getchar)) ();
#endif

}

/* Call this to unget C.  That is, to make C the next character
   to be read. */
#if 0
static int
yy_ungetc (c)
    int c;
{
    return (*(yy_readline_unget)) (c);
}
#endif

