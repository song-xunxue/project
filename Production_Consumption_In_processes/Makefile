# 编译器设置
CXX = g++
#chcp 65001
# 编译选项:
CXXFLAGS = -g -Wall -std=c++11 -finput-charset=UTF-8 -fexec-charset=UTF-8
LDFLAGS =

# 定义源文件和目标文件
SOURCES_COMMON = Common.cpp
OBJECTS_COMMON = $(SOURCES_COMMON:.cpp=.o)

TARGET_MAIN = main.exe
TARGET_PRODUCER = producer.exe
TARGET_CONSUMER = consumer.exe

all: $(TARGET_MAIN) $(TARGET_PRODUCER) $(TARGET_CONSUMER)

$(TARGET_MAIN): main.cpp $(OBJECTS_COMMON)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(TARGET_PRODUCER): producer.cpp $(OBJECTS_COMMON)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(TARGET_CONSUMER): consumer.cpp $(OBJECTS_COMMON)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(OBJECTS_COMMON): $(SOURCES_COMMON) Common.h
	$(CXX) $(CXXFLAGS) -c $(SOURCES_COMMON)

clean:
	@if exist *.o del /Q *.o
	@if exist $(TARGET_MAIN) del /Q $(TARGET_MAIN)
	@if exist $(TARGET_PRODUCER) del /Q $(TARGET_PRODUCER)
	@if exist $(TARGET_CONSUMER) del /Q $(TARGET_CONSUMER)

.PHONY: all clean