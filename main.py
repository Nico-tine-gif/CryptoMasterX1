from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
import os

class CryptoMasterApp(App):
    def build(self):
        self.l = Label(text='CryptoMasterX1 Starting...')
        Clock.schedule_interval(self.upd, 1)
        return self.l
    
    def upd(self, dt):
        p = os.path.expanduser('~/CryptoMasterX1/auto.log')
        if os.path.exists(p):
            try:
                with open(p, errors='ignore') as f:
                    self.l.text = f.read()[-3000:]
            except:
                pass
        else:
            self.l.text = 'Waiting for log...'

CryptoMasterApp().run()
