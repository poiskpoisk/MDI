# -*- coding: utf-8 -*-
__author__ = 'AMA'

import os
import pickle

import wx

import ECUdata as ED
from mixin import Func


#  Запись калибровки на диск в формате PY
def onCalWrite(self):
    # Проверка на неубываемость массивов
    if Func.checkAllTable()== False and Func.checkDieselCal() == False:
        wildcard = "Calibration (*.py)|*.py|"+"All files (*.*)|*.*"
        dialog = wx.FileDialog(None, u"Выберите файл для записи калибровки ", os.getcwd()+"\data","", wildcard,\
                               wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
            with open(dialog.GetPath(), 'wb') as f:
                pickle.dump( ED.Gas_table, f)
                pickle.dump( ED.Osnova_Gas_table, f)
                pickle.dump( ED.Diesel_table, f)

                pickle.dump( ED.gen_setup, f)
                pickle.dump( ED.RPM_table, f )
                pickle.dump( ED.Turbo_table, f )
                pickle.dump( ED.PPS1_table, f)
                pickle.dump( ED.PPS2_table, f)
                pickle.dump( ED.PPS2_PWM_table, f)
                pickle.dump( ED.PPS1_PWM_table, f)

                pickle.dump( ED.Speed_table, f)
                pickle.dump( ED.Speed_gas_table, f)
                pickle.dump( ED.Speed_diesel_table, f)

                pickle.dump( ED.EGT_table, f)
                pickle.dump( ED.EGT_gas_table, f)
                pickle.dump( ED.calWinSetupCheckBox, f)

                pickle.dump( ED.diesel_table_setup, f)

                pickle.dump( ED.PPSviewDIESEL_k_table, f)
                pickle.dump( ED.PPSviewGAS_k_table, f)

                dialog.Destroy()

# Чтение калибровки с диска в формате PY
def onCalRead(self):
    wildcard = "Calibration (*.py)|*.py|"+"All files (*.*)|*.*"
    dialog = wx.FileDialog(None, u"Выберите файл для чтения калибровки", os.getcwd()+"\data","", wildcard, wx.OPEN)
    if dialog.ShowModal() == wx.ID_OK:
        # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
        with open(dialog.GetPath(), 'rb') as f:

            try:
                ED.Gas_table              = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу с газовой калибровкой',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

            try:
                ED.Osnova_Gas_table = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу основа для газовой калибровки',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

            try:
                ED.Diesel_table           = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу с дизельной калибровкой',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.gen_setup              = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать не табличные значения',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.RPM_table              = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу RPM',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.Turbo_table            = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу Turbo',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPS1_table             = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу PPS1',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPS2_table             = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу PPS2',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPS2_PWM_table         = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу PPS2 PWM',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPS1_PWM_table         = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу PPS1 PWM',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.Speed_table            = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу Speed',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.Speed_gas_table        = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу Speed_gas',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.Speed_diesel_table     = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу Speed_DIESEL',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.EGT_table              = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу EGT',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.EGT_gas_table          = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу EGT gas',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.calWinSetupCheckBox    = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу положения чекбоксов',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.diesel_table_setup     = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу авторазноски для дизельной калибровки',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPSviewDIESEL_k_table  = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу зависимости PPS/PPS emul',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            try:
                ED.PPSviewGAS_k_table     = pickle.load(f)
            except:
                wx.MessageBox(u'Не удалось считать таблицу зависимости PPS/GAS',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

        # Записываем значения PPS, Turbo и RPM из таблиц
        Func.SetDataFromCal_Disc()
        ED.name_cal = dialog.GetPath()
