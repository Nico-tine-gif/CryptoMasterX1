#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CryptoMasterX1 - Kivy Android App
Wrapper for the terminal-based CryptoMasterX1
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

# Import your existing code
from CryptoMasterX1 import CryptoMasterTermux

class CryptoMasterX1App(App):
    def build(self):
        Window.size = (400, 700)
        self.crypto = CryptoMasterTermux()
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='CryptoMasterX1', font_size=24, size_hint_y=0.1)
        layout.add_widget(title)
        
        # Output area (scrollable)
        self.output = TextInput(
            text='Welcome to CryptoMasterX1\nType a command below...',
            readonly=True,
            multiline=True,
            size_hint_y=0.7
        )
        layout.add_widget(self.output)
        
        # Input area
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        self.input = TextInput(text='', multiline=False, size_hint_x=0.8)
        self.input.bind(on_text_validate=self.execute_command)
        input_layout.add_widget(self.input)
        
        send_btn = Button(text='Send', size_hint_x=0.2)
        send_btn.bind(on_press=self.execute_command)
        input_layout.add_widget(send_btn)
        
        layout.add_widget(input_layout)
        
        # Quick buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        for cmd in ['status', 'price', 'balance', 'help']:
            btn = Button(text=cmd)
            btn.bind(on_press=lambda x, c=cmd: self.quick_command(c))
            button_layout.add_widget(btn)
        layout.add_widget(button_layout)
        
        return layout
    
    def execute_command(self, instance):
        command = self.input.text.strip()
        if command:
            self.update_output(f">>> {command}")
            response = self.crypto.process_command(command)
            self.update_output(response)
            self.input.text = ''
    
    def quick_command(self, command):
        self.input.text = command
        self.execute_command(None)
    
    def update_output(self, text):
        current = self.output.text
        self.output.text = f"{current}\n{text}"
        # Scroll to bottom
        self.output.cursor = (0, len(self.output.text))

if __name__ == '__main__':
    CryptoMasterX1App().run()
