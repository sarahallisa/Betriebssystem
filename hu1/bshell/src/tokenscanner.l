%{
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "shell.h"
#include "command.h"
#include "types.h"
#include "tokenparser.h"
#include "debug.h"

/* this is later done by bison */

extern int yy_getc();
int fileno(FILE *stream);

#define YY_INPUT(buf,result,max_size) \
         { \
         int c = yy_getc(); \
         result = (c == EOF) ? YY_NULL : (buf[0] = c, 1); \
         }

%}
/* prevent filno warning */
/* %option never-interactive */
%option nounput
%option noinput

%%

[ \t]+ {} /* skip all blanks and tabs */

"\n" { /* EOL */
          return '\n';
     }

[;<>&|] { /* Tokens with length 1 */
            return yytext[0];
       }


"||" { return OR;}

"&&" { return AND;}

">>" { return APPEND;}

\"[^"]+\"  { /* Quoted String */
        /*this variant does not remove the quoting characters*/
        size_t len=strlen(yytext);
        yylval.str=calloc(len+1,sizeof(char));
        strncpy(yylval.str, yytext, len); /*copy after first quote sign "*/
        return STRING;
        
        /*this variant does remove the quoting characters*/
        //size_t len=strlen(yytext)-2;
        //yylval.str=calloc(len+1,sizeof(char));
        //strncpy(yylval.str, yytext+1, len); /*copy after first quote sign "*/
        //return STRING;
}

[A-Za-z0-9/_.\-+*#^,:~$%@?]+  { /* Unquoted String */
        size_t len=strlen(yytext)+1;
        yylval.str=calloc(len,sizeof(char));
        strncpy(yylval.str, yytext, len);
        return STRING;
}

.   {
        size_t len=strlen(yytext)+1;
        yylval.str=calloc(len,sizeof(char));
        strncpy(yylval.str, yytext, len);
        return UNDEF;
    }

%%

int yywrap(){
      return 1;
}

