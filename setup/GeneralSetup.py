# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx

import ECUdata as ED
from mixin import InputMixin as SM
from mixin.Func import Raznoska


# Модальный диалог основных настроек
class GeneralSetupWindow(SM.InputMixin):
    def __init__(self, evt ):
        dialogSetup = wx.Dialog(ED.main_parent, -1, u"Основные настройки", pos = (100,50), size = (960,740))
        dialogSetup.SetBackgroundColour("WHITE")
        main_sizer = wx.FlexGridSizer(rows=5, cols=2, hgap=0, vgap=0)

        rpmSizer    = self.box( dialogSetup, u"Обороты двигателя в минуту ( RPM )", ED.gen_setup,
                                ( u"Минимальный   уровень  RPM (  холостой ход  ) :",  "RPM_min", 4  ),
                                ( u"Максимальный  уровень RPM ( отсечка ):", "RPM_max",  4),
                                ( u"Поправочный  коэффициент  для  RPM:", "K_RPM",  4)     )

        turboSizer = self.box( dialogSetup, u"Давление наддува Turbo в миллибарах", ED.gen_setup,
                               ( u"Минимальное   значение  давления  наддува   :", "Turbo_min", 4),
                               ( u"Максимальное   значение  давления  наддува  :", "Turbo_max", 4)  )

        ppsSizer = self.box(dialogSetup, u"Педаль газа PPS", ED.gen_setup,
                              (u"Минимум датчика педали газа PPS1 (мВ):", "PPS1_min", 4),
                              ( u"Максимум  датчика педали газа PPS1 (мВ):", "PPS1_max", 4) )

        ch_choise_type_PPS = self.list( dialogSetup, ppsSizer, u"Выберите тип используемого PPS:",
                            [ u'Два сенсора', u'Один сенсор', u'Цифровой'], ED.gen_setup['PPS_type'] )

        reductorSizer = self.box(dialogSetup,  u"Настройки редуктора", ED.gen_setup,
                              (u"Давление  в  редукторе  для  выключения :", "Red_press", 4 ),
                              (u"Температура в редукторе для  включения  :", "T_red", 4 )  )

        protectEngineSizer    = self.box(dialogSetup, u"Защита двигателя", ED.gen_setup,
                              (u"Максимальная   температура   EGT  (  C  )  :", "EGT_max", 3),
                              (u"Максимальная    температура   ОЖ  (  C  )  :", "CL_max", 3) )

        otherSizer = self.box(dialogSetup, u"Разное", ED.gen_setup,
                              (u"Поправка  для    вычисления  скорости  :", "V_cor", 3),
                              (u"Граница нормального напряжения питания :", "Upower", 2))

        box = wx.StaticBox(dialogSetup, -1, u'Общие настройки')
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        ch_choise_GPS_mode = self.list(dialogSetup, boxSizer , u"Коррекция    подачи    газа  по  GPS    :",
                                       [u'Не использовать', u'Использовать'], ED.gen_setup['GPS_mode'])

        ch_choise_LOG_mode = self.list(dialogSetup, boxSizer, u"Вести логирование:",
                                       [u'Не использовать', u'Использовать'], ED.gen_setup['LOG_mode'])

        chCOMspeed = self.list(dialogSetup, boxSizer, u"Скорость  обмена   по   COM порту :",
                               ['9600', '19200', '38400'], ED.gen_setup['comSpeed'])

        gasSizer = self.box(dialogSetup, u"Корректировка подачи газа", ED.gen_setup,
                              (u"Абсолютный максимум подачи газа, не больше:", "Abs_max_GAS", 3),
                              ( u"Не корр. газ по скорости, при уровне газа < чем:", "safety_level_GAS", 3))

        buttons_sizer = wx.StdDialogButtonSizer()
        b = wx.Button(dialogSetup, wx.ID_OK, u"Принять изменения")
        b.SetDefault()
        buttons_sizer.AddButton(b)
        buttons_sizer.AddButton(wx.Button(dialogSetup, wx.ID_CANCEL, u"Отказаться"))
        buttons_sizer.Realize()

        main_sizer.Add(turboSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(reductorSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(boxSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(ppsSizer,            0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(rpmSizer,            0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(otherSizer,          0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(gasSizer, 0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(protectEngineSizer,  0, wx.LEFT | wx.TOP, 30)
        main_sizer.Add(buttons_sizer,       0, wx.LEFT | wx.TOP, 30)

        main_sizer.Add((0, 10))  # Пустое пространство

        dialogSetup.SetSizer(main_sizer)
        result =  dialogSetup.ShowModal()
        if result == wx.ID_OK:
            # Разносим RPM
            Raznoska( ED.RPM_table, ED.gen_setup['RPM_min'], ED.gen_setup['RPM_max'] )
            # Разносим Turbo
            Raznoska( ED.Turbo_table, ED.gen_setup['Turbo_min'], ED.gen_setup['Turbo_max'] )
            # Разносим PPS1
            Raznoska( ED.PPS1_table, ED.gen_setup['PPS1_min'], ED.gen_setup['PPS1_max'] )
            # Разносим PPS2  в зависимсти от типа PPS
            # 2 или 1 аналоговых датчика - половина от PPS1
            if ED.gen_setup['PPS_type'] == 0 or ED.gen_setup['PPS_type'] == 1:
                Raznoska(ED.PPS2_table, ED.gen_setup['PPS1_min']/2, ED.gen_setup['PPS1_max']/2)
            # Если цифровой PPS, то PPS2 разносим в обратном порядке
            else:
                Raznoska(ED.PPS2_table, ED.gen_setup['PPS1_max'], ED.gen_setup['PPS1_min'])
            # Разносим EGT
            Raznoska( ED.EGT_gas_table, 100, 0 )
            Raznoska( ED.EGT_table, ED.gen_setup['EGT_max']-39, ED.gen_setup['EGT_max'] )

            ED.gen_setup['PPS_type'] = ch_choise_type_PPS.GetCurrentSelection()
            ED.gen_setup['GPS_mode'] = ch_choise_GPS_mode.GetCurrentSelection()
            ED.gen_setup['LOG_mode'] = ch_choise_LOG_mode.GetCurrentSelection()
            ED.gen_setup['comSpeed'] = chCOMspeed.GetCurrentSelection()
            if ED.gen_setup['comSpeed'] == 0:
                ED.gen_setup['comSpeedReal'] = 9600
            elif ED.gen_setup['comSpeed'] == 1:
                ED.gen_setup['comSpeedReal'] = 19200
            elif ED.gen_setup['comSpeed'] == 2:
                ED.gen_setup['comSpeedReal'] = 38400

        dialogSetup.Destroy()



