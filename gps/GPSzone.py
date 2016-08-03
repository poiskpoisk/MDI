# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import wx
import wx.dataview as dv
import ECUdata as ED
import re

# ----------------------------------------------------------------------
# Отображает и обрабатывает список зон, сгрупированных в группы для GPS
# -----------------------------------------------------------------------


class Zone(object):
    def __init__(self, group, long, lat, radius, type ):
        self.group  = group
        self.long   = long
        self.lat    = lat
        self.radius = radius
        self.type   = type


    def __repr__(self):
        return 'Zone'

# Группа зон по географическому признаку
class Group(object):
    def __init__(self, name):
        self.name = name
        self.zones = []

    def __repr__(self):
        return 'Group'

# Модель данных
class MyTreeListModel(dv.PyDataViewModel):
    def __init__(self, data ):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.objmapper.UseWeakRefs(True)

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return 5

    # Map the data column numbers to the data type
    def GetColumnType(self, col):
        mapper = {0: 'string',
                  1: 'string',
                  2: 'string',
                  3: 'string',
                  4: 'string',

                  }
        return mapper[col]

    def GetChildren(self, parent, children):
        # The view calls this method to find the children of any node in the
        # control. There is an implicit hidden root node, and the top level
        # item(s) should be reported as children of this node. A List view
        # simply provides all items as children of this hidden root. A Tree
        # view adds additional items as children of the other items, as needed,
        # to provide the tree hierachy.
        ##self.log.write("GetChildren\n")

        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the group objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for group in self.data:
                children.append(self.ObjectToItem(group))
            return len(self.data)

        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Group):
            for zone in node.zones:
                children.append(self.ObjectToItem(zone))
            return len(node.zones)
        return 0

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.
        ##self.log.write("IsContainer\n")

        # The hidden root is a container
        if not item:
            return True
        # and in this model the group objects are containers
        node = self.ItemToObject(item)
        if isinstance(node, Group):
            return True
        # but everything else (the zone objects) are not
        return False

    def GetParent(self, item):
        # Return the item which is this item's parent.
        ##self.log.write("GetParent\n")

        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)
        if isinstance(node, Group):
            return dv.NullDataViewItem
        elif isinstance(node, Zone):
            for g in self.data:
                if g.name == node.group:
                    return self.ObjectToItem(g)

    def GetValue(self, item, col):
        # Return the value to be displayed for this item and column. For this
        # example we'll just pull the values from the data objects we
        # associated with the items in GetChildren.

        # Fetch the data object for this item.
        node = self.ItemToObject(item)

        if isinstance(node, Group):
            # We'll only use the first column for the Group objects,
            # for the other columns lets just return empty values
            mapper = {0: node.name,
                      1: "",
                      2: "",
                      3: "",
                      4: "",

                      }
            return mapper[col]


        elif isinstance(node, Zone):
            mapper = {0: node.group,
                      1: node.long,
                      2: node.lat,
                      3: node.radius,
                      4: node.type,
                      }
            return mapper[col]

        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        node = self.ItemToObject(item)
        if isinstance(node, Group):
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False

    def SetValue(self, value, item, col):

        # We're not allowing edits in column zero (see below) so we just need
        # to deal with Zone objects and cols 1 - 5

        node = self.ItemToObject(item)
        if isinstance(node, Zone):
            if col == 1:
                node.long = value
            elif col == 2:
                node.lat = value
            elif col == 3:
                node.radius = value
            elif col == 4:
                node.type = value

