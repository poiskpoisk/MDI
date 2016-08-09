# -*- coding: utf-8 -*-#
__author__ = 'AMA'


import pickle
import ECUdata as ED
import wx
import os

def readFile( evt ):
    wildcard = "LOG (*.lgs)|*.lgs|"+"All files (*.*)|*.*"
    dialog = wx.FileDialog(None, u"Выберите файл для чтения настроек лога", os.getcwd()+"\data","", wildcard, wx.OPEN)
    if dialog.ShowModal() == wx.ID_OK:
        # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try1
        with open(dialog.GetPath(), 'rb') as f:
            try:
                ED.log_setup = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать данные настроек лога',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)


#  Запись калибровки на диск в формате PY
def saveFile( evt ):

        wildcard = "LOG (*.lgs)|*.lgs|"+"All files (*.*)|*.*"
        dialog = wx.FileDialog(None, u"Выберите файл для записи настроек лога ", os.getcwd()+"\data","", wildcard,\
                               wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
            with open(dialog.GetPath(), 'wb') as f:
                pickle.dump( ED.log_setup, f)


