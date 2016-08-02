# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import grid
import ECUdata as ED

# Табличные настройки и автокалибровка PPS
def TableSetup( self ):
        dTabl=wx.Dialog(ED.main_parent, -1, u"Табличные настройки", pos = (200,0), size = (820,768))
        dTabl.SetBackgroundColour("WHITE")
        main_sz = wx.BoxSizer( wx.HORIZONTAL)
        sz1 = wx.FlexGridSizer(rows=1, cols=16, hgap=0, vgap=50 )

        # def __init__(self, parent, label, size, row_hight, row_hight_label, border, sizer, table )
        p1g =   grid.One_grid(dTabl,  "PPS1",  ED.PPS_table_size, 21, 21, 10, sz1, ED.PPS1_table )
        pwm1g = grid.One_grid(dTabl,  "PWM",   ED.PPS_table_size, 21, 0,  0,  sz1, ED.PPS1_PWM_table )
        p2g =   grid.One_grid(dTabl,  "PPS2",  ED.PPS_table_size, 21, 21, 10, sz1, ED.PPS2_table )
        pwm2g = grid.One_grid(dTabl,  "PWM",   ED.PPS_table_size, 21, 0,  0,  sz1, ED.PPS2_PWM_table )

        eg =    grid.One_grid(dTabl,  u"EGT"       ,ED.EGT_table_size, 17, 17, 10, sz1, ED.EGT_table )
        egg =   grid.One_grid(dTabl,  u"Газ /100"  ,ED.EGT_table_size, 17, 0,  0,  sz1, ED.EGT_gas_table )

        sg =    grid.One_grid(dTabl,  u"V"         ,ED.Speed_table_size, 17, 17, 10, sz1, ED.Speed_table )
        sgg =   grid.One_grid(dTabl,  u"Газ /100"  ,ED.Speed_table_size, 17, 0,  0,  sz1, ED.Speed_gas_table )
        sdg =   grid.One_grid(dTabl,  u"ДТ /100"   ,ED.Speed_table_size, 17, 0,  0,  sz1, ED.Speed_diesel_table )

        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(dTabl, wx.ID_OK, u"ДА", size=(100, 25))
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(dTabl, wx.ID_CANCEL, u"НЕТ", size=(100, 25)))
        buttons.Realize()
        sz1.Add( buttons,    0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_BOTTOM,0)

        main_sz.Add( sz1,    0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_BOTTOM,5)

        dTabl.SetSizer(main_sz)

        result =  dTabl.ShowModal()
        if result == wx.ID_OK:
            for row in range ( ED.Speed_table_size) :
                ED.Speed_table[row]           = int(sg.GetCellValue ( row,0 ))
                ED.Speed_gas_table[row]       = int(sgg.GetCellValue( row,0 ))
                ED.Speed_diesel_table[row]    = int(sdg.GetCellValue( row,0 ))
            for row in range (ED.PPS_table_size) :
                ED.PPS1_table[row]            = int(p1g.GetCellValue( row,0 ))
                ED.PPS2_table[row]            = int(p2g.GetCellValue( row,0 ))
                ED.PPS1_PWM_table[row]        = int(pwm1g.GetCellValue( row,0 ))
                ED.PPS2_PWM_table[row]        = int(pwm2g.GetCellValue( row,0 ))
            for row in range (ED.EGT_table_size) :
                ED.EGT_table[row]             = int(eg.GetCellValue( row,0 ))
                ED.EGT_gas_table[row]         = int(egg.GetCellValue( row,0 ))

        dTabl.Destroy()



