# -*- coding: utf-8 -*-
__author__ = 'AMA'

import re
import time

import wx
from serial.tools.list_ports import comports

import DieselGasCalWindow
import ECUdata as ED
import ReadWriteCalDisk
import ReadWriteCalECU as RW
import generalpribor as GP
import thserial as TH

from gps import GPS2ECU
from gps import GPSfile
from gps import GPSzone

from mixin import Func
from mixin import ParseMixin
from mixin import MenuMixin

from setup import GeneralSetup
from setup import ProgramSetup
from setup import TableSetup
from setup import GPS_Setup


class MainFrame( wx.MDIParentFrame, ParseMixin.Parse, MenuMixin.Menu ):

    def __init__(self):
        self.gpw=0
        self.com ='?'
        self.manualPWM  =0 # Значение PWM по умолчанию для ручной калибровки PPS
        # Разбираем заголовок в драйвере COM порта и определяем какая плата подключена, выводим главное окно с надписью
        # что именно подключено
        self.connectCOMport()
        # Настройка размеров окон под различные разрешения экрана и запуск РОДИТЕЛЬСКОГО окна и приборной панели
        self.tuneScreenSize()
        ED.main_parent = wx.MDIParentFrame.__init__(self, None, -1, self.title_str, pos=(0, 0), size=ED.mainPriborSize)
        # Привязываем сигнал выхода из программы к ф-цц обработки этого события
        self.Bind(wx.EVT_CLOSE, self.mainOnClose )

    def createMenu(self, funcReadECU, funcWriteECU ):

        # Добавляем на меню бар все меню
        self.menubar = wx.MenuBar()

        # Создаем меню для работ блоком управления
        self.menuBlock( u"&Блок управления",
                        [u"&Открыть COM порт",          self.onConnectECU,      None,           False],
                        [u"&Закрыть COM порт",          self.onDisconnectECU,   None,           True],
                        [u"&ECU ВКЛ/ВЫКЛ\tCtrl+Z",      self.onManualON,        'on-off16.png', False],
                        [u"&Перегрузить ECU\tCtrl+R",   self.onResetECU,        'reset1616.gif',False],
                        [u"&Заводские установки",       self.onFillDefaultCal,  None,           True],
                        [u"&Выход\tCtrl+X",             self.onExit,            None,           False] )

        # Создаем меню для работ с калибровкой
        self.menuBlock( u"&Калибровки",
                       [u"&Калибровка ГАЗ основа\tCtrl+B",  DieselGasCalWindow.OsnovaGasCalWindow, 'gas16.png',  False],
                       [u"&Калибровка ГАЗ\tCtrl+G",         DieselGasCalWindow.GasCalWindow,        'gas16.png', False],
                       [u"&Калибровка ДИЗЕЛЬ\tCtrl+D",      DieselGasCalWindow.DieselCalWindow,     'oil16.png', True],
                       [u"&Считать из файла *.py\tCtrl+L",  ReadWriteCalDisk.onCalRead,         'readdisk16.png',False],
                       [u"&Записать в файл *.py\tCtrl+S",   ReadWriteCalDisk.onCalWrite,        'savedisk16.png', True],
                       [u"&Считать калибровку из ECU\tCtrl+O",  funcReadECU,                      'write16.png', False],
                       [u"&Загрузить калибровку в ECU\tCtrl+W", funcWriteECU,                     'read16.png', False],)

        # Создаем меню для опций и натсроек
        self.menuBlock( u"&Настройки",
                       [u"&Основные\tCtrl+E",   GeneralSetup.GeneralSetupWindow,    None, False],
                       [u"&Табличные\tCtrl+T",  TableSetup.TableSetup,              None, False],
                       [u"&Програмные\tCtrl+P", ProgramSetup.programSetupWindow,    None, False])

        # Создаем меню для работы с настройками PPS
        self.menuBlock( u"&Педаль газа",
                       [u"&Автоматическая калибровка PPS",  self.onAutoCalPPS,      None, False],
                       [u"&Ручная калибровка PPS",          self.onManualCalPPS,    None, False] )

        # Создаем меню для работы с форсунками
        self.menuBlock( u"&Форсунки",
                       [u"&Тестирование форсунок.",         self.onTestINJ_ON, None, False] )

        # Создаем меню для работы c GPS
        self.menuBlock( u"&GPS",
                       [u"&Список зон\tCtrl+1",                     GPSzone.ZoneList,           None, False],
                       [u"&Настройки\tCtrl+2",                      GPS_Setup.SetupGPSWindow,   None, True],
                       [u"&Список активных зон\tCtrl+3",            ED.az.showActiveZoneList,   None, False],
                       [u"&Считать активные зоны\tCtrl+4",          ED.az.readActiveZone,       'write16.png', True],
                       [u"&Считать из файла *.gp\tCtrl+5",          GPSfile.readFile,          'readdisk16.png', False],
                       [u"&Записать в файл *.gp\tCtrl+6",           GPSfile.saveFile,           'savedisk16.png', True],
                       [u"&Считать GPS калибровку из ECU\tCtrl+7",  GPS2ECU.GPS2ECU().GPSwriteECU,'write16.png', False],
                       [u"&Загрузить GPS калибровку в ECU\tCtrl+8", GPS2ECU.GPS2ECU().GPSreadECU, 'read16.png', False] )

        self.SetMenuBar(self.menubar)

    # Ручное включение или выключение блока
    def onManualON(self, evt):
        if ED.flag_ECU_ON_VISU:
            self.sendCommandECU( self.manualECUoff )
            ED.flag_ECU_ON_VISU=False
        else:
            self.sendCommandECU( self.manualECUon )
            ED.flag_ECU_ON_VISU = True

    # Посылаем запрос RESET ECU
    def onResetECU(self, evt):
        self.sendCommandECU( self.resetECU, 0)
        time.sleep(2)
        # Закрываем и открываем COM порт после перезагрузки ECU
        self.onDisconnectECU(100)
        self.onConnectECU(1)
        # todo переустановить надпись на заголовке окна с новой скоростью, а лучше ECU перезагружено СОМ такой то
        # todo на скорости такой то

    # Залить заводские установки
    def onFillDefaultCal(self, evt):
        if RW.ReadWriteCalECU().writeCalECU():
            self.sendCommandECU(self.fillDefault)
        else:
            wx.MessageBox(u'Не могу записать пустую калибровку, фабричные значения не записанны.',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

    # Выход из программы
    def onExit(self, evt):
        try:
            ED.thser.close()
        except:
            self.Close()
        else:
            self.Close()

    # Выход из программы
    def mainOnClose(self, evt):
        self.Destroy()

    def onAutoCalPPS(self, event):
        result = Func.msgWarning(ED.main_parent)
        if result == wx.ID_OK:
            ED.pdlgAutocal = wx.ProgressDialog(u"Автокалибровка", u"Команда отправлена в ECU", maximum = 150,
                                               parent=ED.main_parent, style = wx.PD_APP_MODAL)
            self.sendCommandECU( self.autocalON )      # Включить режим автокалибровки PPS

    def onManualCalPPS(self, event):
        self.manualPWM = wx.GetNumberFromUser(u"УСЛОВИЯ ВКЛЮЧЕНИЯ : "
                                              u"конпка и ручное управление ВКЛ, температура редуктора в норме ) :",
                                              u"Введите PWM для установления соответствующего ему напряжения (0..255):",
                                              u"Калибровка PPS в ручном режиме.", value=0, min=0, max=255)
        if self.manualPWM != -1 :
            self.sendCommandECU( self.manualCalPPSon )              # Включить режим ручной калибровки PPS
            time.sleep(1)                                           # пауза обязательна !
            self.sendCommandECU( self.manualPWM )                   # Значение PWM для ручной калибровки

    # Разбираем заголовок в драйвере COM порта и определяем какая плата подключена
    def connectCOMport(self):
        ED.name_cal = u'ПУСТАЯ'
        self.title_str = u'Программа для калибровки ГДС TRIOL. ECU не обнаружено.'
        coms = comports()
        self.flagGoodECU = False
        for com, desc, hwid in coms:
            self.com = com
            if re.search("Arduino Mega", desc):
                self.title_str = u"Программа для калибровки ГДС TRIOL. ECU типа: M " + u'на COM порту: ' + com
            elif re.search("Arduino Uno", desc):
                self.title_str = u"Программа для калибровки ГДС TRIOL. ECU типа: U " + u'на COM порту: ' + com
            elif re.search("Arduino Nano", desc):
                self.title_str = u"Программа для калибровки ГДС TRIOL. ECU типа: N " + u'на COM порту: ' + com
            elif re.search("Arduino", desc):
                self.title_str = u"Программа для калибровки ГДС TRIOL. ECU типа: ?(а) " + u'на COM порту: ' + com
            elif re.search("USB", desc):
                self.title_str = u"Программа для калибровки ГДС TRIOL. ECU типа: ? " + u'на COM порту: ' + com
            else: break

            self.onConnectECU( 1 )

    # Настройка размеров окон под различные разрешения экрана
    def tuneScreenSize(self):
        self.screenSize = wx.DisplaySize()
        if self.screenSize == (1600, 900):
            ED.CalWindowSize        = (1600, 853)   # Окно калибровок
            ED.calWinButtonOffset   = 1220          # Смещение для положения кнопок ОК в калибровочной таблице
            ED.calGridLabelFont     = 10            # Шрифт для заголовков в калибровочной таблице
            ED.calGridCellFont      = 11            # Шрифт для ячеек в калибровочной таблице
            ED.colSize              = 32            # Ширина колонок в пикселях для калибровочных таблиц
            ED.rowSize              = 23            # Ширина СТОЛЮЦОВ в пикселях для калибровочных таблиц
        elif self.screenSize == (1360, 768) or self.screenSize == (1366, 768) or self.screenSize == (1440, 900):
            ED.CalWindowSize        = (1360, 768)   # Окно калибровок
            ED.calWinButtonOffset   = 850           # Смещение для положения кнопок ОК в калибровочной таблице
            ED.calGridLabelFont     = 8             # Шрифт для заголовков в калибровочной таблице
            ED.calGridCellFont      = 11            # Шрифт для ячеек в калибровочной таблице
            ED.colSize              = 27            # Ширина колонок в пикселях для калибровочных таблиц
            ED.rowSize              = 20            # Ширина СТОЛЮЦОВ в пикселях для калибровочных таблиц
        elif self.screenSize[0] < 1024 or self.screenSize[1] < 768:
            print u"Разрешения мешьше 1024х768 программой не поддерживаются"
            exit(1)
        else:
            ED.CalWindowSize        = (1024, 768)   # Окно калибровок
            ED.calWinButtonOffset   = 580           # Смещение для положения кнопок ОК в калибровочной таблице
            ED.calGridLabelFont     = 6             # Шрифт для заголовков в калибровочной таблице
            ED.calGridCellFont      = 8             # Шрифт для ячеек в калибровочной таблице
            ED.colSize              = 20            # Ширина колонок в пикселях для калибровочных таблиц
            ED.rowSize              = 19            # Ширина СТОЛЮЦОВ в пикселях для калибровочных таблиц

    # Закрываем СОМ порт
    def onDisconnectECU(self, evt):
        try:
            ED.thser.close()
        except:
            wx.Bell()
            wx.MessageBox(u"Не удается закрыть СОМ порт." + self.com, caption=u"Сообщение о проблемах",
                          style=wx.OK | wx.ICON_ERROR)
        else:
            if evt != 100 : # Что тбы при перегрузке ECU не доставало сообщениями
                wx.MessageBox(self.com + u" порт закрыт.", caption=u"Информация")

    # Включение режима тестирования форсунок
    def onTestINJ_ON(self, event ):
        INJ_test_setup = wx.GetNumberFromUser(u"УСЛОВИЯ ВКЛЮЧЕНИЯ :"
                                              u"конпка и ручное управление ВКЛ, температура редуктора в норме ) :",
                                              u" "u"Длительность открытия форсунок ( значение 0..230 ):",
                                              u"Тестирование форсунок", value=0, min=0, max=230)
        if INJ_test_setup != -1:
            self.sendCommandECU( self.testINJon )  # Команда ECU перейти в режим тестирования форсунок
            time.sleep(1)
            self.sendCommandECU( INJ_test_setup )

class mainFrame_MEGA(MainFrame):
    def __init__(self):
        MainFrame.__init__(self)
        # Создаем меню для работ с калибровкой
        self.createMenu(RW.ReadWriteCalECU_MEGA().readCalECU, RW.ReadWriteCalECU_MEGA().writeCalECU)

        # Запускаем ту или иную версию приборной панели в зависимости от размер экрана
        if ED.mainPriborSize == (1024, 768):
            GP.GeneralPriborWindow_MEGA_1024(self)
        elif ED.mainPriborSize == (1600, 900):
            GP.GeneralPriborWindow_MEGA_1600(self)
        else:
            GP.GeneralPriborWindow_MEGA_1366(self)

        # Если в настройках программы выставленно автосчитывание калибровки
        if self.flagGoodECU and ED.prog_setup['typeRedCal'] == 0:
            RW.ReadWriteCalECU_MEGA().readCalECU(1)

    def tuneScreenSize(self):
        MainFrame.tuneScreenSize(self)
        if self.screenSize == (1600, 900):
            ED.mainPriborSize = (1600, 900)  # Главный экран
        elif self.screenSize == (1360, 768) or self.screenSize == (1366, 768) or self.screenSize == (1440, 900):
            ED.mainPriborSize = (1360, 768)  # Главный экран
        else:
            ED.mainPriborSize = (1024, 768)  # Главный экран

    # Открываем COM порт
    def onConnectECU(self, evt):
        try:
            ED.thser = TH.ThSerial_MEGA(self.com, ED.prog_setup['comSpeedReal'] )
        except:
            wx.Bell()
            wx.MessageBox(u"ECU подключено, но связь неможет быть установлена,"
                          u" возможно запущено несколько экземляров программы."
                          u"Работа программы будет прекращена.",
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
        else:
            self.title_str = self.title_str + u' ECU подключено на скорости, порт открыт. '\
                             +str( ED.prog_setup['comSpeedReal'])
            self.flagGoodECU = True
            return

class mainFrame_NANO(MainFrame):
    def __init__(self):
        MainFrame.__init__(self)
        # Создаем меню для работ с калибровкой
        self.createMenu(RW.ReadWriteCalECU_NANO().readCalECU, RW.ReadWriteCalECU_NANO().writeCalECU)
        # Запускаем ту или иную версию приборной панели в зависимости от размер экрана
        GP.GeneralPriborWindow_NANO(self)
        # Если в настройках программы выставленно автосчитывание калибровки
        if self.flagGoodECU and ED.prog_setup['typeRedCal'] == 0:
            RW.ReadWriteCalECU_NANO().readCalECU()

    def tuneScreenSize(self):
        MainFrame.tuneScreenSize( self )
        if self.screenSize == (1600, 900):
            ED.mainPriborSize = (1024, 768)  # Главный экран
        elif self.screenSize == (1360, 768) or self.screenSize == (1366, 768) or self.screenSize == (1440, 900):
            ED.mainPriborSize = (1024, 768)  # Главный экран
        else:
            ED.mainPriborSize = (1024, 768)  # Главный экран

    # Открываем COM порт
    def onConnectECU(self, evt):
        try:
            ED.thser = TH.ThSerial_NANO(self.com, ED.prog_setup['comSpeedReal'])
        except:
            wx.Bell()
            wx.MessageBox(u"Не удается открыть СОМ порт." + self.com, caption=u"Сообщение о проблемах",
                          style=wx.OK | wx.ICON_ERROR)

    # Открываем COM порт  во время первого подключения
    def tryFirstConnectECU(self):
        try:
            ED.thser = TH.ThSerial_NANO(self.com, ED.prog_setup['comSpeedReal'])
        except:
            self.title_str = self.title_str + u' ECU не подключено, порт не открыт.'
        else:
            self.title_str = self.title_str + u' ECU подключено, порт открыт.'
            self.flagGoodECU = True

if __name__ == '__main__':

    class MyApp(wx.App):
        def OnInit(self):
            # Безопасно считываем файл настроек
            Func.readSetupFile()
            #----------------------------------------------------------------------
            # We first have to set an application-wide help provider.  Normally you
            # would do this in your app's OnInit or in other startup code...
            # Запускаем ту или иную версию приборной панели в зависимости от размер экрана
            if ED.prog_setup['typeECU'] == 0:
                frame = mainFrame_MEGA()
            elif ED.prog_setup['typeECU'] == 1:
                frame = mainFrame_NANO()
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
    app = MyApp(False)
    app.MainLoop()





