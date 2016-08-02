# -*- coding: utf-8 -*-
__author__ = 'AMA'

import pickle

import wx

import ECUdata as ED


# Сообщение : Предупреждение о нужных условиях для авто и ручной калибровки PPS
def msgWarning( parent ):
        dAutocal = wx.Dialog( parent, -1, u"Предупреждение о режиме работы АВТО КАЛИБРОВКИ PPS "
                                           , pos = (550,250), size = (750,300))
        dAutocal.SetBackgroundColour("WHITE")
        sz = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL )
        st_1 = wx.StaticText( dAutocal, -1, u"Для успешной работы необходимы следующие условия:" )
        st_2 = wx.StaticText( dAutocal, -1, u"1 Кнопка у водителя ВКЛ. 2 Ручное управление режимом включения ВКЛ.")
        st_3 = wx.StaticText( dAutocal, -1, u"3 Температура редуктора БОЛЬШЕ МИНИМУМА в течении всего времени "
                                            u"калибровки" )
        st_4 = wx.StaticText( dAutocal, -1, u"Если все условия выполненны, нажмите ДА и ждите результата." )
        st_1.SetFont(font)
        st_2.SetFont(font)
        st_3.SetFont(font)
        st_4.SetFont(font)
        sz.Add( st_1,    0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_TOP,20)
        sz.Add( st_2,    0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_TOP,20)
        sz.Add( st_3,    0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_TOP,20)
        sz.Add( st_4,    0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_TOP,20)
        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(dAutocal, wx.ID_OK, u"ДА")
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(dAutocal, wx.ID_CANCEL, u"НЕТ"))
        buttons.Realize()
        sz.Add( (0,20)) # Пустое пространство
        sz.Add(buttons,  0, wx.LEFT|wx.ALIGN_LEFT,250)
        dAutocal.SetSizer(sz)
        res = dAutocal.ShowModal()
        dAutocal.Destroy()
        return ( res )

# Функция выбора номера элемента, по его значению.
def array_number( mas, Volume_now ):
    '''
    Функция выбора номера элемента, по его значению. Используется для подсветки текущего значения, соответствующего
    текущему RPM и TURBO. Учтено, что в Pythone списки начинаются с 0, а в CDS массивы с 1 !!!
    '''
    i=0
    j = ArraySize = len(mas)-1
    while i != j:
        med=(i+j)/2
        if Volume_now  > mas[med]: i=med+1
        else : j=med

# Искомый элемент находится справа от полученного срединного индекса, но не крайний справа *)

    if Volume_now > mas[i] and  i != ArraySize :
        if abs( Volume_now-mas[i] ) < abs( Volume_now-mas[i+1] ):
            Array_number = i			# Ошибка у срединного индекса меньше *)
        else:
            Array_number =i+1			# Ошибка у следующего элемента справа от срединного индекса меньше *)

    elif i != 1 :				        # Искомый элемент находится слева от полученного срединного индекса, но не первый элемент массива *)
        if abs( Volume_now-mas[i] ) < abs( Volume_now-mas[i-1] ):
            Array_number =i			    # Ошибка у срединного индекса меньше *)
        else:
            Array_number =i-1			#  Ошибка у предидущего элемента справа от срединного индекса меньше *)
    else:                   			# Искомый элемент меньше первого элемента массива *)
        Array_number = 1

    return( Array_number )

# Разноска для одноколоночных таблиц
def Raznoska( table, min_value, max_value):
    '''
    :param table: Таблица, в которой происходит разноска
    :param min_value: Значение для начала разноски
    :param max_value: Значение для окончания разноски
    :return:
    '''
    size = len(table)
    if min_value < 0 or max_value < 0:
        for row in range(0, size):
            table[row] = 0
    else:
        table[0]= min_value
        table[size-1]= max_value
        delta = float(  table[size-1] - table[0] ) / float( size-1)
        for row in range(1, size):
            table[row]=table[row-1]+delta
            if table[row] < 0 :
                table[row] = 0
            else:
                table[row] = int(table[row])

