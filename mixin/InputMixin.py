# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import string

class InputMixin():
    #Выпадающий список для выбора значений из cписка на 2,3 или 4 значения
    def list(self, parent, sizer, label, list, val):
        '''
        :param parent: Родительское окно
        :param sizer:  Сизер в который прописываем список выбора
        :param label:  Заголовок для списка выбора
        :param list:   Варианты выбора
        :param val:    Значение, на основании которго выбираются варианты
        :return:
        '''

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        st_choise_type = wx.StaticText( parent, -1, label, (15, 10))
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        st_choise_type.SetFont(font)
        ch_choise_type = wx.Choice( parent, -1, (100, 50), choices=list)
        if len(list) == 2:
            if val == 0:
                ch_choise_type.SetStringSelection(list[0])
            elif val == 1:
                ch_choise_type.SetStringSelection(list[1])
        elif len(list) == 3:
            if val == 0:
                ch_choise_type.SetStringSelection(list[0])
            elif val == 1:
                ch_choise_type.SetStringSelection(list[1])
            elif val == 2:
                ch_choise_type.SetStringSelection(list[2])
        elif len(list) ==4:
            if val   == 0:
                ch_choise_type.SetStringSelection(list[0])
            elif val == 1:
                ch_choise_type.SetStringSelection(list[1])
            elif val == 2:
                ch_choise_type.SetStringSelection(list[2])
            elif val == 3:
                ch_choise_type.SetStringSelection(list[3])

        h_sizer.Add(st_choise_type, 0, wx.ALL | wx.ALIGN_LEFT, 10)
        h_sizer.Add(ch_choise_type, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(h_sizer, 0, wx.ALIGN_TOP, 0)
        return ch_choise_type

    def box(self, parent, boxLabel, dict, *args ):
        box = wx.StaticBox(parent, -1, boxLabel)
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        flexSizer = wx.FlexGridSizer(rows=len(args), cols=2, hgap=5, vgap=5)
        for arg in args:
            if len(arg)==4:
                self.Item_input(parent, flexSizer, arg[0], arg[1], dict, arg[2], arg[3])
            else:
                self.Item_input(parent, flexSizer, arg[0], arg[1], dict, arg[2] )
        boxSizer.Add(flexSizer, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        return boxSizer

    # Ввод одного поля с подписью и валидатором
    def Item_input(self, parent, sizer, label, name, inputData, number, inputSize=50):
        ''' Выводит сочетание статического текста и поля для ввода в слайдере
        :param parent: диалог, куда добавляются пункты для ввода
        :param sizer: сизер, упорядочнещиц текст и поле для ввода
        :param label: статический текст
        :param name: поле в словаре для ввода
        :param inputData: словарь
        :param number: максимальное кол-во цифр в проле для контроля валидатором
        :param inputSize: физический размер поля ввода
        '''
        st = wx.StaticText(parent, -1, label)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        st.SetFont(font)
        sizer.Add(st, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, 5)
        tc = wx.TextCtrl(parent, -1, size=(inputSize, -1), validator=DigitalValidator(inputData, name, number))
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        tc.SetFont(font)
        sizer.Add(tc, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, 5)

    # Ввод 2 значений через диалог
    def twoVolumeSetup(self,parent, win_label, var_label1, var_label2, var1, var2, dict):
        '''
        Выводит в отдельном окошке поле ввода на одну переменную
        :rtype : object
        :param parent:
        :param win_label:
        :param var_label:
        :param var:
        :param dict:
        :return:
        '''
        dialog = wx.Dialog(parent, -1, win_label, pos=(600, 350), size=(400, 180))
        dialog.SetBackgroundColour("WHITE")
        main_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=10, vgap=10)
        self.Item_input(dialog, main_sizer, var_label1, var1, dict, 11, inputSize=100)
        self.Item_input(dialog, main_sizer, var_label2, var2, dict, 11, inputSize=100)
        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(dialog, wx.ID_OK, u"Принять изменения")
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(dialog, wx.ID_CANCEL, u"Отказаться"))
        buttons.Realize()
        main_sizer.Add(buttons, 0, wx.TOP, 10)
        dialog.SetSizer(main_sizer)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()

class DigitalValidator(wx.PyValidator):
    def __init__(self, data, key, number ):
        self.data = data
        self.key = key
        self.number = number
        wx.PyValidator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """
        Обратите внимание, что каждый валидатор должен реализовать метод Clone().
        """
        return DigitalValidator(self.data, self.key, self.number )

    # метод проверки
    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        for x in val:
            if x not in string.digits :
                wx.Bell()
                wx.MessageBox(u"В этои поле должны быть только цифровые значения !", u"Ошибка")
                tc.SetBackgroundColour("pink")
                tc.SetFocus()
                return False

        if len(val) > self.number :
            wx.Bell()
            wx.MessageBox(u"Максимальная длинна этого поля "+str(self.number)+u" символа !", u"Ошибка")
            tc.SetBackgroundColour("pink")
            tc.SetFocus()
            return False

        tc.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        tc.Refresh()
        return True

    def OnChar(self, event):
        key = event.GetKeyCode()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
        if chr(key) in string.digits:
            event.Skip()
            return
        if not wx.Validator_IsSilent():
            wx.Bell()
        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return
    # При открытии диалога
    def TransferToWindow(self):
        textCtrl = self.GetWindow()
        textCtrl.SetValue(str(self.data.get(self.key, 0 )))
        return True

    # При закрытиии диалога
    def TransferFromWindow(self):
        textCtrl = self.GetWindow()
        self.data[self.key] = int( textCtrl.GetValue() )
        return True