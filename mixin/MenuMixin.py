# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import os

# Примеси, необходимые для создания главного меню
class Menu():

    # Блок меню
    def menuBlock(self, label, *lst ):
        '''

        :param label: Заголовок блока
        :param lst:   Список описывающий пункт меню внутри блока
                     [ u'Заголовок', обработчик на выбор пункта, картинка или None, True/False видимость сепаратора]
        :return:
        '''
        # Создаем блок выпадающего меню
        menu = wx.Menu()
        for item in lst:
            self.menuItem( item[0], menu, item[1], item[2])
            if item[3]:
                menu.AppendSeparator()
        self.menubar.Append( menu, label)

    # Пункт меню внутри блока
    def menuItem(self, label, menu, handler, pic=None ):
        '''

        :param label:   Заголовок пункта
        :param menu:    Блок, куда вставлять пункт
        :param handler: Обработчик на выбор пункта
        :param pic:     Иконка 16px ( должна лежать в /pic) , если нет то None
        :return:
        '''
        ID = wx.NewId()
        resetItem = wx.MenuItem(menu, ID, label )
        if pic !=None :
            img = wx.Image(os.getcwd() + '\pic\\'+pic, wx.BITMAP_TYPE_ANY)
            resetItem.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(resetItem)
        self.Bind(wx.EVT_MENU, handler, id=ID )