# Устанавливает значения в массиве из данных калибровки при чтении с Диска
def SetDataFromCal_Disc():
    ED.gen_setup['RPM_min']   = ED.RPM_table[0]
    ED.gen_setup['RPM_max']   = ED.RPM_table[ED.Cal_table_RPM_size-1]
    ED.gen_setup['Turbo_min'] = ED.Turbo_table[0]
    ED.gen_setup['Turbo_max'] = ED.Turbo_table[ED.Cal_table_TURBO_size-1]
    ED.gen_setup['PPS1_min']  = ED.PPS1_table[0]
    ED.gen_setup['PPS1_max']  = ED.PPS1_table[ED.PPS_table_size-1]

# проверка массивов на неубываемость
def checkTable( table, label ):
    for row in range(1,len(table)):
            if (( table[row]-table[row-1]) < 0) or (table[row]<0):
                #print table[row], table[row-1], row
                wx.MessageBox(u'Неубывающиq массив или массив с отрицательными элементами -> '+label+
                              u'. Это серьезнаяя ошибка. Оборудование может работать не корректно. Устраните',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
                return (True)
    return (False)

def checkAllTable( ):

    if checkTable( ED.RPM_table, 'RPM' ) or checkTable( ED.Turbo_table, 'Turbo' ) or\
            checkTable( ED.PPS1_table, 'PPS1' ) or checkTable( ED.Speed_table, u'Скорость' ) or \
           checkTable( ED.EGT_table, 'EGT' ):
        if ED.gen_setup['PPS_type'] == 0:
            # Проверяем PPS2 только в том случае если 2 аналоговых жатчика
            if checkTable(ED.PPS2_table, 'PPS2'):
                return (True)
            else:
                return (False)
        return(True)
    else:
        return (False)

def checkDieselCal():
    for row in range(ED.Cal_table_TURBO_size):
                for col in range(ED.Cal_table_RPM_size):
                    if ED.Diesel_table[row][col]>99 and ED.Diesel_table[row][col]<>0:
                        wx.MessageBox(u'В дизельной калибровке максимальное значение 99% а минимальное >0.'
                                      u' Это серьезнаяя ошибка. Оборудование может работать не корректно. Устраните',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
                        return (True)
    return (False)

# Рекурсивная разноска, последний отрезок убывает, до этого возрастают значения в отрезках
def recRaznoska( table, result, cycle, len_table,row, label ):
    '''

    :param table:  Строка для обработки
    :param result:
    :param cycle: Переменная номера итерации
    :param len_table: Длина строки для обработки
    :param row:  Номер строки которая обрабатывается
    :param label:  Текст "строка" или "столбец"
    :return:
    '''
    max =0
    # ищем начало отрезка для разноски
    min = table[0]
    # ищем конец отрезка для разноски
    for i in range(1, len(table) ):
        if table[i] !=0 :
            max = table[i]
            break

    # Проверка, что найдены начало и конец отрезка для разноски
    if min == 0 or max == 0 :
        wx.MessageBox(label+str(row)+u' Не найдено начало или конец отрезка '+str(cycle)+u' для разноски. Приведите все в порядок и '
                                                           u'попробуйте еще раз',
                      caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
        return (0)
    if i < 2 :
        wx.MessageBox(label+str(row)+u' Отрезок '+str(cycle)+u' для масштабирования слишком мал. '
                                             u'Приведите все в порядок и попробуйте еще раз',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
        return 0
    # Проверка, ноборот что начальное значение больше конечного
    delta_segment = max - min
    delta_step = float(delta_segment)/float(i)

    len_table -=i
    if len_table == 1 : # Последний отрезок, значения на котором убывают
        buf=[0 * x for x in range(i+1)]
        buf[0] = min
        for x in range( 1, len(buf) ):
            buf[x]=buf[x-1]+delta_step
        result +=  buf
        return result
    else:
        buf=[0 * x for x in range(i)]
        buf[0] = min
        for x in range( 1, len(buf) ):
            buf[x]=buf[x-1]+delta_step
        table = table[i:]
        cycle +=1
        result +=  buf
        return recRaznoska(table, result, cycle, len_table, row, label )

def readSetupFile():
    try:
        d = open('mdisettings.dat', 'rb')
        d.close()
    except:
        wx.MessageBox(u'Не удалось считать таблицу с програмными настройками, создали новую',
                      caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
        # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
        with open('mdisettings.dat', 'wb') as f:
            pickle.dump(ED.prog_setup, f)
    else:
        # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
        with open('mdisettings.dat', 'rb') as f:
            try:
                ED.prog_setup = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу с програмными настройками',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
                exit(1)

