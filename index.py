from kivy.app import App

import os


from src.spreadsheet import Spreadsheet
    
class SpreadsheetApp(App):
    def build(self):
        ss = Spreadsheet(program_paths = {'index':os.path.dirname(os.path.realpath(__file__))},
                         rows=20, cols=8)
        return ss.build()

SpreadsheetApp().run()