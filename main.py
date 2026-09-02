#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CryptoMasterX1 - Main Entry Point
This is the Kivy application entry point for Android
"""

import os
import sys

# Import your main app
try:
    from CryptoMasterX1 import CryptoMasterX1App
except ImportError:
    # If your app is defined differently, adjust this import
    print("Could not import CryptoMasterX1App, looking for other apps...")
    # Try to find any Kivy app
    import inspect
    import importlib
    
    for file in os.listdir('.'):
        if file.endswith('.py') and file != 'main.py':
            try:
                module_name = file[:-3]
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and 'App' in name:
                        print(f"Found app: {name} in {file}")
                        # Set the app class
                        exec(f"from {module_name} import {name}")
                        exec(f"app = {name}()")
                        app.run()
                        sys.exit(0)
            except Exception as e:
                print(f"Error importing {file}: {e}")
    
    # If no app found, create a simple one
    from kivy.app import App
    from kivy.uix.label import Label
    
    class SimpleApp(App):
        def build(self):
            return Label(text='CryptoMasterX1\nVersion 1.0.0')
    
    app = SimpleApp()
    app.run()
    sys.exit(0)

if __name__ == '__main__':
    app = CryptoMasterX1App()
    app.run()
