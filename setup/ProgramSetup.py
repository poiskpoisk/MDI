# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import pickle

import wx

import ECUdata as ED
import mixin.InputMixin as SM
from mixin import Func


# Модальный диалог основных настроек
class programSetupWindow(SM.InputMixin):
    def __init__(self, evt):
        # Безопасно считываем файл настроек
        Func.readSetupFile()

        dialogSetup = wx.Dialog(ED.main_parent, -1, u"Настройки программы", pos = (100,150), size = (964,630))
        dialogSetup.SetBackgroundColour("WHITE")

        main_sizer = wx.FlexGridSizer(rows=3, cols=1, hgap=5, vgap=5)

        wifiSizer = self.box( dialogSetup, u"Настройки Wifi", ED.prog_setup, (u"SSID WiFi сети ECU:", "SSID", 4),
                                 (u"Пароль Wifi сети:", "WIFI_pass", 4), (u"IP ECU:", "IP_ECU", 4) )

        commonSizer = self.box( dialogSetup, u"Общие настройки", ED.prog_setup,
        (u"Задержка в мс при при определении скорости при первом подключении ( 2000 по умолчанию ):","delayFirstCon",4),
        (u"Задержка в мс при передаче символов в UART при  записиu  калибровки ( 4 по умолчанию ) :","delay", 4),
        (u"Задержка в мс при передаче БЛОКОВ символов в UART при записи калибровки (500 умолчание):","delayBlock", 4) )

        ch_choise_type_comSpeed = self.list(dialogSetup, commonSizer,
                                        u"Скорость обмена по COM порту :",
                                        ['9600', '19200',  '38400'], ED.prog_setup['comSpeed'])
        ch_choise_type_ECU = self.list(dialogSetup, commonSizer, u"Выберите тип используемого ECU:",
                                       [u'Тип М', u'Тип N'],  ED.prog_setup['typeECU'])
        ch_choise_type_redCal = self.list(dialogSetup, commonSizer, u"Считывать калибровку при запуске:",
                                          [u'Считывать', u'Не считывать'], ED.prog_setup['typeRedCal'])

        buttons_sizer = wx.StdDialogButtonSizer()
        b = wx.Button(dialogSetup, wx.ID_OK, u"Принять изменения и сохранить в файле настроек")
        b.SetDefault()
        buttons_sizer.AddButton(b)
        buttons_sizer.AddButton(wx.Button(dialogSetup, wx.ID_CANCEL, u"Отказаться от изменений"))
        buttons_sizer.Realize()

        main_sizer.Add(commonSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(wifiSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(buttons_sizer, 0, wx.LEFT | wx.TOP, 25)

        dialogSetup.SetSizer(main_sizer)
        result =  dialogSetup.ShowModal()
        if result == wx.ID_OK:
                ED.prog_setup['typeRedCal']     = ch_choise_type_redCal.GetCurrentSelection()
                ED.prog_setup['typeECU']        = ch_choise_type_ECU.GetCurrentSelection()
                ED.prog_setup['comSpeed']       = ch_choise_type_comSpeed.GetCurrentSelection()

                if ED.prog_setup['comSpeed'] == 0:
                    ED.prog_setup['comSpeedReal'] = 9600
                elif ED.prog_setup['comSpeed'] == 1:
                    ED.prog_setup['comSpeedReal'] = 19200
                elif ED.prog_setup['comSpeed'] == 2:
                    ED.prog_setup['comSpeedReal'] = 38400

                # with используется что бы в ЛЮБОМ случае закрыть файл после чтения, применяется вместо try
                with open('mdisettings.dat', 'wb') as f:
                        pickle.dump(ED.prog_setup, f)

        dialogSetup.Destroy()



