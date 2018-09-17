import src.utils as utils

from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

import operator

class Spreadsheet(Widget):
    class _CellManager(object):
        class _CellView(TextInput):
            def __init__(self, row = None, col = None, *args, **kw):
                self.__row = row
                self.__col = col
                super().__init__(*args, **kw)

                self.__conversions = {}
                self.__init_conversions()

            def __init_conversions(self):
                self.__conversions['default'] = [1, 1, 1, 1]
                self.__conversions['selected'] = [0, 1, 0, 1]
                self.__conversions['anchor'] = [218/255, 165/255, 32/255, 1]

            def _feed_cell_manager(self, cell_manager):
                self.__cell_manager = cell_manager

            @property
            def coordinates(self):
                return self.__row, self.__col

            def config(self, **options):
                for key, value in options.items():
                    if value in self.__conversions:
                        value = self.__conversions[value]
                    self.__setattr__(key, value)

            def on_touch_down(self, touch):
                return self.__cell_manager.on_touch_down(touch)

            def on_touch_move(self, touch):
                return self.__cell_manager.on_touch_move(touch)

        class _Cell(object):
            def __init__(self, row, col):
                self.row = row
                self.col = col

                self.__options = {}
                self.__init_options()

                self.__formula = ''

                self.__mode = 'computed'

                self.__computed = str(row*2**5+col)

            def __init_options(self):
                pass

            @property
            def coordinates(self):
                return (self.row, self.col)

            @property
            def index(self):
                return utils.get_cell_index(self.row, self.col)
            
            def config(self, **options):
                self.__options.update(options)
                return self.__options
            
            @property
            def formula(self):
                return self.__formula_value

            @formula.setter
            def formula(self, value):
                self.__formula = value

            @property
            def mode(self):
                return self.__mode

            @mode.setter
            def mode(self, value):
                self.__mode = value

            @property
            def display(self):
                return self.formula if self.mode == 'formula' else self.computed

            @property
            def computed(self):
                return self.__computed

            def __str__(self):
                return utils.get_cell_index(self.row, self.col)

        def __init__(self, cells=None, texts=None, row=0, col=0):
            self.__cells = cells
            self.__texts = texts
            self.__ulr, self.__ulc = row, col
            self.__selected_cells = []

            self.__anchor_cell = self.__cells[0][0]
            self.__reel_cell = self.__anchor_cell
            self.__prev_reel_cell = None

            self.__click_modifiers = []

            self.__update_display()

        def __cell_to_text(self, cell):
            text_row, text_col = tuple(map(operator.sub, cell.coordinates, self.ul))
            return self.__texts[text_row][text_col]

        def __text_to_cell(self, text):
            cell_row, cell_col = tuple(map(operator.add, text.coordinates, self.ul))
            return self.__cells[cell_row][cell_col]

        def click_cell(self, cell = None):
            print('click')
            if not cell:
                cell = self.__anchor_cell

            if [cell] == self.__selected_cells:
                # Make editable and set focus
                pass
            else:
                self.select_cell(cell, anchor=True, exclusive=True)

        def control_click_cell(self, cell):
            print('control click')
            if cell in self.__selected_cells:
                self.deselect_cell(cell)
            else:
                self.select_cell(cell, anchor=True, exclusive=False)

        def shift_click_cell(self, cell):
            print('shift click ' + str(cell))
            self.__set_reel_cell(cell)
            self.select_range(exclusive=True)

        def control_shift_click_cell(self, cell):
            print('Control shift click ' + str(cell))
            self.__set_reel_cell(cell)
            self.select_range(exclusive=False)

        def on_touch_down(self, touch):
            if touch.button == 'left':
                text = [self.__texts[row][col] for row in range(len(self.__texts)) for col in range(len(self.__texts[0])) if self.__texts[row][col].collide_point(*touch.pos)][0]
                cell = self.__text_to_cell(text)
                if 'ctrl' and 'shift' in self.__click_modifiers:
                    self.control_shift_click_cell(cell)
                elif 'ctrl' in self.__click_modifiers:
                    self.control_click_cell(cell)
                elif 'shift' in self.__click_modifiers:
                    self.shift_click_cell(cell)
                else:
                    self.click_cell(cell)
            return True

        def on_touch_move(self, touch):
            if touch.button == 'left':
                text = [self.__texts[row][col] for row in range(len(self.__texts)) for col in range(len(self.__texts[0])) if self.__texts[row][col].collide_point(*touch.pos)][0]
                cell = self.__text_to_cell(text)
                self.__set_reel_cell(cell)
                self.select_range()

        def select_all_cells(self, event):
            print('Selecting all cells in the grid!')

            self.__set_anchor_cell(self.__cells[0][0])
            self.__set_reel_cell(self.__cells[-1][-1])
            self.select_range(exclusive=True)

        def select_cells(self, cells, exclusive=False):
            if exclusive:
                self.deselect_all_cells()
            
            [self.select_cell(cell, exclusive=False) for cell in cells]

        def select_cell(self, cell, anchor=False, exclusive=False):
            if exclusive:
                self.deselect_all_cells()

            self.__selected_cells.append(cell)

            if anchor:
                self.__set_anchor_cell(cell)
            else:
                print('config')
                self.config(cell, background_color = 'selected')

        def deselect_all_cells(self, but=[]):
            print('deselect all')

            self.deselect_cells([cell for cell in self.__selected_cells if cell not in but])

        def deselect_cells(self, cells):
            [self.deselect_cell(cell) for cell in cells]

        def deselect_cell(self, cell):
            try:
                self.__selected_cells.remove(cell)
                self.config(cell, background_color = 'default')

                if cell == self.__anchor_cell:
                    if self.__selected_cells:
                        self.__set_anchor_cell(self.__selected_cells[-1])
                    else:
                        self.__clear_anchor_cell()

            except ValueError:
                pass

        def select_range(self, exclusive=False):
            anchor_coordinates = (a_row, a_column) = self.__anchor_cell.coordinates
            prev_reel_coordinates = (p_row, p_column) = self.__prev_reel_cell.coordinates
            reel_coordinates = (r_row, r_column) = self.__reel_cell.coordinates

            row_range = utils.closed_range(a_row, r_row)[::-1]
            if self.__prev_reel_cell:
                prev_row_range = utils.closed_range(a_row, p_row)[::-1]

            column_range = utils.closed_range(a_column, r_column)[::-1]
            if self.__prev_reel_cell:
                prev_column_range = utils.closed_range(a_column, p_column)[::-1]

            if row_range[-1] > prev_row_range[-1]:
                print('The row minimum increased')
                for row in range(prev_row_range[-1], row_range[-1]):
                    self.deselect_cells([self.__cells[row][column] for column in prev_column_range])

            elif row_range[0] < prev_row_range[0]:
                print('The row maximum decreased')
                for row in range(prev_row_range[0], row_range[0], -1):
                    self.deselect_cells([self.__cells[row][column] for column in prev_column_range])

            if row_range[-1] < prev_row_range[-1]:
                print('The row minimum decreased')
                for row in range(row_range[-1], prev_row_range[-1]):
                    self.select_cells([self.__cells[row][column] for column in prev_column_range])

            elif row_range[0] > prev_row_range[0]:
                print('The row maximum increased')
                for row in range(row_range[0], prev_row_range[0], -1):
                    self.select_cells([self.__cells[row][column] for column in prev_column_range])

            
            if column_range[-1] > prev_column_range[-1]:
                print('The column minimum increased')
                for column in range(prev_column_range[-1], column_range[-1]):
                    self.deselect_cells([self.__cells[row][column] for row in row_range])

            elif column_range[0] < prev_column_range[0]:
                print('The column maximum decreased')
                for column in range(prev_column_range[0], column_range[0], -1):
                    self.deselect_cells([self.__cells[row][column] for row in row_range])


            if column_range[-1] < prev_column_range[-1]:
                print('The column minimum decreased')
                for column in range(column_range[-1], prev_column_range[-1]):
                    self.select_cells([self.__cells[row][column] for row in row_range])

            elif column_range[0] > prev_column_range[0]:
                print('The column maximum increased')
                for column in range(column_range[0], prev_column_range[0], -1):
                    self.select_cells([self.__cells[row][column] for row in row_range])

        def __clear_anchor_cell(self):
            self.__anchor_cell = None

        def __set_anchor_cell(self, cell):        
            print('Setting cell ' + str(cell) + ' to anchor')

            if self.__anchor_cell and self.__anchor_cell in self.__selected_cells:
                self.config(self.__anchor_cell, background_color = 'selected')
            self.__set_reel_cell(cell)
            self.__anchor_cell = cell
            self.config(self.__anchor_cell, background_color = 'anchor')

        def __set_reel_cell(self, cell):
            self.__include_cell_in_box(cell)
            self.__reel_cell, self.__prev_reel_cell = cell, self.__reel_cell

        @property
        def ul(self):
            return (self.__ulr, self.__ulc)
        
        @ul.setter
        def ul(self, value):
            ulr_old, ulc_old = self.__ulr, self.__ulc
            self.__ulr, self.__ulc = utils.normalize_cell_notation(value)
            if ulr_old != self.__ulr or ulc_old != self.__ulc:
                self.__update_display()

        def vertical(self, amt):
            row, col = self.__anchor_cell.coordinates
            if row + amt >= 0 and row + amt < len(self.__cells):
                self.select_cell(self.__cells[row + amt][col], anchor=True, exclusive=True)
            elif row + amt >= 0:
                self.select_cell(self.__cells[len(self.__cells) - 1][col], anchor=True, exclusive=True)
            elif row + amt < len(self.__cells):
                self.select_cell(self.__cells[0][col], anchor=True, exclusive=True)

        def horizontal(self, amt):
            row, col = self.__anchor_cell.coordinates
            if col + amt >= 0 and col + amt < len(self.__cells[0]):
                self.select_cell(self.__cells[row][col + amt], anchor=True, exclusive=True)
            elif col + amt >= 0:
                self.select_cell(self.__cells[row][len(self.__cells[0]) - 1], anchor=True, exclusive=True)
            elif col + amt < len(self.__cells):
                self.select_cell(self.__cells[row][0], anchor=True, exclusive=True)

        def up(self, amt = 1):
            self.vertical(-1 * amt)
            
        def down(self, amt=1):
            self.vertical(amt)

        def left(self, amt=1):
            self.horizontal(-1 * amt)

        def right(self, amt=1):
            self.horizontal(amt)

        def move_reel_vertical(self, amt):
            row, col = tuple(map(operator.add, self.__reel_cell.coordinates, (amt, 0)))
            
            if row < 0:
                row = 0
            elif row >= len(self.__cells):
                row = len(self.__cells) - 1

            self.__set_reel_cell(self.__cells[row][col])
            self.select_range(exclusive=True)

        def move_reel_horizontal(self, amt):
            row, col = tuple(map(operator.add, self.__reel_cell.coordinates, (0, amt)))
            if col < 0:
                col = 0
            elif col >= len(self.__cells[0]):
                col = len(self.__cells[0]) - 1
            self.__set_reel_cell(self.__cells[row][col])
            self.select_range(exclusive=True)

        def shift_up(self, amt = 1):
            self.move_reel_vertical(-1 * amt)
            
        def shift_down(self, amt=1):
            self.move_reel_vertical(amt)

        def shift_left(self, amt=1):
            self.move_reel_horizontal(-1 * amt)

        def shift_right(self, amt=1):
            self.move_reel_horizontal(amt)

        def __include_cell_in_box(self, cell):
            row, col = cell.coordinates

            if row < self.__ulr:
                self.ul = (row, self.__ulc)
            elif row > self.__ulr + len(self.__texts) - 1:
                self.ul = (row - (len(self.__texts) - 1), self.__ulc)

            if col < self.__ulc:
                self.ul = (self.__ulr, col)
            elif col > self.__ulc + len(self.__texts[0]) - 1:
                self.ul = (self.__ulr, col - (len(self.__texts[0]) - 1))

        def config(self, cell, **options):
            cell.config(**options)
            try:
                self.__update_style(cell)
            except IndexError:
                pass

        def __update_style(self, cell):
            text = self.__cell_to_text(cell)
            text.config(**cell.config())

        def __update_display(self):
            for text in utils.flatten(self.__texts):
                cell = self.__text_to_cell(text)
                text.text = cell.display
                text.config(**cell.config())

        def add_click_modifier(self, mod):
            print('adding' + mod)
            if mod not in self.__click_modifiers:
                self.__click_modifiers.append(mod)

        def remove_click_modifier(self, mod):
            print('removing' + mod)
            self.__click_modifiers.remove(mod)

    class elist(list):
        def shape(self, filler, wrapperlist=list):
            l = wrapperlist([None for i in range(len(self))])
            for idx in range(len(self)):
                if isinstance(self[idx], wrapperlist):
                    l[idx] = self[idx].shape(filler)
                else:
                    l[idx] = filler
            return l

    class celllist(elist):
        @property
        def formula_value(self):
            formulas = formulalist()
            for item in self:
                if isinstance(item, celllist):
                    formulas.append(formulalist([subitem.formula_value for subitem in item]))
                else: # isinstance(item, _Cell)
                    formulas.append(item.formula_value)
            return formulas


        @formula_value.setter
        def formula_value(self, formula_value):
            if isinstance(formula_value, zip) or type(formula_value) == tuple:
                formula_value = celllist(formula_value)
            if isinstance(formula_value, list):
                if len(formula_value) == len(self):
                    for idx, item in enumerate(self):
                        item.formula_value = formula_value[idx]
            else:
                for item in self:
                    item.formula_value = formula_value


        def config(self, **options):
            for item in self:
                item.config(**options)

        def shape(self, filler):
            return super().shape(filler, wrapperlist=celllist)
        
        def __sub__(self, other):
            return [item for item in self if item not in other]
        
        def __getitem__(self, index):
            if type(index) == str:
                index = utils.get_column_index(index)

            elif type(index) == slice:
                start = utils.get_column_index(index.start) if isinstance(index.start, str) else index.start if index.start else index.start
                stop = utils.get_column_index(index.stop) if isinstance(index.stop, str) else index.stop if index.stop else index.stop
                
                slce = slice(start, stop, index.step)
                return celllist(super().__getitem__(slce))

            return super().__getitem__(index)


        def __getattr__(self, attr):
            print('getattr')
            a = attr.lower()

            if a == 'col' or a == 'column':
                return formulalist([item[a] if isinstance(item, list) else item.coordinates[1] for item in self])
            elif a == 'row':
                return formulalist([item.__getattr__(attr) if isinstance(item, list) else item.coordinates[0] for item in self])

    import operator as op

    class formulalist(elist):

        def shape(self, filler):
            return super().shape(filler, wrapperlist=formulalist)

        def combine(self, other, operator):
            if isinstance(other, celllist):
                other = other.formula_value
            if isinstance(other, formulalist) and self.shape(1) == self.shape(1):
                flist = formulalist([None for i in range(len(self))])
                for idx in range(len(self)):
                    flist[idx] = operator(self[idx], other[idx])
                return flist
            else:
                return operator(self, self.shape(other))


        def __add__(self, other):
            return self.combine(other, op.add)

        def __radd__(self, other):
            return self + other

        def __iadd__(self, other):
            return self + other


        def __sub__(self, other):
            return self.combine(other, op.sub)

        def __rsub__(self, other):
            return -1 * (self - other)

        def __isub__(self, other):
            return self - other

        def merge(self, other, operator):
            try:
                other = float(other.formula_value)
            except (AttributeError, TypeError):
                pass
            if isinstance(other, list) or isinstance(other, int) or isinstance(other, float):
                return self.combine(other, operator)

        def __mul__(self, other):
            return self.merge(other, op.mul)

        def __rmul__(self, other):
            return self * other

        def __imul__(self, other):
            return self * other

        def inverse(self):
            return [item.inverse() if isinstance(item, list) else 1 / item for item in self]

        def __div__(self, other):
            return self.merge(other, op.div)

        def __rdiv__(self, other):
            return self.inverse() * other

        def __idiv__(self, other):
            return self / other

        def __pow__(self, other):
            return self.merge(other, op.pow)

        def __ipow__(self, other):
            return self ** other
    

    def build(self):
        return self.__layout

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.__on_key_press)
        self._keyboard = None

    def _modify(self, amt):
        for row in range(self.rows):
            for col in range(self.cols):
                self.__cells[row][col].text = str(int(self.__cells[row][col].text) + amt)

    def __on_key_press(self, keycode, modifiers):
        if keycode[1] == 'up':
            if 'shift' in modifiers:
                self.__cell_manager.shift_up()
            else:
                self.__cell_manager.up()
        elif keycode[1] == 'down':
            if 'shift' in modifiers:
                self.__cell_manager.shift_down()
            else:
                self.__cell_manager.down()

        if keycode[1] == 'right':
            if 'shift' in modifiers:
                self.__cell_manager.shift_right()
            else:
                self.__cell_manager.right()
        elif keycode[1] == 'left':
            if 'shift' in modifiers:
                self.__cell_manager.shift_left()
            else:
                self.__cell_manager.left()
        
        if keycode[1] == 'pageup':
            if 'shift' in modifiers:
                self.__cell_manager.shift_up(self.rows)
            else:
                self.__cell_manager.up(self.rows)
        elif keycode[1] == 'pagedown':
            if 'shift' in modifiers:
                self.__cell_manager.shift_down(self.rows)
            else:
                self.__cell_manager.down(self.rows)

        if keycode[1] == 'home':
            if 'shift' in modifiers:
                self.__cell_manager.shift_left(self.cols)
            else:
                self.__cell_manager.left(self.cols)
        elif keycode[1] == 'end':
            if 'shift' in modifiers:
                self.__cell_manager.shift_right(self.cols)
            else:
                self.__cell_manager.right(self.cols)

        if keycode[1] == 'lctrl' or keycode[1] == 'rctrl':
            self.__cell_manager.add_click_modifier('ctrl')
        elif keycode[1] == 'shift' or keycode[1] == 'rshift':
            self.__cell_manager.add_click_modifier('shift')
        elif keycode[1] == 'enter':
            self.__cell_manager.click_cell()

        return True

    def __on_key_release(self, keycode):
        if keycode[1] == 'lctrl' or keycode[1] == 'rctrl':
            self.__cell_manager.remove_click_modifier('ctrl')
        elif keycode[1] == 'shift' or keycode[1] == 'rshift':
            self.__cell_manager.remove_click_modifier('shift')

    def __init__(self, program_paths, rows, cols, *args, **kw):
        super().__init__(*args, **kw)

        self._Cell = self._CellManager._Cell
        self._CellView = self._CellManager._CellView

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=lambda idc1, keycode, idc2, modifiers: self.__on_key_press(keycode, modifiers),
                            on_key_up=lambda idc1, keycode: self.__on_key_release(keycode))

        self.program_paths = program_paths

        self.rows = rows
        self.cols = cols

        self.__anchor_cell = None
        self.__reel_cell = None
        self.__prev_reel_cell = None

        self.__layout = BoxLayout(orientation='vertical')

        self.__cell_layout = GridLayout(cols = self.cols)

        self.__cells = [[self._Cell(row, col) for col in range(2**5)] for row in range(2**10)]
        self.__texts = [[None for col in range(self.cols)] for row in range(self.rows)]

        for row in range(self.rows):
            for col in range(self.cols):
                t = self._CellView(disabled=True, row=row, col=col)
                self.__cell_layout.add_widget(t)
                self.__texts[row][col] = t

        self.__cell_manager = self._CellManager(cells = self.__cells, texts = self.__texts, row=0, col=0)

        [text._feed_cell_manager(self.__cell_manager) for text in utils.flatten(self.__texts)]

        self.__layout.add_widget(self.__cell_layout)

        #Window.size = (self.cols * 120, self.rows*30)

        