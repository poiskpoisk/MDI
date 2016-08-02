# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
from struct import *
import ECUdata as ED
from mixin import InputMixin as SM

# Модальный диалог настроек GPS
class SetupGPSWindow(SM.InputMixin):
    def __init__(self, evt ):
        dialogSetup = wx.Dialog(ED.main_parent, -1, u"Настройки параметров GPS", pos = (100,150), size = (800,500))
        dialogSetup.SetBackgroundColour("WHITE")
        main_sizer = wx.FlexGridSizer(rows=4, cols=2, hgap=5, vgap=5)

        zoneTypeSizer    = self.box( dialogSetup, u"Коэффициенты по газу и дизелю для разных типов зон", ED.gps_setup,
                                    ( u"Тип зоны 0 Коэффициент по газу :",  "zoneType0_GAS",    3),
                                    ( u"Тип зоны 0 Коэффициент по дизелю:", "zoneType0_DIESEL", 3),
                                    (u"Тип зоны 1 Коэффициент по газу :",   "zoneType1_GAS",    3),
                                    (u"Тип зоны 1 Коэффициент по дизелю:",  "zoneType1_DIESEL", 3),
                                    (u"Тип зоны 2 Коэффициент по газу :",   "zoneType2_GAS",    3),
                                    (u"Тип зоны 2 Коэффициент по дизелю:",  "zoneType2_DIESEL", 3),
                                    (u"Тип зоны 3 Коэффициент по газу :",   "zoneType3_GAS",    3),
                                    (u"Тип зоны 3 Коэффициент по дизелю:",  "zoneType3_DIESEL", 3) )

        otherSizer = self.box(dialogSetup, u"Разное", ED.gps_setup,
                                    (u"Нулевая точка, долгота градусы:", "zeroPointLONgrad", 3 ),
                                    (u"Нулевая точка, долгота секунды:", "zeroPointLONsec", 6, 80),
                                    (u"Нулевая точка, широта градусы :", "zeroPointLATgrad", 2 ),
                                    (u"Нулевая точка, широта градусы :", "zeroPointLATsec", 6, 80) )

        buttons_sizer = wx.StdDialogButtonSizer()
        b = wx.Button(dialogSetup, wx.ID_OK, u"Принять изменения")
        b.SetDefault()
        buttons_sizer.AddButton(b)
        buttons_sizer.AddButton(wx.Button(dialogSetup, wx.ID_CANCEL, u"Отказаться"))
        buttons_sizer.Realize()

        main_sizer.Add(zoneTypeSizer,   0, wx.LEFT  |wx.TOP, 30)
        main_sizer.Add(otherSizer,      0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(buttons_sizer,   0, wx.LEFT | wx.TOP, 25)

        main_sizer.Add((0, 10))  # Пустое пространство

        dialogSetup.SetSizer(main_sizer)
        dialogSetup.ShowModal()
        dialogSetup.Destroy()



