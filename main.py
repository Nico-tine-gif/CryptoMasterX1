from dotenv import load_dotenv
load_dotenv()

import os
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock

# Your pipeline files
import master_pipeline

print(f"ENV CHECK: SPOT={os.getenv('BINANCE_SPOT')} LIVE={os.getenv('LIVE_EXECUTION')} TESTNET={os.getenv('BINANCE_TESTNET')}")

class CryptoMasterX1App(App):
    def build(self):
        self.label = Label(text='CryptoMasterX1\nInitializing Binance...\nSPOT: '+str(os.getenv('BINANCE_SPOT')))
        # Start pipeline after UI loads
        Clock.schedule_once(self.start_pipeline, 2)
        return self.label

    def start_pipeline(self, dt):
        try:
            self.label.text = "Starting Master Pipeline...\nLive: " + str(os.getenv('LIVE_EXECUTION'))
            # Call your main function from master_pipeline
            if hasattr(master_pipeline, 'main'):
                master_pipeline.main()
            elif hasattr(master_pipeline, 'run'):
                master_pipeline.run()
            else:
                self.label.text = "Pipeline loaded\nCheck logs"
        except Exception as e:
            self.label.text = f"Error: {e}"
            print(f"PIPELINE ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    CryptoMasterX1App().run()
