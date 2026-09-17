#!/usr/bin/env python3
"""
CryptoMasterX1 - Kivy Dashboard
Dark professional trading terminal UI
"""
import json
import threading
import importlib.util
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

# ---------------- Theme ----------------
COLORS = {
    'bg':       (0.03, 0.04, 0.06, 1),
    'card':     (0.07, 0.09, 0.12, 1),
    'card_alt': (0.09, 0.11, 0.15, 1),
    'border':   (0.15, 0.18, 0.24, 1),
    'text':     (0.90, 0.93, 0.96, 1),
    'text_dim': (0.55, 0.60, 0.68, 1),
    'accent':   (0.10, 0.85, 0.70, 1),
    'green':    (0.20, 0.90, 0.55, 1),
    'red':      (0.95, 0.35, 0.45, 1),
    'yellow':   (0.98, 0.78, 0.25, 1),
    'blue':     (0.35, 0.65, 0.98, 1),
    'muted':    (0.20, 0.24, 0.30, 1),
}
Window.clearcolor = COLORS['bg']

KV = r'''
#:import COLORS __main__.COLORS
#:import dp kivy.metrics.dp

<Card@BoxLayout>:
    canvas.before:
        Color:
            rgba: COLORS['card']
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12]
        Color:
            rgba: COLORS['border']
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 12)
            width: 1
    padding: [14, 12]
    spacing: 8

<PhaseDot>:
    orientation: 'vertical'
    size_hint_x: None
    width: '60dp'
    padding: [4, 6]
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: self.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 1
    Label:
        text: root.phase_id
        font_size: '13sp'
        bold: True
        color: COLORS['text']
        halign: 'center'
        text_size: self.size
    Label:
        text: root.phase_label
        font_size: '9sp'
        color: COLORS['text_dim']
        halign: 'center'
        text_size: self.size

<CryptoMasterX1Dashboard>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: COLORS['bg']
        Rectangle:
            pos: self.pos
            size: self.size

    # ======= HEADER =======
    BoxLayout:
        size_hint_y: None
        height: '66dp'
        padding: [16, 8, 16, 4]
        spacing: 10
        canvas.before:
            Color:
                rgba: COLORS['card_alt']
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: COLORS['accent']
            Rectangle:
                pos: self.x, self.y
                size: self.width, 2
        Label:
            text: '[b]CryptoMasterX1[/b]'
            markup: True
            font_size: '22sp'
            color: COLORS['text']
            size_hint_x: None
            width: self.texture_size[0] + dp(10)
        Label:
            text: 'SPOT ONLY  |  LIVE P1-P12'
            font_size: '11sp'
            color: COLORS['text_dim']
            valign: 'middle'
        Widget:
        Label:
            id: live_pill
            text: 'IDLE'
            font_size: '13sp'
            bold: True
            color: COLORS['text_dim']
            size_hint_x: None
            width: '90dp'
            halign: 'right'
            text_size: self.size

    # ======= SCROLL BODY =======
    ScrollView:
        do_scroll_x: False
        bar_width: dp(4)
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: [12, 12]
            spacing: 12

            # --- PIPELINE ---
            Card:
                size_hint_y: None
                height: '190dp'
                orientation: 'vertical'
                Label:
                    text: 'PIPELINE STATUS  |  P1 -> P12'
                    font_size: '12sp'
                    color: COLORS['text_dim']
                    size_hint_y: None
                    height: '18dp'
                    halign: 'left'
                    text_size: self.size
                GridLayout:
                    id: pipeline_grid
                    cols: 6
                    spacing: 6
                    row_default_height: '60dp'
                    row_force_default: True

            # --- SIGNAL ---
            Card:
                size_hint_y: None
                height: '200dp'
                orientation: 'vertical'
                Label:
                    text: 'ACTIVE SIGNAL'
                    font_size: '12sp'
                    color: COLORS['text_dim']
                    size_hint_y: None
                    height: '18dp'
                    halign: 'left'
                    text_size: self.size
                BoxLayout:
                    orientation: 'horizontal'
                    spacing: 20
                    BoxLayout:
                        orientation: 'vertical'
                        spacing: 4
                        Label:
                            id: sig_symbol
                            text: '--'
                            font_size: '26sp'
                            bold: True
                            color: COLORS['text']
                            halign: 'left'
                            text_size: self.size
                            size_hint_y: None
                            height: '36dp'
                        Label:
                            id: sig_direction
                            text: 'NO SIGNAL'
                            font_size: '18sp'
                            bold: True
                            color: COLORS['text_dim']
                            halign: 'left'
                            text_size: self.size
                            size_hint_y: None
                            height: '28dp'
                        Label:
                            id: sig_conf
                            text: 'Confidence: --'
                            font_size: '13sp'
                            color: COLORS['text_dim']
                            halign: 'left'
                            text_size: self.size
                        Widget:
                    BoxLayout:
                        orientation: 'vertical'
                        spacing: 4
                        Label:
                            id: sig_price
                            text: 'Price: --'
                            font_size: '13sp'
                            color: COLORS['text']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: sig_atr
                            text: 'ATR: --'
                            font_size: '13sp'
                            color: COLORS['text_dim']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: sig_sl
                            text: 'SL: --'
                            font_size: '13sp'
                            color: COLORS['red']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: sig_tp1
                            text: 'TP1: --'
                            font_size: '13sp'
                            color: COLORS['green']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: sig_tp2
                            text: 'TP2: --'
                            font_size: '13sp'
                            color: COLORS['green']
                            halign: 'left'
                            text_size: self.size

            # --- MARKET SCANNER ---
            Card:
                size_hint_y: None
                height: '240dp'
                orientation: 'vertical'
                Label:
                    text: 'MARKET SCANNER  |  BINANCE SPOT'
                    font_size: '12sp'
                    color: COLORS['text_dim']
                    size_hint_y: None
                    height: '18dp'
                    halign: 'left'
                    text_size: self.size
                GridLayout:
                    id: scanner_grid
                    cols: 4
                    spacing: 2
                    row_default_height: '24dp'
                    row_force_default: True

            # --- EXECUTION BOUNDARY ---
            Card:
                size_hint_y: None
                height: '160dp'
                orientation: 'vertical'
                Label:
                    text: 'EXECUTION BOUNDARY'
                    font_size: '12sp'
                    color: COLORS['text_dim']
                    size_hint_y: None
                    height: '18dp'
                    halign: 'left'
                    text_size: self.size
                BoxLayout:
                    orientation: 'horizontal'
                    spacing: 12
                    BoxLayout:
                        orientation: 'vertical'
                        spacing: 4
                        Label:
                            id: ex_spot
                            text: 'Spot Only: --'
                            font_size: '12sp'
                            color: COLORS['green']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: ex_fut
                            text: 'Futures: --'
                            font_size: '12sp'
                            color: COLORS['text_dim']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: ex_with
                            text: 'Withdrawals: --'
                            font_size: '12sp'
                            color: COLORS['green']
                            halign: 'left'
                            text_size: self.size
                    BoxLayout:
                        orientation: 'vertical'
                        spacing: 4
                        Label:
                            id: ex_armed
                            text: 'Bot Armed: --'
                            font_size: '12sp'
                            color: COLORS['accent']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: ex_exec
                            text: 'Live Execution: --'
                            font_size: '12sp'
                            color: COLORS['accent']
                            halign: 'left'
                            text_size: self.size
                        Label:
                            id: ex_status
                            text: 'Status: --'
                            font_size: '12sp'
                            color: COLORS['accent']
                            halign: 'left'
                            text_size: self.size

            # --- STATUS ---
            Card:
                size_hint_y: None
                height: '70dp'
                Label:
                    id: status_line
                    text: 'Status: Idle'
                    font_size: '13sp'
                    color: COLORS['text']
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

    # ======= FOOTER =======
    BoxLayout:
        size_hint_y: None
        height: '76dp'
        padding: [12, 12]
        spacing: 12
        canvas.before:
            Color:
                rgba: COLORS['card_alt']
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: COLORS['border']
            Rectangle:
                pos: self.x, self.top - 1
                size: self.width, 1
        Button:
            id: btn_start
            text: 'START'
            font_size: '15sp'
            bold: True
            background_normal: ''
            background_color: COLORS['green']
            color: (0.04, 0.06, 0.08, 1)
            on_release: root.start_pipeline()
        Button:
            id: btn_stop
            text: 'STOP'
            font_size: '15sp'
            bold: True
            background_normal: ''
            background_color: COLORS['red']
            color: (1, 1, 1, 1)
            on_release: root.stop_pipeline()
'''

