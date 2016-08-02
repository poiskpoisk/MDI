# -*- coding: utf-8 -*-
__author__ = 'AMA'

import os
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
from gps import GPSactiveZone
from gps import GPSfile
from gps import GPSzone

from mixin import Func
from mixin import ParseMixin

from setup import GeneralSetup
from setup import ProgramSetup
from setup import TableSetup
from setup import GPS_Setup


class MainFrame(wx.MDIParentFrame, ParseMixin.Parse):

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
        # ----------------------------------------------------------------------
        ID_Gas_cal = wx.NewId(); ID_Diesel_cal = wx.NewId(); ID_Osnova_cal = wx.NewId()
        ID_General_setup = wx.NewId(); ID_Grid_setup = wx.NewId(); ID_Read_cal = wx.NewId()
        ID_Write_cal = wx.NewId(); ID_Exit = wx.NewId(); ID_Connect = wx.NewId()
        ID_ReadECU_cal = wx.NewId(); ID_WriteECU_cal = wx.NewId(); ID_Disconnect = wx.NewId()
        ID_ECU_reset = wx.NewId(); ID_INJ_test_ON = wx.NewId(); ID_autocal_PPS = wx.NewId()
        ID_manualcal_PPS = wx.NewId(); ID_program_setup = wx.NewId(); ID_defaultCal =wx.NewId()
        ID_manual_ON = wx.NewId(); ID_GPSlistZone = wx.NewId(); ID_GPSreadFile = wx.NewId()
        ID_GPSsaveFile = wx.NewId(); ID_GPSWriteECU_cal  = wx.NewId(); ID_GPSReadECU_cal  = wx.NewId()
        ID_GPS_setup = wx.NewId();ID_GPS_activeZone = wx.NewId();ID_GPS_activeZoneList = wx.NewId()

        # ----------------------------------------------------------------------

        # Создаем меню для работ с калибровкой
        cal_menu = wx.Menu()

        osnovaItem = wx.MenuItem(cal_menu, ID_Osnova_cal, u"&Калибровка ГАЗ основа\tCtrl+B")
        img = wx.Image(os.getcwd() + '\pic\\gas16.png', wx.BITMAP_TYPE_ANY)
        osnovaItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(osnovaItem)

        gasItem = wx.MenuItem(cal_menu, ID_Gas_cal, u"&Калибровка ГАЗ\tCtrl+G")
        img = wx.Image(os.getcwd() + '\pic\\gas16.png', wx.BITMAP_TYPE_ANY)
        gasItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(gasItem)

        dieselItem = wx.MenuItem(cal_menu, ID_Diesel_cal, u"&Калибровка ДИЗЕЛЬ\tCtrl+D")
        img = wx.Image(os.getcwd() + '\pic\\oil16.png', wx.BITMAP_TYPE_ANY)
        dieselItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(dieselItem)

        cal_menu.AppendSeparator()

        readDiskItem = wx.MenuItem(cal_menu, ID_Read_cal, u"&Считать из файла *.py\tCtrl+L")
        img = wx.Image(os.getcwd() + '\pic\\readdisk16.png', wx.BITMAP_TYPE_ANY)
        readDiskItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(readDiskItem)

        saveDiskItem = wx.MenuItem(cal_menu, ID_Write_cal, u"&Записать в файл *.py\tCtrl+S")
        img = wx.Image(os.getcwd() + '\pic\\savedisk16.png', wx.BITMAP_TYPE_ANY)
        saveDiskItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(saveDiskItem)

        cal_menu.AppendSeparator()

        readECUItem = wx.MenuItem(cal_menu, ID_ReadECU_cal, u"&Считать калибровку из ECU\tCtrl+O")
        img = wx.Image(os.getcwd() + '\pic\\write16.png', wx.BITMAP_TYPE_ANY)
        readECUItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(readECUItem)

        writeECUItem = wx.MenuItem(cal_menu, ID_WriteECU_cal, u"&Загрузить калибровку в ECU\tCtrl+W")
        img = wx.Image(os.getcwd() + '\pic\\read16.png', wx.BITMAP_TYPE_ANY)
        writeECUItem.SetBitmap(wx.BitmapFromImage(img))
        cal_menu.AppendItem(writeECUItem)

        # Создаем меню для опций и натсроек
        setup_menu = wx.Menu()
        setup_menu.Append(ID_General_setup, u"&Основные\tCtrl+E")
        setup_menu.Append(ID_Grid_setup, u"&Табличные\tCtrl+T")
        setup_menu.Append(ID_program_setup, u"&Програмные\tCtrl+P")

        # Создаем меню для работы с ECU
        ECU_menu = wx.Menu()
        ECU_menu.Append(ID_Connect, u"&Открыть COM порт")
        ECU_menu.Append(ID_Disconnect, u"&Закрыть COM порт")
        ECU_menu.AppendSeparator()
        manualItem = wx.MenuItem(ECU_menu, ID_manual_ON, u"&ECU ВКЛ/ВЫКЛ\tCtrl+Z")
        img = wx.Image(os.getcwd() + '\pic\\on-off16.png', wx.BITMAP_TYPE_ANY)
        manualItem.SetBitmap(wx.BitmapFromImage(img))
        ECU_menu.AppendItem(manualItem)
        ECU_menu.AppendSeparator()
        resetItem = wx.MenuItem(ECU_menu, ID_ECU_reset, u"&Перегрузить ECU\tCtrl+R")
        img = wx.Image(os.getcwd() + '\pic\\reset1616.gif', wx.BITMAP_TYPE_ANY)
        resetItem.SetBitmap(wx.BitmapFromImage(img))
        ECU_menu.AppendItem(resetItem)
        ECU_menu.Append(ID_defaultCal, u"&Заводские установки")
        ECU_menu.AppendSeparator()
        ECU_menu.Append(ID_Exit, u"&Выход\tCtrl+X")

        # Создаем меню для работы с форсунками
        INJ_menu = wx.Menu()
        INJ_menu.Append(ID_INJ_test_ON, u"&Тестирование форсунок.")
        # Создаем меню для работы с настройками PPS
        PPS_menu = wx.Menu()
        PPS_menu.Append(ID_autocal_PPS, u"&Автоматическая калибровка PPS")
        PPS_menu.Append(ID_manualcal_PPS, u"&Ручная калибровка PPS")

        # Создаем меню для работы c GPS
        GPS_menu = wx.Menu()
        GPS_menu.Append(ID_GPSlistZone, u"&Список зон\tCtrl+1")
        GPS_menu.Append(ID_GPS_setup, u"&Настройки\tCtrl+2")
        GPS_menu.AppendSeparator()
        GPS_menu.Append(ID_GPS_activeZoneList, u"&Список активных зон\tCtrl+3")
        readActiveZoneGPS = wx.MenuItem(GPS_menu, ID_GPS_activeZone, u"&Считать активные зоны\tCtrl+4")
        img = wx.Image(os.getcwd() + '\pic\\write16.png', wx.BITMAP_TYPE_ANY)
        readActiveZoneGPS.SetBitmap(wx.BitmapFromImage(img))
        GPS_menu.AppendItem(readActiveZoneGPS)

        GPS_menu.AppendSeparator()

        readDiskItemGPS = wx.MenuItem(GPS_menu, ID_GPSreadFile, u"&Считать из файла *.gp\tCtrl+5")
        img = wx.Image(os.getcwd() + '\pic\\readdisk16.png', wx.BITMAP_TYPE_ANY)
        readDiskItemGPS.SetBitmap(wx.BitmapFromImage(img))
        GPS_menu.AppendItem(readDiskItemGPS)

        saveDiskItemGPS = wx.MenuItem(GPS_menu, ID_GPSsaveFile, u"&Записать в файл *.gp\tCtrl+6")
        img = wx.Image(os.getcwd() + '\pic\\savedisk16.png', wx.BITMAP_TYPE_ANY)
        saveDiskItemGPS.SetBitmap(wx.BitmapFromImage(img))
        GPS_menu.AppendItem(saveDiskItemGPS)

        GPS_menu.AppendSeparator()

        GPSreadECUItem = wx.MenuItem(GPS_menu, ID_GPSReadECU_cal, u"&Считать GPS калибровку из ECU\tCtrl+7")
        img = wx.Image(os.getcwd() + '\pic\\write16.png', wx.BITMAP_TYPE_ANY)
        GPSreadECUItem.SetBitmap(wx.BitmapFromImage(img))
        GPS_menu.AppendItem(GPSreadECUItem)

        GPSwriteECUItem = wx.MenuItem(GPS_menu, ID_GPSWriteECU_cal, u"&Загрузить GPS калибровку в ECU\tCtrl+8")
        img = wx.Image(os.getcwd() + '\pic\\read16.png', wx.BITMAP_TYPE_ANY)
        GPSwriteECUItem.SetBitmap(wx.BitmapFromImage(img))
        GPS_menu.AppendItem(GPSwriteECUItem)

        # Добавляем на меню бар все меню
        menubar = wx.MenuBar()
        menubar.Append(ECU_menu, u"&Блок управления")
        menubar.Append(cal_menu, u"&Калибровки")
        menubar.Append(setup_menu, u"&Настройки")
        menubar.Append(PPS_menu, u"&Педаль газа")
        menubar.Append(INJ_menu, u"&Форсунки")
        menubar.Append(GPS_menu, u"&GPS")

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, DieselGasCalWindow.GasCalWindow,       id=ID_Gas_cal)
        self.Bind(wx.EVT_MENU, DieselGasCalWindow.OsnovaGasCalWindow, id=ID_Osnova_cal)
        self.Bind(wx.EVT_MENU, DieselGasCalWindow.DieselCalWindow,    id=ID_Diesel_cal)

        self.Bind(wx.EVT_MENU, GeneralSetup.GeneralSetupWindow, id=ID_General_setup)
        self.Bind(wx.EVT_MENU, TableSetup.TableSetup,           id=ID_Grid_setup)
        self.Bind(wx.EVT_MENU, ProgramSetup.programSetupWindow, id=ID_program_setup)

        self.Bind(wx.EVT_MENU, ReadWriteCalDisk.onCalWrite, id=ID_Write_cal)
        self.Bind(wx.EVT_MENU, ReadWriteCalDisk.onCalRead,  id=ID_Read_cal)

        self.Bind(wx.EVT_MENU, self.onAutoCalPPS,        id=ID_autocal_PPS)
        self.Bind(wx.EVT_MENU, self.onManualCalPPS,      id=ID_manualcal_PPS)

        self.Bind(wx.EVT_MENU, funcWriteECU, id=ID_WriteECU_cal)
        self.Bind(wx.EVT_MENU, funcReadECU,  id=ID_ReadECU_cal)

        self.Bind(wx.EVT_MENU, self.onConnectECU,     id=ID_Connect)
        self.Bind(wx.EVT_MENU, self.onDisconnectECU,  id=ID_Disconnect)
        self.Bind(wx.EVT_MENU, self.onManualON,       id=ID_manual_ON)
        self.Bind(wx.EVT_MENU, self.onResetECU,       id=ID_ECU_reset)
        self.Bind(wx.EVT_MENU, self.onFillDefaultCal, id=ID_defaultCal)

        self.Bind(wx.EVT_MENU, self.onTestINJ_ON,   id=ID_INJ_test_ON)

        self.Bind(wx.EVT_MENU, GPSzone.ZoneList,                              id=ID_GPSlistZone )
        self.Bind(wx.EVT_MENU, GPS_Setup.SetupGPSWindow, id=ID_GPS_setup)
        self.Bind(wx.EVT_MENU, ED.az.showActiveZoneList, id=ID_GPS_activeZoneList )
        self.Bind(wx.EVT_MENU, ED.az.readActiveZone,     id=ID_GPS_activeZone)
        self.Bind(wx.EVT_MENU, GPSfile.readFile,                              id=ID_GPSreadFile)
        self.Bind(wx.EVT_MENU, GPSfile.saveFile,                              id=ID_GPSsaveFile)
        self.Bind(wx.EVT_MENU, GPS2ECU.GPS2ECU().GPSwriteECU,                 id=ID_GPSWriteECU_cal)
        self.Bind(wx.EVT_MENU, GPS2ECU.GPS2ECU().GPSreadECU,                  id=ID_GPSReadECU_cal)


        self.Bind(wx.EVT_MENU, self.onExit, id=ID_Exit)

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





