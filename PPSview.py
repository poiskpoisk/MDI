# -*- coding: utf-8 -*-#
__author__ = 'AMA'
'''
Отображает в виде таблицы и графиков зависимости подачи газа и эмуляции PPS от PPS
'''

import wx
import grid
import ECUdata as ED
import matplotlib.figure
from   matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# Таблица зависимости подачи газа от PPS

def PPSview(Cal_hold, DIESEL_cal):

    PPSview_dialog=wx.Dialog(ED.main_parent, -1, u"Таблица зависимости подачи газа и эмуляции PPS от PPS",
                       pos = (100,00), size = (900,768))
    PPSview_dialog.SetBackgroundColour("WHITE")
    main_sz = wx.BoxSizer( wx.HORIZONTAL )
    sz0 = wx.BoxSizer (wx.VERTICAL)
    sz1 = wx.FlexGridSizer(rows=2, cols=3, hgap=0, vgap=50 )
    # def __init__(self, parent, label, size, row_hight, row_hight_label, border, sizer, table )
    grid.PPSviewGrid(PPSview_dialog,  "PPS1",     ED.PPS_table_size, 20, 20, 10, sz1, ED.PPS1_table )
    gas_k    = grid.PPSviewGrid(PPSview_dialog,  u"ГАЗ_K",     ED.PPS_table_size, 20, 0,  0,  sz1,ED.PPSviewGAS_k_table)
    diesel_k = grid.PPSviewGrid( PPSview_dialog,  u"ДТ_K",  ED.PPS_table_size, 20, 0, 0,
                                     sz1, ED.PPSviewDIESEL_k_table )
    buttons = wx.StdDialogButtonSizer()
    b = wx.Button(PPSview_dialog, wx.ID_OK, u"ДА", size=(100, 25))
    b.SetDefault()
    buttons.AddButton(b)
    buttons.AddButton(wx.Button(PPSview_dialog, wx.ID_CANCEL, u"НЕТ", size=(100, 25)))
    buttons.Realize()
    sz0.Add( sz1,    0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_TOP,0)
    sz0.Add( buttons,0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_BOTTOM,5)

    main_sz.Add( sz0,    0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_TOP,0)
     # 1. Создание фигуры
    PPSview_dialog.figure = matplotlib.figure.Figure ()
    # 2. Создание осей
    PPSview_dialog.axes =  PPSview_dialog.figure.add_subplot (2, 1, 1)
    PPSview_dialog.axes2 = PPSview_dialog.figure.add_subplot (2, 1, 2)
    # 3. Создание панели для рисования с помощью Matplotlib
    PPSview_dialog.canvas = FigureCanvasWxAgg (PPSview_dialog, -1, PPSview_dialog.figure)
    PPSview_dialog.canvas.SetMinSize ((700, 720))
    # Размещение элементов управления в окне
    mSizer = wx.FlexGridSizer (0, 1)
    mSizer.AddGrowableCol (0)
    mSizer.AddGrowableRow (5)
    # Размещение элементов интерфейса
    mSizer.Add(PPSview_dialog.canvas, flag=wx.ALL | wx.EXPAND, border=2)
    main_sz.Add(mSizer)
    PPSview_dialog.Layout()
    ED.dialog    = PPSview_dialog
    ED.diesel_k  = diesel_k
    ED.gas_k     = gas_k
    calcGraph(Cal_hold, DIESEL_cal, ED.dialog , ED.diesel_k, ED.gas_k )

    PPSview_dialog.SetSizer(main_sz)
    result =  PPSview_dialog.ShowModal()
    if result == wx.ID_OK:
        for row in range ( ED.PPS_table_size) :
            ED.PPSviewDIESEL_k_table[row] = int(diesel_k.GetCellValue ( row,0 ))
            ED.PPSviewGAS_k_table[row]    = int(gas_k.GetCellValue ( row,0 ))

    PPSview_dialog.Destroy()

def calcGraph(Cal_hold, DIESEL_cal, dialog, diesel_k, gas_k ):
    PPSdelta100 = ED.PPS1_table[ED.PPS_table_size-1]-ED.PPS1_table[0]
    Max_PPS_emul =  ( DIESEL_cal* PPSdelta100)/100
    for i in range(ED.PPS_table_size):
        PPSdelta = ED.PPS1_table[i] - ED.PPS1_table[0]
        try:
            k = float(PPSdelta)/float(PPSdelta100)
        except:
            k = 0
        ED.PPSviewDIESEL_table[i]           = ED.PPS1_table[0] + int( Max_PPS_emul*k )
        ED.PPSviewDIESEL_overdrive_table[i] = ED.PPS1_table[0] + (Max_PPS_emul* int( diesel_k.GetCellValue ( i,0 )))/100
        if ED.PPSviewDIESEL_overdrive_table[i] > ED.PPS1_table[i] :
            ED.PPSviewDIESEL_overdrive_table[i] = ED.PPS1_table[i]

        ED.PPSviewGAS_table[i] = int( Cal_hold * k )
        ED.PPSviewGAS_overdrive_table[i] = ( Cal_hold * int( gas_k.GetCellValue( i,0 ) ) )/100
    # Удалим предыдущий график, если он есть
    dialog.axes.clear()
    dialog.axes2.clear()

    # Нарисуем новый график
    dialog.axes.plot  (ED.PPS1_table, ED.PPSviewGAS_table )
    dialog.axes.plot  (ED.PPS1_table, ED.PPSviewGAS_overdrive_table)

    dialog.axes2.plot (ED.PPS1_table, ED.PPSviewDIESEL_table )
    dialog.axes2.plot (ED.PPS1_table, ED.PPSviewDIESEL_overdrive_table )
    dialog.axes2.plot (ED.PPS1_table, ED.PPS1_table)

    # Включим сетку
    dialog.axes.grid ()
    dialog.axes2.grid ()
    dialog.axes.legend ([u"Подача класика", u"Подача по новому"], prop={"family": "verdana"}, loc='upper left')
    dialog.axes.text (ED.PPS1_table[1], ED.PPSviewGAS_table[29],
                      u"Газ калибровка - "+str(Cal_hold), family="verdana")
    dialog.axes2.legend ([u"PPS_emul_k","PPS_emul","PPS"], prop={"family": "verdana"}, loc='upper left' )
    dialog.axes2.text (ED.PPS1_table[1], 3000, u"Эмуляция - "+str(DIESEL_cal)+"%", family="verdana")
    # Установим пределы по осям
    if 2*Cal_hold > 220 :
        dialog.axes.set_ylim ([0, 220])
    else:
        dialog.axes.set_ylim ([0, 2*Cal_hold])
    # Обновим окно
    dialog.canvas.draw()





