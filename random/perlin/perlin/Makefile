# Directories
BDIR		:=	bin
SDIR		:=	src
ODIR		:=	obj
IDIR		:=	include

# Compiler and Flags
CC			:=	g++
STD			:=	-std=c++17
WARNINGS	:=	-Wall -Wextra -pedantic
OPTIMIZE	:=	-O3
CFLAGS		:=	$(STD) $(WARNINGS) $(OPTIMIZE) -I$(IDIR)
LIBS		:=	-lm

# Dependencies and Objects
DEPS_FILES	:=	template.hpp io.hpp flow_field.hpp perlin.hpp perlin_io.hpp \
           		particle.hpp particle_io.hpp
DEPS		:=	$(addprefix $(IDIR)/, $(DEPS_FILES))

OBJ_FILES	:=	main.o flow_field.o perlin_public.o perlin_private.o \
           		particle_public.o particle_private.o
OBJ 		:=	$(addprefix $(ODIR)/, $(OBJ_FILES))

# Rules
all: $(BDIR)/perlin

$(ODIR)/%.o: $(SDIR)/%.cpp $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

$(BDIR)/perlin: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ core $(IDIR)/*~