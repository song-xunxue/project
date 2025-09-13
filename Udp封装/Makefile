.PHONY:all
all:UdpServe UdpClient
UdpServe:UdpServe.cc
	g++ -o $@ $^ -std=c++11
UdpClient:UdpClient.cc
	g++ -o $@ $^ -std=c++11


.PHONY:clean
clean:
	rm -f UdpClient UdpServe
