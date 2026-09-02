#!/usr/bin/env python3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class CryptoMasterX1App(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='CryptoMasterX1', font_size=24))
        
        self.output = TextInput(text='Welcome!', readonly=True, multiline=True)
        layout.add_widget(self.output)
        
        input_box = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        self.input = TextInput(multiline=False)
        input_box.add_widget(self.input)
        
        btn = Button(text='Send')
        btn.bind(on_press=self.execute_command)
        input_box.add_widget(btn)
        
        layout.add_widget(input_box)
        return layout
    
    def execute_command(self, instance):
        self.output.text = f"You typed: {self.input.text}"

if __name__ == '__main__':
    CryptoMasterX1App().run()
