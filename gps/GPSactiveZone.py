# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import ECUdata as ED
from mixin import OutputMixin
import wx.dataview as dv
import Shema

# Список активных зон из ECU
class ActiveZone( Shema.ReadECU, OutputMixin.OutputMixin ):

    numberNearZone = 20  # Количество активных зон
    ActiveZoneSize = 31
    # Размер передаваемой калибровки с активными зонвми
    # 4 - дистанция до активной зоны LONG
    # 2 CRC
    # 8 координаты точки старта поездки
    GPSActiveZoneCalSize = numberNearZone * (ActiveZoneSize + 4) + 2 + 8

    # Обязателдьное свойство ! Размер пересылаемых данных
    bufSize = GPSActiveZoneCalSize

    def __init__(self):

        self.startPointLON  = "12.123456"
        self.startPointLAT  = "23.456789"
        self.listActiveZone = []

    # Показывает список зон
    def showActiveZoneList(self, evt):
        dTabl = wx.Dialog(ED.main_parent, -1, u"Список активных зон для текущей поездки",
                          pos=(300, 100), size=(730, 600))
        dTabl.SetBackgroundColour("WHITE")
        main_sz = wx.BoxSizer( wx.VERTICAL )

        self.dvlc = dvlc = dv.DataViewListCtrl( dTabl )

        # Give it some columns.
        # The ID col we'll customize a bit:
        dvlc.AppendTextColumn(u'Номер',         width=50)
        dvlc.AppendTextColumn(u'Имя',           width=100)
        dvlc.AppendTextColumn(u'Долгота',       width=150)
        dvlc.AppendTextColumn(u'Широта',        width=150)
        dvlc.AppendTextColumn(u'Радиус',        width=90)
        dvlc.AppendTextColumn(u'Вид',           width=90)
        dvlc.AppendTextColumn(u'Расстояние',    width=90)

        # Load the data. Each item (row) is added as a sequence of values
        # whose order matches the columns
        for itemvalues in self.listActiveZone:
            dvlc.AppendItem(itemvalues)

        main_sz.Add(dvlc, 1, wx.EXPAND)
        self.stSP_LON = self.Item_simple(u'Точка старта LON: '  + str( self.startPointLON), main_sz, win= dTabl )
        self.stSP_LAT = self.Item_simple(u'Точка старта LAT:  ' + str( self.startPointLAT), main_sz, win = dTabl )

        dTabl.SetSizer(main_sz)

        dTabl.ShowModal()

    # метод для ЧТЕНИЯ калибровки, реализует диалог и посылает команду ECU
    def readActiveZone(self, evt):
        # Открываеи диалог прогресса выполнения и посылает команду на чтение калибровки
        ActiveZone.progressDlg = wx.ProgressDialog(u"Процент выполнения чтения активных зон GPS",
            u"Чтение из FLASH памяти:", maximum=5, parent=ED.main_parent, style=wx.PD_APP_MODAL)
        self.sendCommandECU(self.readActiveZoneRequet, 1)
        ActiveZone.progressDlg.Update(1, u'Команда на считывание послана ECU')

    # Обязательный метод ! для ЧТЕНИЯ калибровки, реализующий разбор принятых данных
    def calParserBin(self, data):

        self.parsePosition = 0                                          # Важно ! Обнуление счетчика для разбора данных
        self.listActiveZone = []

        # Координаты начальной точки поездки
        self.startPointLON = self.getLON( data )
        self.startPointLAT = self.getLAT( data )

        # Разбираем список зон из калибровки пока не дойдем до конца по количеству зон
        # Первые 8 байт занимает точка старта поездки
        # todo Оттестировать на 20 зонах с целью проверки условий выхода из цикла

        numberRecord = 0
        while (ActiveZone.GPSActiveZoneCalSize-8)  > self.parsePosition :
            distance = str(self.getLong( data ))
            if distance == '0': break  # Или до пустой зоны
            (zoneName, long, lat, radius, typeZone) = self.getZoneRecord( data )
            numberRecord+= 1
            self.listActiveZone.append( [ numberRecord, zoneName, long, lat, radius, typeZone, distance ] )

