CXXFLAGS = -fPIC -Wall -Iinclude
#LDFLAGS = -shared 
LDFLAGS = 

ifndef SRC_DIR
	SRC_DIR = src
endif

ifndef OBJ_DIR
	OBJ_DIR = .
endif

ifndef LIB_DIR
	LIB_DIR = .
endif

ifdef BOOST_ROOT
	CXXFLAGS += -I${BOOST_ROOT}/include
	LDFLAGS += -L${BOOST_ROOT}/lib 
endif

LDFLAGS += -lboost_system -lboost_thread

SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS= $(SOURCES:$(SRC_DIR)/%.cpp=$(OBJ_DIR)/%.o)
TARGET = $(LIB_DIR)/libfem_api.a

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(AR) $(ARFLAGS) $@ $(OBJECTS)      
        
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) $< -c -o $@
        
clean:
	rm -f $(TARGET)
	rm -f $(OBJECTS)
