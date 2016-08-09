# -*- coding: utf-8 -*-

import threading
import time
import serial
import wx
import ECUdata as ED
from mixin import ParseMixin

# Serial port daemon class.
class ThSerial ( ParseMixin.Parse ):

    def __init__(self, port, baudrate ):

        self.flag_autocal   = False
        self.Count_autocal  = 0
        self.markerLength   = 8  # Длина маркера в байтах
        self.in_data        = []  # Первичный входной буффер
        self.out_data       = []  # Первичный выходной буффер
        self.dataFromECU    = []  # Блок данных для парсинга, полученных из ECU

        # Словарь Маркера-ключи, показывающие различные состояния ECU и функции которые эти состояния обрабатывают

        self.dMF = \
            {'12345678': self.getOperData,          # Маркер, озхначающий начало блока данных
             '16990532': self.autoCalGood,          # Маркер, озхначающий УСПЕШНУЮ автокалибровку
             '14545529': self.autoCalWrong,         # Маркер, озхначающий НЕ УСПЕШНУЮ автокалибровку
             '11223340': self.autoCalON,            # Маркер, озхначающий что блок включил режим автокалибровки
             '14223204': self.autoCalOFF,           # Режим автокалибровки не может быть включен или редуктор или кнопка
             '79998880': ED.rw.readBufferFromECU,   # Маркер, озхначающий ОКОНЧАНИЯ (!) блока КАЛИБРОВКИ
             '19451945': self.writeCalOK,           # Маркер, озхначающий калебровка успешно послана в ECU
             '19411941': self.writeCalWrong,        # Маркер, озхначающий калебровка НЕ послана в ECU
             '01233210': self.checkINJon,           # Маркер, озхначающий что будет ВКЮЧЕН режим тестирования форсунок
             '71995880': ED.rwGPS.readBufferFromECU,# GPS калибровка посланна из ECU
             '51993884': ED.az.readBufferFromECU,   # Список активных зон послан из ECU
             # Маркер, озхначающий что будет выполнен Reset ECU
             '19171917': u'OK Сейчас ECU перезагрузится и будет закрыт COM порт и откройт снова. '
                         u'Если что-то пойдет не так выйдите из программы и зайдите снова.',
             # Маркер, озхначающий что будет ВЫКЛ режим тестирования форсунок
             '98766789': u'Er ВЫКЛЮЧЕН режим тестирования форсунок. Для продолжения работы нажмите ОК',
             # Маркер, режим проверки форсунок не включен из-за ошибки по редуктору или кнопкам
             '08346751': u'Er Режим проверки форсунок не включен из за выключенных кнопок включения'
                         u'  или ТЕМПЕРАТУРЫ РЕДУТОРА',
             # Режим РУЧНОЙ калибровки не включен или редуктор или кнопка
             '99934567': u'Er Ручная калибровка не включена из за выключенных кнопок включения или ТЕМПЕРАТУРЫ РЕДУТОРА',
             # Маркер, озхначающий что блок включил режим ручной калибровки PPS
             '77332211': u'OK ВКЛЮЧЕН режим ручной калибровки PPS. Для продолжения работы нажмите ОК и наблюдайте за'
                         u' значениями PPS1 эм. и PPS2 эм. У вас на это есть 30 секунд, после чего вы автоматически'
                         u' выйдете u из режима ручной калибровки ',
             # Маркер, озхначающий что блок выключил режим ручной калибровки PPS
             '54433222': u'ВЫКЛЮЧЕН режим ручной калибровки PPS. Для продолжения работы нажмите ОК',
             # заливка дефолтных значений в калибровку проведена успешно
             '01983217': u'Заводские установки закисанны в ECU. По необходимости считайте их обычным путем.'
                         u' Для продолжение нажмите ОК',
            }

        try:
            self.serial = serial.Serial(port, baudrate, timeout = 0  )

        except serial.SerialException:
            wx.Bell()
            wx.MessageBox(u"Не удается открыть порт %s.\n" % port,
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            exit()
        else:
            self.open()

    # Открытие и настройка потоков
    def open(self):
        self.alive = True
        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()
        self.transmitter_thread = threading.Thread(target=self.writer)
        self.transmitter_thread.setDaemon(1)
        self.transmitter_thread.start()

    # Закрытие потоков
    def close(self):
        self.alive = False
        # Ожидаем закрытич потоков
        self.transmitter_thread.join(1)
        self.receiver_thread.join(1)
        self.serial.close()

    # ПОТОК (!) чтения из ком порта
    def reader(self):
        while self.alive:
            data = self.serial.read(1)
            # serial.read читает символ в виде экранированной последовательности ( формаат/xXX ),
            # его надо явно преобразовать в байт
            if len(data) == 1:
                self.in_data.append(ord(data))  # Если символ считан, то записываем в входной буффер
                self.searchingMarker()          # Ищем в входном потоке маркеры и вызываем функции-обработчики
                if self.flag_autocal :
                    ED.pdlgAutocal.Update(self.Count_autocal, u'Подбираем PWM ' + str(self.Count_autocal))
                    self.Count_autocal +=1

    # Просматривает в потоке маркер и вызывает функцию обработчик
    def searchingMarker(self):
        for k, val in self.dMF.items():
            # Преобразуем маркер из строки в список чисел
            lMarker = [int(k[0]), int(k[1]), int(k[2]), int(k[3]), int(k[4]), int(k[5]), int(k[6]), int(k[7])]
            # Если просто надо печатать сообщения, то аргумент в словаре эти сообщения
            if self.in_data[-self.markerLength:] == lMarker:
                if type(val) == type(u'строка'):
                    # Тип строки сообщения закодирован первыми 3 символами, который потом не выводятся
                    if val[:2]=='Er':
                        self.clearSoundMsgErr( val[3:])
                    else:
                        self.clearSoundMsgOK( val )
                else:
                    self.in_data = val( self.in_data ) # Или вызываем функцию обработчик
                return

    # Пришел блок оперативных данных
    def getOperData(self, in_data ):
        # Отрезаем рвзмер передаваемого буфера и предидущий маркер
        tempBuf = in_data[-(self.markerLength + self.ECU_buf):]

        # 8 байт, соответствующих предидущему маркеру, корректны ?
        if [1,2,3,4,5,6,7,8] == tempBuf[:-self.ECU_buf]:
            del tempBuf[- self.markerLength:]  # Обрезаем последние 8 символов маркера
            # И наконей вырезаем собственно данные
            self.dataFromECU = tempBuf[-(self.ECU_buf - self.markerLength):]
            # Обрезаем входрой буфер на длину успешно принятого блока данных, что бы не рос входной буффер
            del in_data[-(self.ECU_buf):]
        else:
            print u'Разовая ошибка чтения оперативных данных'
            in_data = [1, 2, 3, 4, 5, 6, 7, 8]  # Что бы не было переполнения входного буфер
        return in_data

    # Включен режим тестирования форсунок
    def checkINJon(self, in_data ):
        self.clearSoundMsgOK(u'Включен режим тестирования форсунок. Для выхода из режима нажмите ОК')
        self.sendCommandECU( self.testINJoff )  # Команда ECU ВЫЙТИ ИЗ режима тестирования форсунок
        return in_data

    # Включен режим автокалибровки PPS
    def autoCalON(self, in_data):
        ED.pdlgAutocal.Update(1, u'Включен режим автокалибровки PPS')
        self.flag_autocal = True
        self.Count_autocal = 0
        # Обрезаем последние 8 символов маркера
        del in_data[-self.markerLength:]
        return in_data

    # Автокалибровка PPS не включена
    def autoCalOFF(self, in_data):
        self.clearSoundMsgErr(u'Автокалибровка PPS не включена из за выключенных кнопок включения'
                              u' или низкой температуры редуктора')
        ED.pdlgAutocal.Destroy()
        return in_data

    # Автокалибровка PPS проведенна успешно
    def autoCalGood(self, in_data):
        # Отрезаем рвзмер передаваемого буфера и маркер
        self.dataFromECU = in_data[-(self.markerLength + ED.PPS_table_size * 4):]
        self.clearSoundMsgOK(u'Автокалибровка PPS проведенна успешно. Нажмите ОК и '
                             u'посмотрите результаты в табличных настройках обновление калибровки.')
        ED.pdlgAutocal.Destroy()
        self.flag_autocal = False
        ED.rw.readCalECU( 1 )
        return in_data

    # Автокалибровка PPS не удалась.
    def autoCalWrong(self, in_data):
        ED.pdlgAutocal.Destroy()
        self.clearSoundMsgErr(u'Автокалибровка PPS не удалась.')
        self.flag_autocal = False
        return in_data

    # Калибровка НЕ ЗАПИСАННА в ECU
    def writeCalWrong(self, in_data ):
        ED.progressDialog.Destroy()
        self.clearSoundMsgErr(u'Калибровка НЕ ЗАПИСАННА в ECU')
        return in_data

    # Калибровка записанна в EEPROM
    def writeCalOK(self, in_data):
        # Обрезаем последние 8 символов маркера
        del in_data[-self.markerLength:]
        ED.progressDialog.Update (1, u'Калибровка записанна в EEPROM')
        time.sleep(1)
        ED.progressDialog.Destroy()
        return in_data

    # Возвращает последний успешно считанный блок данных из ECU
    def dataECU(self):
        return (self.dataFromECU)

    # Запись байта в COM порт
    def writer(self):
        while self.alive:
            if len(self.out_data) > 0:
                character = self.out_data.pop(0)
                try:
                    self.serial.write(character)
                except:
                    self.clearSoundMsgErr( u'Ошибка записи в COM порт.')

    # Для улучшения читаемости кода, чистим , пищим и сообщаем, что все ОК
    def clearSoundMsgOK(self, msg ):
        # Грохаем входную и выходные очереди для гарантии
        self.in_data=[]
        self.out_data=[]
        wx.Bell()
        wx.MessageBox( msg, caption=u"Информация")

    # Для улучшения читаемости кода, чистим , пищим и сообщаем, что ОШИБКА
    def clearSoundMsgErr(self, msg):
        # Грохаем входную и выходные очереди для гарантии
        self.in_data=[]
        self.out_data=[]
        wx.Bell()
        wx.MessageBox( msg, caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

class ThSerial_MEGA(ThSerial):
    def __init__(self, port, baudrate):
        ThSerial.__init__( self, port, baudrate )
        self.ECU_buf = 84+2  # Длина буффера и маркера на передачу со стороны газодизельного ECU

