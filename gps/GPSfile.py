# -*- coding: utf-8 -*-
__author__ = 'AMA'

import pickle
import ECUdata as ED
import wx
import os

def readFile( evt ):
    wildcard = "GPS (*.gp)|*.gp|"+"All files (*.*)|*.*"
    dialog = wx.FileDialog(None, u"Выберите файл для чтения данных GPS", os.getcwd()+"\data","", wildcard, wx.OPEN)
    if dialog.ShowModal() == wx.ID_OK:
        ED.zonedata.clear()
        # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try1
        with open(dialog.GetPath(), 'rb') as f:
            try:
                ED.zonedata  = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать данные настроек зон GPS',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.gps_setup = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать данные настроек GPS',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

#  Запись калибровки на диск в формате PY
def saveFile( evt ):

        wildcard = "GPS (*.gp)|*.gp|"+"All files (*.*)|*.*"
        dialog = wx.FileDialog(None, u"Выберите файл для записи данных GPS ", os.getcwd()+"\data","", wildcard,\
                               wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
            with open(dialog.GetPath(), 'wb') as f:
                pickle.dump( ED.zonedata, f)
                pickle.dump( ED.gps_setup, f)
