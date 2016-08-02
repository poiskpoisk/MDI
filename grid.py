# -*- coding: utf-8 -*-
__author__ = 'AMA'

'''
---------------------------------------------------------------------------------------------------
В этом файле содержатся все классы, связанные с табличным представлением данных
Cal_grid - базовый класс для работы с калибровки, от которого наследуются Gas_grid и
Diesel_grid  - таблицы газовой и дизельной калибровки
One_grid -  таблица из одного столбца, используется для задания Turbo, PPS и т.д.
Setup_grid -  вспомогательная таблица, что бы из нее можно было сразу брать значения, не нажимая ЕНТЕР и не закрывая
текущее окно ( что бы не как в модальном диалоге )
GradientRenderer - редендер, который раскрашивает газовую и дизельную калибровку более ярко для больших величин
---------------------------------------------------------------------------------------------------
'''


import wx
import wx.grid as gridlib  # Из-за большого размера wx.grid надо импортировать отдельно
import os
import ECUdata as ED
import PPSview as PV
from mixin import Func, InputMixin as SM

class GradientRenderer(wx.grid.PyGridCellRenderer):
    """ Отрисовывает ячейки более ярким цветом, в зависимости от величины калибровки
        max_number - самый яркий участок
        type_table - тип калибровочной таблицы 'gas' или 'diesel'
    """
    def __init__(self, max_number, type_table):
        # Незабываем принудительно вызывать конструктор родительского класса
        wx.grid.PyGridCellRenderer.__init__(self)
        # Делаем доступными переменные, полученные при вызове класса, доступными во всем классе
        self.max_number = max_number
        self.type_table = type_table

    # Переопределяем стандартный метод
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        text = grid.GetCellValue(row, col)
        # Контроль что бы значения в таблице были числами
        try:
            k = float(text) / self.max_number  # float преобразует из строки, что бы явно сказать что нам нужно дробное
        except:
            k = 0

        if k > 1:  # Если попадаются числа больше максимально возможного то красим в максимальный
            k = 1
        hAlign, vAlign = attr.GetAlignment()
        dc.SetFont(attr.GetFont())
        if isSelected:
            bg = grid.GetSelectionBackground()
            fg = grid.GetSelectionForeground()
        else:
            # Если клетоочка не выбрана, то
            if self.type_table == 'gas' or self.type_table == 'osnova':        # Работаем над газовой калибровкой
                if ED.calWinSetupCheckBox[0]:
                    bg = (255,255,255)          # Фон белый, расскрашивтаь не надо
                else:
                    # Красный цвет в RGB модели это 255,000.000 а белый 255,255,255 остальный розовые цвета между
                    bg = ( int(255 * k), 255, int(255 * (1 - k))  ) # Цвет фона между голубоватым и желтым
            else:   # Работаем над дизельной калибровкой
                if ED.calWinSetupCheckBox[0]:
                    bg = (255,255,255)          # Фон белый, расскрашивтаь не надо
                else:
                    # Красный цвет в RGB модели это 255,000.000 а белый 255,255,255 остальный розовые цвета между
                    #bg = ( int(255 * k ), int(255 * (1-k) ), int(255 * (1 - k)) )
                    bg = ( int(255 * (1 - k)), int(255 * k ), int(255 * (1-k) )  ) # фиолет зеленый


        fg = attr.GetTextColour()
        dc.SetTextBackground(bg)
        dc.SetTextForeground(fg)
        dc.SetBrush(wx.Brush(bg, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)
        grid.DrawTextRectangle(dc, text, rect, hAlign, vAlign)

    def Clone(self):
        return GradientRenderer()

# Отрисовывает таблицу калибровки и обеспечивает весь функционал таблицы, БАЗОВЫЙ для всех конкретных таблиц класс

class Cal_grid(gridlib.Grid):  # gridlib синоним wx.grid
    ''' Отрисовывает таблицу калибровки и обеспечивает весь функционал таблицы
    :param parent родительский фрейм
    :param cal_type тип калибровки 'gas' или 'diesel'
    :param maxValue максимальное значение для данногго вида калибровки
    '''
    def __init__(self, parent, max_value, table ):
        self.flagArrayErr = False
        self.table = table
        self.parent = parent
        self.maxValue = max_value
        # Явно вызываем конструктор wx.grid, но этого недостаточно что бы создать сетку
        gridlib.Grid.__init__(self, parent, -1)
        # Инициализируем переменные, для ф-ции Update
        self.row = self.col  = 0
        # Механеизм обновления значений по таймеру
        self.timer = wx.Timer( self )
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(500)
        # Устанавливаем стартовую ячейку
        self.currentlySelectedCell = (0, 0)
        # Создаем таблицу
        self.CreateGrid( ED.Cal_table_TURBO_size, ED.Cal_table_RPM_size )
        # Установить редактор для всех элементов сетки, только цифры -1,-1 это без контроля диапазона
        self.SetDefaultEditor( wx.grid.GridCellNumberEditor(-1,-1))
        # Размер столбца МЕТКИ
        self.SetRowLabelSize(40)
        self.SetColLabelSize(30)
        self.SetLabelFont(wx.Font(ED.calGridLabelFont, wx.SWISS, wx.NORMAL, wx.BOLD))
        # Запрещаем изменять размеры строк, столюцов и ячеек
        self.DisableDragColSize()
        self.DisableDragRowSize()
        self.DisableDragGridSize()
        self.SetDefaultCellFont(wx.Font(ED.calGridCellFont, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.SetDefaultCellAlignment(wx.CENTRE, wx.CENTRE)

        for col in range( ED.Cal_table_RPM_size ):
            self.SetColSize( col, ED.colSize )  # Размер колонок
        # Выводим в сетку значения из калибровочного массива
        self.popupItemRead(1)  # 1 это заглушка, так как должно быть 2 аргумента
        # Устанавливаем обработчик, что бы из редактора можно было выходить по нажатой стрелке как в Excel
        self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.onCellEdit_like_Excel)
        # Устанавливаем обработчик на правую кнопку мыши
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.showPopupMenu)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.cellChanged)
        self.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        # Инициализируем фонт, для ф-ции Update
        self.font = self.GetCellFont( self.row, self.col )

    def cellChanged(self, event):
        cell = self.GetCellValue( self.GetGridCursorRow(), self.GetGridCursorCol() )
        if int(cell) > self.maxValue:
            wx.MessageBox(u'Максимальное значение - '+str(self.maxValue),
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR )
            self.SetCellValue( self.GetGridCursorRow(), self.GetGridCursorCol(), str(self.maxValue) )
        event.Skip()

    # Установить выделенные ячейки таблицы в Значение
    def popupItemSet(self, event):
        # Задаем значение в которое будем устанавливать
        setValue=wx.GetNumberFromUser(u"Ввод значения в которое будут установленны выделенные ячейки ", u"Значение:",
                                   u"Ввод значения в которое будут установленны выделенные ячейки ",
                                   value = 0, min = 0, max = self.maxValue )
        # Устанавливаем флаг, что содержание таблицы измененно
        if setValue <= self.maxValue :
            # Проверка есть ли выделенное
            flagSel = True
            for row in range(ED.Cal_table_TURBO_size):
                for col in range(ED.Cal_table_RPM_size):
                    if self.IsInSelection(row, col):
                        self.SetCellValue(row, col, str( setValue))
                        flagSel = False
            if flagSel:
                wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете установить в Значение',
                              caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
        else :
            wx.MessageBox(u'Максимальное значение - '+str(self.maxValue),
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR )

    # Ограничение максимального уровня подачи газа для всех ячеек
    def popupItemLimit(self, event):
        # Задаем значение которое будет ограничивать ВСЕ ячейки
        limit=wx.GetNumberFromUser(u"Вввод значения которое будет ограничивать ВСЕ ячейки.", u"Значение:",
                                   u"Вввод значения которое будет ограничивать ВСЕ ячейки.",
                                   value = 0, min = 0, max = self.maxValue )
        # Устанавливаем флаг, что содержание таблицы измененно
        if limit <= self.maxValue :
            for row in range(ED.Cal_table_TURBO_size):
                for col in range(ED.Cal_table_RPM_size):
                    if int(self.GetCellValue(row, col)) > limit :
                        self.SetCellValue(row, col, str( limit))
        else :
            wx.MessageBox(u'Максимальное значение - '+str(self.maxValue),
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR )

    # Увеличить все выделенные ячейки на ЗНАЧЕНИЕ
    def popupItemPlus(self, event):  # Увеличить все ячейки таблицы на Значение
        # Задаем значение на которое будем увеличивать выделенные ячейкиэ
        plusValue=wx.GetNumberFromUser(u"Ввод значения на которое будем увеличивать выделенные ячейки ", u"Значение:",
                                   u"Ввод значения на которое будем увеличивать выделенные ячейки ",
                                   value = 0, min = 0, max = self.maxValue )
        # Проверка есть ли выделенное
        flagSel = True
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if self.IsInSelection(row, col):
                    zn = int(self.GetCellValue(row, col)) + plusValue
                    # Контроль максимального значения
                    if zn > self.maxValue : zn =self.maxValue
                    self.SetCellValue(row, col, str( zn ))
                    flagSel = False
        if flagSel:
            wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете увеличить на Значение',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
    def popupItemMinus(self, event):
        # Задаем значение на которое будем уменьшать выделенные ячейки
        minusValue=wx.GetNumberFromUser(u"Вввод значения на которое будут уменьшатся выделенные ячейки ", u"Значение:",
                                   u"Вввод значения на которое будут уменьшатся выделенные ячейки ",
                                   value = 0, min = 0, max = self.maxValue )
        # Проверка есть ли выделенное
        flagSel = True
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if self.IsInSelection(row, col):
                    zn = int(self.GetCellValue(row, col)) - minusValue
                    # 0 - минимальная значение
                    if zn < 0: zn =0
                    self.SetCellValue(row, col, str(zn))
                    flagSel = False
        if flagSel:
            wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете уменьшить на Значение',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
    # Умножить все выделенные ячейки на ЗНАЧЕНИЕ
    def popupItemMult(self, event):  # Умножить все ячейки таблицы на Значение
        # Задаем значение на которое будем увеличивать выделенные ячейкиэ
        plusValue=wx.GetNumberFromUser(u"Ввод значения d % на которое будем умножать выделенные ячейки ", u"Значение:",
                                   u"Ввод значения в на которое будем умножать выделенные ячейки ",
                                   value = 0, min = 0, max = self.maxValue )
        # Проверка есть ли выделенное
        flagSel = True
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if self.IsInSelection(row, col):
                    zn = (int(self.GetCellValue(row, col)) * plusValue)/100
                    # Контроль максимального значения
                    if zn > self.maxValue : zn =self.maxValue
                    self.SetCellValue(row, col, str( zn ))
                    flagSel = False
        if flagSel:
            wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете умножить на Значение',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
    # Показать зависимость от уровня PPS
    def popupItemPPSview(self, event):
        row = self.GetGridCursorRow()
        col = self.GetGridCursorCol()
        ED.Cal_hold = ED.Gas_table[row][col]
        ED.DIESEL_cal = ED.Diesel_table[row][col]
        PV.PPSview(ED.Cal_hold, ED.DIESEL_cal)

    def onCellEdit_like_Excel(self, event):
        '''  Метод N1, что бы из редактора можно было выходить по нажатой стрелке как в Excel
            When cell is edited, get a handle on the editor widget
            and bind it to EVT_KEY_DOWN
            '''
        editor = event.GetControl()
        editor.Bind(wx.EVT_KEY_DOWN, self.onEditorKey_like_Excel)
        event.Skip()

    def onEditorKey_like_Excel(self, event):
        ''' Метод N2, что бы из редактора можно было выходить по нажатой стрелке как в Excel
            Handler for the wx.grid's cell editor widget's keystrokes. Checks for specific
            keystrokes, such as arrow up or arrow down, and responds accordingly. Allows
            all other key strokes to pass through the handler.
            '''
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_UP:
            self.MoveCursorUp(False)
        elif keycode == wx.WXK_DOWN:
            self.MoveCursorDown(False)
        elif keycode == wx.WXK_LEFT:
            self.MoveCursorLeft(False)
        elif keycode == wx.WXK_RIGHT:
            self.MoveCursorRight(False)
        else:
            pass
        event.Skip()

    # Записать в таблицу значения из кодировки
    def popupItemRead(self, event):
        # Записываем заголовки строк и столбцов как значения Turbo и RPM
        for row in range(ED.Cal_table_TURBO_size):
            # Устанавливаем значения Turbo и RPM как заголовки таблицы
            self.SetRowLabelValue(row, str(ED.Turbo_table[row]))
        for col in range(ED.Cal_table_RPM_size):
            self.SetColLabelValue( col, str(ED.RPM_table[col]))
        # Записываем в сетку данные из калибровочной таблицы
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                self.SetCellValue(row, col, str('%d'%self.table[row][col]))

    # Сохраняем данные из экранной таблицы в калибровку
    def popupItemWrite(self, event):
        '''
        Сохраняем данные из экранной таблицы в калибровку
        '''
        # Записываем в сетку данные из калибровочной таблицы
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                cell = int(self.GetCellValue(row, col))
                if cell > self.maxValue :
                    wx.MessageBox(u'Максимальное значение -' + str(self.maxValue) ,
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)
                    cell = self.maxValue
                self.table[row][col] = cell
                self.SetCellValue( row,col, str(cell))

    # Обновляем прыгающую красную цифру
    def update(self, evt ):
        if ED.calWinSetupCheckBox[1]: # Включена ли в настройках эта функция и масссивы корректны ?
            # Берем значение с прошлого захода
            cell = self.GetCellValue( self.row, self.col )
            # Возвращаем назад цвет
            self.SetCellTextColour(self.row, self.col, wx.BLACK )
            # Возвращаем назад фонты
            self.SetCellFont( self.row, self.col, self.font )
            # Перезаписываем значение, что бы ячейка перерисовалось
            self.SetCellValue( self.row, self.col , cell )
            # Устанавливаем номер ячейки исходя из текущих RPM и Turbo
            self.row = Func.array_number(ED.Turbo_table, ED.Turbo)
            self.col = Func.array_number(ED.RPM_table, ED.RPM)
            # Сохраняем фонты, что бы потом вернуть все ина место
            self.font = self.GetCellFont( self.row, self.col )
            # Берем текущее значение ячейки
            cell = self.GetCellValue( self.row, self.col )
            # Раскрашиваем текущую ячейку красным
            self.SetCellTextColour(self.row, self.col, wx.RED)
            # Устанавливаем большой и жирный фонт
            self.SetCellFont( self.row, self.col, wx.Font( 16, wx.SWISS, wx.NORMAL, wx.BOLD ))
            # Перезаписываем значение в ячейку, что бы ячейка перерисовалось
            self.SetCellValue( self.row, self.col , cell )

    # Копируем в буффер выделенные ячейки
    def popupItemCopy(self, event):
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                ED.bufer[row][col] = '*'
        # Проверка есть ли выделенное
        flagSel = True
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if self.IsInSelection(row, col):
                    ED.bufer[row][col] = self.GetCellValue(row, col)
                    flagSel = False
        if flagSel:
            wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете КОПИРОВАТЬ',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

    # Вставляем из буфера скопированные ячейки ( шаблон )
    def popupItemPaste(self, addition ):
        pasteRow=self.rowRightMouse
        for row in range(ED.Cal_table_TURBO_size):
            pasteCol=self.colRightMouse
            flag = False
            for col in range(ED.Cal_table_RPM_size):
                if ED.bufer[row][col] != '*':
                    if pasteRow < ED.Cal_table_TURBO_size and pasteCol < ED.Cal_table_RPM_size :
                        self.SetCellValue(pasteRow, pasteCol, str(int(ED.bufer[row][col])+addition))
                        pasteCol += 1
                        flag = True
            if flag : pasteRow+=1

    # Вставляем из буфера скопированные ячейки ( +0 )
    def popupItemPaste0(self, event ):
        self.popupItemPaste( 0)

    # Вставляем из буфера скопированные ячейки ( +1 )
    def popupItemPaste1(self, event ):
        self.popupItemPaste(1)

    # Вставляем из буфера скопированные ячейки ( +2 )
    def popupItemPaste2(self, event):
        self.popupItemPaste(2)