class ZoneList():
    def __init__(self, evt ):

        self.parent = wx.Dialog(ED.main_parent, -1, u"Список безопасных зон", pos=(300, 0), size=(817, 768))
        self.parent.SetBackgroundColour("WHITE")
        main_sz = wx.BoxSizer(wx.VERTICAL)

        # Create a dataview control
        self.dvc = dv.DataViewCtrl(self.parent, size=(800, 630), style=wx.BORDER_THEME | dv.DV_ROW_LINES
                                                                  | dv.DV_HORIZ_RULES | dv.DV_VERT_RULES | dv.DV_MULTIPLE)

        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.onPopUpMenu)
        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.onEditCng)
        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_STARTED, self.onEditStart)

        zonedata = ED.zonedata.items()
        data = dict()
        for key, val in zonedata:
            zone = Zone(val[0], val[1], val[2], val[3], val[4])
            group = data.get(zone.group)
            if group is None:
                group = Group(zone.group)
                data[zone.group] = group
            group.zones.append(zone)
        data = data.values()

        # Create an instance of our model...
        self.model = MyTreeListModel(data)

        # Tel the DVC to use the model
        self.dvc.AssociateModel(self.model)

        # Define the columns that we want in the view.  Notice the
        # parameter which tells the view which col in the data model to pull
        # values from for each view column.


        self.tr = tr = dv.DataViewTextRenderer()

        c0 = dv.DataViewColumn(u"Группа", tr, 0,  width=450 )
        self.dvc.AppendColumn(c0)
        c1 = self.dvc.AppendTextColumn(u"Долгота", 1, width=100, mode=dv.DATAVIEW_CELL_EDITABLE)
        c2 = self.dvc.AppendTextColumn(u"Широта",  2, width=100, mode=dv.DATAVIEW_CELL_EDITABLE)
        c3 = self.dvc.AppendTextColumn(u'Радиус',  3, width=70, mode=dv.DATAVIEW_CELL_EDITABLE)
        c4 = self.dvc.AppendTextColumn(u'Вид',     4, width=70, mode=dv.DATAVIEW_CELL_EDITABLE)

        # Set some additional attributes for all the columns
        for c in self.dvc.Columns:
            c.Sortable = True
            c.Reorderable = True

        main_sz.Add((0, 40))  # Пустое пространство
        main_sz.Add(self.dvc, 0,  wx.EXPAND )

        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(self.parent, wx.ID_OK, u"ДА", size=(100, 25))
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(self.parent, wx.ID_CANCEL, u"НЕТ", size=(100, 25)))
        buttons.Realize()
        main_sz.Add(buttons, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, 20)

        self.parent.SetSizer(main_sz)

        result = self.parent.ShowModal()
        if result == wx.ID_OK:
            pass

    def onPopUpMenu(self, evt):
        ### 2. Launcher creates wxMenu. ###
        menu = wx.Menu()
        item = menu.Append(-1, u"Новая зона или группа")
        self.dvc.Bind(wx.EVT_MENU, self.onNewLine, item)
        item = menu.Append(-1, u"Удалить зону или группу")
        self.dvc.Bind(wx.EVT_MENU, self.onDeleteGroup, item)
        item = menu.Append(-1, u"Переименовать зону или группу")
        self.dvc.Bind(wx.EVT_MENU, self.onRenameGroup, item)

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
        self.dvc.PopupMenu(menu)
        menu.Destroy()  # destroy to avoid mem leak

    def onRenameGroup(self, evt):
        item = self.dvc.GetSelection()
        node = self.model.ItemToObject(item)
        parent = wx.Dialog(self.parent, -1, u"Переименовать группу или зону", pos=(500, 200), size=(380, 250))
        parent.SetBackgroundColour("WHITE")
        main_sz = wx.BoxSizer(wx.VERTICAL)
        basicLabel = wx.StaticText(parent, -1, u"Новое название группы или зоны:")
        basicText = wx.TextCtrl(parent, -1, size=(275, -1))
        basicText.SetInsertionPoint(0)

        buttons = wx.StdDialogButtonSizer()
        b = wx.Button(parent, wx.ID_OK, u"ДА", size=(100, 25))
        b.SetDefault()
        buttons.AddButton(b)
        buttons.AddButton(wx.Button(parent, wx.ID_CANCEL, u"НЕТ", size=(100, 25)))
        buttons.Realize()

        main_sz.Add(basicLabel, 0, wx.LEFT |wx.TOP | wx.ALIGN_TOP, 40)
        main_sz.Add((0, 20))  # Пустое пространство
        main_sz.Add(basicText,  0, wx.LEFT | wx.ALIGN_TOP, 40)
        main_sz.Add(buttons,    0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, 40)

        parent.SetSizer(main_sz)

        result = parent.ShowModal()
        if result == wx.ID_OK:
            newGroup=basicText.GetValue()
            zonedata = ED.zonedata.items()
            for key, val in zonedata:
                if 'Zone' in str(node):
                    if val[0] == node.group and val[1] == node.long and val[2] == node.lat and val[3] == node.radius:
                        updDict = {key: (newGroup, val[1], val[2], val[3], val[4])}
                        ED.zonedata.update(updDict)
                else:
                    if val[0] == node.name:
                        updDict = {key: (newGroup, val[1], val[2], val[3], val[4])}
                        ED.zonedata.update(updDict)
            self.parent.Destroy()
            ZoneList(1)

    # Добавление новой зоны или группы
    def onNewLine(self, evt):

        item = self.dvc.GetSelection()
        node = self.model.ItemToObject(item)
        keys = ED.zonedata.keys()
        keys.sort(reverse=True)
        newKey=keys[0]+1

        if 'Zone' in str(node):
            if newKey <= 9:
                updDict= { newKey: ( node.group, '000.00000'+str(newKey), '00.000000', '100', '1' )  }
            elif newKey > 9 and newKey <=99:
                updDict = {newKey: (node.group, '000.0000' + str(newKey), '00.000000', '100', '1')}
            elif newKey >99 and newKey <=999:
                updDict = {newKey: (node.group, '000.000' + str(newKey), '00.000000', '100', '1')}
            ED.zonedata.update( updDict )
            self.parent.Destroy()
            ZoneList(1)
        elif 'Group' in str(node):
            if newKey <= 9:
                updDict = {newKey: ('New group '+str(newKey), '000.00000' + str(newKey), '00.000000', '100', '1')}
            elif newKey > 9 and newKey <= 99:
                updDict = {newKey: ('New group '+str(newKey), '000.0000' + str(newKey), '00.000000', '100', '1')}
            elif newKey > 99 and newKey <= 999:
                updDict = {newKey: ('New group  '+str(newKey), '000.000' + str(newKey), '00.000000', '100', '1')}
            ED.zonedata.update(updDict)
            self.parent.Destroy()
            ZoneList(1)

    # Всплывающее меню, на правой кнопке Удаление строки или группы
    def onDeleteGroup(self, evt):
        item = self.dvc.GetSelection()
        node = self.model.ItemToObject(item)
        dict = ED.zonedata.copy()
        if len(dict.keys()) == 1:
            wx.Bell()
            wx.MessageBox(u"Недьзя удалить последую строку",
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
            return
        if 'Zone' in str(node):
            for key, val in dict.iteritems():
                if val[0] == node.group and val[1] == node.long and val[2] == node.lat and val[3] == node.radius:
                    ED.zonedata.pop(key)
                    self.parent.Destroy()
                    ZoneList( 1)

        elif 'Group' in str(node):
            for key, val in dict.iteritems():
                if val[0] == node.name:
                    ED.zonedata.pop(key)
            self.parent.Destroy()
            ZoneList(1)

    # Вызывается, когда редактирование елемента ЗАВЕРШЕНО
    def onEditCng(self, evt):

        # Что бы когда сработало исключение переменные были переопределенны
        resLong     =  False
        resGrLong   =  False
        resLat      =  False
        resGrLat    =  False
        resRadius   =  False
        resType     =  False

        item = self.dvc.GetSelection()
        self.nodeEdit = self.model.ItemToObject(item)

        for key, val in ED.zonedata.iteritems():
            if val[0] == self.nodeEdit.group and val[1] == self.nodeEdit.long and val[2] == self.nodeEdit.lat \
                    and val[3] == self.nodeEdit.radius and val[4] == self.nodeEdit.type and key != self.editing_key:
                wx.Bell()
                wx.MessageBox(u"Необходимо закончить редактирование , а только потом перейти на новую строку.",
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
                self.parent.Destroy()
                return


        try:
            resLong     = re.match( '\d{3}\.\d{6}', str(self.nodeEdit.long))
            resGrLong   = re.match( '\d{3}', str(self.nodeEdit.long))
            resLat      = re.match( '\d{2}\.\d{6}', str(self.nodeEdit.lat))
            resGrLat    = re.match( '\d{2}', str(self.nodeEdit.long))
            resRadius   = re.match( '\d{1,4}', str(self.nodeEdit.radius))
            resType     = re.match( '\d{1,3}', str(self.nodeEdit.radius))
        except:
            self.errHandler() # Ошибка обработки, вызываемая воодом русских букв
        else:
            if resLong and resLat and resRadius and resType and resType and \
                            int(self.nodeEdit.radius) <= 64000  and int(self.nodeEdit.radius) >= 100 \
                            and  int(self.nodeEdit.type) <= 2 and \
                            int(resGrLong.group(0)) <= 180 and int(resGrLat.group(0)) <= 90:
                if self.isHaveDublicate( self.nodeEdit ) :
                    self.errHandler()
                    return
                # Обновляем в глобальном словаре настроек GPS данные
                editingItemList =  ['group','long','lat','radius', 'type']
                editingItemList[0] = self.nodeEdit.group
                editingItemList[1] = resLong.group(0)
                editingItemList[2] = resLat.group(0)
                editingItemList[3] = self.nodeEdit.radius
                editingItemList[4] = self.nodeEdit.type
                dict = {self.editing_key: editingItemList}
                ED.zonedata.update(dict)
                # Показываем в отображаемом списке первую часть ( правильную ) широты и долготы
                self.nodeEdit.long = resLong.group(0)
                self.nodeEdit.lat  = resLat.group(0)
                item = self.model.ObjectToItem(self.nodeEdit)
            else:
                self.errHandler()           # Не корректные данные

    # Вернуть введенные данные в исходное состояние и выдать сообщение об ошибки
    def errHandler(self):
        list = ED.zonedata.get(self.editing_key)
        self.nodeEdit.group = list[0]
        self.nodeEdit.long = list[1]
        self.nodeEdit.lat = list[2]
        item = self.model.ObjectToItem(self.nodeEdit)
        self.dvc.SetCurrentItem(item)
        wx.Bell()
        wx.MessageBox(u"Не допустимое значение. Допустимые значения - "
                      u"Долгота: +/-XXX.XXXXXX ( ХХХ: 0..180 ) градусов, "
                      u"Широта: +/- YY.YYYYYY ( YY: 0..90 ) градусов,"
                      u" Радиус: 100..64000 метров, Тип: 0,1,2 "
                      u"Так же не допускается дублирование зон с одинаковыми координатами.",
                      caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

    # При начале редактирования, запоминаем ключ ( что бы по нему искать скорректированую запись )
    def onEditStart(self, evt):
        item = self.dvc.GetSelection()
        node = self.model.ItemToObject(item)
        dict = ED.zonedata.copy()
        for key, val in dict.iteritems():
            if val[0] == node.group and val[1] == node.long and val[2] == node.lat and val[3] == node.radius:
                self.editing_key=key

    # Не допускаются зоны с одинаковыми координатами.
    def isHaveDublicate(self, node ):
        zonedata = ED.zonedata.items()
        for key, val in zonedata:
            if val[1] == node.long and val[2] == node.lat and self.editing_key != key:
                return True
        return  False
