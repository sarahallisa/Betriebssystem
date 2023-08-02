#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>
#include "shell.h"
#include "helper.h"
#include "command.h"
#include <signal.h>
#include <errno.h>
#include <pwd.h>
#include <sys/types.h>
#include <fcntl.h>
#include "statuslist.h"
#include "debug.h"
#include "execute.h"


/* do not modify this */
#ifndef NOLIBREADLINE
#include <readline/history.h>
#endif /* NOLIBREADLINE */

#define INPUT 0
#define OUTPUT 1

extern int shell_pid;
extern int fdtty;
int interruptflag = 0;
StatusList * list;

/* do not modify this */
#ifndef NOLIBREADLINE
static int builtin_hist(char ** command){

    register HIST_ENTRY **the_list;
    register int i;
    printf("--- History --- \n");

    the_list = history_list ();
    if (the_list)
        for (i = 0; the_list[i]; i++)
            printf ("%d: %s\n", i + history_base, the_list[i]->line);
    else {
        printf("history could not be found!\n");
    }

    printf("--------------- \n");
    return 0;
}
#endif /*NOLIBREADLINE*/
void unquote(char * s){
	if (s!=NULL){
		if (s[0] == '"' && s[strlen(s)-1] == '"'){
	        char * buffer = calloc(sizeof(char), strlen(s) + 1);
			strcpy(buffer, s);
			strncpy(s, buffer+1, strlen(buffer)-2);
                        s[strlen(s)-2]='\0';
			free(buffer);
		}
	}
}

void unquote_command_tokens(char ** tokens){
    int i=0;
    while(tokens[i] != NULL) {
        unquote(tokens[i]);
        i++;
    }
}

void unquote_redirect_filenames(List *redirections){
    List *lst = redirections;
    while (lst != NULL) {
        Redirection *redirection = (Redirection *)lst->head;
        if (redirection->r_type == R_FILE) {
            unquote(redirection->u.r_file);
        }
        lst = lst->tail;
    }
}

void unquote_command(Command *cmd){
    List *lst = NULL;
    switch (cmd->command_type) {
        case C_SIMPLE:
        case C_OR:
        case C_AND:
        case C_PIPE:
        case C_SEQUENCE:
            lst = cmd->command_sequence->command_list;
            while (lst != NULL) {
                SimpleCommand *cmd_s = (SimpleCommand *)lst->head;
                unquote_command_tokens(cmd_s->command_tokens);
                unquote_redirect_filenames(cmd_s->redirections);
                lst = lst->tail;
            }
            break;
        case C_EMPTY:
        default:
            break;
    }
}

