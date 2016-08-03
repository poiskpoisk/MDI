# -*- coding: utf-8 -*-
__author__ = 'AMA'

from gps import GPSactiveZone
from gps import GPS2ECU
import ReadWriteCalECU

''' ******************************************************************
 Инициализация данных, поступающих из ECU и глобальных переменных
 Нужна, что бы удобно было обращаться из разных мест
 Так же некоторые функции, которые используются из многих модулей ( удобно так как этот модуль везде подключен )
 ********************************************************************'''
# глобальные копии, нужно что бы в модуле grid отображалось бегание по клеточкам калибровчочной таблицы
RPM=0
Turbo=0

thser=''

main_parent = 1 # ID главного окна, которое будет родительским для всех остальных

# Чекбоксы калибровочных таблиц Раскраска и Отобращатель состояния
# Оставить глобальным, пытался что бы хранилось в классе сделать - жуткий гемор
calWinSetupCheckBox   = [True, False]

#---------------------- Размеры таблиц --------------------------------
Cal_table_RPM_size   = 48  # размер калибровочной таблицы по RPRM
Cal_table_TURBO_size = 32  # размер калибровочной таблицы по TURBO
PPS_table_size       = 32
Speed_table_size     = 40
EGT_table_size       = 40
Osnova_table_size    = 48

# В питоне нет массивов. Это списки и нужно задать их, выполнив инициализацию
Turbo_table         = [0 * x for x in range(Cal_table_TURBO_size)]
RPM_table           = [0 * x for x in range(Cal_table_RPM_size)]
PPS1_table          = [0 * x for x in range(PPS_table_size)]
PPS2_table          = [0 * x for x in range(PPS_table_size)]
PPS1_PWM_table      = [0 * x for x in range(PPS_table_size)]
PPS2_PWM_table      = [0 * x for x in range(PPS_table_size)]

Speed_table         = [0 * x for x in range(Speed_table_size )]
Speed_gas_table     = [0 * x for x in range(Speed_table_size )]
Speed_diesel_table  = [0 * x for x in range(Speed_table_size )]

EGT_table           = [0 * x for x in range(EGT_table_size)]
EGT_gas_table       = [0 * x for x in range(EGT_table_size)]

Gas_table           = [[0 for x in range(Cal_table_RPM_size)] for x in range(Cal_table_TURBO_size)]  # список из списков
Osnova_Gas_table    = [[0 for x in range(Cal_table_RPM_size)] for x in range(Cal_table_TURBO_size)]  # список из списков
Diesel_table        = [[0 for x in range(Cal_table_RPM_size)] for x in range(Cal_table_TURBO_size)]  # список из списков
# Таблица для хранения опорных точек для основы газовой калибровки
osnovaTable = [0 * x for x in range(Osnova_table_size)]

# Буфер для копирования сюдя выделенных значений и их последующей вставки
bufer = [['*' for x in range(Cal_table_RPM_size)] for x in range(Cal_table_TURBO_size)]  # список из списков

# Вычисленное значение подачи газа в зависимости от PPS используется в PPSview
PPSviewGAS_table    = [0 * x for x in range(PPS_table_size)]
# Вычисленное значение подачи газа в зависимости от PPS используется в PPSview с учетом стартовой коррекции
PPSviewGAS_overdrive_table    = [0 * x for x in range(PPS_table_size)]
# Значение поправочеого коэффициента в зависимости от PPS
PPSviewGAS_k_table = [0 * x for x in range(PPS_table_size)]

# Вычисленное значение эмуляции PPS в зависимости от PPS по классике через К, используется в PPSview
PPSviewDIESEL_table = [0 * x for x in range(PPS_table_size)]
# Вычисленное значение эмуляции PPS в зависимости от PPS с учетом поправочного коэффициента, используется в PPSview
PPSviewDIESEL_overdrive_table = [0 * x for x in range(PPS_table_size)]
# Значение поправочеого коэффициента в зависимости от PPS
PPSviewDIESEL_k_table = [0 * x for x in range(PPS_table_size)]

# Кортеж для хранения данных, вводимых в GeneralSetup
# Abs_max_GAS Абсолютный максимум газа закоторый нельзя выходить при расчетах
# safety_level_GAS Совсем безопамсный уровень подачи газа, когда не требуется его уменьшение в зависимости от скорости
# PPS_type = 0 - 2 аналоговых датчика, 1 - 1 датчик, 2 - цифра
gen_setup = { 'RPM_max': 0, 'RPM_min': 0, 'Turbo_max': 0, "V_cor": 0,"K_RPM": 0,"EGT_max": 0,
             'Turbo_min': 0 , "Red_press": 0, "PPS1_min":0, "PPS1_max":0,  "T_red":0,  "PPS_type":0,
              'Abs_max_GAS':0, 'safety_level_GAS':0, 'GPS_mode':0, 'CL_max':0, 'comSpeed':0 }

# Кортеж для хранения данных, вводимых в ProgramSetup
# typeECU =0 МЕГА typeECU=1 НАНО
# typeRedCal =0  Считывать typeRedCal = 1 Не считывать
prog_setup = { 'SSID':0, 'WIFI_pass':0, 'IP_ECU':0, 'delay':4 , 'typeRedCal':1, 'typeECU':0, 'delayBlock':500,
               'comSpeed':0, 'comSpeedReal':9600, "delayFirstCon":2000 }

gps_setup ={ "zoneType0_GAS":0, "zoneType0_DIESEL":0, "zoneType1_GAS":0, "zoneType1_DIESEL":0,
             "zoneType2_GAS":0, "zoneType2_DIESEL": 0,
             "zeroPointLONgrad":0, "zeroPointLATgrad":0, "zeroPointLONsec":0, "zeroPointLATsec":0,
             "zeroPointLON": b'\x00\x00\x00\x00',    "zeroPointLAT": b'\x00\x00\x00\x00' }

# Переменные, использующиеся в TableSetup для автокалибровки и ручной калибровки PPS
PPSview =0 # используется в PPSview

# Прогресс бары, глобально определены, что бы можно было их убивать из разных мест
progressDialog  = 0    # Диалог прогресса записи калибровки


# Значения для авторазносок в калибровочной таблице
diesel_table_setup     = {'Emul_min': 0, 'Emul_max': 0 }

name_cal='' # Имя файла считанной калибровки, для вывода в верхнюю строку окна калибровки
# для передачи глобальных значений в модуле PPSview
Cal_hold = DIESEL_cal = dialog = diesel_k = gas_k =  0

# Размеры экранных элементов для различных экранных разрешений
mainPriborSize      = (1360,768)   # Главное окно
CalWindowSize       = (1600,853)   # Окно калибровок
colSize             = 32           # Ширина колонок в пикселях для калибровочных таблиц
rowSize             = 23           # Ширина СТОЛЮЦОВ в пикселях для калибровочных таблиц
calGridLabelFont    = 11           # Шрифт для заголовков в калибровочной таблице
calGridCellFont     = 11           # Шрифт для ячеек в калибровочной таблице
calWinButtonOffset  = 1220         # Смещение для положения кнопок ОК в калибровочной таблице

# GPS

zonedata = {
    1: ("New group 1    ", "000.000001", "00.000000", "100", '1'),
}

flag_ECU_ON_VISU    = False
flag_Relay          = False  # Сигнал включения главного реде, аналог gRELAY в ESX

az      = GPSactiveZone.ActiveZone()
rw      = ReadWriteCalECU.ReadWriteCalECU_MEGA()
rwGPS   = GPS2ECU.GPS2ECU()
