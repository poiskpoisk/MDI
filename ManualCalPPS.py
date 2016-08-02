# -*- coding: utf-8 -*-
__author__ = 'AMA'

import wx

class manualCalWindow( wx.MDIChildFrame ):
    def __init__(self, parent):
        wx.MDIChildFrame.__init__( self, parent, -1, u"Ручная калибровка PPS", pos = (0,0), size=(200,400),
                                   style=wx.MAXIMIZE )
        self.SetBackgroundColour( wx.SystemSettings_GetColour(0) )
        # Устанавливаем таймер для изменения, показываемых значений
        self.showTimer = wx.Timer( self )
        self.Bind(wx.EVT_TIMER, self.update, self.showTimer)
        self.showTimer.Start(300)

        main_sz = wx.BoxSizer(wx.HORIZONTAL)