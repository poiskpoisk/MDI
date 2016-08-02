# -*- coding: utf-8 -*-#
__author__ = 'AMA'

from abc import ABCMeta, abstractmethod, abstractproperty

class ReadECUcal:
    """ Абстрактный класс """
    __metaclass__ = ABCMeta

    @abstractproperty
    def bufSize(self):
        # Абстрактное свойство, которое обязательно должен быть у класса занимающегося чтением блоков данных в ECU.
        # Размер буффера принятый из ECU, CRC будет внутри это блока и займет 2 последних байта
        pass

    @abstractmethod
    def calParserBin(self, calFromECU):
        '''
        Абстрактный метод, который обязательно должен быть у класса занимающегося чтением блоков данных ( калибровки )
        из ECU. Для чтения оперативных данных не требуется.
        :param calFromECU: Данные полученные из COM порта для разборки
        :return:
        '''
        pass

class WriteECUcal:
    """ Абстрактный класс """
    __metaclass__ = ABCMeta

    @abstractproperty
    def bufSize(self):
        # Абстрактное свойство, которое обязательно должен быть у класса занимающегося записью блоков данных в ECU.
        # Размер буффера для передачи в ECU, CRC будет внутри это блока и займет 2 последних байта
        pass

    @abstractmethod
    def createCal2Send(self):
        # Абстрактный метод, который обязательно должен быть у класса занимающегося записью блоков данных в ECU.
        pass

class ReadWriteECUcal(ReadECUcal, WriteECUcal):
    pass

# Для целей тестирования
class ts(ReadWriteECUcal):

    bufSize = 42

    def calParserBin(self, calFromECU):
        print 'calparserbin', calFromECU

    def createCal2Send(self):
        print 'createCal2send'


if __name__ == '__main__':
    a=ts()
    a.calParserBin(24)
    print a.bufSize
    a.bufSize = 100
    print a.bufSize





