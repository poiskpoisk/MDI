# -*- coding: utf-8 -*-#
__author__ = 'AMA'

# Аналоговые красивые приборы

import os
import random
import wx
import wx.gizmos
import ECUdata as ED

from mixin import OutputMixin as OM
from mixin import ParseMixin




# Минимальный набор переменных и функций, общий для МЕГА и НАНО
class GeneralPriborWindow(wx.MDIChildFrame, OM.OutputMixin, ParseMixin.ReadECU ):
    ED.flag_ECU_ON_VISU    = False
    ED.flag_Relay          = False  # Сигнал включения главного реде, аналог gRELAY в ESX

    # Определяем данные общие для всех типов ECU
    def __init__(self, parent):

        self.err_green  = wx.Image(os.getcwd() + "\pic\\green_small.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.err_red    = wx.Image(os.getcwd() + "\pic\\red_small.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        self.parent = parent
        # ************************************* Данные из ECU ************************************
        # -- ФЛАГИ ошибок одинаковые для NANO и MEGA ----
        self.flag_block_ON  = False  # Нажатая кнопки, включения блока

        self.flag_red_temp  = False  # Ошибки по температуре
        self.flag_RPM       = False  # ошибка по RPM
        self.flag_PPS       = False  # Ошибки: PPS
        self.flag_EGT       = False  # максимальный EGT

        # --- ДАННЫЕ одинаковые для NANO и MEGA  -----
        self.RPM = self.Turbo = 1234
        # Подача газа
        self.Gas = 12
        # родные сигналы от педали
        self.PPS1 = self.PPS2 = 12
        # Соотношение родных сигналов PPS1/PPS2
        self.PPS1PPS2 = 12
        # Расчетное замещение, вычисляется расчетным путем и служит ТОЛЬКО для индикации
        self.K_emul = 12
        # сPPS1 и cPPS2 фактические значения эмуляции
        self.PPS1emul = self.PPS2emul = 12
        # Соотношение эмулированных сигналов cPPS1/cPPS2
        self.PPS1PPS2emul = 12
        # Расчетная эмуляция дизеля, получаемая из калибровочной таблицы и поправочных коэффициентов
        self.Emul = 12
        # Температура выхлопа и поправочные коэффициенты, вычисляемые на базе темп. выхлопа
        self.EGT = self.EGT_gas = 12
        # Для вывола отладочной информации
        self.Test_val = 0
        self.gasPPSmax = 100  # Подача газа при максимальном PPS
        self.timeCycle = 100  # Время работы главного цикла в ECU


        self.showPribor()

        # Устанавливаем таймер для преобразования блока данных, полученных из ком порта в переменные
        self.getDataTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.getData, self.getDataTimer)
        self.getDataTimer.Start(300)

    # Вывести окно ( БАЗОВЫЙ ВИД - 3 КОЛОНКИ )и дернуть функции отрисовывающие колонки
    def showPribor(self):
        wx.MDIChildFrame.__init__(self, self.parent, -1, u"Стандартная приборная панель", pos=(0, 0),
                                  size=ED.mainPriborSize, style=wx.MAXIMIZE)
        self.SetBackgroundColour(wx.SystemSettings_GetColour(0))

        # Минимальный набо информации размещается в 3-х колонках шириной 1024 пикселя
        # При необходимости дочернии классы раширяют его до 5 колонок
        self.main_sz = wx.BoxSizer(wx.HORIZONTAL)
        first_sizer     = self.firstColumn()  # Первая колонка
        second_sizer    = self.secondColumn() # Вторая колонка
        third_sizer     = self.thirdColumn()  # Третяя колонка

        self.main_sz.Add(first_sizer,    0, wx.LEFT  | wx.RIGHT | wx.ALIGN_TOP, 10)
        self.main_sz.Add(second_sizer,   0, wx.RIGHT | wx.ALIGN_TOP, 15)
        self.main_sz.Add(third_sizer,    0, wx.LEFT  | wx.ALIGN_TOP, 10)

        self.SetSizer(self.main_sz)

    # 1 и 2 колонка одинаковые для всех классов приборов, остальные колонки реализованны в конкретных классах
    def firstColumn(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gaugeRPM(sizer, self.RPM)  # Комплектный прибор RPM с подписью
        # Индикатор подачи газа
        self.gGAS = self.Item_gauge(240, wx.LEFT | wx.TOP | wx.ALIGN_TOP | wx.ALIGN_RIGHT, u'ГАЗ: {:.0f}', sizer,
                                    0, False, sizeGauge=(300, 60), fontSize=28, txtColor=wx.RED)
        sizer.Add((0, 10))  # Пустое пространство
        self.stGasPPSmax = self.Item_simple(u'ГАЗ по калибровке:' + str(self.gasPPSmax), sizer)
        self.gaugeTurbo(sizer, self.Turbo)  # Комплектный прибор Turbo с подписью

        return sizer

    def secondColumn(self):
        second_sizer = wx.BoxSizer(wx.VERTICAL)
        second_sizer.Add((0, 10))  # Пустое пространство
        # ======================= PPS фактический ===================================
        self.gPPS1 = self.Item_gauge(10000, wx.LEFT | wx.TOP | wx.ALIGN_TOP | wx.ALIGN_RIGHT, 'PPS1 {:.0f} mV',
                                     second_sizer, 20, False)
        self.gPPS2 = self.Item_gauge(10000, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_TOP | wx.ALIGN_RIGHT,
                                     'PPS2 {:.0f} mV',
                                     second_sizer, 15, False)
        self.stPPS1PPS2 = self.Item_simple(u'PPS1/PPS2 :  ' + str('%5.2f' % self.PPS1PPS2), second_sizer)
        # ======================= PPS эмуляция ===============================
        self.gPPS1emul = self.Item_gauge(10000, wx.LEFT | wx.TOP | wx.ALIGN_TOP | wx.ALIGN_RIGHT, u'PPS1 эм. {:.0f} mV',
                                         second_sizer, 30, False)
        self.gPPS2emul = self.Item_gauge(10000, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_TOP | wx.ALIGN_RIGHT,
                                         u'PPS2 эм. {:.0f} mV', second_sizer, 15, False)
        self.stPPS1PPS2e = self.Item_simple(u'PPS1/PPS2 эмул:  ' + str('%5.2f' % self.PPS1PPS2emul), second_sizer)
        # ======================= Коэффициент эмуляции и расчетное значение эмуляции ===============================
        self.gKemul = self.Item_gauge(150, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_TOP | wx.ALIGN_RIGHT,
                                      u'Эмуляция {:.0f} %',
                                      second_sizer, 15, False, txtColor=wx.RED)
        self.ledemul = self.Item_gauge(10000, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_TOP | wx.ALIGN_RIGHT,
                                       u'PPS1 расч. {:.0f} mV',
                                       second_sizer, 15, False)
        return second_sizer

    # Третья колонка иммет специфичный вид
    def thirdColumn(self):
        third_sizer = wx.BoxSizer(wx.VERTICAL)
        self.gaugeEGT( third_sizer )    # Циферблат EGT с подписью и коэффициентами
        third_sizer.Add((0, 5))         # Пустое пространство
        self.nanoErr( third_sizer )     # 4 ошибки для NANO ( минимум, который будет расширятся для МЕГИ )
        third_sizer.Add((0, 10))        # Пустое пространство
        self.nanoLampsAndButton( third_sizer )
        return third_sizer

    # Ручное включение/выключение блока (55/77)
    def OnClickButtonManual(self, event):
        if ED.flag_ECU_ON_VISU:
            self.sendCommandECU( self.manualECUoff )
        else:
            self.sendCommandECU( self.manualECUon)

    # Вызывается по таймеру и РАЗБИРАЕТ ОПЕРАТИТВНУЮ ИНФОРМАЦИЮ, а потом обновляет ее
    def getData(self, event):
        try:
            dataFromECU = ED.thser.dataECU()
        except:
            self.getRandomValue()
        else:
            if len(dataFromECU) > 0 : self.parseData( dataFromECU )
            else: print u'Пакет нулевой длины получен из ECU'
        self.update()

    # Эмуляция поступивших значений из ECU для "жизни" когда ECU не поделючено
    def getRandomValue(self):
        self.RPM    = random.randint(500, 3000)
        self.Turbo  = random.randint(1000, 3000)
        self.Gas    = random.randint(1, 200)

        self.K_emul = random.randint(10, 50)  # Коэффициент эмуляции
        # Второй сизер
        self.PPS1           = random.randint(1000, 4000)
        self.PPS2           = random.randint(1000, 4000)
        self.PPS1PPS2       = float(self.PPS1)/self.PPS2
        self.PPS1emul       = random.randint(1000, 4500)
        self.PPS2emul       = self.PPS1emul / 2
        self.PPS1PPS2emul   = random.uniform(0.5, 2.5)
        self.Emul           = random.randint(0, 2500)  # Эмяляция расчетная
        self.Test_val       = random.randint(0, 2500)
        self.timeCycle      = random.randint(0, 2500)

        self.EGT        = random.randint(100, 450)
        self.EGT_gas    = random.uniform(0.5, 1.5)
        self.EGT_diesel = random.uniform(0.5, 1.5)

        self.gasPPSmax = random.randint(0, 255)

        self.flag_EGT       = random.choice([True, False])
        self.flag_PPS       = random.choice([True, False])
        self.flag_RPM       = random.choice([True, False])
        self.flag_red_temp  = random.choice([True, False])

        self.flag_block_ON = random.choice([True, False])
        ED.flag_Relay = random.choice([True, False])
        ED.flag_ECU_ON_VISU = random.choice([True, False])

    # Обновляет экранные значения общие для МЕГА и НАНО( минимальный ОБЩИЙ набор )
    def update(self):
        # Первая колонка
        self.saveUpdateCircleGauge(self.prRPM, self.RPM / 100)
        self.stRPM.SetLabel(str(self.RPM))
        self.saveUpdateLineGauge(self.gGAS, self.Gas)
        self.saveUpdateCircleGauge(self.prTurbo, self.Turbo / 100)
        self.stTurbo.SetLabel(str(self.Turbo))
        # Вторая колонка
        self.saveUpdateLineGauge(self.gPPS1, self.PPS1)
        self.saveUpdateLineGauge(self.gPPS2, self.PPS2)
        self.stPPS1PPS2.SetLabel(u'PPS1/PPS2 :  ' + str('%5.2f' % self.PPS1PPS2))
        self.saveUpdateLineGauge(self.gPPS1emul, self.PPS1emul)
        self.saveUpdateLineGauge(self.gPPS2emul, self.PPS2emul)
        self.stPPS1PPS2e.SetLabel(u'PPS1/PPS2 эмул:  ' + str('%5.2f' % self.PPS1PPS2emul))
        self.saveUpdateLineGauge(self.ledemul, self.Emul)
        self.saveUpdateLineGauge(self.gKemul, self.K_emul)

        self.stTest.SetLabel(u'Служебное :' + str(self.Test_val))
        self.stGasPPSmax.SetLabel(u'ГАЗ по калибровке:' + str(self.gasPPSmax))
        self.stTimeCycle.SetLabel(u'T цикла (мкс):' + str(self.timeCycle))

        # Третья колонка
        self.stegtp.SetLabel(str(self.EGT))
        self.stEGTGK.SetLabel(u'Газ кор.: ' + str('%5.2f' % self.EGT_gas))

        self.bitmapTriger(self.flag_red_temp, self.err_green, self.err_red, self.errRedTemp)
        self.bitmapTriger(self.flag_EGT, self.err_green, self.err_red, self.errEGT)
        self.bitmapTriger(self.flag_RPM, self.err_green, self.err_red, self.errRPM)
        self.bitmapTriger(self.flag_PPS, self.err_green, self.err_red, self.errPPS)

        # Индикатор включения кнопки
        self.bitmapTriger(self.flag_block_ON, self.green, self.red, self.b_knopka)
        self.bitmapTriger(ED.flag_Relay, self.green, self.red, self.b_block)
        self.bitmapTriger(ED.flag_ECU_ON_VISU, self.green, self.red, self.b_manual)

class GeneralPriborWindow_NANO(GeneralPriborWindow):

    def __init__(self, parent):
        # Если появятся данные, специфичные для NANO их определять тут
        GeneralPriborWindow.__init__( self, parent)

    def secondColumn(self):
        sizer = GeneralPriborWindow.secondColumn( self )
        sizer.Add((20, 45))  # Пустое пространство
        self.stGasPPSmax = self.Item_simple(u'ГАЗ по калибровке:' + str(self.gasPPSmax), sizer)
        self.stTimeCycle = self.Item_simple(u'Время цикла (мкс):' + str(self.timeCycle), sizer)
        self.stTest = self.Item_simple(u'Служебное:' + str(self.Test_val), sizer)
        return sizer

    def update(self):
        GeneralPriborWindow.update(self)
        # Расширяет обновление специфичными для НАНО приборами
        self.saveUpdateCircleGauge(self.meterEGT, self.EGT)

class GeneralPriborWindow_MEGA_1024(GeneralPriborWindow):

    # Определяет данные специфичные для МЕГА. Данные едины для всех экранных разрешений
    def __init__(self, parent):

        # 3 дополнительных флага ошибок
        self.flag_red_press = False         # Давлению редуктора
        self.flag_speed     = False         # Скорость
        self.flag_cLiq      = False         # Охлаждающая жидкость

        self.flagGPS_ON                     = False         # Включение GPS
        self.flagGPS_NO_START_COORDINATE    = False
        self.flagGPS_NO_DATA                = False
        self.flagGPS_FORWARD                = False

        self.Reductor_press = self.Reductor_temp = self.Cylinder_press = 12

        # Физическая скорость и поправочные коэффициенты, вычисляемые на базе скорости
        self.Speed  = self.Speed_gas = self.Speed_diesel = 12
        self.cLiq   = 12 # Температура охлаждающей жидкости
        self.SAT    = 5

        self.LON = '123.123456'  # Текущие координаты ДОЛГОТА
        self.LAT = '23.123456'  # Текущие координаты ШИРОТА

        self.activeZoneLON = '123.123456'  # Координаты активной зоны ДОЛГОТА
        self.activeZoneLAT = '23.123456'  # Координаты активной зоны ШИРОТА
        self.activeZoneDistance = '1000'  # Текущее расстояние до центра активной зоны

        self.zeroPointLON = '123.123456'  # Координаты точки отсчета ДОЛГОТА
        self.zeroPointLAT = '23.123456'  # Координаты точки отсчета ШИРОТА
        self.zeroPointDistance = '1000'  # Текущее расстояние до точки отсчета

        self.Upower     = 24                # Напряжение питания
        self.loadPress  = 1000              # Давление в пневмоподвеске

        self.GPSgas     = 100
        self.GPSdiesel  = 100

        self.loadGas    = 100
        self.loadDiesel = 100

        self.flagLOG_ON = False

        # Определяем данные для всех типов ECU путем вызова конструктора базового класса и запускаем дальнейшую работу
        GeneralPriborWindow.__init__(self, parent)

    # Случайные значения, что юы была видимость работы, когда ECU не подключено.
    def getRandomValue(self):
        # Общие для МГА и НАНО значения
        GeneralPriborWindow.getRandomValue(self)

        # Добавляем специфичные для МЕГИ значения
        self.Speed          = random.randint(0, 100)
        self.Speed_gas      = random.uniform(0.5, 1.5)
        self.Speed_diesel   = random.uniform(0.5, 1.5)

        self.Reductor_press = random.randint(100, 2500)
        self.Cylinder_press = random.randint(1800, 3200)
        self.Reductor_temp  = random.randint(0, 300)

        self.cLiq = random.randint(0, 100)

        self.flag_red_press = random.choice([True, False])
        self.flag_speed     = random.choice([True, False])
        self.flag_cLiq      = random.choice([True, False])

        self.SAT = random.randint(0, 15)
        self.Upower = random.randint(5, 80)

    def secondColumn(self):
        sizer = GeneralPriborWindow.secondColumn(self)
        sizer.Add((20, 0))  # Пустое пространство
        fontSize=(15,18)
        self.stTimeCycle    = self.Item_simple(u'Время цикла (мкс):' + str(self.timeCycle)   , sizer, fontsize=16 )
        self.stTest         = self.Item_simple(u'Служебное:'         + str(self.Test_val)    , sizer, fontsize=16 )
        self.hipress_item   = self.itemLine(u'P баллоны: ',     str(self.Cylinder_press)     , sizer, fontsize=fontSize)
        self.sttr           = self.itemLine(u"Т редуктора: ",   str(self.Reductor_temp)      , sizer, fontsize=fontSize)
        self.sttb           = self.itemLine(u"P редуктора: ",   str(self.Reductor_press)     , sizer, fontsize=fontSize)
        self.stColLiq       = self.itemLine(u"Охл. жидкость: ", str(self.cLiq), sizer, fontsize=fontSize)
        self.stUpower       = self.itemLine(u"U питания ",      str(self.Upower), sizer, fontsize=fontSize)
        return sizer

    # Третья колонка иммет специфичный вид
    def thirdColumn(self):
        third_sizer = wx.BoxSizer(wx.VERTICAL)
        # ===================== Скорость подпись =======================================================
        spp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.spp = self.Item(u"Скорость", str(self.Speed), 20, 26, (0, 0, 0), spp_sizer)
        third_sizer.Add(spp_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 30)
        self.stSG = self.Item_simple(u'Газ кор.: ' + str(self.Speed_gas), third_sizer, padding=60)
        self.stSD = self.Item_simple(u'ДТ кор. : ' + str(self.Speed_diesel), third_sizer, padding=60)
        third_sizer.Add((0, 15))  # Пустое пространство
        # ===================== EGT подпись =======================================================
        egtp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stegtp = self.Item(u"  EGT", str(self.EGT), 20, 26, (0, 0, 0), egtp_sizer)
        third_sizer.Add(egtp_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)
        self.stEGTGK = self.Item_simple(u'Газ кор.: ' + str(self.EGT_gas), third_sizer, padding=60)
        third_sizer.Add((0, 15))  # Пустое пространство
        self.fullSetErr(third_sizer)    # Полный набор маленьких индикаторов об ошибках
        self.nanoLampsAndButton( third_sizer )
        return  third_sizer

    # Обновляет экранные значения
    def update(self):
        # Обновляет экранные значения общие для МЕГА и НАНО( минимальный ОБЩИЙ набор )
        GeneralPriborWindow.update(self)
        # Расширяет обновление специфичными для МЕГИ  приборами

        self.spp.SetLabel(str(self.Speed))
        self.stSG.SetLabel(u'Газ кор.: ' + str('%5.2f' % self.Speed_gas))
        self.stSD.SetLabel(u'ДТ кор. : ' + str('%5.2f' % self.Speed_diesel))

        self.bitmapTriger(self.flag_red_press,  self.err_green, self.err_red, self.errRedPress)
        self.bitmapTriger(self.flag_speed,      self.err_green, self.err_red, self.errSpeed)
        self.bitmapTriger(self.flag_cLiq,       self.err_green, self.err_red, self.errCoolLiq)

        self.hipress_item.SetLabel( str(self.Cylinder_press))
        self.sttr.SetLabel(         str(self.Reductor_temp))
        self.sttb.SetLabel(         str(self.Reductor_press))
        self.stColLiq.SetLabel(str(self.cLiq))

        self.stUpower.SetLabel(str(self.Upower))

    # Разбор информации из ECU о
    def parseData(self, dataFromECU):

        self.parsePosition = 0

        self.RPM        = self.getWord( dataFromECU )
        self.Turbo      = self.getWord( dataFromECU )
        self.EGT        = self.getWord( dataFromECU )
        self.PPS1       = self.getWord( dataFromECU )
        self.PPS2       = self.getWord( dataFromECU )
        self.Gas        = self.getWord( dataFromECU )
        self.Emul       = self.getWord( dataFromECU )
        self.PPS1emul   = self.getWord( dataFromECU )
        self.PPS2emul   = self.getWord( dataFromECU )

        self.Speed          = self.getByte( dataFromECU )
        self.Reductor_press = self.getWord( dataFromECU )
        self.Reductor_temp  = self.getWord( dataFromECU )
        self.Cylinder_press = self.getWord( dataFromECU )

        self.Speed_gas      = self.getByte( dataFromECU )
        self.Speed_diesel   = self.getByte( dataFromECU )
        self.EGT_gas        = self.getByte( dataFromECU )

        # Разбираем статусы флагов ошибок
        # Байт ошибок
        self.flag_red_temp, self.flag_red_press, self.flag_EGT, self.flag_cLiq , \
        self.flag_PPS, self.flag_RPM, self.flag_speed, self.flagGPS_NO_START_COORDINATE = self.getFlag( dataFromECU )
        # Байт флагов ( инверсия по состоянию см. PACK_BYTE в arduino
        ED.flag_Relay, self.flag_block_ON, self.flagGPS_NO_DATA, self.flagGPS_FORWARD,\
        self.flagGPS_ON, ED.flag_ECU_ON_VISU, res1, reserv2 = self.getFlag( dataFromECU )

        self.Test_val   = self.getWord( dataFromECU )
        self.K_emul     = self.getByte( dataFromECU )
        self.gasPPSmax  = self.getByte( dataFromECU )
        self.timeCycle  = self.getWord( dataFromECU )

        self.LON = self.getLON( dataFromECU )
        self.LAT = self.getLAT( dataFromECU )

        self.cLiq   = self.getByte( dataFromECU )
        self.SAT    = self.getByte( dataFromECU )

        self.activeZoneLON = self.getLON( dataFromECU )
        self.activeZoneLAT = self.getLAT( dataFromECU )

        self.zeroPointDistance = self.getLong( dataFromECU )

        self.zeroPointLON = self.getLON( dataFromECU )
        self.zeroPointLAT = self.getLAT( dataFromECU )

        self.activeZoneDistance = self.getLong( dataFromECU )

        self.GPSgas     = self.getByte( dataFromECU )
        self.GPSdiesel  = self.getByte( dataFromECU )

        self.Upower     = self.getWord( dataFromECU )
        self.loadPress  = self.getWord( dataFromECU )

        # Вычисляем, то что можно вычислить на основании полученных данных
        try:
            self.PPS1PPS2 = float(self.PPS1) / float(self.PPS2)  # Соотношение между входящим PPS1 и PPS2
        except:
            self.PPS1PPS2 = 0
        try:
            self.PPS1PPS2emul = float(self.PPS1emul) / float(
                self.PPS2emul)  # Соотношение между эмуляцией PPS1 и PPS2
        except:
            self.PPS1PPS2emul = 0

        ED.RPM = self.RPM
        ED.Turbo = self.Turbo

class GeneralPriborWindow_MEGA_1366(GeneralPriborWindow_MEGA_1024):
    # Определяет данные специфичные для МЕГА_1366
    def __init__(self, parent):
        # Определяем данные для всех типов ECU путем вызова конструктора базового класса
        GeneralPriborWindow_MEGA_1024.__init__(self, parent)

    # Добавляет еще 2 колонки информации, всего становится 5 колонок
    def showPribor(self):
        GeneralPriborWindow.showPribor(self)

        fourth_sizer = self.fourthColumn()  # Четвертая колонка
        fifth_sizer  = self.fifthColumn()   # Пятая колонка

        self.main_sz.Add(fourth_sizer, 0, wx.LEFT | wx.ALIGN_TOP | wx.ALIGN_LEFT, 0)
        self.main_sz.Add(fifth_sizer, 0,  wx.LEFT | wx.ALIGN_TOP | wx.ALIGN_LEFT, 40)

    def thirdColumn(self):
        third_sizer = wx.BoxSizer(wx.VERTICAL)
        self.gaugeSpeed(third_sizer, offset=2 )              # Спидометр с подписями и коэффициентами
        third_sizer.Add((0, 8))                   # Пустое пространство
        self.fullSetErr( third_sizer, offset=3 )  # Полный набор маленьких индикаторов об ошибках
        self.gaugeEGT(third_sizer, offset=0 )

        return third_sizer

    def fourthColumn(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.GPSData(sizer)
        return sizer

    def fifthColumn(self):
        return (self.fullLampsAndButton())

    # Случайные значения, что юы была видимость работы, когда ECU не подключено. Добавляем специфичные для МЕГИ значения
    def getRandomValue(self):
        GeneralPriborWindow_MEGA_1024.getRandomValue(self)

        self.LON = random.uniform(100.7, 123.5)
        self.LAT = random.uniform(0.5, 80.5)

        self.activeZoneLON      = random.uniform(100.8, 123.5)
        self.activeZoneLAT      = random.uniform(0.5, 80.5)
        self.activeZoneDistance = random.randint( 100,900000 )

        self.zeroPointLON       = random.uniform(100.8, 123.5)
        self.zeroPointLAT       = random.uniform(0.5, 80.5)
        self.zeroPointDistance  = random.randint(100, 900000)

        self.flagGPS_ON                     = random.choice([True, False])
        self.flagLOG_ON                     = random.choice([True, False])
        self.flagGPS_NO_DATA                = random.choice([True, False])
        self.flagGPS_NO_START_COORDINATE    = random.choice([True, False])
        self.flagGPS_FORWARD                = random.choice([True, False])

    # Обновляет экранные значения
    def update(self):
        # Обновляет экранные значения общие для МЕГА и НАНО( минимальный ОБЩИЙ набор )
        GeneralPriborWindow_MEGA_1024.update(self)

        # Расширяет обновление специфичными для МЕГИ_1366  приборами
        self.saveUpdateCircleGauge(self.speed, self.Speed)
        self.saveUpdateCircleGauge(self.meterEGT, self.EGT)

        # Индикатор включения кнопки
        self.bitmapTriger(self.flagGPS_ON, self.green, self.red, self.b_gps )
        self.bitmapTriger(self.flagLOG_ON, self.green, self.red, self.b_log)

        # Индикаторы GPS
        self.bitmapTriger(self.flagGPS_NO_DATA, self.err_green, self.err_red, self.errGPSnoData)
        self.bitmapTriger(self.flagGPS_NO_START_COORDINATE, self.err_green, self.err_red, self.errGPSnoSTART_COORD)
        self.bitmapTriger(self.flagGPS_FORWARD, self.err_green, self.err_red, self.flagDirection)

        # Данные GPS, текущие кординаты
        self.stLON.SetLabel(u'LON: '            + str('%3.6f' % float(self.LON)))
        self.stLAT.SetLabel(u'LAT:  '           + str('%2.6f' % float(self.LAT)))
        self.stSAT.SetLabel(u'Спутники:  '      + str(self.SAT) )

        # Данные GPS, кординаты и растояние до центра активной зоны
        self.stAzLON.SetLabel(u'LON: '              + str('%3.6f' % float(self.activeZoneLON)))
        self.stAzLAT.SetLabel(u'LAT:  '             + str('%2.6f' % float(self.activeZoneLAT)))
        self.stAzDistance.SetLabel(u'Расст.: '  + str(self.activeZoneDistance ) )

        # Данные GPS, кординаты и растояние до стартовой точки
        self.stZpLON.SetLabel(u'LON: '              + str('%3.6f' % float(self.zeroPointLON)))
        self.stZpLAT.SetLabel(u'LAT:  '             + str('%2.6f' % float(self.zeroPointLAT)))
        self.stZpDistance.SetLabel(u'Расст.: '  + str( self.zeroPointDistance ) )

class GeneralPriborWindow_MEGA_1600(GeneralPriborWindow_MEGA_1366):
    def __init__(self, parent):
        self.smallGaugeSize = (160, 160)
        GeneralPriborWindow_MEGA_1366.__init__( self, parent)

    # Добавляет еще 2 колонки информации, всего становится 5 колонок
    def showPribor(self):
        GeneralPriborWindow.showPribor(self)

        fourth_sizer = self.fourthColumn()  # Четвертая колонка
        fifth_sizer = self.fifthColumn()    # Пятая колонка
        sixth_sizer = self.sixthColumn()    # Шестая колонка

        self.main_sz.Add(fourth_sizer, 0, wx.LEFT | wx.ALIGN_TOP | wx.ALIGN_LEFT, 0)
        self.main_sz.Add(fifth_sizer, 0, wx.LEFT | wx.ALIGN_TOP | wx.ALIGN_LEFT, 0)
        self.main_sz.Add(sixth_sizer, 0, wx.LEFT | wx.ALIGN_TOP , 20 )

    def secondColumn(self):
        sizer = GeneralPriborWindow.secondColumn(self)
        sizer.Add((20, 45))  # Пустое пространство
        self.fullSetErr( sizer)
        return sizer

    def thirdColumn(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gaugeSpeed(sizer,          offset=0, size=self.smallGaugeSize)  # Спидометр с подписями и коэффициентами
        self.gaugeCylPress( sizer,      offset=0, size=self.smallGaugeSize )
        self.gaugeLiqColTemp(sizer,     offset=0, size=self.smallGaugeSize )
        sizer.Add((0, 60))  # Пустое пространство
        self.stTimeCycle = self.Item_simple(u'T цикла (мкс):' + str(self.timeCycle), sizer, padding=50)
        sizer.Add((0, 10))  # Пустое пространство
        self.stTest = self.Item_simple(u'Служебное:' + str(self.Test_val), sizer, padding=50)
        return sizer

    def fourthColumn(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gaugeEGT(sizer,       offset = 0, size=self.smallGaugeSize)  # Циферблат EGT с подписью и коэффициентами
        self.gaugeRedTemp(sizer,   offset = 0, size=self.smallGaugeSize)
        self.gaugeRedPress(sizer,  offset = 0, size=self.smallGaugeSize)
        self.gaugeVoltmeter(sizer, offset = 0, size=self.smallGaugeSize)
        return sizer

    def fifthColumn(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.GPSData( sizer )
        sizer.Add((0, 20))  # Пустое пространство
        self.gaugePressureLoad(sizer, offset=0, size=self.smallGaugeSize)
        self.stLoadgas = self.Item_simple(u'Газ кор.: ' + str(self.loadGas), sizer, padding=60)
        self.stLoaddiesel = self.Item_simple(u'ДТ кор. : ' + str(self.loadDiesel), sizer, padding=60)
        return sizer

    def sixthColumn(self):
        return ( self.fullLampsAndButton() )

        GeneralPriborWindow_MEGA_1366.update( self )

        self.saveUpdateCircleGauge(self.hipress,     self.Cylinder_press, 2500)
        self.saveUpdateCircleGauge(self.meterRT,     self.Reductor_temp, 400)
        self.saveUpdateCircleGauge(self.meterBlt,    self.Reductor_press,1000)
        self.saveUpdateCircleGauge(self.meter_cLiq,  self.cLiq)
        self.saveUpdateCircleGauge(self.meterPower,  self.Upower)
        self.stUpower.SetLabel(str('%2.1f' % self.Upower))
        self.saveUpdateCircleGauge(self.meterLoad, self.loadPress)
        self.stML.SetLabel(str('%2.1f' % self.loadPress))

    # Случайные значения, что юы была видимость работы, когда ECU не подключено. Добавляем специфичные для МЕГИ значения
    def getRandomValue(self):
        GeneralPriborWindow_MEGA_1366.getRandomValue(self)

        self.loadPress  = random.randint(0, 3000)

        self.GPSgas     = random.uniform(0.5, 1.5)
        self.GPSdiesel  = random.uniform(0.5, 1.5)

        self.loadGas    = random.uniform(0.5, 1.5)
        self.loadDiesel = random.uniform(0.5, 1.5)

    # Обновляет экранные значения, специфичные для МЕГИ 1600
    def update(self):
        # Обновляет экранные значения общие для МЕГА и НАНО( минимальный ОБЩИЙ набор )
        GeneralPriborWindow_MEGA_1366.update(self)

        # Расширяет обновление специфичными для МЕГИ_1600  приборами
        self.saveUpdateCircleGauge(self.meterRT,    self.Reductor_temp)
        self.saveUpdateCircleGauge(self.meterBlt,   self.Reductor_press, 500)
        self.saveUpdateCircleGauge(self.hipress,    self.Cylinder_press)
        self.saveUpdateCircleGauge(self.meter_cLiq, self.cLiq)

        self.saveUpdateCircleGauge( self.meterLoad, self.loadPress)
        self.saveUpdateCircleGauge( self.meterPower,self.Upower )

        self.stML.SetLabel(str(self.loadPress))

        self.stGPSgas.SetLabel(u'Газ кор.: ' +  str('%2.2f' % self.GPSgas))
        self.stGPSdiesel.SetLabel(u'ДТ кор. : ' + str('%2.2f' % self.GPSdiesel))
        self.stLoadgas.SetLabel(u'Газ кор.: ' + str('%2.2f' % self.loadGas))
        self.stLoaddiesel.SetLabel(u'ДТ кор. : ' + str('%2.2f' % self.loadDiesel))

