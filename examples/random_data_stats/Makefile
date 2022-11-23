CC=g++
CFLAGS=-c -Wall -I../../src -I../../stats/include -I../../gcem/include -std=c++17
LDFLAGS= 
CPPFLAGS=  -DSTATS_ENABLE_STDVEC_WRAPPERS -DSTATS_GO_INLINE -DUSE_STATS=1 -I../../src  -I../../stats/include -I../../gcem/include -std=c++17
LIBS= 
SOURCES=main.cpp ../../src/random_stats.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=randomdatastats

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) -O2 $(LIBS) -o $@

.cpp.o:
	$(CC) $(CFLAGS) $(CPPFLAGS) -O2 -DUSE_STATS $< -o $@
