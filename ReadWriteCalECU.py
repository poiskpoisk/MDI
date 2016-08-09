# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import ECUdata as ED
from mixin import Func
import Shema

# Формирует и передает для записи в ECU текущую калибровку, посылает запрос на чтение и парсит калибровку при приеме
class ReadWriteCalECU( Shema.ReadWriteECU ):

    bufSize = 4096  # Обязательный атрибут для ЗАПИСИ! Размер блока считывеамых данных

    def __init__(self):
        self.sendCalBuf    = [0 for x in range(self.bufSize)]  # Инициализируем буфер для отправки в ECU

    # Выполняет все проверки безопсаности перед записью ECU и шлет запрос на запись
    def writeCalECU(self, evt):
        # Проверка на неубываемость массивов
        if Func.checkAllTable() == True or Func.checkDieselCal() == True: return False
        return self.dialogWriteFLASH( self.writeCalRequest )

    # Формирует буфер для передачи в ECU ___ ОБЯЗАТЕЛЬНЫЙ МЕТОД !
    def createCal2Send(self):

        self.createOsnova_table()                   # Формируем список опорных точек из ПОЛНОЙ ОПРНОЙ таблицы
        self.parsePosition = 0                      # Начинаем формировать буфер для пересылки с первого элементв

        self.setCalTable( ED.Gas_table )            # Формируем газовую калибровку
        self.setCalTable( ED.Diesel_table )         # Формируем дизельную калибровку
        self.setWordTable( ED.RPM_table )           # Таблицы RPM
        self.setWordTable( ED.Turbo_table )         # Таблицы Turbo
        self.setWordTable( ED.PPS1_table )
        self.setWordTable( ED.PPS1_PWM_table )
        self.setWordTable( ED.PPS2_table )
        self.setWordTable( ED.PPS2_PWM_table )
        self.setWordTable( ED.PPSviewGAS_k_table )
        self.setWordTable( ED.PPSviewDIESEL_k_table )
        self.setWordTable( ED.EGT_table )
        self.setByteTable( ED.EGT_gas_table )
        self.setWord( ED.gen_setup['K_RPM'] )       # Коэффициент коррекции для RPM
        self.setWord( ED.gen_setup['EGT_max'] )
        self.setByte( 50 )                          # Флаг, что записанна осмысленная калибровка
        self.setByte( ED.gen_setup['PPS_type'] )
        self.setByte( ED.gen_setup['GPS_mode'] )
        self.setByte( ED.gen_setup['comSpeed'] )    # скорось COM порта ECU
        self.setByteTable( ED.osnovaTable )         # Опорные точки для основы газовой калибровки
        self.setByte( ED.diesel_table_setup['Emul_min'] ) # Минимум и максимум для разноски дизеля
        self.setByte( ED.diesel_table_setup['Emul_max'] )

    # Формируем список опорных точек из ПОЛНОЙ ОПРНОЙ таблицы
    def createOsnova_table(self):
        i = 0
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if ED.Osnova_Gas_table[row][col] != 0:
                    # Количество опорных точек ограничено
                    if i <= ED.Osnova_table_size - 3:
                        ED.osnovaTable[i] = row
                        ED.osnovaTable[i + 1] = col
                        ED.osnovaTable[i + 2] = ED.Osnova_Gas_table[row][col]
                        i += 3
                    else:
                        wx.MessageBox(u'Количество опорных точек в таблице '
                                      u'Газовой основы не должно превышать 16',
                                      caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

    # Парсит двоичные данные, поступающие из ECU ( общее для NANO и МЕГи ) ____ ОБЯЗАТЕЛЬНЫЙ МЕТОД !
    def calParserBin(self, calFromECU):

        self.parsePosition = 0

        ED.Gas_table    = self.getCalTable( ED.Gas_table,    calFromECU )    # Формируем газовую калибровку
        ED.Diesel_table = self.getCalTable( ED.Diesel_table, calFromECU )    # Формируем дизельную калибровку
        ED.RPM_table            = self.getWordTable( ED.RPM_table,   calFromECU )   # Таблицы RPM
        ED.Turbo_table          = self.getWordTable( ED.Turbo_table, calFromECU )   # Таблицы Turbo
        ED.PPS1_table           = self.getWordTable( ED.PPS1_table,             calFromECU  )
        ED.PPS1_PWM_table       = self.getWordTable( ED.PPS1_PWM_table,         calFromECU )
        ED.PPS2_table           = self.getWordTable( ED.PPS2_table,             calFromECU )
        ED.PPS2_PWM_table       = self.getWordTable( ED.PPS2_PWM_table,         calFromECU )
        ED.PPSviewGAS_k_table   = self.getWordTable( ED.PPSviewGAS_k_table,     calFromECU )
        ED.PPSviewDIESEL_k_table= self.getWordTable( ED.PPSviewDIESEL_k_table,  calFromECU )
        ED.EGT_table            = self.getWordTable( ED.EGT_table,              calFromECU )
        ED.EGT_gas_table        = self.getByteTable( ED.EGT_gas_table,          calFromECU )
        ED.gen_setup['K_RPM']   = self.getWord( calFromECU )                 # Коэффициент коррекции для RPM
        ED.gen_setup['EGT_max'] = self.getWord( calFromECU )
        self.getByte(calFromECU) # Флаг, что записанна осмысленная калибровка в питоньей программе не используется !
        ED.gen_setup['PPS_type'] = self.getByte( calFromECU )
        ED.gen_setup['GPS_mode'] = self.getByte( calFromECU )
        ED.gen_setup['comSpeed'] = self.getByte( calFromECU )           # скорось COM порта ECU
        ED.osnovaTable = self.getByteTable(ED.osnovaTable, calFromECU )# Опорные точки для основы газовой калибровки
        ED.diesel_table_setup['Emul_min'] = self.getByte(calFromECU)    # Минимум и максимум для разноски дизеля
        ED.diesel_table_setup['Emul_max'] = self.getByte(calFromECU)

        # Записываем значения PPS, Turbo и RPM и OSNOVA из таблиц
        self.setDataFromCal()

    # Посылаем запрос на ЧТЕНИЕ калибровки из ECU, РАЗБОР КАЛИБРОВКИ ПРОИСХОДИТ В МОДУЛЕ THSERIAL (90)
    def readCalECU(self, evt ):
        ReadWriteCalECU.progressDlg = wx.ProgressDialog(u"Процент выполнения чтения калибровки в EEPROM", u"Чтение:", maximum=5,
                                              parent=ED.main_parent, style=wx.PD_APP_MODAL)
        self.sendCommandECU( self.readCalRequest )
        ReadWriteCalECU.progressDlg.Update(1, u'Команда на считывание послана ECU')
        ED.name_cal = u'СЧИТАННА ИЗ ECU'

    # Устанавливает значения в массиве из данных калибровки
    def setDataFromCal(self):
        if ED.gen_setup['comSpeed'] == 0:
            ED.gen_setup['comSpeedReal'] = 9600
        elif ED.gen_setup['comSpeed'] == 1:
            ED.gen_setup['comSpeedReal'] = 19200
        elif ED.gen_setup['comSpeed'] == 2:
            ED.gen_setup['comSpeedReal'] = 57600
        elif ED.gen_setup['comSpeed'] == 3:
            ED.gen_setup['comSpeedReal'] = 115200

        ED.gen_setup['RPM_min'] = ED.RPM_table[0]
        ED.gen_setup['RPM_max'] = ED.RPM_table[ED.Cal_table_RPM_size - 1]
        ED.gen_setup['Turbo_min'] = ED.Turbo_table[0]
        ED.gen_setup['Turbo_max'] = ED.Turbo_table[ED.Cal_table_TURBO_size - 1]
        ED.gen_setup['PPS1_min']  = ED.PPS1_table[0]
        ED.gen_setup['PPS1_max']  = ED.PPS1_table[ED.PPS_table_size - 1]
        # Восстанавливаем таблицу основы калибровки
        for i in range(0, ED.Osnova_table_size, 3):
            row = ED.osnovaTable[i]
            col = ED.osnovaTable[i + 1]
            vol = ED.osnovaTable[i + 2]
            if vol != 0:
                ED.Osnova_Gas_table[row][col] = vol

# Добавляет специфику для НАНО
class ReadWriteCalECU_NANO(ReadWriteCalECU):

    def __init__(self):
        ReadWriteCalECU.__init__(self)

    # Формирует буфер для передачи в ECU
    def createCal2Send(self):
        ReadWriteCalECU.createCal2Send(self)
        self.setWord( ED.gen_setup['Red_temp_delay'] )
        self.setCRC()

    # Парсит двоичные данные, поступающие из ECU
    def calParserBin(self, calFromECU):
        ReadWriteCalECU.calParserBin(self, calFromECU )
        ED.gen_setup['Red_temp_delay'] = self.getWord( calFromECU)

# Добавляет специфику для МЕГИ
class ReadWriteCalECU_MEGA(ReadWriteCalECU):

    def __init__(self):
        ReadWriteCalECU.__init__(self)

    # Формирует буфер для передачи в ECU, данные специфичные для МЕГИ
    def createCal2Send(self):
        ReadWriteCalECU.createCal2Send(self)        # Распарсивание общих для МЕГИ и НАНО данных

        self.setWord( ED.gen_setup['V_cor'] )       # Коэффициент коррекции датчика скорости
        self.setWord( ED.gen_setup['Red_press'] )   # Давление рудуктора
        self.setWordTable( ED.Speed_table )         # Таблицы коррекции по скорости
        self.setByteTable( ED.Speed_gas_table)
        self.setByteTable( ED.Speed_diesel_table )
        self.setWord( ED.gen_setup['T_red'] )       # Температура редуктора
        self.setByte( ED.gen_setup['Abs_max_GAS'] ) # Абсолютный максимум газа
        self.setByte( ED.gen_setup['safety_level_GAS'])
        self.setByte( ED.gen_setup['CL_max'] )
        self.setByte(ED.gen_setup['LOG_mode'])
        self.setByte(ED.gen_setup['Upower'])
        print self.parsePosition

        self.setCRC()

    # Парсит двоичные данные, поступающие из ECU, данные специфичные для МЕГИ
    def calParserBin(self, calFromECU):
        ReadWriteCalECU.calParserBin(self, calFromECU)

        ED.gen_setup['V_cor'] = self.getWord( calFromECU )      # Поправка по скорости
        ED.gen_setup['Red_press'] = self.getWord( calFromECU )  # Lавление редуктора
        ED.Speed_table        = self.getWordTable( ED.Speed_table, calFromECU )                 # Коррекция по скорости
        ED.Speed_gas_table    = self.getByteTable( ED.Speed_gas_table, calFromECU )
        ED.Speed_diesel_table = self.getByteTable( ED.Speed_diesel_table, calFromECU )
        ED.gen_setup['T_red'] = self.getWord( calFromECU )      # Минимальная температура редуктора для включения
        # Abs_max_GAS Абсолютный максимум газа закоторый нельзя выходить при расчетах
        # safety_level_GAS Совсем безопамсный уровень подачи газа, когда не требуется его уменьшение
        # в зависимости от скорости
        ED.gen_setup['Abs_max_GAS']         = self.getByte( calFromECU )
        ED.gen_setup['safety_level_GAS']    = self.getByte( calFromECU )
        ED.gen_setup['CL_max']              = self.getByte( calFromECU )
        ED.gen_setup['LOG_mode']            = self.getByte(calFromECU)
        ED.gen_setup['Upower']              = self.getByte(calFromECU)