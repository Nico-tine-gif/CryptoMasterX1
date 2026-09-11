from kivy.app import App
from kivy.uix.label import Label
import master_pipeline

class CryptoMasterX1App(App):
    def build(self):
        return Label(text='CryptoMasterX1 - 11 Phase System Ready\nExecution LOCKED - Safe Mode')

if __name__ == '__main__':
    CryptoMasterX1App().run()
