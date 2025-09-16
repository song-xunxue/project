.PHONY:all
all:TCPServe TCPClient
TCPServe:TCPServe.cc
	g++ -o $@ $^ -std=c++11 -lpthread
TCPClient:TCPClient.cc
	g++ -o $@ $^ -std=c++11 -lpthread


.PHONY:clean
clean:
	rm -f TCPClient TCPServe