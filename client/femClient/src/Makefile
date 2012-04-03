TARGET = FemClient

CXX = g++
CXXFLAGS = -g -Wall -fmessage-length=0

VAR =  $(shell $(CXX) -dumpmachine)
PLATFORM = $(shell awk 'BEGIN { print substr("$(VAR)", 1, index("$(VAR)", "-")-1)}')

INCLUDES = ../include/$(TARGET).h
INCLUDES += ../include/FemException.h
INCLUDES += ../include/FemTransaction.h
INCLUDES += ../include/protocol.h
INCLUDES += ../include/dataTypes.h
INCLUDES += ../include/FemDataReceiver.h

OBJ_DIR= objs.$(PLATFORM)
OBJS  =	$(OBJ_DIR)/FemClient.o $(OBJ_DIR)/FemException.o $(OBJ_DIR)/FemTransaction.o
OBJS +=	$(OBJ_DIR)/FemUDP.o $(OBJ_DIR)/FemPersonality.o $(OBJ_DIR)/FemDataReceiver.o
OBJS +=	$(OBJ_DIR)/FemClientAcquisition.o $(OBJ_DIR)/FemClientBusses.o
OBJS +=	$(OBJ_DIR)/FemClientHardwareDevices.o

INCLUDE_DIRS =	-I../include 
CXXFLAGS += $(INCLUDE_DIRS)

LIB = $(OBJ_DIR)/lib$(TARGET).a

$(LIB): $(OBJS)
	rm -f $@
	ar rc $@ $(OBJS)
	ranlib $@

all: $(LIB)

install: $(LIB)
	cp $(LIB) ../../../../det-software/libs/libs.linux.$(PLATFORM)/lib

clean:
	rm -f $(OBJS) $(LIB)

#------------------------------------------------------------------------------
#--  rule: ./*.cpp
#------------------------------------------------------------------------------
$(OBJ_DIR)/%.o: %.cpp $(INCLUDES)
	@echo "Compiling $< ..."
	$(CXX) $(CXXFLAGS) $< -c -o $@	

#------------------------------------------------------------------------------
#--  rule: ./*.c
#------------------------------------------------------------------------------
$(OBJ_DIR)/%.o: %.c $(INCLUDES)
	@echo "Compiling $< ..."
	$(CXX) $(CXXFLAGS) -c $< -o $@
