# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import wx.lib.agw.pygauge as PG
import wx.lib.agw.speedmeter as SM
import os

# Примесь - донор различных сервисных функций для ВЫВОДА информации
class OutputMixin():
    pi = 3.14159

    # Большие приборы RPM и Turbo
    def bigCircleGauge(self, colours, intervals, label):
        # ================================= RPM ====================================================
        # Fifth SpeedMeter: We Use The Following Styles:
        #
        # SM_DRAW_HAND: We Want To Draw The Hand (Arrow) Indicator
        # SM_DRAW_PARTIAL_SECTORS: Partial Sectors Will Be Drawn, To Indicate Different Intervals
        # SM_DRAW_SECONDARY_TICKS: We Draw Secondary (Intermediate) Ticks Between
        #                          The Main Ticks (Intervals)
        # SM_DRAW_MIDDLE_TEXT: We Draw Some Text In The Center Of SpeedMeter
        # SM_ROTATE_TEXT: The Ticks Texts Are Rotated Accordingly To Their Angle
        sm = SM.SpeedMeter(self, size=(310, 310), agwStyle=SM.SM_DRAW_HAND | SM.SM_DRAW_PARTIAL_SECTORS |
                                                           SM.SM_DRAW_SECONDARY_TICKS | SM.SM_DRAW_MIDDLE_TEXT | SM.SM_ROTATE_TEXT)
        # We Want To Simulate The Round Per Meter Control In A Car
        sm.SetAngleRange(-self.pi / 6, 7 * self.pi / 6)
        sm.SetIntervals(intervals)
        sm.SetIntervalColours(colours)
        ticks = [str(interval) for interval in intervals]
        sm.SetTicks(ticks)
        sm.SetTicksColour(wx.WHITE)
        sm.SetTicksFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        sm.SetNumberOfSecondaryTicks(4)
        sm.SetHandColour(wx.Colour(255, 50, 0))
        sm.DrawExternalArc(False)
        sm.SetShadowColour(wx.Colour(50, 50, 50))
        sm.SetMiddleText(label)
        sm.SetMiddleTextColour(wx.WHITE)
        sm.SetMiddleTextFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        sm.SetSpeedBackground(wx.SystemSettings_GetColour(0))
        return sm

    # Малые круглые приборы ( Скорость, давление, температура и тд )
    def smallCircleGauge(self, colours, intervals, label, sz=(170,170)):
        sm = SM.SpeedMeter(self, size=sz, agwStyle=SM.SM_DRAW_HAND | SM.SM_DRAW_SECTORS |
                                                           SM.SM_DRAW_MIDDLE_TEXT | SM.SM_DRAW_SECONDARY_TICKS)
        sm.SetSpeedBackground(wx.SystemSettings_GetColour(0))
        # Set The Region Of Existence Of SpeedMeter (Always In Radians!!!!)
        sm.SetAngleRange(-self.pi / 3, 11 * self.pi / 8)
        sm.SetIntervals(intervals)
        # Assign The Same Colours To All Sectors (We Simulate A Car Control For Speed)
        sm.SetIntervalColours(colours)
        # Assign The Ticks: Here They Are Simply The String Equivalent Of The Intervals
        ticks = [str(interval) for interval in intervals]
        sm.SetTicks(ticks)
        # Set The Ticks/Tick Markers Colour
        sm.SetTicksColour(wx.WHITE)
        # We Want To Draw 5 Secondary Ticks Between The Principal Ticks
        sm.SetNumberOfSecondaryTicks(2)
        # Set The Font For The Ticks Markers
        sm.SetTicksFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
        # Set The Text In The Center Of SpeedMeter
        sm.SetMiddleText(label)
        # Assign The Colour To The Center Text
        sm.SetMiddleTextColour(wx.WHITE)
        # Assign A Font To The Center Text
        sm.SetMiddleTextFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
        # Цвет стрелки
        sm.SetHandColour(wx.Colour(255, 50, 0))
        # Do Not Draw The External (Container) Arc. Drawing The External Arc May
        # Sometimes Create Uglier Controls. Try To Comment This Line And See It
        # For Yourself!
        sm.DrawExternalArc(False)
        return sm

    # Прибор RPM с подписью
    def gaugeRPM(self, sizer, RPM ):
        # ========================== RPM =======================================================
        colours = [wx.BLACK] * 5
        colours.append(wx.Colour(255, 255, 0)); colours.append(wx.Colour(255, 255, 0))
        colours.append(wx.Colour(255, 255, 0)); colours.append(wx.RED); colours.append(wx.RED)
        self.prRPM = self.bigCircleGauge(colours, range(0, 55, 5), "RPM")
        sizer.Add(self.prRPM, 0, wx.RIGHT | wx.LEFT | wx.ALIGN_TOP, 10)
        self.stRPM = wx.StaticText(self, -1, str(RPM), pos=(150, 250))
        font = wx.Font(26, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.stRPM.SetFont(font)
        self.stRPM.SetForegroundColour("BLACK")

    # Прибор Turbo с подписью
    def gaugeTurbo(self, sizer, turbo):
        # ========================== Turbo =======================================================
        colours = [wx.BLACK] * 6
        colours.append(wx.Colour(255, 255, 0))
        colours.append(wx.RED)
        self.prTurbo = self.bigCircleGauge(colours, range(0, 45, 5), "Turbo")
        sizer.Add((0, 20))  # Пустое пространство
        sizer.Add(self.prTurbo, 0, wx.RIGHT | wx.LEFT | wx.ALIGN_TOP, 10)
        self.stTurbo = wx.StaticText(self, -1, str(turbo), pos=(150, 650))
        font = wx.Font(26, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.stTurbo.SetFont(font)
        self.stTurbo.SetForegroundColour("BLACK")

    # Прибор EGT с подписью и коэффициентами
    def gaugeEGT(self, sizer, offset=10, size=(170,170) ):
        # ======================= EGT метер ==================================================
        colours = [wx.BLUE] * 4
        colours.append((214, 162, 43)); colours.append((214, 162, 43))
        colours.append(wx.RED)
        self.meterEGT = self.smallCircleGauge(colours, range(0, 800, 100), u"гр.С", sz=size)
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.meterEGT, 0, wx.LEFT | wx.ALIGN_BOTTOM, 63)
        # ===================== EGT подпись =======================================================
        egtp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stegtp = self.Item(u"  EGT", str(self.EGT), 20, 26, (0, 0, 0), egtp_sizer)
        sizer.Add(egtp_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)
        sizer.Add((0, offset), 0)  # Пустое пространство
        self.stEGTGK = self.Item_simple(u'Газ кор.: ' + str(self.EGT_gas), sizer, padding=60)

    # Прибор Скорость с подписью и коэффициентами
    def gaugeSpeed(self, sizer, offset=10 , size=(170,170)):
        # ========================= Спидометр ====================================
        # Количество цветовых интервалов на цифирблате приборе
        colours = [wx.BLACK] * 12
        # Интервал цифирок в подписях, должно совпадать с количеством цветовых интервалов
        self.speed = self.smallCircleGauge(colours, range(0, 121, 10), "Km/h", sz=size)
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.speed, 0, wx.LEFT | wx.ALIGN_BOTTOM, 63)
        # ===================== Скорость подпись =======================================================
        spp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.spp = self.Item(u"Скорость", str(self.Speed), 20, 26, (0, 0, 0), spp_sizer)
        sizer.Add(spp_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 30)
        sizer.Add((0, offset/2), 0)  # Пустое пространство
        self.stSG = self.Item_simple(u'Газ кор.: ' + str(self.Speed_gas), sizer, padding=60)
        sizer.Add((0, offset), 0)  # Пустое пространство
        self.stSD = self.Item_simple(u'ДТ кор. : ' + str(self.Speed_diesel), sizer, padding=60)

    # Прибор Давление в баллонах с подписью
    def gaugeCylPress(self, sizer, offset=15, size=(170,170) ):
        # ========================= Давление по высокому ====================================
        colours = [wx.BLACK] * 10
        self.hipress = self.smallCircleGauge(colours, range(0, 5001, 500), "mV", sz=size)
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.hipress, 0, wx.LEFT | wx.ALIGN_BOTTOM, 63)
        # ===================== Давление по высокому подпись =======================================================)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hipress_item = self.Item(u'P баллоны:', str(self.Cylinder_press), 18, 26, (0, 0, 0), self.hsizer)
        sizer.Add(self.hsizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)

    # Прибор Давление редуктора с подписью
    def gaugeRedPress(self, sizer, offset=15, size=(170,170) ):
        # ======================= Давление редуктора  ==================================================
        colours = [wx.RED]
        colours.append((214, 162, 43))
        colours.append(wx.BLUE)
        colours.append(wx.BLUE)
        colours.append((214, 162, 43))
        self.meterBlt = self.smallCircleGauge(colours, range(300, 2100, 300), u"mV", sz=size)
        sizer.Add((0, offset))  # Пустое пространство
        sizer.Add(self.meterBlt, 0, wx.LEFT | wx.ALIGN_BOTTOM, 70)
        # ===================== Давленние редуктора блока подпись ========================================
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sttb = self.Item(u"P редуктора", str(self.Reductor_press), 18, 26, (0, 0, 0), tb_sizer)
        sizer.Add(tb_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)

    # Прибор Температура редуктора с подписью
    def gaugeRedTemp(self, sizer, offset=10, size=(170, 170)):
        # ======================= Температура редутора  ==================================================
        colours = [wx.BLUE] * 2
        colours.append((214, 162, 43))
        colours.append(wx.RED)
        self.meterRT = self.smallCircleGauge(colours, range(0, 500, 100), u"mV", sz=size)
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.meterRT, 0, wx.LEFT | wx.ALIGN_BOTTOM, 70)
        # ===================== Температура редуктора подпись =======================================================)
        self.tred_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sttr = self.Item(u"Т редуктора", str(self.Reductor_temp), 18, 26, (0, 0, 0), self.tred_sizer)
        sizer.Add(self.tred_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)

    # Прибор Температура редуктора с подписью
    def gaugePressureLoad(self, sizer, offset=10, size=(170,170) ):
        # ======================= Температура редутора  ==================================================
        colours = [wx.BLUE] * 2
        colours.append((214, 162, 43))
        colours.append(wx.RED)
        self.meterLoad = self.smallCircleGauge(colours, range(0, 5000, 1000), u"mV", sz=size )
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.meterLoad, 0, wx.LEFT | wx.ALIGN_BOTTOM, 70)
        # ===================== Температура редуктора подпись =======================================================)
        self.tred_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stML = self.Item(u"P груз", str(self.loadPress), 18, 26, (0, 0, 0), self.tred_sizer)
        sizer.Add(self.tred_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)

    # Прибор Температура редуктора с подписью
    def gaugeVoltmeter(self, sizer, offset=10, size=(170, 170) ):
        # ======================= Температура редутора  ==================================================
        colours = [wx.BLUE] * 2
        colours.append((214, 162, 43))
        colours.append(wx.RED)
        self.meterPower = self.smallCircleGauge(colours, range(0, 100, 20), u"V", sz=size)
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.meterPower, 0, wx.LEFT | wx.ALIGN_BOTTOM, 70)
        # ===================== Напряжение питания подпись =======================================================)
        self.tred_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stUpower = self.Item(u"U питания ", str(self.Upower), 18, 26, (0, 0, 0), self.tred_sizer)
        sizer.Add(self.tred_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 70)

    # Прибор Температура охлаждающей жидкости с подписью
    def gaugeLiqColTemp(self, sizer, offset=10, size=(170, 170)):
        # ======================= Температура редутора  ==================================================
        colours = [wx.BLUE] * 4
        colours.append((214, 162, 43))
        colours.append(wx.RED)
        self.meter_cLiq = self.smallCircleGauge(colours, range(0, 140, 20), u"C", sz=size )
        sizer.Add((0, offset), 0)  # Пустое пространство
        sizer.Add(self.meter_cLiq, 0, wx.LEFT | wx.ALIGN_BOTTOM, 70)
        # ===================== Температура редуктора подпись =======================================================)
        self.tred_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stColLiq = self.Item(u"Т охл. жидк.", str(self.cLiq), 18, 26, (0, 0, 0), self.tred_sizer)
        sizer.Add(self.tred_sizer, 0, wx.LEFT | wx.ALIGN_TOP, 40)

    # Безопасное обновление для круглых приборов
    def saveUpdateCircleGauge(self, gauge, value, minValue=0):
        try:
            gauge.SetSpeedValue(value)
        except:
            gauge.SetSpeedValue(minValue)

    # Безопасное обновление для прибров с линейным индикатором
    def saveUpdateLineGauge(self, gauge, value):
        try:
            gauge.SetValue(value)
        except:
            gauge.SetValue(0)
        gauge.Refresh()

    # Просто выводит подпись и значение одним шрифтом и одним размером
    def Item_simple(self, str, sizer, padding=30, fontsize=18, win=0 ):
        if win==0: windows= self
        else: windows = win
        st = wx.StaticText( windows, -1, str)
        font = wx.Font( fontsize, wx.SWISS, wx.NORMAL, wx.BOLD)
        st.SetFont(font)
        st.SetForegroundColour("BLACK")
        sizer.Add(st, 0, wx.LEFT | wx.ALIGN_TOP, padding)
        return (st)

    # Отображает стандартный блок информации Заголовок - значение, добавляя его к сайзеру РАЗНЫЙ РАЗМЕР шрифта
    def Item(self, label, volume, size_l, size_v, color, sizer):
        '''
        :param label: Заголовок
        :param volume: Изменяющееся значение
        :param size_l: Размер фонта для Заголовка
        :param size_v: Размер фонта для изменяющегося значения
        :param color: Цвет фона
        :param sizer: Сайзер куда добавляем этот пункт
        :return:
        '''
        st1 = wx.StaticText(self, -1, label)
        font = wx.Font(size_l, wx.SWISS, wx.NORMAL, wx.BOLD)
        st1.SetFont(font)
        st1.SetForegroundColour(color)
        sizer.Add(st1, 0, wx.RIGHT | wx.LEFT | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, 10)
        st2 = wx.StaticText(self, -1, volume)
        font = wx.Font(size_v, wx.SWISS, wx.NORMAL, wx.BOLD)
        st2.SetFont(font)
        st2.SetForegroundColour(color)
        sizer.Add(st2, 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER | wx.ALIGN_BOTTOM, 10)
        return st2

    # Item, помещенный в горизонтальный сайзер для выводв в одну линию
    def itemLine(self, label, volume, sizer, fontsize=(18,26)):
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.item = self.Item(label, str(volume), fontsize[0], fontsize[1], (0, 0, 0), self.hsizer)
        sizer.Add(self.hsizer, 0, wx.LEFT | wx.ALIGN_TOP, 20)
        return self.item

    # Отображает маленькую сигнальную лампочку ( индикатор ошибки ) и подпись к ней
    def Item_Err(self, str, sizer, offset=7, offsetX=30 ):
        self.err_green = wx.Image(os.getcwd() + "\pic\\green_small.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.err_red = wx.Image(os.getcwd() + "\pic\\red_small.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        err_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.err_block = wx.StaticBitmap(self, -1, self.err_green, style=wx.GA_HORIZONTAL)
        err_sizer.Add(self.err_block, 0, wx.LEFT | wx.ALIGN_CENTER | wx.ALIGN_LEFT, offsetX)
        st = wx.StaticText(self, -1, str)
        font = wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD)
        st.SetFont(font)
        st.SetForegroundColour("BLACK")
        err_sizer.Add(st, 0, wx.LEFT | wx.ALIGN_CENTER | wx.ALIGN_LEFT, 5 )
        sizer.Add(err_sizer, 0, wx.BOTTOM, offset)
        return (self.err_block)

    # Четыре стандартные маленькие лампочки индикатора ошибки, общие для МЕГА и НАНО
    def nanoErr(self, sizer, offset=7):
        self.errRedTemp = self.Item_Err(u'   Темп. редуктора',  sizer, offset)
        self.errEGT     = self.Item_Err(u'   Превышение EGT',   sizer, offset)
        self.errRPM     = self.Item_Err(u'   Ошибка чтения RPM',sizer, offset)
        self.errPPS     = self.Item_Err(u'   Фактический PPS',  sizer, offset)

    # Полный набор маленьких индикаторов об ошибках
    def fullSetErr(self, sizer, offset=7):
        self.nanoErr(sizer, offset)  # 4 ошибки для NANO
        self.errRedPress    = self.Item_Err(u'   Давление редуктора', sizer, offset)
        self.errSpeed       = self.Item_Err(u'   Высокая скорость', sizer, offset)
        self.errCoolLiq     = self.Item_Err(u'   Охл. жидкость', sizer, offset)

    # Индикатор в виде полоски
    def Item_gauge(self, range, align, str, sizer, szpadding, percent, sizeGauge=(280, 45), fontSize=20,
                   txtColor=wx.BLUE):
        '''
        :param range: Максимальное значение
        :param align:
        :param str: Надпись на полосе индикатора
        :param sizer:
        :param szpadding:
        :param percent: Отображать ли % False, True
        :param sizeGauge: Размер полосы индикатора
        :param fontSize: Шрифт надписи на полосе индикатора
        :param txtColor: Цвет надписи на полосе индикатора
        :return:
        '''
        g = PG.PyGauge(self, -1, range=range, size=(sizeGauge))
        gfont = wx.Font(fontSize, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        g.SetBackgroundColour(wx.WHITE)
        g.SetBorderColor(wx.BLACK)
        g.SetBorderPadding(4)
        # g.SetBarColor( color )
        g.SetDrawValue(draw=True, drawPercent=percent, font=gfont, colour=txtColor, formatString=str)
        sizer.Add(g, 0, align, szpadding)
        return (g)

    # Устанавливает цвет индикатора- лампочки ( зеленый, красный ) в зависимости от состояния флага
    def bitmapTriger(self, flag, green, red, bitmap):
        if flag:
            bitmap.SetBitmap(green)
        else:
            bitmap.SetBitmap(red)

    # Большая лампочка-индикатор с регулируемым смещением по левому краю
    def bigLamp(self, sizer, label, offset=50 ):
        self.green = wx.Image(os.getcwd() + "\pic\\green_big.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.red = wx.Image(os.getcwd() + "\pic\\red_big.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        but = wx.StaticBitmap(self, -1, self.green, pos=(10, 20), style=wx.GA_HORIZONTAL)
        sizer.Add( but, 0, wx.LEFT, offset)
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD)
        stBlock = wx.StaticText(self, -1, label)
        stBlock.SetFont(font)
        sizer.Add(stBlock, 0, wx.TOP, 10)
        return but

    # Три стандартные для МЕГА и НАНО большие лампочки
    def bigLamps(self, sizer, offset=50 ):

        self.b_block    = self.bigLamp(sizer, u' Блок',   offset)
        self.b_knopka   = self.bigLamp(sizer, u'Кнопка', offset)
        self.b_manual   = self.bigLamp(sizer, u'Ручное', offset)

    def nanoLampsAndButton(self, sizer):
        biglamp_sizer = wx.FlexGridSizer(rows=4, cols=2, hgap=30, vgap=10)
        self.bigLamps(biglamp_sizer)  # Большие лампочки
        # кнопка ручного включения ECU
        bManualON = wx.Button(self, 20, u"ВКЛ/ВЫКЛ", size=(240, 40))
        self.Bind(wx.EVT_BUTTON, self.OnClickButtonManual, bManualON)
        sizer.Add(biglamp_sizer, 0, wx.TOP, 15)
        sizer.Add((0, 30))  # Пустое пространство
        sizer.Add(bManualON, 0, wx.LEFT, 25)

    # Полный набор больших лампочек и кнопка ручного включения блока
    def fullLampsAndButton(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0, 20))  # Пустое пространство
        self.bigLamps(sizer, offset=12)  # Три стандартные для МЕГА и НАНО большие лампочки
        # Расширяем три стандартных лампочки
        self.b_gps = self.bigLamp(sizer, u'  GPS', offset=12)  # Индикатор режима работы GPS
        self.b_log = self.bigLamp(sizer, u'   Лог', offset=12)  # Индикатор режима работы GPS
        # Кнопка ручного включения блока
        bManualON = wx.Button(self, 20, u"ВКЛ/ВЫКЛ", size=(85, 50))
        self.Bind(wx.EVT_BUTTON, self.OnClickButtonManual, bManualON)
        sizer.Add(bManualON, 0, wx.TOP, 10)
        return sizer

    # Вывод блока данных по GPS
    def GPSData(self, sizer ):
        sizer.Add((0, 20))                                                                      # Пустое пространство
        self.stLON                  = self.Item_simple(u'LON: '    + str(self.LON), sizer)
        self.stLAT                  = self.Item_simple(u'LAT:  '   + str(self.LAT), sizer)
        sizer.Add((0, 5))                                                                       # Пустое пространство
        self.stSAT                  = self.Item_simple(u'Спутники:  '  + str(self.SAT), sizer)
        sizer.Add((0, 5))                                                                       # Пустое пространство
        stZeroPoint = wx.StaticText(self, -1, u"Нулевая точка")
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD)
        stZeroPoint.SetFont(font)
        sizer.Add(stZeroPoint, 0, wx.ALIGN_CENTER, 0)
        sizer.Add((0, 5))  # Пустое пространство
        self.stZpLON = self.Item_simple(u'LON: ' + str(self.zeroPointLON), sizer)
        self.stZpLAT = self.Item_simple(u'LAT:  ' + str(self.zeroPointLAT), sizer)
        self.stZpDistance = self.Item_simple(u'Расст.: ' + str(self.zeroPointDistance), sizer)
        sizer.Add((0, 5))
        stActiveZone = wx.StaticText(self, -1, u"Активная зона")
        stActiveZone.SetFont(font)
        sizer.Add( stActiveZone, 0, wx.ALIGN_CENTER, 0 )
        sizer.Add((0, 5))                                                                       # Пустое пространство
        self.stAzLON        = self.Item_simple(u'LON: '         + str(self.activeZoneLON), sizer)
        self.stAzLAT        = self.Item_simple(u'LAT:  '        + str(self.activeZoneLAT), sizer)
        self.stAzDistance   = self.Item_simple(u'Расст.: '  + str(self.activeZoneDistance), sizer)
        self.stGPSgas       = self.Item_simple(u'Газ кор.: ' + str(self.GPSgas), sizer, padding=60)
        self.stGPSdiesel    = self.Item_simple(u'ДТ кор. : ' + str(self.GPSdiesel), sizer, padding=60)

        sizer.Add((0, 5))  # Пустое пространство

        sizer.Add((0, 15))                                                                      # Пустое пространство
        self.errGPSnoData           = self.Item_Err(u'Данные от GPS',    sizer)
        self.errGPSnoSTART_COORD    = self.Item_Err(u'Стартовые коорд.', sizer)
        self.flagDirection          = self.Item_Err(u'Приближаемся',     sizer)









