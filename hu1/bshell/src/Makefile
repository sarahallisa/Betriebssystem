CC = gcc
TARGET = shell

CFLAGS  = -std=c99
CPPFLAGS += -g -Wall -MMD -MP -pedantic
LDFLAGS = -lreadline

all: $(TARGET)

objs := shell.o command.o tokenparser.o tokenscanner.o helper.o list.o statuslist.o execute.o readlineparsing.o stringbuffer.o
deps := $(objs:.o=.d)

shell: $(objs) $(LDFLAGS)

tokenscanner.c: tokenscanner.l tokenparser.h
	    flex -I -otokenscanner.c tokenscanner.l

tokenparser.c tokenparser.h: tokenparser.y
	bison -o tokenparser.c -dtv $<


.PHONY: clean
clean: ; $(RM) foo $(objs) $(deps) tokenscanner.c tokenparser.c tokenparser.h *.output

dist-clean:
	make clean
	$(RM) $(TARGET)

-include $(deps)


