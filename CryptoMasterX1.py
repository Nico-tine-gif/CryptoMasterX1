#!/usr/bin/env python3
import os
import time
import json

class CryptoMasterTermux:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.crypto_dir = os.path.join(self.home, "CryptoMasterX1")
        os.makedirs(self.crypto_dir, exist_ok=True)
        
        self.log_path = os.path.join(self.crypto_dir, "auto.log")
        self.command_path = os.path.join(self.crypto_dir, "command.txt")
        self.response_path = os.path.join(self.crypto_dir, "response.txt")
        self.state_path = os.path.join(self.crypto_dir, "state")
        
        self.running = True
        self.log("CryptoMasterX1 started")
        self.log(f"Directory: {self.crypto_dir}")
    
    def log(self, message):
        try:
            with open(self.log_path, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except:
            pass
        print(message)
    
    def process_command(self, command):
        cmd = command.lower().strip()
        
        if cmd == 'status':
            return "Status: Running\nUptime: Active\nSystem: Operational"
        elif cmd == 'price':
            return "BTC: $65,000\nETH: $3,500\nSOL: $150"
        elif cmd == 'balance':
            return "Balance: 0.5 BTC\nTotal: $32,500 USD"
        elif cmd == 'help':
            return "Commands: status, price, balance, help"
        else:
            return f"Unknown command: {command}"
    
    def run(self):
        self.log("Processing commands from APK...")
        
        while self.running:
            try:
                if os.path.exists(self.command_path):
                    with open(self.command_path, 'r') as f:
                        command = f.read().strip()
                    
                    if command:
                        self.log(f"Command received: {command}")
                        response = self.process_command(command)
                        
                        with open(self.response_path, 'w') as f:
                            f.write(response)
                        
                        open(self.command_path, 'w').close()
                
                time.sleep(0.5)
                
            except Exception as e:
                self.log(f"Error: {e}")
                time.sleep(1)

if __name__ == '__main__':
    crypto = CryptoMasterTermux()
    crypto.run()
