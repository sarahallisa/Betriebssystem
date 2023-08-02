%{
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

#define YYDEBUG 1
/*typedef struct token_string_seq_t{*/
    /*int len;*/
    /*int position;*/
    /*char ** str;*/
/*} token_string_seq_t;*/

int yy_getc();
int yylex(void);
void yyerror (char const *s) {
    fprintf(stderr, "[%s %s %i] ERROR: %s\n", __FILE__, __func__, __LINE__, s);
}

int ret=0;
char ** str_buffer;
Command *cmd;

%}

%define parse.error verbose
%union {
    char *str;
    Command *cmd;
    token_string_seq_t tokseq;
    SimpleCommand *simple_cmd;
    Redirection *redirection;
    List *list;
}

/*     &&  || >>        */
%token AND OR APPEND IF THEN ELSE FI
%token <str> STRING UNDEF
%type <str> StringType
%type <tokseq> TokenStringSequence;
%type <cmd> Command;
%type <simple_cmd> SimpleCommand;
%type <cmd> CommandSequence CommandPipe CommandAnd CommandOr;
%type <redirection> Redirection;
%type <list> Redirections;
%left     ';'

%%
/* The ret=0; here is necessary, else the parser does not handle the mixing of
 * undefined chars and valid commands properly.
 * If this is set later in StringType for STRING, then e.g. [` ls] becomes a valid
 * input, which it is not!
 * It seems this resets ret once per received line.
 */
Line: {ret=0;} Command '\n' {cmd = $2; return ret;}
    //| Command {cmd = $1; return ret;}
    | /* empty */ '\n' {cmd=command_new_empty(); return ret;}
    | /* EOF */ { fprintf(stdout, "\n"); exit(1);}
;

Command: SimpleCommand {$$=command_new(C_SIMPLE, $1, NULL);}
       | CommandSequence {$$=$1;}
       | CommandOr {$$=$1;}
       | CommandAnd {$$=$1;}
       | CommandPipe {$$=$1;}
       ;

CommandSequence: SimpleCommand ';' SimpleCommand {$$= command_new(C_SEQUENCE, $1, $3);}
               | SimpleCommand ';' CommandSequence {$$= command_append(C_SEQUENCE, $1, $3);}

CommandPipe: SimpleCommand '|' SimpleCommand {$$= command_new(C_PIPE, $1, $3);}
               | SimpleCommand '|' CommandPipe {$$= command_append(C_PIPE, $1, $3);}

CommandAnd: SimpleCommand AND SimpleCommand {$$= command_new(C_AND, $1, $3);}
               | SimpleCommand AND CommandAnd {$$= command_append(C_AND, $1, $3);}

CommandOr: SimpleCommand OR SimpleCommand {$$= command_new(C_OR, $1, $3);}
               | SimpleCommand OR CommandOr {$$= command_append(C_OR, $1, $3);}


Redirections: /* empty */ {$$=NULL;}
            | Redirection Redirections { $$=list_append($1, $2);}

Redirection: '>' TokenStringSequence {
                        $$=malloc(sizeof(Redirection));
                        $$->r_type=R_FILE;
                        $$->r_mode=M_WRITE;
                        $$->u.r_file=$2.str[0];
                        /* no longer nedded */
                        free($2.str);

           }
           | '<' TokenStringSequence {
                        $$=malloc(sizeof(Redirection));
                        $$->r_type=R_FILE;
                        $$->r_mode=M_READ;
                        $$->u.r_file=$2.str[0];
                        /* no longer nedded */
                        free($2.str);
           }
           | APPEND TokenStringSequence {
                        $$=malloc(sizeof(Redirection));
                        $$->r_type=R_FILE;
                        $$->r_mode=M_APPEND;
                        $$->u.r_file=$2.str[0];
                        /* no longer nedded */
                        free($2.str);
           }

SimpleCommand: TokenStringSequence Redirections { 
             $$ = simple_command_new($1.len, $1.str, $2, 0); 
             }
             | TokenStringSequence Redirections '&' { 
             $$ = simple_command_new($1.len, $1.str, $2, 1); 
             }
;
               
