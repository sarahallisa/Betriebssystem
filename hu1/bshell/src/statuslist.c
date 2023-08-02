#define _GNU_SOURCE
#include "statuslist.h"
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>



void printList(StatusList *list) {
    if (list == NULL) {
        printf("Status list is empty.\n");
        return; 
    } else {
        printf("\tPID\tPGID\tSTATUS\t\tPROG\n");
        
        StatusList *current = list; // Introduce a new variable to traverse the list
        
        while (current != NULL) {
            Process *process = current->process;
            char status[100];  // Allocate memory for the status string
            
            if (process->status == -1) {
                strcpy(status, "running");
            } else if (WIFEXITED(process->status)) {
                int exit_status = WEXITSTATUS(process->status);
                sprintf(status, "exit(%d)", exit_status);
            } else if (WIFSIGNALED(process->status)) {
                int exit_status = WTERMSIG(process->status);
                sprintf(status, "signal(%d)", exit_status);
            } else {
                strcpy(status, "unknown");
            } 
            
            printf("\t%d\t%d\t%s\t\t%s\n", process->pid, process->pgid, status, process->prog);
            current = current->tail; // Move to the next node
        }
    }
}

StatusList* refreshList(StatusList *list, pid_t pid, int status) {
    if(list == NULL) {
        return list;
    }

    StatusList *current = list;

     while (current != NULL) {
        // Found the process in the list
        if (current->process->pid == pid) {
            current->process->status = status;
            if (pid == 0) {
                // The process is still running
                current->process->status = -1;
            } else if (pid == -1) {
                // An error occurred, handle it accordingly
                perror("waitpid");
            } else {
                // The process has changed state, update the status
                current->process->status = status;
            }
            break;
        }
        current = current->tail;
    }

    return list;
}

StatusList *deleteProcess(StatusList *list) {
    if (list == NULL) {
        return NULL;
    }

    StatusList *current = list;
    StatusList *previous = NULL;

    while (current != NULL) {
        if (current->process->status != -1) {
            // Process has stopped, delete it from the list
            if (previous == NULL) {
                // Process is at the head of the list
                StatusList *temp = list;
                list = list->tail;
                current = list;
                free(temp->process->prog);
                free(temp->process);
                free(temp);
            } else {
                // Process is in the middle or end of the list
                StatusList *temp = current;
                previous->tail = current->tail;
                current = current->tail;
                free(temp->process->prog);
                free(temp->process);
                free(temp);
            }
        } else {
            // Process is still running, move to the next node
            previous = current;
            current = current->tail;
        }
    }

    return list;
}

StatusList *appendProcess(pid_t pid, pid_t pgid, int status, char **prog, StatusList *list) {
    Process *newProcess = malloc(sizeof(Process));
    if (newProcess == NULL) {
        perror("malloc failed\n");
        exit(EXIT_FAILURE);
    }

    newProcess->pid = pid;
    newProcess->pgid = pgid;
    newProcess->status = status;
    newProcess->prog = malloc(strlen(*prog) + 1);

    if (newProcess->prog == NULL) {
        perror("malloc failed");
        exit(EXIT_FAILURE);
    }

    strcpy(newProcess->prog, *prog);

    StatusList *newList = malloc(sizeof(StatusList));

    if (newList == NULL) {
        perror("malloc failed\n");
        exit(EXIT_FAILURE);
    }

    newList->process = newProcess;
    newList->tail = NULL;

    if (list == NULL) {
        // If the list is initially empty, set the new list as the head
        list = newList;
    } else {
        StatusList *current = list;
        while (current->tail != NULL) {
            current = current->tail;
        }
        current->tail = newList;
    }

    return list;
}

StatusList* setNewPGID(StatusList* list, pid_t pid, pid_t pgid) {
    if(list == NULL) {
        return list;
    }

    StatusList *current = list;

     while (current != NULL) {
        // Found the process in the list
        if (current->process->pid == pid) {
            current->process->pgid = pgid;
            break;
        }
        current = current->tail;
    }

    return list;
}

StatusList* setNewPID(StatusList* list, pid_t pid, int background) {

    StatusList *current = list;

    while (current->tail != NULL) {
        current = current->tail;
    }

    current->process->pid = pid;

    if(background == 0){
        current->process->status = 0;
    }else if(background == 1){
        current->process->status = -1;
    }

    return list;
}