Builder.load_string(KV)


PHASES = [
    ('P1', 'Scanner'), ('P2', 'Auth'), ('P3', 'Acct'),
    ('P4', 'Universe'), ('P5', 'Mkt'), ('P6', 'Trades'),
    ('P7', 'Entry'), ('P8', 'Lifecycle'), ('P9', 'Gate'),
    ('P10', 'Monitor'), ('P11', 'Verify'), ('P12', 'Execute'),
]

REPORT_MAP = {
    'P1':  'p1_data_collection.json',
    'P2':  'p2_features.json',
    'P3':  'p3_signals.json',
    'P4':  'p4_risk.json',
    'P5':  'p5_market_intelligence.json',
    'P6':  'p6_trade_quality.json',
    'P7':  'p7_entry_validation.json',
    'P8':  'p8_execution_lifecycle.json',
    'P9':  'p9_decision_gate.json',
    'P10': 'p10_trade_lifecycle.json',
    'P11': 'p11_full_system_verification.json',
    'P12': 'p12_live_execution.json',
}


class PhaseDot(BoxLayout):
    phase_id = StringProperty('')
    phase_label = StringProperty('')
    bg_color = ListProperty(COLORS['card'])
    border_color = ListProperty(COLORS['border'])


class CryptoMasterX1Dashboard(BoxLayout):
    running = BooleanProperty(False)
    _dots = {}
    _runner_thread = None
    _stop_event = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.reports_dir = Path(self.app.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        Clock.schedule_once(self._build_pipeline, 0)
        Clock.schedule_interval(self._refresh_ui, 1.5)

    def _build_pipeline(self, dt):
        grid = self.ids.pipeline_grid
        grid.clear_widgets()
        self._dots = {}
        for pid, label in PHASES:
            d = PhaseDot(phase_id=pid, phase_label=label)
            self._dots[pid] = d
            grid.add_widget(d)

    def _read_json(self, name):
        p = self.reports_dir / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def _refresh_ui(self, dt):
        # ---- Pipeline dots ----
        for pid, fname in REPORT_MAP.items():
            data = self._read_json(fname)
            dot = self._dots.get(pid)
            if not dot:
                continue
            if data is None:
                dot.bg_color = COLORS['card']
                dot.border_color = COLORS['border']
            else:
                status = str(data.get('status', '')).upper()
                if 'FAIL' in status or 'REJECT' in status:
                    dot.bg_color = COLORS['red']
                elif 'FLAT' in status:
                    dot.bg_color = COLORS['yellow']
                else:
                    dot.bg_color = COLORS['green']
                dot.border_color = COLORS['accent']

        # ---- Signal ----
        p6 = self._read_json('p6_trade_quality.json') or {}
        trades = p6.get('trades') or []
        if trades:
            t = trades[0]
            self.ids.sig_symbol.text = str(t.get('symbol', '--'))
            d = str(t.get('direction', '--')).upper()
            self.ids.sig_direction.text = d
            self.ids.sig_direction.color = (
                COLORS['green'] if d == 'LONG'
                else COLORS['red'] if d == 'SHORT'
                else COLORS['text_dim']
            )
            conf = t.get('confidence')
            self.ids.sig_conf.text = (
                f"Confidence: {conf}%" if conf is not None else "Confidence: --"
            )
            e = t.get('entry') or {}
            r = t.get('risk') or {}
            tg = t.get('targets') or {}
            self.ids.sig_price.text = f"Price: {e.get('reference_price', '--')}"
            self.ids.sig_atr.text = f"ATR: {e.get('atr_15m', '--')}"
            self.ids.sig_sl.text = f"SL: {r.get('stop_loss', '--')}"
            self.ids.sig_tp1.text = f"TP1: {tg.get('tp1', '--')}"
            self.ids.sig_tp2.text = f"TP2: {tg.get('tp2', '--')}"
        else:
            self.ids.sig_symbol.text = '--'
            self.ids.sig_direction.text = 'NO SIGNAL'
            self.ids.sig_direction.color = COLORS['text_dim']
            self.ids.sig_conf.text = 'Confidence: --'
            self.ids.sig_price.text = 'Price: --'
            self.ids.sig_atr.text = 'ATR: --'
            self.ids.sig_sl.text = 'SL: --'
            self.ids.sig_tp1.text = 'TP1: --'
            self.ids.sig_tp2.text = 'TP2: --'

        # ---- Scanner ----
        self._refresh_scanner()

        # ---- Execution boundary ----
        exec_data = (
            (self._read_json('p12_live_execution.json') or {}).get('execution')
            or (self._read_json('p11_full_system_verification.json') or {}).get('execution_boundary')
            or (self._read_json('p10_trade_lifecycle.json') or {}).get('execution_boundary')
            or {}
        )
        if exec_data:
            spot = exec_data.get('spot_only', False)
            fut = exec_data.get('futures_enabled', False)
            with_ = exec_data.get('withdrawals', True)
            armed = exec_data.get('bot_armed', False)
            live = exec_data.get('live_execution', False)
            status = exec_data.get('status', '--')
            self.ids.ex_spot.text = f"Spot Only: {'ON' if spot else 'OFF'}"
            self.ids.ex_spot.color = COLORS['green'] if spot else COLORS['red']
            self.ids.ex_fut.text = f"Futures: {'ON' if fut else 'OFF'}"
            self.ids.ex_fut.color = COLORS['red'] if fut else COLORS['text_dim']
            self.ids.ex_with.text = f"Withdrawals: {'LOCKED' if not with_ else 'OPEN'}"
            self.ids.ex_with.color = COLORS['green'] if not with_ else COLORS['red']
            self.ids.ex_armed.text = f"Bot Armed: {'YES' if armed else 'NO'}"
            self.ids.ex_armed.color = COLORS['accent'] if armed else COLORS['text_dim']
            self.ids.ex_exec.text = f"Live Execution: {'ON' if live else 'OFF'}"
            self.ids.ex_exec.color = COLORS['accent'] if live else COLORS['text_dim']
            self.ids.ex_status.text = f"Status: {status}"

        # ---- Status line ----
        p12 = self._read_json('p12_live_execution.json') or {}
        p12s = p12.get('status', '--')
        orders = p12.get('orders_placed', 0)
        self.ids.status_line.text = (
            f"Status: {'RUNNING' if self.running else 'Idle'}    "
            f"Orders: {orders}    P12: {p12s}"
        )

    def _refresh_scanner(self):
        grid = self.ids.scanner_grid
        grid.clear_widgets()
        for h in ('Symbol', 'Price', 'Change', 'Signal'):
            grid.add_widget(Label(
                text=f'[b]{h}[/b]', markup=True, font_size='11sp',
                color=COLORS['text_dim'], halign='left', valign='middle',
            ))
        scan = self._read_json('binance_universe_scan.json') or {}
        rows = scan.get('symbols') or scan.get('universe') or []
        if not rows:
            p6 = self._read_json('p6_trade_quality.json') or {}
            for t in (p6.get('trades') or [])[:8]:
                rows.append({
                    'symbol': t.get('symbol', '--'),
                    'price': (t.get('entry') or {}).get('reference_price', '--'),
                    'change': '--',
                    'signal': t.get('direction', 'NEUTRAL'),
                })
        if not rows:
            for s in ('BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'FILUSDT'):
                rows.append({'symbol': s, 'price': '--',
                             'change': '--', 'signal': 'NEUTRAL'})
        for row in rows[:8]:
            sym = row.get('symbol', '--') if isinstance(row, dict) else str(row)
            price = row.get('price', '--') if isinstance(row, dict) else '--'
            chg = row.get('change', '--') if isinstance(row, dict) else '--'
            sig = row.get('signal', 'NEUTRAL') if isinstance(row, dict) else 'NEUTRAL'
            grid.add_widget(Label(text=str(sym), font_size='12sp',
                                  color=COLORS['text'], halign='left',
                                  valign='middle'))
            grid.add_widget(Label(text=str(price), font_size='12sp',
                                  color=COLORS['text_dim'], halign='left',
                                  valign='middle'))
            grid.add_widget(Label(text=str(chg), font_size='12sp',
                                  color=COLORS['text_dim'], halign='left',
                                  valign='middle'))
            sig_color = (
                COLORS['green'] if str(sig).upper() == 'LONG'
                else COLORS['red'] if str(sig).upper() == 'SHORT'
                else COLORS['text_dim']
            )
            grid.add_widget(Label(text=str(sig), font_size='12sp', bold=True,
                                  color=sig_color, halign='left',
                                  valign='middle'))

    def start_pipeline(self):
        if self.running:
            return
        self.running = True
        self.ids.live_pill.text = 'RUNNING'
        self.ids.live_pill.color = COLORS['accent']
        self._stop_event = threading.Event()
        self._runner_thread = threading.Thread(
            target=self._run_pipeline, daemon=True)
        self._runner_thread.start()

    def stop_pipeline(self):
        self.running = False
        self.ids.live_pill.text = 'IDLE'
        self.ids.live_pill.color = COLORS['text_dim']
        if self._stop_event:
            self._stop_event.set()

    def _log_ui(self, msg):
        def _do(dt):
            self.ids.status_line.text = f"Status: {msg}"
        Clock.schedule_once(_do, 0)

    def _run_pipeline(self):
        try:
            master_path = Path(self.app.master_path)
            if not master_path.exists():
                self._log_ui(f"Master not found: {master_path}")
                return
            spec = importlib.util.spec_from_file_location(
                "cryptomasterx1_master", str(master_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.REPORTS = self.reports_dir
            mod.P1()
            mod.P2(None)
            mod.P3(None)
            mod.P4(None)
            mod.P5(None)
            mod.P6(None)
            p7 = mod.P7(None)
            p8 = mod.P8(p7)
            p9 = mod.P9(p8)
            p10 = mod.P10(p9)
            p11 = mod.P11(p10)
            p12 = mod.P12(p11)
            self._log_ui(
                f"Cycle done. P7={p7['summary']['validated']} "
                f"P12={p12['status']}"
            )
        except Exception as e:
            self._log_ui(f"Pipeline error: {e}")
        finally:
            def _done(dt):
                self.running = False
                self.ids.live_pill.text = 'IDLE'
                self.ids.live_pill.color = COLORS['text_dim']
            Clock.schedule_once(_done, 0)


class CryptoMasterX1App(App):
    reports_dir = StringProperty('')
    master_path = StringProperty('')

    def build(self):
        self.title = 'CryptoMasterX1'
        base = Path(self.user_data_dir)
        self.reports_dir = str(base / 'reports')
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
        self.master_path = str(
            Path(__file__).resolve().parent
            / 'core' / 'live_combined'
            / 'CryptoMasterX1_LIVE_MASTER_P1_P12.py'
        )
        return CryptoMasterX1Dashboard()


if __name__ == '__main__':
    CryptoMasterX1App().run()
