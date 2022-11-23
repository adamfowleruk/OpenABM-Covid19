CC=g++
CFLAGS=-c -I../../src -I../../stats/include -I../../gcem/include -std=c++17
LDFLAGS= 
CPPFLAGS= -I../../stats/include -I../../gcem/include -std=c++17 -DSTATS_ENABLE_STDVEC_WRAPPERS -DSTATS_GO_INLINE 
LIBS= 
SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=invgamma

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) -O3 $(LIBS) -o $@

.cpp.o:
	$(CC) $(CFLAGS) $(CPPFLAGS) -O3 $< -o $@