# Таблица дизельной калибровки, наследует от Cal_grid и добавляет свои конкретные методы
class DieselGrid(Cal_grid, SM.InputMixin):
    def __init__(self, parent):
        Cal_grid.__init__(self, parent, 99, ED.Diesel_table)
        self.paintGrid()

    def paintGrid(self):
        attr = wx.grid.GridCellAttr()
        attr.SetRenderer(GradientRenderer(99, 'diesel'))
        # Именуем строки и столбцы как значения Turbo и RPM
        for row in range(ED.Cal_table_TURBO_size):
            self.SetRowSize(row, ED.rowSize)  # Размер строк
            self.SetRowAttr(row, attr)

    # Метод для меню по правой кнопки мыши
    def showPopupMenu(self, event):
        """ Метод для меню по правой кнопки мыши
        Интерпретатор ожидает 2 аргумента для Bind, поэтому все ф-ции обрабатывающие EVNT с 2 аргументами  """

        # Определяем координаты клеточки , где была нажата правая кнопка мыши
        self.rowRightMouse = event.GetRow()
        self.colRightMouse = event.GetCol()

        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.popupID8 = wx.NewId()
            self.popupID9 = wx.NewId()
            self.popupID10 = wx.NewId()
            self.popupID11 = wx.NewId()
            self.popupID12 = wx.NewId()
            self.popupID14 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.popupItemSet,           id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.popupItemPlus,          id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.popupItemMinus,         id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.popupItemLimit,         id=self.popupID7)
            self.Bind(wx.EVT_MENU, self.popupItemMult,          id=self.popupID8)
            self.Bind(wx.EVT_MENU, self.popupItemPPSview,       id=self.popupID9)
            self.Bind(wx.EVT_MENU, self.popupItemCopy,          id=self.popupID10)
            self.Bind(wx.EVT_MENU, self.popupItemPaste0,        id=self.popupID11)
            self.Bind(wx.EVT_MENU, self.popupItemPaste1,        id=self.popupID12)
            self.Bind(wx.EVT_MENU, self.popupItemPaste2,        id=self.popupID14)
            self.Bind(wx.EVT_MENU, self.popupItemRaznestiDiesel,id=self.popupID6)

            # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID6, u"Разнести")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID1, u"Установить выделенные ячейки")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID7, u"Ограничить ВСЕ ячейки")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID10, u"Копировать")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID11, u"Вставить")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID12, u"Вставить +1")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID14, u"Вставить +2")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID2, u"Увеличить выделенные ячейки")
        img = wx.Image(os.getcwd() + '\pic\\arrow_top.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID3, u"Уменьшить выделенные ячейки")
        img = wx.Image(os.getcwd() + '\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID8, u"Умножить выделенные ячейки")
        img = wx.Image(os.getcwd() + '\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID9, u"Посмотреть зависимость от PPS")
        img = wx.Image(os.getcwd() + '\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # Автоматическая разнеоска подачи дизеля
    def popupItemRaznestiDiesel(self, event):
        self.twoVolumeSetup(self.parent, u'Задание параметров для автоматической разноски ДИЗЕЛЬ',
                            u"Начальный уровень эмуляции:", u"Конечный уровень эмуляции:",
                            'Emul_min', 'Emul_max', ED.diesel_table_setup)
        number_spot = 40  # Количество диапазонов для разноски, от этого зависит точность разноски
        gas_spot = [0 * x for x in range(number_spot)]
        diesel_spot = [0 * x for x in range(number_spot)]
        temp_list = [0 * x for x in range(ED.Cal_table_TURBO_size)]

        # Ищем максимум в газовой калибровке
        for col in range(ED.Cal_table_TURBO_size):
            temp_list[col] = max(ED.Gas_table[col])
        max_gas = max(temp_list)

        # Ищем минимум в газовой калибровке
        for col in range(ED.Cal_table_TURBO_size):
            temp_list[col] = min(ED.Gas_table[col])
        min_gas = min(temp_list)

        delta_gas = max_gas - min_gas
        step_gas = float(delta_gas) / float(number_spot)

        for i in range(number_spot):
            gas_spot[i] = int(min_gas + step_gas * i)
        delta_diesel = ED.diesel_table_setup['Emul_min'] - ED.diesel_table_setup['Emul_max']
        step_diesel = float(delta_diesel) / float(number_spot)
        for i in range(number_spot):
            diesel_spot[i] = int(ED.diesel_table_setup['Emul_min'] - step_diesel * i)
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                i = Func.array_number(gas_spot, ED.Gas_table[row][col])
                self.SetCellValue(row, col, str(diesel_spot[i]))

    # Ограничение минимального уровня эмуляции для всех ячеек
    def popupItemLimit(self, event):
        # Задаем значение которое будет ограничивать ВСЕ ячейки
        limit = wx.GetNumberFromUser(
            u"Вввод значения которое будет ограничивать ВСЕ ячейки  ( НЕ МЕНЬШЕ ).",
            u"Значение:", u"Вввод значения которое будет ограничивать ВСЕ ячейки.",
            value=0, min=0, max=self.maxValue)

        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                if int(self.GetCellValue(row, col)) < limit:
                    self.SetCellValue(row, col, str(limit))

# Таблица газовой калибровки, наследует от Cal_grid и добавляет свои конкретные методы
class GasGrid( Cal_grid ):

    def __init__(self, parent ):
        Cal_grid.__init__( self, parent, 210, ED.Gas_table)
        self.paintGrid()

    def paintGrid(self):
        attr = wx.grid.GridCellAttr()
        attr.SetRenderer(GradientRenderer(210, 'gas'))
        # Именуем строки и столбцы как значения Turbo и RPM
        for row in range(ED.Cal_table_TURBO_size):
            self.SetRowSize(row, ED.rowSize)  # Размер строк
            self.SetRowAttr(row, attr)

    # Метод для меню по правой кнопки мыши
    def showPopupMenu(self, event):
        """ Метод для меню по правой кнопки мыши
        Интерпретатор ожидает 2 аргумента для Bind, поэтому все ф-ции обрабатывающие EVNT с 2 аргументами  """

        # Определяем координаты клеточки , где была нажата правая кнопка мыши
        self.rowRightMouse = event.GetRow()
        self.colRightMouse = event.GetCol()

        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.popupID8 = wx.NewId()
            self.popupID9 = wx.NewId()
            self.popupID10 = wx.NewId()
            self.popupID11 = wx.NewId()
            self.popupID12 = wx.NewId()
            self.popupID14 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.popupItemSet,       id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.popupItemPlus,      id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.popupItemMinus,     id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.popupItemLimit,     id=self.popupID7)
            self.Bind(wx.EVT_MENU, self.popupItemMult,      id=self.popupID8)
            self.Bind(wx.EVT_MENU, self.popupItemPPSview,   id=self.popupID9)
            self.Bind(wx.EVT_MENU, self.popupItemCopy,      id=self.popupID10)
            self.Bind(wx.EVT_MENU, self.popupItemPaste0,    id=self.popupID11)
            self.Bind(wx.EVT_MENU, self.popupItemPaste1,    id=self.popupID12)
            self.Bind(wx.EVT_MENU, self.popupItemPaste2,    id=self.popupID14)
            self.Bind(wx.EVT_MENU, self.popupItemRaznestiGAZ, id=self.popupID6)

            # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID6, u"Разнести")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID1, u"Установить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID7, u"Ограничить ВСЕ ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID10, u"Копировать")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID11, u"Вставить")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID12, u"Вставить +1")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID14, u"Вставить +2")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID2, u"Увеличить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_top.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID3, u"Уменьшить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID8, u"Умножить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID9, u"Посмотреть зависимость от PPS")
        img = wx.Image(os.getcwd()+'\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # Автоматическая разнеоска подачи газа
    def popupItemRaznestiGAZ(self, event):
        # Читаем из таблицы в калибровку
        self.popupItemWrite(1)
        # Сначала разносим строки
        for row in range(ED.Cal_table_TURBO_size):
            # Проверяем что бы строка была не пустая
            if ED.Gas_table[row].count(0) != ED.Cal_table_RPM_size:
                temp =  Func.recRaznoska(ED.Gas_table[row], [], 1, len(ED.Gas_table[row]), row, u'Строка -')
                if temp !=0: # Если функция разноски вернула 0, значит в ней была ошибка
                    ED.Gas_table[row] = temp
                    #self.popupItemRead(1)
                else: return
        # Потом разносим столбцы
        for col in range(ED.Cal_table_RPM_size):
            # Получаем столбец калибровки
            work_col=[row[col] for row in ED.Gas_table ]
            # Проверяем что бы столбец был не пустой
            if work_col.count(0) != ED.Cal_table_TURBO_size:
                temp =  Func.recRaznoska(work_col, [], 1, len(work_col), col, u'Столбец - ')
                if temp !=0:  # Если функция разноски вернула 0, значит в ней была ошибка
                    for row in range(ED.Cal_table_TURBO_size):
                        ED.Gas_table[row][col] = temp[row]
                else: return

        self.popupItemRead(1)

# Таблица основы для газовой калибровки, наследует от Cal_grid и добавляет свои конкретные методы
class OsnovaGrid( Cal_grid ):

    def __init__(self, parent ):
        Cal_grid.__init__( self, parent, 210, ED.Osnova_Gas_table )
        self.paintGrid()

    def paintGrid(self):
        attr = wx.grid.GridCellAttr()
        attr.SetRenderer(GradientRenderer(210, 'gas'))
        # Именуем строки и столбцы как значения Turbo и RPM
        for row in range(ED.Cal_table_TURBO_size):
            self.SetRowSize(row, ED.rowSize)  # Размер строк
            self.SetRowAttr(row, attr)

    # Метод для меню по правой кнопки мыши
    def showPopupMenu(self, event):
        """ Метод для меню по правой кнопки мыши
        Интерпретатор ожидает 2 аргумента для Bind, поэтому все ф-ции обрабатывающие EVNT с 2 аргументами  """

        # Определяем координаты клеточки , где была нажата правая кнопка мыши
        self.rowRightMouse = event.GetRow()
        self.colRightMouse = event.GetCol()

        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.popupID8 = wx.NewId()
            self.popupID9 = wx.NewId()
            self.popupID10 = wx.NewId()
            self.popupID11 = wx.NewId()
            self.popupID12 = wx.NewId()
            self.popupID14 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.popupItemSet,       id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.popupItemPlus,      id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.popupItemMinus,     id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.popupItemLimit,     id=self.popupID7)
            self.Bind(wx.EVT_MENU, self.popupItemMult,      id=self.popupID8)
            self.Bind(wx.EVT_MENU, self.popupItemPPSview,   id=self.popupID9)
            self.Bind(wx.EVT_MENU, self.popupItemCopy,      id=self.popupID10)
            self.Bind(wx.EVT_MENU, self.popupItemPaste0,    id=self.popupID11)
            self.Bind(wx.EVT_MENU, self.popupItemPaste1,    id=self.popupID12)
            self.Bind(wx.EVT_MENU, self.popupItemPaste2,    id=self.popupID14)
            self.Bind(wx.EVT_MENU, self.popupCopy2GAS,      id=self.popupID6)

            # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID6, u"Копировать основу")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID1, u"Установить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID7, u"Ограничить ВСЕ ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID10, u"Копировать")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID11, u"Вставить")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID12, u"Вставить +1")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID14, u"Вставить +2")
        img = wx.Image(os.getcwd() + '\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.popupID2, u"Увеличить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_top.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID3, u"Уменьшить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.popupID8, u"Умножить выделенные ячейки")
        img = wx.Image(os.getcwd()+'\pic\\arrow_down.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # Копировать основу в газовую калибровку
    def popupCopy2GAS(self, event):
        for row in range(ED.Cal_table_TURBO_size):
            for col in range(ED.Cal_table_RPM_size):
                ED.Gas_table[row][col] = int(self.GetCellValue(row, col))

class One_grid(gridlib.Grid):
    ''' Выводит таблицу в одну строку и добавляет к сизеру
    '''
    def __init__(self, parent, label, size, row_hight, row_hight_label, border, sizer, table):
        '''
        :param parent: Родительское окно
        :param label: Заголовок строки
        :param size: Размер таблицы
        :param row_hight - Высота строки
        :param row_hight_label - Высота строки заголовков, 0 - нет вообще заголовкоы
        :param border Отступ вокруг таблицы
        :param sizer Сизер к которому добавится таблица
        :param table: Собственно таблица, которую выводим
        :return:
        '''
        self.table = table  # копируем переменные, что бы к ним был доступ из других методов класса
        self.size = size
        self.parent = parent
        # Явно вызываем конструктор wx.grid, но этого недостаточно что бы создать сетку
        gridlib.Grid.__init__(self, self.parent, -1)
        self.currentlySelectedCell = (0, 0)
        # Создаем таблицу
        self.CreateGrid(size, 1)
        # Установить редактор для всех элементов сетки, только цифры -1,-1 это без контроля диапазона
        self.SetDefaultEditor( wx.grid.GridCellNumberEditor(-1,-1))
        # Размер столбца
        self.SetRowLabelSize(row_hight_label)
        self.SetColLabelSize(40)
        # Запрещаем изменять размеры строк, столюцов и ячеек
        self.DisableDragColSize()
        self.DisableDragRowSize()
        self.DisableDragGridSize()
        self.SetColSize(0, 50)  # Размер колонок
        self.SetColLabelValue(0, label)
        # Именуем строки столбцы
        for row in range(size):
            self.SetRowSize(row, row_hight)  # Размер строк
            # Устанавливаем порядковый номер как заголовки строк
            self.SetRowLabelValue(row, str(row + 1))
            # Инициализируем значения таблицы
            self.SetCellValue(row, 0, str(table[row]))

        # Устанавливаем обработчик, что бы из редактора можно было выходить по нажатой стрелке как в Excel
        self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.onCellEdit_like_Excel)
        # Устанавливаем обработчик на правую кнопку мыши
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.showPopupMenu)

        sizer.Add(self, 0, wx.LEFT | wx.TOP | wx.ALIGN_LEFT | wx.ALIGN_BOTTOM, border)

    def showPopupMenu(self, event):
        """ Метод для меню по правой кнопки мыши
        Интерпретатор ожидает 2 аргумента для Bind, поэтому все ф-ции обрабатывающие EVNT с 2 аргументами
        """
        # make a menu
        menu = wx.Menu()
        # Добавляем пункты в меню
        self.popupItemPreparation( menu )
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def popupItemPreparation(self, menu):
        '''
        :param menu: Меню в которое добавляются пункты
        :return:
        '''
        self.popupID1 = wx.NewId()
        self.popupID3 = wx.NewId()

        self.Bind(wx.EVT_MENU, self.popupItemRaznoska, id=self.popupID1)
        self.Bind(wx.EVT_MENU, self.popupItemSet,id=self.popupID3)

        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID1, u"Разнести")
        img  = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)

        item = wx.MenuItem(menu, self.popupID3, u"Установить")
        img = wx.Image(os.getcwd()+'\pic\\arrow_top.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)

    # Разнести
    def popupItemRaznoska(self, event):
        ''' Берет полседнее и первое значение из таблицы и линейно апроксимирует всю таблицу
        :param event: Формальный параметр
        :return:
        '''
        Func.Raznoska(self.table, int(self.GetCellValue(0, 0)), int(self.GetCellValue(self.size - 1, 0)))
        for row in range(1, self.size):
           self.SetCellValue(row, 0, str(self.table[row]))

    # Установить в Значение выделенные ячейки
    def popupItemSet(self, event):
        '''  Заполняем выделенные ячейки значением
        :param event: Формальный параметр
        :return:
        '''
        # Задаем значение в которое будем устанавливать
        setValue=wx.GetNumberFromUser(u"Ввод значения в которое будут установленны выделенные ячейки ", u"Значение:",
                                   u"Ввод значения в которое будут установленны выделенные ячейки ",
                                   value = 0, min = 0 )
        # Проверка есть ли выделенное
        flagSel = True
        for row in range(self.size):
            if self.IsInSelection(row, 0):
                flagSel = False
                self.SetCellValue(row, 0, str( setValue) )
        if flagSel:
            wx.MessageBox(u'Необходимо выбрать ячейки, которые вы желаете установить в Значение',
                          caption=u"Сообщение о проблемах", style=wx.OK | wx.ICON_ERROR)

    def onCellEdit_like_Excel(self, event):
        '''  Метод N1, что бы из редактора можно было выходить по нажатой стрелке как в Excel
        When cell is edited, get a handle on the editor widget
        and bind it to EVT_KEY_DOWN
        '''
        editor = event.GetControl()
        editor.Bind(wx.EVT_KEY_DOWN, self.onEditorKey_like_Excel)
        event.Skip()

    def onEditorKey_like_Excel(self, event):
        ''' Метод N2, что бы из редактора можно было выходить по нажатой стрелке как в Excel
        Handler for the wx.grid's cell editor widget's keystrokes. Checks for specific
        keystrokes, such as arrow up or arrow down, and responds accordingly. Allows
        all other key strokes to pass through the handler.
        '''
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_UP:
            self.MoveCursorUp(False)
        elif keycode == wx.WXK_DOWN:
            self.MoveCursorDown(False)
        elif keycode == wx.WXK_LEFT:
            self.MoveCursorLeft(False)
        elif keycode == wx.WXK_RIGHT:
            self.MoveCursorRight(False)
        else:
            pass
        event.Skip()

class PPSviewGrid(One_grid):
    def popupItemPreparation(self, menu):
        One_grid.popupItemPreparation(self,menu)
        self.popupID5 = wx.NewId()
        self.Bind(wx.EVT_MENU, self.popupItemRefresh,id=self.popupID5)
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID5, u"Обновить графики")
        img  = wx.Image(os.getcwd()+'\pic\\arrow_next.bmp', wx.BITMAP_TYPE_ANY)
        item.SetBitmap(wx.BitmapFromImage(img))
        menu.AppendItem(item)

    def popupItemRefresh(self, event):
        PV.calcGraph( ED.Cal_hold, ED.DIESEL_cal, ED.dialog, ED.diesel_k, ED.gas_k )
