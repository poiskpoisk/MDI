# -*- coding: utf-8 -*-#
__author__ = 'AMA'

# В этом файле находятся классы-примеси, необходимые для организации двухстороннего обсена данными с ECU

import time
import wx
import ECUdata as ED
from struct import *
import codecs
from   CRCModules.CRC16 import CRC16


# Класс-примесь. Базовый родительский клас, содержащий константы и общую для всего логику
class Parse():

    markerLength    = 8    # Длина маркера, использующаяся для идентификации команд
    progressDlg     = 0    # Диалог прогресса

    resetECU                = 13    # Посылаем запрос RESET ECU
    manualECUoff            = 55    # Ручное ВЫКЛЮЧЕНИЕ блока програмной кнопкой
    manualECUon             = 77    # Ручное ВКЛЮЧЕНИЕ  блока програмной кнопкой
    readCalRequest          = 90    # Посылаем запрос на ЧТЕНИЕ калибровки из ECU
    readGPScalRequest       = 95    # Посылаем запрос на ЧТЕНИЕ GPS калибровки из ECU
    writeCalRequest         = 100   # Запрос на ЗАПИСЬ калибровки в EEPROM
    manualCalPPSon          = 101   # Включить режим ручной калибровки PPS
    autocalON               = 103   # Включить режим автокалибровки PPS
    writeGPScalRequest      = 105   # Посылаем запрос на ЗАПИСЬ GPS калибровки из ECU
    fillDefault             = 150   # Залить заводские установки
    testINJon               = 200   # Команда ECU перейти в режим тестирования форсунок
    readActiveZoneRequet    = 222   # Запрос на чтение списка активных зон для работы GPS
    testINJoff              = 250   # Команда ECU ВЫЙТИ ИЗ режима тестирования форсунок

    def __init__(self):
        self.parsePosition = 0 # Обязательно ! Счетчик позиции при разборе или формировании калибровки

    # Прием блока данных из ECU
    def readBufferFromECU(self, in_data):
        # Отрезаем рвзмер передаваемого буфера и предидущий маркер
        data4parse = in_data[-(self.markerLength + self.bufSize):]
        self.progressDlg.Update(2, u'Данные считанны из ECU')  # Обновляем прогресс бар
        # Обрезаем последние 8 символов маркера
        del data4parse[- self.markerLength:]
        # Убиваем входной буфер, что бы он не накапливался
        in_data = []
        crc_given = data4parse[self.bufSize - 1] * 256 + data4parse[self.bufSize - 2]
        # Обрезаем последние 2 символа, где хранился CRC
        del data4parse[- 2:]
        s = ''  # Инициализируем строку
        for i in range(len(data4parse)):
            s = s + chr(data4parse[i])
        crc_calc = CRC16(True).calculate(s)
        self.progressDlg.Update(3, u'Контрольная сумма рассчитана')  # Обновляем прогресс бар
        if crc_calc == crc_given:
            self.calParserBin(data4parse)  # Разбор кодировки из двоичного вида по переменны
            self.progressDlg.Update(4, u'Данные успешно считанны из ECU')
        else:
            wx.Bell()
            self.progressDlg.Update(4, u'Данные НЕ считаны из ECU. Не сошлась контрольная сумма.')
            wx.MessageBox(u'Не удалось считать из данные из ECU.',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

        time.sleep(0.5)
        self.progressDlg.Destroy()

        return in_data

    # Посылает команду в ECU и обрабатывает ошибку
    def sendCommandECU( self, command, sleep=0.5 ):
        '''
        :param command: Числовой номер команды
        :param sleep:   Время в секундах паузы, после команды, если паузка не нужна , то 0
        :return True:   Если все нормально, False если порт не открыт
        '''
        rxECU = 60  # Объем посылки командных байт ( Внимание ! если менять, то есть зависимости в ECU )
        try:
           ED.thser.out_data=[ chr( command ) for x in range( rxECU ) ]
           time.sleep(sleep) # Нужно дать время ECU сбросить мусор в входном буфере
        except:
           wx.Bell()
           wx.MessageBox( u"COM порт не открыт", caption=u"Сообщение о проблемах",
                          style=wx.OK | wx.ICON_ERROR)
           return False
        else:
           return True

# Класс-примесь. Функционал, необходимый для чтения ( разбора ) двоичных данных из ECU
class ReadECU( Parse ):

    def getCalTable(self, table, data):

        turboSize = len(table)
        startPosition = self.parsePosition
        # Формируем газовую и дизельную калибровку
        for row in range(turboSize):
            for col in range(len(table[0])):
                table[row][col] = data[startPosition + col * turboSize + row]
                self.parsePosition += 1
        return table

    def getWordTable(self, table, data):
        for i in range(len(table)):
            table[i] = data[self.parsePosition] + data[self.parsePosition + 1] * 256
            self.parsePosition += 2
        return table

    def getByteTable(self, table, data):
        for i in range(len(table)):
            table[i] = data[self.parsePosition]
            self.parsePosition += 1
        return table

    # Взять строку произвольной длинны из данных, по умолчанию длина строки 20
    def getStr(self, data, lenStr=20):
        byteStr = ''
        # Преобразуем с строку БАЙТ
        for c in range(self.parsePosition, self.parsePosition + lenStr):
            byteStr = byteStr + chr(data[c])
            self.parsePosition += 1
        # Получаем кодек
        codec = codecs.lookup('utf-8')
        # Пробуем декодировать назад в Уникод
        try:
            zoneName, ln = codec.decode(byteStr)
        except:
            zoneName = '???'  # Если не удалось, то зона пусть называется ???

        return zoneName

    # Декодировать из оперативных данных ДОЛГОТУ
    def getLON(self, data):
        # Превращаем список ЦИФР, сначала в список СИМВОЛОВ, а потом в СТРОКУ
        st = chr(data[self.parsePosition]) + chr(data[self.parsePosition + 1]) + \
             chr(data[self.parsePosition + 2]) + chr(data[self.parsePosition + 3])  # строка байт
        tuple = unpack('f', st)  # кортеж значений
        # > выравнивать с правого края
        # от права - 6 цифр через точку всего 10, f = исходное значение float
        self.parsePosition += 4
        return '{:0>10.6f}'.format(tuple[0])  # строка

        # Декодировать из данных ШИРОТУ

    def getLAT(self, data):
        # Превращаем список ЦИФР, сначала в список СИМВОЛОВ, а потом в СТРОКУ
        st = chr(data[self.parsePosition]) + chr(data[self.parsePosition + 1]) + \
             chr(data[self.parsePosition + 2]) + chr(data[self.parsePosition + 3])  # строка байт
        tuple = unpack('f', st)  # кортеж значений
        # > выравнивать с правого края
        # от права - 6 цифр через точку всего 10, f = исходное значение float
        self.parsePosition += 4
        return '{:0>9.6f}'.format(tuple[0])  # строка

    # Декодировать все данные из записи ЗОНЫ
    def getZoneRecord(self, data):
        long = self.getLON(data)
        lat = self.getLAT(data)
        radius = str(self.getWord(data))
        typeZone = str(self.getByte(data))
        zoneName = self.getStr(data)

        return (zoneName, long, lat, radius, typeZone)

    # Берет из калибрвки или оперативных данных данные в формате word ( 2 байта )
    def getWord(self, data):
        val = data[self.parsePosition] + data[self.parsePosition + 1] * 256
        self.parsePosition += 2
        return val

    # Берет из калибрвки или оперативных данных данные в формате байт
    def getByte(self, data):
        val = data[self.parsePosition]
        self.parsePosition += 1
        return val

    # Взять ДОЛГОТУ из данных
    def getLong(self, dataFromECU):
        val = dataFromECU[self.parsePosition] + dataFromECU[self.parsePosition + 1] * 256 + \
              dataFromECU[self.parsePosition + 2] * 256 * 256 + dataFromECU[
                                                                    self.parsePosition + 3] * 256 * 256 * 256
        self.parsePosition += 4
        return val

    # Устанавливает флаг TRUE/FALSE в зависимости от состояния бита в байте пересланном из ECU
    def getFlag(self, dataFromECU):
        # Сервисное, для разбора байта по битам
        bits = (1, 2, 4, 8, 16, 32, 64, 128)
        flags = [False for x in range(8)]
        i = 0
        for bit in bits:
            if dataFromECU[self.parsePosition] & bit:
                flags[i] = False
            else:
                flags[i] = True
            i += 1
        self.parsePosition += 1
        return flags

# Класс-примесь. Функционал, необходимый для записи данных из ECU
class WriteECU( Parse ):

    # Выдача предупреждения о перезаписи калибровки в ECU
    def showWarning(self):
        wx.Bell()
        dWarning = wx.Dialog(ED.main_parent, -1, u"Предупреждение о записи калибровки в ECU",
                             pos=(550, 350), size=(500, 200))
        dWarning.SetBackgroundColour("WHITE")
        sz = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        st_1 = wx.StaticText(dWarning, -1, u"Вы собираетесь перезаписать калибровку в EEPROM ECU.")
        st_2 = wx.StaticText(dWarning, -1, u"ВНИМАНИЕ ! Старая калибровка будет утеренаа !")
        st_3 = wx.StaticText(dWarning, -1, u"Нажмите ДА, если с этим согласны, НЕТ если не хотите. ")
        st_1.SetFont(font)
        st_2.SetFont(font)
        st_3.SetFont(font)
        sz.Add(st_1, 0, wx.TOP | wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_TOP, 20)
        sz.Add(st_2, 0, wx.TOP | wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_TOP, 20)
        sz.Add(st_3, 0, wx.TOP | wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_TOP, 20)
        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(dWarning, wx.ID_OK, u"ДА")
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(dWarning, wx.ID_CANCEL, u"НЕТ"))
        buttons.Realize()
        sz.Add((0, 20))  # Пустое пространство
        sz.Add(buttons, 0, wx.LEFT | wx.ALIGN_LEFT, 150)
        dWarning.SetSizer(sz)
        res = dWarning.ShowModal()
        dWarning.Destroy()
        return (res)

    # Записать в выходной буфер строку, длинной lenStr
    def setStr(self, data, lenStr=20):
        startParsePosition = self.parsePosition
        # todo Сделать проверку что если имя зоны английское, то обрезать до 20 байтn
        codec = codecs.lookup('utf-8')
        st, length = codec.encode(data)
        st = st[:lenStr]
        try:
            codec.decode(st)
        except:
            st = st[:-1]
        for s in st:
            self.sendCalBuf[self.parsePosition] = s
            self.parsePosition += 1

        self.parsePosition = startParsePosition + lenStr

    # Записать в выходной буфер двухмерную таблицу состоящую из байт
    def setCalTable(self, table):
        turboSize = len(table)
        startPosition = self.parsePosition
        # Формируем газовую и дизельную калибровку
        for row in range(turboSize):
            for col in range(len(table[0])):
                self.sendCalBuf[startPosition + col * turboSize + row] = table[row][col]
                self.parsePosition += 1

    # Записать в выходной буфер таблицу состоящую из слов
    def setWordTable(self, table):
        startPosition = self.parsePosition
        for i in range(len(table)):
            self.sendCalBuf[startPosition + 2 * i] = table[i] % 256  # Остаток от деления
            self.sendCalBuf[startPosition + 2 * i + 1] = table[i] // 256
            self.parsePosition += 2

    # Записать в выходной буфер таблицу состоящую из байтов
    def setByteTable(self, table):
        startPosition = self.parsePosition
        for i in range(len(table)):
            self.sendCalBuf[startPosition + i] = table[i]
            self.parsePosition += 1

    # Записать в выходной буфер данные размерностью WORD
    def setWord(self, data):
        self.sendCalBuf[self.parsePosition] = data % 256
        self.parsePosition += 1
        self.sendCalBuf[self.parsePosition] = data // 256
        self.parsePosition += 1

    # Записать в выходной буфер данные размерностью BYTE
    def setByte(self, data):
        self.sendCalBuf[self.parsePosition] = data
        self.parsePosition += 1

    # Закодировать ДОЛГТОУ в двоичные данные
    def setLAT(self, data):
        # val - список из полей
        # val[1] - долгота в виде букв из экранного представления
        fl = float(data)  # преобразуем в честный флоат
        st = pack('f', fl)  # получаем 4 байтное представление в С формате строка
        for i in range(len(st)):  # побайтно записываем в калибровку
            self.sendCalBuf[self.parsePosition] = st[i]
            self.parsePosition += 1

    # Закодировать ШИРОТУ в двоичные данные
    def setLON(self, data):
        self.setLAT(data)  # Синтаксический сахар, кодирование одинаковое, но что разные названия, что бы не перепутать

    # Закодировать полностью запись зоны
    def setZoneRecord(self, val ):
        ''' :param val: это кортеж, содержащий строки '''
        self.setLON(val[1])         # Долгота
        self.setLAT(val[2])         # Широта
        self.setWord(int(val[3]))   # Радиус зоны
        self.setByte(int(val[4]))   # Тип зоны
        self.setStr(val[0])         # Имя зоны

    # Подсчитать и записать в выходной буфер контрольную сумму CRC
    def setCRC(self):
        st = ''  # Инициализируем строку
        for i in range(len(self.sendCalBuf) - 2):  # Без 2-х последних байт, куда запишем вычисленное CRC\
            if type(self.sendCalBuf[i]) == type('1'):
                st = st + self.sendCalBuf[i]
            else:
                st = st + chr(self.sendCalBuf[i])

        crc_calc = CRC16(True).calculate(st)
        self.sendCalBuf[len(self.sendCalBuf) - 2] = crc_calc % 256  # мл.байт
        self.sendCalBuf[len(self.sendCalBuf) - 1] = crc_calc // 256  # ст. байт

    # Стандартный дмалог с пользователем о записи калибровки
    def dialogWriteFLASH(self, com):
        # Предупреждение о перезаписи калибровки, если пользователь согласен, то продолжаем
        if self.showWarning() != wx.ID_OK: return False
        # Нельзя перешиваться на работающем ECU, проверяем что бы оно было выключено в ручную
        if ED.flag_ECU_ON_VISU == False and ED.flag_Relay == False:
            ''' Есть проблемы с тем, что когда прогресс диалог закрывается штатным AUTO_HIDE все подвисает
             поэтому сделано что бы он всегда не доходил до конца ( имено для этого добавлено 2 к размеру
             калибровки). А окно убивается принудительно из модуля thserial при получении ответа от ECU
             ED.progressDialog - один на все процессы записи, так одновременно он может быть только один  '''
            ED.progressDialog = wx.ProgressDialog(u"Процент выполнения записи калибровки в EEPROM", u"Запись:",
                                                  maximum=len(self.sendCalBuf) + 2, parent=ED.main_parent,
                                                  style=0 | wx.PD_APP_MODAL)
            if self.sendCommandECU(com, 3) == False: return False  # Если команда ECU послана НЕ успешно
            self.createCal2Send()  # Формируем газовую и дизельную калибровку
            # Флэш записывается на НАНЕ и МЕГЕ порциями различной длины
            if ED.prog_setup['typeECU'] == 1:
                block_size = 256
            else:
                block_size = 128
            # Передаем полученные данные в очередь на передачу
            for i in range(len(self.sendCalBuf)):
                if type(self.sendCalBuf[i]) == type('1'):
                    s = self.sendCalBuf[i]
                else:
                    s = chr(self.sendCalBuf[i])

                ED.thser.out_data.append( s )
                if i % block_size == 0:
                    time.sleep(float(ED.prog_setup['delayBlock']) / 1000)  # дефолтное знач. 0.5
                else:
                    time.sleep(float(ED.prog_setup['delay']) / 1000)  # дефолтное значение 0.004
                ED.progressDialog.Update(i + 1, u'Записанно ' + str(i + 1) + u' байт')
            return True
        else:
            wx.MessageBox(u'Для записи калибровки ECU должно быть выключено кнопкой из программы '
                          u'( требование безопасности )', caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            return False

# Класс-примесь. Функционал, необходимый для записи и чтения данных из ECU
class ReadWriteECU( ReadECU, WriteECU):
    '''
    Комбинаторный класс, служит для объединения примесей в функциональную группу. Т.е. класс, который занмается
    двухсторноним обменом с ECU должен просто наследовать это класс и там уже будет весь необходимый функционал
    '''
    pass