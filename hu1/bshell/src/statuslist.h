#include <unistd.h>
#ifndef STATUSLIST_H

#define STATUSLIST_H

typedef struct Process {
    pid_t pid;
    pid_t pgid;
    int status;
    char * prog;
} Process;

typedef struct StatusList {
    Process *process;
    struct StatusList *tail;
} StatusList;

void printList(StatusList *list);
StatusList* refreshList(StatusList *list, int wpid, int status);
StatusList *deleteProcess(StatusList *list);
StatusList *appendProcess(pid_t pid, pid_t pgid, int status, char ** prog, StatusList *list);
StatusList* setNewPGID(StatusList* list, pid_t pid, pid_t pgid);
StatusList* setNewPID(StatusList* list, pid_t pid, int background);

#endif