static int execute_fork(SimpleCommand *cmd_s, int background){
    char ** command = cmd_s->command_tokens;
    pid_t pid, wpid;

    list = appendProcess(-1, -1, 0, cmd_s->command_tokens, list);

    pid = fork();

    // if(background == 0){
    //     list = appendProcess(pid, -1, 0, cmd_s->command_tokens, list);
    // }else if(background == 1){
    //     list = appendProcess(pid, -1, -1, cmd_s->command_tokens, list);
    // }
    
  
    if (pid==0){
        /* child */
        signal(SIGINT, SIG_DFL);
        signal(SIGTTOU, SIG_DFL);
        signal(SIGCHLD, SIG_DFL);
        /*
         * handle redirections here (start)
         */
        List *redirections = cmd_s->redirections;
        while (redirections != NULL) {
            Redirection *redirection = (Redirection *)redirections->head;
            int fd;

            if (redirection->r_type == R_FILE) {
                if (redirection->r_mode == M_READ) {
                    fd = open(redirection->u.r_file, O_RDONLY);
                    if (fd == -1) {
                        if(errno == EACCES){
                            fprintf(stderr, "%s: Permission denied\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }else if (errno == ENOENT){
                            fprintf(stderr, "%s: No such file or directory\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }else{
                            fprintf(stderr, "%s: Error opening file\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }
                        
                    }
                    dup2(fd, STDIN_FILENO);
                } else if (redirection->r_mode == M_WRITE) {
                    fd = open(redirection->u.r_file, O_WRONLY | O_CREAT | O_TRUNC, 0644);
                    if (fd == -1) {
                         if(errno == EACCES){
                            fprintf(stderr, "%s: Permission denied\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }else{
                            fprintf(stderr, "%s: Error opening file\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }
                    }
                    dup2(fd, STDOUT_FILENO);
                } else if (redirection->r_mode == M_APPEND) {
                    fd = open(redirection->u.r_file, O_WRONLY | O_CREAT | O_APPEND, 0644);
                    if (fd == -1) {
                         if(errno == EACCES){
                            fprintf(stderr, "%s: Permission denied\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }else{
                            fprintf(stderr, "%s: Error opening file\n", redirection->u.r_file);
                            exit(EXIT_FAILURE);
                        }
                    }
                    dup2(fd, STDOUT_FILENO);
                }
                close(fd);
            }

            redirections = redirections->tail;
        /*
        * handle redirections end
        */

       }
        if (execvp(command[0], command) == -1){
            fprintf(stderr, "-bshell: %s : command not found \n", command[0]);
            perror("");
        }
        
        /*exec only return on error*/
        exit(EXIT_FAILURE);
    } else if (pid < 0) {
        perror("shell");

    } else {
        /*parent*/
        setpgid(pid, pid);
        pid_t pgid = getpgid(pid);
        list = setNewPID(list, pid, background);
        list = setNewPGID(list, pid, pgid);

        if (background == 0) { 
            /* wait only if no background process */
            tcsetpgrp(fdtty, pid);

            int status;
            wpid = waitpid(pid, &status, 0);
     
            tcsetpgrp(fdtty, shell_pid);
            list = refreshList(list, wpid, status);

            return 0;
        }
    }

    return 0;
}



static int do_execute_simple(SimpleCommand *cmd_s, int background){
    if (cmd_s==NULL){
        return 0;
    }
    if (strcmp(cmd_s->command_tokens[0],"exit")==0){
        exit(0);
    }else if (strcmp(cmd_s->command_tokens[0], "true") == 0) {
        // Always return success (zero exit status)
        return 1;
    } else if (strcmp(cmd_s->command_tokens[0], "false") == 0) {
        // Always return failure (non-zero exit status)
        return 0;
    } else if (strcmp(cmd_s->command_tokens[0], "status") == 0) {
        printList(list);
        list = deleteProcess(list);
        return 0;
    } else if(strcmp(cmd_s->command_tokens[0], "cd") == 0){  // cd command
        if(cmd_s->command_token_counter < 2) {
            // keine Pfad angegeben, wechseln zum Login-Verzeichnis des Benutzers
            const char *home_dir = getenv("HOME");
            if(home_dir != NULL) {
                chdir(home_dir);
            }
        } else {
            // Pfad angegeben, wechseln zum angegebenen Verzeichnis
            if(chdir(cmd_s->command_tokens[1]) != 0) {
                fprintf(stderr, "%s: No such file or directory.\n", cmd_s->command_tokens[1]);
            }
        }
        
        return 0;

/* do not modify this */
#ifndef NOLIBREADLINE
    } else if (strcmp(cmd_s->command_tokens[0],"hist")==0){
        return builtin_hist(cmd_s->command_tokens);
#endif /* NOLIBREADLINE */
    } else {
        return execute_fork(cmd_s, background);
    }
    fprintf(stderr, "This should never happen!\n");
    exit(1);
}

/*
 * check if the command is to be executed in back- or foreground.
 *
 * For sequences, the '&' sign of the last command in the
 * sequence is checked.
 *
 * returns:
 *      0 in case of foreground execution
 *      1 in case of background execution
 *
 */
int check_background_execution(Command * cmd){
    List * lst = NULL;
    int background =0;
    switch(cmd->command_type){
    case C_SIMPLE:
        lst = cmd->command_sequence->command_list;
        background = ((SimpleCommand*) lst->head)->background;
        break;
    case C_OR:
    case C_AND:
    case C_PIPE:
    case C_SEQUENCE:
        /*
         * last command in sequence defines whether background or
         * forground execution is specified.
         */
        lst = cmd->command_sequence->command_list;
        while (lst !=NULL){
            background = ((SimpleCommand*) lst->head)->background;
            lst=lst->tail;
        }
        break;
    case C_EMPTY:
    default:
        break;
    }
    return background;
}

int execute(Command * cmd){
    unquote_command(cmd);

    int res=0;
    List * lst=NULL;

    int execute_in_background=check_background_execution(cmd);
    switch(cmd->command_type){
    case C_EMPTY:
        {
            break;
        }
    case C_SIMPLE:
        {
            res=do_execute_simple((SimpleCommand*) cmd->command_sequence->command_list->head, execute_in_background);
            fflush(stderr);
            break;
        }
    case C_OR:
        {
            lst = cmd->command_sequence->command_list;
            while (lst != NULL) {
                res = do_execute_simple((SimpleCommand *)lst->head, execute_in_background);
                fflush(stderr);
                if (res != 0) {
                    // A command returned an exit status of 0, break the OR chain.
                    break;
                }
                lst = lst->tail;
            }
            break;
        }
    case C_AND:
        {
            lst = cmd->command_sequence->command_list;
            while (lst != NULL) {
                res = do_execute_simple((SimpleCommand *)lst->head,execute_in_background);
                fflush(stderr);
                if (res == 0) {
                    // A command returned a non-zero exit status, break the AND chain.
                    break;
                }
                lst = lst->tail;
            }
            break;
        }
     case C_SEQUENCE:
        {
            lst = cmd->command_sequence->command_list;
            while(lst != NULL) {
                res = do_execute_simple((SimpleCommand*) lst->head, execute_in_background);
                
                lst = lst->tail;
            }
            break;
        }
    case C_PIPE:
        {
            pid_t pids[cmd->command_sequence->command_list_len - 1];
            // Pipe file descriptors
            int pipefd[cmd->command_sequence->command_list_len - 1][2];

            int pidCounter = 0;
            pid_t pid, wpid, pgid;

            lst = cmd->command_sequence->command_list;
            
            for(int i = 0; i<  cmd->command_sequence->command_list_len - 1; i++){
                if (pipe2(pipefd[i], O_CLOEXEC) == -1) { // Pipe
                    perror("Pipe failed: \n");
                    exit(EXIT_FAILURE);
                }
            }

            while (lst != NULL) {
                SimpleCommand *sc = (SimpleCommand *)lst->head;
                char **commands = sc->command_tokens;

                if ((pid = fork()) == -1) {
                    // Error fork
                    perror("fork failed");
                    exit(1);
                }

                pids[pidCounter++] = pid;

                list = appendProcess(pid, pids[0], 0, commands, list);

                if (pid == 0) { // Child
                    if (lst->tail != NULL) { 
                        if (dup2(pipefd[pidCounter - 1][OUTPUT], STDOUT_FILENO) == -1) { // STDOUT
                            perror("dup2 failed: ");
                            exit(EXIT_FAILURE);
                        }
                    }

                    if (pidCounter > 1) { 
                        if (dup2(pipefd[pidCounter - 2][INPUT], STDIN_FILENO) == -1) { // STDIN
                            perror("dup2 failed: ");
                            exit(EXIT_FAILURE);
                        }
                    }

                    setpgid(0, pids[0]);

                    if(execute_in_background == 0) {
                        tcsetpgrp(fdtty, getpgid(0));
                    }

                    signal(SIGINT, SIG_DFL);
                    signal(SIGTTOU, SIG_DFL);
                    signal(SIGCHLD, SIG_DFL);

                    // Close pipes
                    for (int i = 0; i < cmd->command_sequence->command_list_len - 1; i++) {
                        close(pipefd[i][INPUT]);
                        close(pipefd[i][OUTPUT]);
                    }

                    execvp(commands[0], commands);

                    perror("execvp failed: ");
                    exit(EXIT_FAILURE);
                } else { // Parent
                    lst = lst->tail;
                }
        
            }

            // Parent
            setpgid(pids[0], pids[0]);
            pgid = getpgid(pids[0]);
            list = setNewPGID(list, pids[0], pgid);
            
            if (execute_in_background == 0) {
                int status;
               
                tcsetpgrp(fdtty, pids[0]);

                // Close all pipe data descriptors in parent process
                for (int i = 0; i < cmd->command_sequence->command_list_len - 1; i++) {
                    close(pipefd[i][0]);
                    close(pipefd[i][1]);
                }

                for(int i = 0; i < cmd->command_sequence->command_list_len; i++){
                    while((wpid = waitpid(pids[i], &status, 0)) > 0) {
                        list = refreshList(list, wpid, status);
                    }
                    
                }

                tcsetpgrp(fdtty, shell_pid);
                res = status;
            }

            break;
        }

    default:
        {
            printf("[%s] unhandled command type [%i]\n", __func__, cmd->command_type);
            break;
        }
    }
    return res;
}
