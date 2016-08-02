# -*- coding: utf-8 -*-
__author__ = 'AMA'

import socket
import wx
import threading
import ECUdata as ED


class ThWIFIserver:

    def __init__(self, host='localhost', port=9090 ):

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((host, port))
        self.udp_socket.settimeout(1)

        self.alive = True
        # создаеи поток
        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

        self.transmitter_thread = threading.Thread(target=self.writer)
        self.transmitter_thread.setDaemon = True
        self.transmitter_thread.start()

    def close(self):
        self.alive = False
        # Ожидаем закрытич потоков
        self.transmitter_thread.join(1)
        self.receiver_thread.join(1)
        self.udp_socket.close()

    def reader(self):
        # ПОТОК (!) чтения из ком порта
        while self.alive:
            try:
                data, self.addr = self.udp_socket.recvfrom(10)
                print 'addr CLIENT', self.addr
                print 'data from CLIENT', data
            except:
                pass
                #print 'no data from client'

    def writer(self):
        while self.alive:
            try:
                self.udp_socket.sendto(b'MSGserver', self.addr)
            except:
                print "can't send data to CLIENT"


class ThWIFIclient:

    def __init__(self, host='localhost', port=9090 ):

        self.addr = (host,port)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.connect(self.addr)
        self.udp_socket.settimeout(2)

        self.alive = True

        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.setDaemon = True
        self.receiver_thread.start()

        #self.transmitter_thread = threading.Thread(target=self.writer)
        #self.transmitter_thread.setDaemon = True
        #self.transmitter_thread.start()

    def close(self):
        self.alive = False
        # Ожидаем закрытич потоков
        self.transmitter_thread.join(1)
        self.receiver_thread.join(1)
        self.udp_socket.close()

    def reader(self):
        # ПОТОК (!) чтения из ком порта
        while self.alive:
            try:
                data = self.udp_socket.recvfrom(5000,self.addr)
                print 'data from server-',data
            except:
                print "can't recive data from SERVER"

    def writer(self):
        while self.alive:
            try:
                self.udp_socket.sendto(b'11114', self.addr)
                print 'send data to SERVER'
            except:
                print "can't send data to SERVER"

if __name__ == '__main__':


    ser=ThWIFIserver( host='192.168.4.1')
    #cli= ThWIFIclient( host='192.168.4.1' )
    raw_input()


