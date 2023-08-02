/*
 * list.h
 *
 * Definition of the represenation of a list.
 *
 */

#ifndef LIST_H

#define LIST_H

typedef struct list {
    void *head;
    struct list *tail;
} List;

List * list_append(void * head, List * tail);

#endif /* end of include guard: LIST_H */
