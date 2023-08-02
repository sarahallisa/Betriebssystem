/*
 * command.h
 *
 * Definition of the represenation of a command.
 *
 */

#ifndef COMMAND_H

#define COMMAND_H

#include "list.h"

/*
 * There are different types of command types
 *
 */

typedef enum {
    C_EMPTY,         /* empty command*/
    C_SIMPLE,        /* plain simple command*/
    C_SEQUENCE,      /* sequence of commands using ";"*/
    C_PIPE,          /* using "|"  */
    C_AND,           /* using "&&" */
    C_OR,            /* using "||" */
    C_IF,            /* conditional construct*/
    C_WHILE          /* loop construct */
} CommandType;

typedef enum {
    M_READ,            /* <  */
    M_WRITE,           /* >  */
    M_APPEND           /* >> */
} RedirectionMode;

typedef enum {
    R_FD,
    R_FILE
} RedirectionType;

/*
 * A redirection can either be using a file or filedescriptor
 * like stdin, stdout or stderr.
 */

typedef struct {
    RedirectionType r_type;
    RedirectionMode r_mode;          /* controls how fd is used (READ/WRITE/APPEND) */
    union {
        int r_fd;         /* file descriptor of source or target */
        char * r_file;    /* full filename of source or target */
    } u;
} Redirection;

/*
 * A simple command can have different redirections
 * and consists of tokens that describe the command
 */
typedef struct SimpleCommand {
  List *redirections;
  int  command_token_counter;
  int background;
  char ** command_tokens;
} SimpleCommand;


/* 
 * A command squence is a list of simple commands
 * 
 */

typedef struct {
  List *command_list;    /*storage of SimpleCommand */
  int  command_list_len;
} CommandSequence;

typedef struct command {
    CommandType command_type;
    CommandSequence *command_sequence;
} Command;


SimpleCommand * simple_command_new(int, char **, List *, int);
Command * command_new_empty();
Command * command_new(int type, SimpleCommand * cmd, SimpleCommand * cmd2);
Command * command_append(int type, SimpleCommand * s_cmd, Command * cmd);
void command_print(Command *cmd);
void command_delete(Command *cmd);
void delete_redirections(List *rd);
void simple_command_print(int indent, SimpleCommand *cmd_s);
char * command_get(Command *);

#endif /* end of include guard: COMMAND_H */