TokenStringSequence: StringType {
                   /* NOTE: This function tries to use a fully dynamic memory allocation approach
                    * to support unlimited numbers of tokens.
                    * A much easier approach is to limit the tokens to a specific number.
                    * In this case, all that needs to be done is:
                    * $$.str=calloc(1024,sizeof(char *));
                    * for 1024 possible command line arguments!
                    */
                   $$.len=1;
                   /* We allocate 8 bytes more "container space"-memory than necessary, because
                    * we need initialized memory here after the last argv*, 
                    * if not valgrind complains that argv points to uninitialized memory.
                    * Note: $$.str is char **, so this is only the array $$.str[here][] container 
                    * for the tokens 
                    */
                   $$.str=calloc(2,sizeof(char *));
                   
                   /* this is the actual token string that is used $$.str[0][here] */
                   /* now we have: 
                    * $$.str[0][here]="A TOKEN STRING"
                    */
                   $$.str[0]=$1;

                   /* we do not need to allocate new memory and use strcpy.
                    * the string is already alocated and available from the scanner!
                    * strcpy($$.str[0], $1);
                    * calloc(strlen($1)+1, sizeof(char));
                    */
                   
                   //hexDump("HEXDUMP OF ALLOCATE $$", $$.str, 32, 0);
                   //hexDump("HEXDUMP OF ALLOCATE STRING", $$.str[0], strlen($$.str[0]) , 0);
                   }
                   | TokenStringSequence StringType {
                   char * tmp = NULL;
                   
                   /* Remember: We allocate 8 bytes more initialized (ZERO) memory than necessary!
                    * It makes also sense to allocate initially a fixed number of Bytes and keep
                    * track of used and free memory. Actually, this is what the original implementation
                    * did. But in this case, we need an additional managed memory area, that keeps track
                    * of used and free memory. (This was the original wortspeicher, which used realloc
                    * and was explicitly managing this memory)
                    */
                   
                   /* NOTE: In a static version, all that must be done is
                    * $$.str[$$.len]=$2
                    */
                   

                   /* NOTE: Intead of copying the strings around, realloc could have been used instead.
                    * But, the problem in this case is that execve expects initialized memory and, as such,
                    * it would have been necessray to initialize the reallocated memory manually to '\0'.
                    * By using calloc, we get the initilization for free, but need the copy mechanism.
                    */
                   /* The idea is the following:
                    * 1. Copy the current container ( holding the string pointers) to a temporary container
                    * 2. Create a new container for one more item
                    * 3. Copy the original container to the new container(on head position)
                    * 4. allocate memory for the new token and insert it into the enlarged container
                    */


                   /* 1.*/
                   /* copy original old stringpointer */
                   tmp = calloc($$.len+1, sizeof(char *)); /* current container size + 1 */
                   memcpy(tmp, $$.str, (1+$$.len)* sizeof(char *));
                   /* contents of $$.str has been copied to tmp and will be copied back to
                    * the head position of the new enlarged $$.str container 
                    * Since it no longer required, we free it now.
                    */ 
                   free($$.str); /* aka the memory for the "old" string */
                   
                   /* 2. */
                   /* make a bigger array $$.str[here++][] and copy values back (c.f. execve requirement)*/
                   $$.str=calloc(2+$$.len,sizeof(char *));

                   /* 3. */
                   /* now we simply copy back the old string/strings to the new memory area*/
                   memcpy($$.str, tmp, (1+$$.len) * sizeof(char *));
                   /* tmp can be freed now, we do not need it anymore */
                   free(tmp);

                   /* 4. */
                   /* now we allocate another memory slot for the new token */
                   $$.str[$$.len]=$2; 
                   /* we do not need to allocate new memory and use strcpy.
                    * the string is already alocated and available from the scanner!
                    * calloc(strlen($2)+1, sizeof(char));
                    * strcpy($$.str[$$.len], $2);
                    */
/* and finally copy the contents from the parser */
                   //hexDump("HEXDUMP OF ALLOCATE $$", $$.str, 32, 0);
                   //hexDump("HEXDUMP OF ALLOCATE STRING", $$.str[$$.len], strlen($$.str[$$.len]), 0);
                   $$.len++; 
                   } 
           ;
StringType: STRING { $$=$1;}
          | UNDEF  { fprintf(stderr, "undefined character \'%c\' (=0x%0x)\n", $1[0], $1[0]);
                    $$=$1;
                    /* this ret prevent the execution of a command when a an invalid char 
                     * is found. This is handled in shell.c in variable parser_res!
                     */
                    ret=2;
                  }

%%

