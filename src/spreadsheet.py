import src.utils as utils

from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import operator

class Spreadsheet(Widget):
    class _CellView(TextInput):
        def __init__(self, row = None, col = None, *args, **kw):
            self.__row = row
            self.__col = col
            super().__init__(*args, **kw)

        def _feed_cell_manager(self, cell_manager):
            self.__cell_manager = cell_manager

        @property
        def coordinates(self):
            return self.__row, self.__col

        def config(self, **options):
            for key, value in options.items():
                self.__setattr__(key, value)

        def on_touch_down(self, touch):
            return self.__cell_manager.on_touch_down(touch)

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

        @property
        def config(self):
            return self.__options
        
        @config.setter
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

    class _CellManager(object):
        def __init__(self, cells=None, texts=None, row=0, col=0):
            self.__cells = cells
            self.__texts = texts
            self.__ulr, self.__ulc = row, col
            self.__selected_cells = []

            self.__anchor_cell = self.__cells[0][0]
            self.__reel_cell = self.__anchor_cell
            self.__prev_reel_cell = None

            self.__update_display()

        def on_touch_down(self, touch):
            [print(('!' if text.collide_point(*touch.pos) else '_'), end=',') for text in utils.flatten(self.__texts)]
            print('\n\n\n')
            return True

        def select_all_cells(self, event):
            print('Selecting all cells in the grid!')
            self.__select_range(exclusive=True, anchor='A1', reel=(-1, -1))
            return 'break'

        def select_cells(self, cells, exclusive=False, flip=False):
            if exclusive:
                self.__deselect_all_cells()
            
            [self.__select_cell(cell, exclusive=False, flip=flip) for cell in cells]

        def select_cell(self, cell, anchor=False, exclusive=False, flip=False):
            if exclusive:
                self.__deselect_all_cells()          

            if cell in self.__selected_cells:
                if flip:
                    print('flip')
                    self.__deselect_cell(cell)
                else:
                    if anchor:
                        self.__set_anchor(cell)
                    return
            elif anchor:
                self.__set_anchor(cell)
                self.__selected_cells.append(cell)
            else:
                cell.config(highlightbackground = 'selected')
                self.__selected_cells.append(cell)

            self.god_entry.focus_set()


        def deselect_all_cells(self, but=[]):
            print('deselect all')

            self.__deselect_cells([cell for cell in self.__selected_cells if cell not in but])

        def deselect_cells(self, cells):
            [self.__deselect_cell(cell) for cell in cells]

        def deselect_cell(self, cell):
            try:
                self.__selected_cells.remove(cell)
                cell.config(highlightbackground = 'ghost white')
                if cell == self.__anchor_cell:
                    print('Anchor')
                    anchor = self.__selected_cells[-1] if self.__selected_cells else None
                    self.__set_anchor(anchor)
            except ValueError:
                pass

            if not self.__selected_cells:
                print('no selected cells')
                self.containing_frame.focus_set()

        def select_range(self, keepanchor = True, exclusive = False, flip=False, anchor = None, reel = None):
            #print('Selecting ' + ('exclusive' if exclusive else '') +  ' range: ', end='')

            if exclusive:
                but = [self.__anchor_cell] if keepanchor else []
                self.__deselect_all_cells(but=but)

            if anchor:
                self.__set_anchor(anchor, add=True)

            if reel:
                self.__set_reel_cell(reel)
            
            prev_reel_cell = self.__anchor_cell if exclusive else self.__prev_reel_cell


            anchor_coordinates = (a_row, a_column) = self.__anchor_cell.coordinates
            prev_reel_coordinates = (p_row, p_column) = self.__reel_cell.coordinates
            reel_coordinates = (r_row, r_column) = self.__prev_reel_cell.coordinates

        
            row_range = utils.closed_range(a_row, r_row)[::-1]
            if self.__prev_reel_cell:
                prev_row_range = utils.closed_range(a_row, p_row)[::-1]

            column_range = utils.closed_range(a_column, r_column)[::-1]
            if self.__prev_reel_cell:
                prev_column_range = utils.closed_range(a_column, p_column)[::-1]

            if row_range[-1] > prev_row_range[-1]:
                print('The row minimum increased')
                for row in range(prev_row_range[-1], row_range[-1]):
                    self.__deselect_cells([self.__cells[row][column] for column in prev_column_range])

            elif row_range[0] < prev_row_range[0]:
                print('The row maximum decreased')
                for row in range(prev_row_range[0], row_range[0], -1):
                    self.__deselect_cells([self.__cells[row][column] for column in prev_column_range])

            if row_range[-1] < prev_row_range[-1]:
                print('The row minimum decreased')
                for row in range(row_range[-1], prev_row_range[-1]):
                    self.__select_cells([self.__cells[row][column] for column in prev_column_range], flip=flip)

            elif row_range[0] > prev_row_range[0]:
                print('The row maximum increased')
                for row in range(row_range[0], prev_row_range[0], -1):
                    self.__select_cells([self.__cells[row][column] for column in prev_column_range], flip=flip)

            

            
            if column_range[-1] > prev_column_range[-1]:
                print('The column minimum increased')
                for column in range(prev_column_range[-1], column_range[-1]):
                    self.__deselect_cells([self.__cells[row][column] for row in row_range])

            elif column_range[0] < prev_column_range[0]:
                print('The column maximum decreased')
                for column in range(prev_column_range[0], column_range[0], -1):
                    self.__deselect_cells([self.__cells[row][column] for row in row_range])


            if column_range[-1] < prev_column_range[-1]:
                print('The column minimum decreased')
                for column in range(column_range[-1], prev_column_range[-1]):
                    self.__select_cells([self.__cells[row][column] for row in row_range], flip=flip)

            elif column_range[0] > prev_column_range[0]:
                print('The column maximum increased')
                for column in range(column_range[0], prev_column_range[0], -1):
                    self.__select_cells([self.__cells[row][column] for row in row_range], flip=flip)

        def __set_anchor(self, ref, col = None, add = False, flip=False):        
            if not ref and ref != 0:
                self.__anchor_cell = None
                return

            if type(ref) != self._Cell:
                row, column = utils.normalize_cell_notation(ref, col)
                ref = self.__cells[row][column]

            if flip and cell in self.__selected_cells:
                self.__deselect_cell(cell)
                return

            print('Setting cell ' + repr(cell) + ' to anchor')

            if self.__anchor_cell in self.__selected_cells:
                self.__anchor_cell.config(highlightbackground = 'selected')
            self.__anchor_cell = cell
            self.__anchor_cell.config(highlightbackground = 'anchor')

            self.__set_reel_cell(cell)

            if add and cell not in self.__selected_cells:
                self.__selected_cells.append(cell)

        def __set_reel_cell(self, cell, col=None):
            if type(cell) != self._Cell:
                row, column = utils.normalize_cell_notation(cell, col)
                if type(row) == int and type(column) == int:
                    cell = self.__cells[row][column]

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
            if self.__ulr + amt >= 0 and self.__ulr + amt + len(self.__texts) - 1 < len(self.__cells):
                self.ul = self.__ulr + amt, self.__ulc

        def horizontal(self, amt):
            if self.__ulc + amt >= 0 and self.__ulc + amt + len(self.__texts[0]) - 1 < len(self.__cells[0]):
                print(len(self.__cells[0]), self.__ulc)
                self.ul = self.__ulr, self.__ulc + amt

        def up(self, amt = 1):
            self.vertical(-1 * amt)
            
        def down(self, amt=1):
            self.vertical(amt)

        def left(self, amt=1):
            self.horizontal(-1 * amt)

        def right(self, amt=1):
            self.horizontal(amt)
        

        def __update_display(self):
            for text in utils.flatten(self.__texts):
                row, col = tuple(map(operator.add, text.coordinates, self.ul))
                cell = self.__cells[row][col]
                text.text = cell.display
                text.config(**cell.config)

        def convert(self, view_coordinates):
            return tuple(map(operator.add, (self.__ulr, self.__ulc), view_coordinates))

        def __contains__(self, value):
            return value in self.__selected_cells

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
            self.__cell_manager.up()
        elif keycode[1] == 'down':
            self.__cell_manager.down()
        elif keycode[1] == 'right':
            self.__cell_manager.right()
        elif keycode[1] == 'left':
            self.__cell_manager.left()
        elif keycode[1] == 'pageup':
            self.__cell_manager.up(self.rows)
        elif keycode[1] == 'pagedown':
            self.__cell_manager.down(self.rows)
        elif keycode[1] == 'home':
            self.__cell_manager.left(self.cols)
        elif keycode[1] == 'end':
            self.__cell_manager.right(self.cols)
        else:
            return True

        print(keycode[1])
        print(modifiers)

        return True

    def __init__(self, program_paths, rows, cols, *args, **kw):
        super().__init__(*args, **kw)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=lambda idc1, keycode, idc2, modifiers: self.__on_key_press(keycode, modifiers))

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

        [print(text.coordinates) for text in utils.flatten(self.__texts)]

        self.__layout.add_widget(self.__cell_layout)

        #Window.size = (self.cols * 120, self.rows*30)

        