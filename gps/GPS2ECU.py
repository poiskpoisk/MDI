# -*- coding: utf-8 -*-
__author__ = 'AMA'

import wx
import ECUdata as ED
import Shema

# Должен иметь определенные элементы интерфейса !
class GPS2ECU ( Shema.ReadWriteECU ):

    bufSize = 4096  # Обящательный атрибут ! Размер блока считывеамых данных, CRC внутри 2 последних байта

    def __init__(self):
        self.sendCalBuf         = [0 for x in range(GPS2ECU.bufSize)]   # Обящательный атрибут ! Инициализируем буфер
        self.GPSnoZoneDataSize  = 100                                   # Размер GPS данных, не данные зоны
        self.GPSZoneDataEnd = GPS2ECU.bufSize - self.GPSnoZoneDataSize  # Смещение начала GPS данных не зоны

    # Стандартный диалог на запись калибровки и отсылка команды
    def GPSwriteECU( self, evt):
        return self.dialogWriteFLASH( self.writeGPScalRequest )

    # Обязательный методод !, реализующий формирования буффера для отсылки в ECU
    def createCal2Send(self):
        self.parsePosition = 0          # Важно ! обнуляет указатель на данные, что бы парсить с начала
        zonedata = ED.zonedata.items()

        for key, val in zonedata:
            self.setZoneRecord( val )

        # Данные GPS не зоны. ------------------------------------------------------------------
        zpLON = str(ED.gps_setup['zeroPointLONgrad']) + '.' + str(ED.gps_setup['zeroPointLONsec'])
        zpLAT = str(ED.gps_setup['zeroPointLATgrad']) + '.' + str(ED.gps_setup['zeroPointLATsec'])
        self.parsePosition = self.GPSZoneDataEnd

        self.setLON( zpLON )           # Стартовая точка долгота
        self.setLAT( zpLAT )           # Стартовая точка широта
        # Типы зон
        self.setByte( ED.gps_setup['zoneType0_GAS'] )
        self.setByte( ED.gps_setup['zoneType0_DIESEL'] )
        self.setByte( ED.gps_setup['zoneType1_GAS'] )
        self.setByte( ED.gps_setup['zoneType1_DIESEL'] )
        self.setByte( ED.gps_setup['zoneType2_GAS'] )
        self.setByte( ED.gps_setup['zoneType2_DIESEL'] )
        self.setByte( ED.gps_setup['zoneType3_GAS'] )
        self.setByte( ED.gps_setup['zoneType3_DIESEL'] )

        self.setCRC()                                       # Записываем CRC в 2 последних байта кодировки

    # Открываеи диалог прогресса выполнения и посылает команду на чтение калибровки
    def GPSreadECU( self, evt):
        ED.zonedata.clear()
        GPS2ECU.progressDlg = wx.ProgressDialog(u"Процент выполнения чтения калибровки GPS", u"Чтение из FLASH памяти:",
                                              maximum=5, parent=ED.main_parent, style=wx.PD_APP_MODAL)
        self.sendCommandECU( self.readGPScalRequest, 1)
        GPS2ECU.progressDlg.Update(1, u'Команда на считывание послана ECU')

    # Обязательный метод, реализующий разбор принятых данных
    def calParserBin( self, data):
        key                 = 0
        self.parsePosition  = 0                   # Важно ! обнуляет указатель на данные, что бы парсить с начала

        # Разбираем список зон из калибровки пока не дойдем до конца по количеству зон
        while ( self.GPSZoneDataEnd > self.parsePosition ) :
            (zoneName, long, lat, radius, typeZone ) = self.getZoneRecord( data )
            if int(radius) == 0: break                                  # Или до пустой зоны
            key+=1                                                      # Новый ключ для новой записи в словаре
            dict ={ key: ( zoneName, long, lat, radius, typeZone) }     # Собираем из получившихся данных запись СЛОВАРЯ
            ED.zonedata.update( dict )                                  # Обновляем глобальный словарь

        # Данные GPS не зоны. ------------------------------------------------------------------

        self.parsePosition =  self.GPSZoneDataEnd
        zeroPointLON = self.getLON( data )                      # Стартовая точка долгота
        ED.gps_setup['zeroPointLONgrad'] = zeroPointLON[:3]
        ED.gps_setup['zeroPointLONsec']  = zeroPointLON[4:]
        zeroPointLAT = self.getLAT( data )                      # Стартовая точка широта
        ED.gps_setup['zeroPointLATgrad'] = zeroPointLAT[:2]
        ED.gps_setup['zeroPointLATsec']  = zeroPointLAT[3:]

        # Типы зон
        ED.gps_setup['zoneType0_GAS']       = self.getByte( data )
        ED.gps_setup['zoneType0_DIESEL']    = self.getByte( data )
        ED.gps_setup['zoneType1_GAS']       = self.getByte( data )
        ED.gps_setup['zoneType1_DIESEL']    = self.getByte( data )
        ED.gps_setup['zoneType2_GAS']       = self.getByte( data )
        ED.gps_setup['zoneType2_DIESEL']    = self.getByte( data )
        ED.gps_setup['zoneType3_GAS']       = self.getByte( data )
        ED.gps_setup['zoneType3_DIESEL']    = self.getByte( data )