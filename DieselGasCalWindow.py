# -*- coding: utf-8 -*-
__author__ = 'AMA'

''' ************************************************************
 Базовый класс калибровочного окна
 *************************************************************'''

import wx

import ECUdata as ED
import grid
from mixin import Func


#  Диалог с калибровкой. Базовый класс
class CalWindow():
    def __init__(self, grid ):
        # Проверка что массивы RPM и TURBO не убывающие, если ла то  выходим из функции
        if Func.checkTable(ED.Turbo_table, 'Turbo') == False and Func.checkTable(ED.RPM_table, 'RPM') == False:
            title_str = u"Дизельная калибровка - " + ED.name_cal + u" Горизонталь RPM, вертикаль TURBO.  "
            dialog = wx.Dialog(ED.main_parent, -1, title_str, pos=(0, 0), size=ED.CalWindowSize)
            self.grid = grid(dialog)
            dialog.SetBackgroundColour("WHITE")
            self.grid.popupItemRead(1)
            main_sz = wx.BoxSizer(wx.VERTICAL)
            sz1 = wx.BoxSizer(wx.HORIZONTAL)
            self.cbPaint = wx.CheckBox( dialog, -1, u"Не раскрашивать" )
            self.cbShow  = wx.CheckBox( dialog, -1, u"Подача" )
            ED.calWinSetupCheckBox[0] = False
            self.cbPaint.SetValue( ED.calWinSetupCheckBox[0])
            self.cbShow.SetValue(  ED.calWinSetupCheckBox[1])

            dialog.Bind(wx.EVT_CHECKBOX, self.optionEvtCheckBox, self.cbPaint )
            dialog.Bind(wx.EVT_CHECKBOX, self.optionEvtCheckBox, self.cbShow )
            sz1.Add( self.cbPaint , 0, wx.ALIGN_BOTTOM|wx.LEFT,20 )
            sz1.Add( self.cbShow , 0, wx.ALIGN_BOTTOM|wx.LEFT, 20 )
            buttons = wx.StdDialogButtonSizer()
            OK_button = wx.Button(dialog, wx.ID_OK, u"ДА")
            OK_button.SetDefault()
            buttons.AddButton(OK_button)
            NO_button = wx.Button(dialog, wx.ID_CANCEL, u"НЕТ")
            buttons.AddButton(NO_button)
            sz1.Add( (ED.calWinButtonOffset,0),  0 ) # Пустое пространство
            sz1.Add( buttons , 0, wx.TOP|wx.RIGHT, 10 )
            main_sz.Add( self.grid , 0, wx.ALIGN_TOP  )
            main_sz.Add( sz1 , 0, wx.TOP|wx.LEFT|wx.ALIGN_TOP,0 )
            buttons.Realize()
            dialog.SetSizer(main_sz)
            result =  dialog.ShowModal()
            if result == wx.ID_OK:
                self.grid.popupItemWrite(1)
    def optionEvtCheckBox(self, evt):
        # Вызывается по событию, когда статус чек боксов изменяется
        # Не расскрашивать
        if self.cbPaint.IsChecked():
            ED.calWinSetupCheckBox[0] = True
            for row in range(ED.Cal_table_TURBO_size):
                for col in range(ED.Cal_table_RPM_size):
                    self.grid.SetCellValue(row, col, self.grid.GetCellValue(row, col))
        else:
            ED.calWinSetupCheckBox[0] = False
            for row in range(ED.Cal_table_TURBO_size):
                for col in range(ED.Cal_table_RPM_size):
                    self.grid.SetCellValue(row, col, self.grid.GetCellValue(row, col))
        # Отображение текущих значений подачи
        if self.cbShow.IsChecked():
            ED.calWinSetupCheckBox[1] = True
        else:
            ED.calWinSetupCheckBox[1] = False

# Газовая калибровка
class GasCalWindow( CalWindow ):
    def __init__(self, evt):
        CalWindow.__init__( self, grid.GasGrid )

# Дизельная калибровка
class DieselCalWindow( CalWindow ):
    def __init__(self, evt):
        CalWindow.__init__(self, grid.DieselGrid)


# Основа для газовая калибровки
class OsnovaGasCalWindow(CalWindow):
    def __init__(self, evt):
        CalWindow.__init__(self, grid.OsnovaGrid)
