#!/usr/bin/env python3
"""
CryptoMasterX1 — Kivy Trading Terminal Dashboard
Dark professional UI. Reads reports/*.json live.
"""
import json
import threading
import importlib.util
from pathlib import Path
from datetime import datetime, timezone

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

# ---------- Palette ----------
C_BG      = (0.027, 0.035, 0.055, 1)
C_CARD    = (0.055, 0.075, 0.105, 1)
C_CARD_2  = (0.075, 0.100, 0.140, 1)
C_BORDER  = (0.130, 0.170, 0.230, 1)
C_TEXT    = (0.910, 0.940, 0.970, 1)
C_DIM     = (0.520, 0.590, 0.680, 1)
C_ACCENT  = (0.130, 0.850, 0.750, 1)
C_GREEN   = (0.200, 0.900, 0.550, 1)
C_RED     = (0.960, 0.350, 0.440, 1)
C_YELLOW  = (0.980, 0.780, 0.250, 1)
C_BLUE    = (0.350, 0.650, 0.980, 1)
C_MUTED   = (0.150, 0.190, 0.250, 1)
C_GOLD    = (0.950, 0.740, 0.300, 1)

Window.clearcolor = C_BG


KV = r'''
<Card@BoxLayout>:
    canvas.before:
        Color:
            rgba: (0.055, 0.075, 0.105, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [14]
        Color:
            rgba: (0.130, 0.170, 0.230, 1)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 14)
            width: 1
    padding: [16, 14]
    spacing: 6

<SectionLabel@Label>:
    font_size: '11sp'
    color: (0.520, 0.590, 0.680, 1)
    bold: True
    halign: 'left'
    valign: 'middle'
    text_size: self.size
    size_hint_y: None
    height: '18dp'

<PhaseCard>:
    orientation: 'vertical'
    size_hint_x: None
    width: '66dp'
    padding: [4, 6]
    canvas.before:
        Color:
            rgba: self.card_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: self.card_border
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 1
    Label:
        text: root.pid
        font_size: '14sp'
        bold: True
        color: (0.910, 0.940, 0.970, 1)
        halign: 'center'
        valign: 'middle'
        text_size: self.size
    Label:
        text: root.plabel
        font_size: '9sp'
        color: (0.520, 0.590, 0.680, 1)
        halign: 'center'
        valign: 'middle'
        text_size: self.size
    Label:
        id: dot
        text: root.pstatus
        font_size: '8sp'
        bold: True
        color: root.status_color
        halign: 'center'
        valign: 'middle'
        text_size: self.size

<MetricRow@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '22dp'
    Label:
        text: root.lbl if hasattr(root, 'lbl') else ''
        font_size: '12sp'
        color: (0.520, 0.590, 0.680, 1)
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        size_hint_x: 0.55
    Label:
        text: root.val if hasattr(root, 'val') else ''
        font_size: '12sp'
        bold: True
        color: root.vcolor if hasattr(root, 'vcolor') else (0.910, 0.940, 0.970, 1)
        halign: 'right'
        valign: 'middle'
        text_size: self.size
        size_hint_x: 0.45

<CryptoMasterX1Dashboard>:
    orientation: 'vertical'

    # ======================= HEADER =======================
    BoxLayout:
        size_hint_y: None
        height: '72dp'
        padding: [18, 10, 18, 8]
        spacing: 12
        canvas.before:
            Color:
                rgba: (0.075, 0.100, 0.140, 1)
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: (0.130, 0.850, 0.750, 1)
            Rectangle:
                pos: self.x, self.y
                size: self.width, 2
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: '210dp'
            Label:
                text: '[b]CryptoMasterX1[/b]'
                markup: True
                font_size: '22sp'
                color: (0.910, 0.940, 0.970, 1)
                halign: 'left'
                valign: 'bottom'
                text_size: self.size
            Label:
                text: 'AUTONOMOUS SPOT TERMINAL'
                font_size: '9sp'
                color: (0.130, 0.850, 0.750, 1)
                halign: 'left'
                valign: 'top'
                text_size: self.size
        Widget:
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: '110dp'
            Label:
                id: pill_status
                text: 'IDLE'
                font_size: '14sp'
                bold: True
                color: (0.520, 0.590, 0.680, 1)
                halign: 'right'
                valign: 'middle'
                text_size: self.size
            Label:
                id: pill_time
                text: '--:--:--'
                font_size: '10sp'
                color: (0.520, 0.590, 0.680, 1)
                halign: 'right'
                valign: 'middle'
                text_size: self.size

    # ======================= BODY =======================
    ScrollView:
        do_scroll_x: False
        bar_width: dp(4)
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: [14, 14]
            spacing: 14

            # ---------- PIPELINE ----------
            Card:
                size_hint_y: None
                height: '176dp'
                orientation: 'vertical'
                SectionLabel:
                    text: 'PIPELINE  |  P1 -> P12'
                BoxLayout:
                    id: pipeline_row
                    orientation: 'horizontal'
                    spacing: 6
                    size_hint_y: None
                    height: '108dp'

            # ---------- SIGNAL + EXECUTION ----------
            BoxLayout:
                size_hint_y: None
                height: '240dp'
                spacing: 14

                Card:
                    orientation: 'vertical'
                    SectionLabel:
                        text: 'ACTIVE SIGNAL'
                    BoxLayout:
                        orientation: 'horizontal'
                        spacing: 16
                        BoxLayout:
                            orientation: 'vertical'
                            size_hint_x: 0.55
                            Label:
                                id: sig_symbol
                                text: '--'
                                font_size: '30sp'
                                bold: True
                                color: (0.910, 0.940, 0.970, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '42dp'
                            Label:
                                id: sig_direction
                                text: 'NO SIGNAL'
                                font_size: '16sp'
                                bold: True
                                color: (0.520, 0.590, 0.680, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '26dp'
                            Label:
                                id: sig_conf
                                text: 'confidence  --'
                                font_size: '12sp'
                                color: (0.520, 0.590, 0.680, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            Widget:
                        BoxLayout:
                            orientation: 'vertical'
                            size_hint_x: 0.45
                            spacing: 0
                            Label:
                                id: m_price
                                text: 'PRICE     --'
                                font_size: '12sp'
                                color: (0.910, 0.940, 0.970, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '24dp'
                            Label:
                                id: m_atr
                                text: 'ATR       --'
                                font_size: '12sp'
                                color: (0.520, 0.590, 0.680, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '24dp'
                            Label:
                                id: m_sl
                                text: 'SL        --'
                                font_size: '12sp'
                                color: (0.960, 0.350, 0.440, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '24dp'
                            Label:
                                id: m_tp1
                                text: 'TP1       --'
                                font_size: '12sp'
                                color: (0.200, 0.900, 0.550, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '24dp'
                            Label:
                                id: m_tp2
                                text: 'TP2       --'
                                font_size: '12sp'
                                color: (0.200, 0.900, 0.550, 1)
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                size_hint_y: None
                                height: '24dp'

                Card:
                    orientation: 'vertical'
                    SectionLabel:
                        text: 'EXECUTION BOUNDARY'
                    Label:
                        id: ex_spot
                        text: 'Spot Only        --'
                        font_size: '12sp'
                        color: (0.910, 0.940, 0.970, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'
                    Label:
                        id: ex_fut
                        text: 'Futures          --'
                        font_size: '12sp'
                        color: (0.520, 0.590, 0.680, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'
                    Label:
                        id: ex_with
                        text: 'Withdrawals      --'
                        font_size: '12sp'
                        color: (0.910, 0.940, 0.970, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'
                    Label:
                        id: ex_armed
                        text: 'Bot Armed        --'
                        font_size: '12sp'
                        color: (0.130, 0.850, 0.750, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'
                    Label:
                        id: ex_exec
                        text: 'Live Execution   --'
                        font_size: '12sp'
                        color: (0.130, 0.850, 0.750, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'
                    Label:
                        id: ex_status
                        text: 'Status           --'
                        font_size: '12sp'
                        color: (0.520, 0.590, 0.680, 1)
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        size_hint_y: None
                        height: '22dp'

            # ---------- MARKET SCANNER ----------
            Card:
                size_hint_y: None
                height: '248dp'
                orientation: 'vertical'
                SectionLabel:
                    text: 'MARKET SCANNER  |  BINANCE SPOT'
                GridLayout:
                    id: scanner_grid
                    cols: 5
                    spacing: 2
                    row_default_height: '26dp'
                    row_force_default: True
                    size_hint_y: None
                    height: self.minimum_height

            # ---------- STATUS ----------
            Card:
                size_hint_y: None
                height: '66dp'
                Label:
                    id: status_line
                    text: 'Status: Idle'
                    font_size: '12sp'
                    color: (0.910, 0.940, 0.970, 1)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

    # ======================= FOOTER =======================
    BoxLayout:
        size_hint_y: None
        height: '76dp'
        padding: [14, 12]
        spacing: 12
        canvas.before:
            Color:
                rgba: (0.075, 0.100, 0.140, 1)
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: (0.130, 0.170, 0.230, 1)
            Rectangle:
                pos: self.x, self.top - 1
                size: self.width, 1
        Button:
            text: 'START'
            font_size: '15sp'
            bold: True
            background_normal: ''
            background_color: (0.200, 0.900, 0.550, 1)
            color: (0.027, 0.035, 0.055, 1)
            on_release: root.start_pipeline()
        Button:
            text: 'STOP'
            font_size: '15sp'
            bold: True
            background_normal: ''
            background_color: (0.960, 0.350, 0.440, 1)
            color: (1, 1, 1, 1)
            on_release: root.stop_pipeline()
'''

Builder.load_string(KV)


PHASES = [
    ('P1',  'SCAN'),
    ('P2',  'AUTH'),
    ('P3',  'ACCT'),
    ('P4',  'UNIV'),
    ('P5',  'MKT'),
    ('P6',  'TRADES'),
    ('P7',  'ENTRY'),
    ('P8',  'LIFE'),
    ('P9',  'GATE'),
    ('P10', 'MON'),
    ('P11', 'VERIFY'),
    ('P12', 'EXEC'),
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


class PhaseCard(BoxLayout):
    pid = StringProperty('')
    plabel = StringProperty('')
    pstatus = StringProperty('IDLE')
    card_bg = ListProperty(list(C_CARD_2))
    card_border = ListProperty(list(C_BORDER))
    status_color = ListProperty(list(C_DIM))


class CryptoMasterX1Dashboard(BoxLayout):
    running = BooleanProperty(False)
    _cards = {}
    _thread = None
    _stop = None
    _pulse = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.reports_dir = Path(self.app.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        Clock.schedule_once(self._build_pipeline, 0)
        Clock.schedule_interval(self._refresh, 1.5)
        Clock.schedule_interval(self._tick_time, 1.0)

    def _build_pipeline(self, dt):
        row = self.ids.pipeline_row
        row.clear_widgets()
        self._cards = {}
        for pid, label in PHASES:
            c = PhaseCard(pid=pid, plabel=label)
            self._cards[pid] = c
            row.add_widget(c)

    def _tick_time(self, dt):
        self.ids.pill_time.text = datetime.now().strftime('%H:%M:%S')

    def _read_json(self, name):
        p = self.reports_dir / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def _refresh(self, dt):
        self._refresh_pipeline()
        self._refresh_signal()
        self._refresh_scanner()
        self._refresh_boundary()
        self._refresh_status()

    def _refresh_pipeline(self):
        for pid, fname in REPORT_MAP.items():
            card = self._cards.get(pid)
            if not card:
                continue
            data = self._read_json(fname)
            if data is None:
                card.card_bg = list(C_CARD_2)
                card.card_border = list(C_BORDER)
                card.pstatus = 'IDLE'
                card.status_color = list(C_DIM)
                continue
            status = str(data.get('status', 'OK')).upper()
            if 'FAIL' in status or 'REJECT' in status:
                card.card_bg = list(C_RED)
                card.card_border = list(C_RED)
                card.status_color = list(C_TEXT)
                card.pstatus = 'FAIL'
            elif 'FLAT' in status:
                card.card_bg = list(C_YELLOW)
                card.card_border = list(C_YELLOW)
                card.status_color = (0.027, 0.035, 0.055, 1)
                card.pstatus = 'FLAT'
            elif status in ('RUNNING', 'IN_PROGRESS'):
                card.card_bg = list(C_BLUE)
                card.card_border = list(C_BLUE)
                card.status_color = list(C_TEXT)
                card.pstatus = 'RUN'
            else:
                card.card_bg = list(C_GREEN)
                card.card_border = list(C_GREEN)
                card.status_color = (0.027, 0.035, 0.055, 1)
                card.pstatus = 'OK'

    def _refresh_signal(self):
        p6 = self._read_json('p6_trade_quality.json') or {}
        trades = p6.get('trades') or []
        if not trades:
            self.ids.sig_symbol.text = '--'
            self.ids.sig_direction.text = 'NO SIGNAL'
            self.ids.sig_direction.color = C_DIM
            self.ids.sig_conf.text = 'confidence  --'
            for k in ('m_price', 'm_atr', 'm_sl', 'm_tp1', 'm_tp2'):
                self.ids[k].text = self.ids[k].text.split('  ')[0] + '  --'
            return
        t = trades[0]
        self.ids.sig_symbol.text = str(t.get('symbol', '--'))
        d = str(t.get('direction', '--')).upper()
        self.ids.sig_direction.text = d
        self.ids.sig_direction.color = (
            C_GREEN if d == 'LONG' else C_RED if d == 'SHORT' else C_DIM
        )
        conf = t.get('confidence')
        self.ids.sig_conf.text = (
            f"confidence  {conf}%" if conf is not None else "confidence  --"
        )
        e = t.get('entry') or {}
        r = t.get('risk') or {}
        tg = t.get('targets') or {}
        self.ids.m_price.text = f"PRICE     {e.get('reference_price', '--')}"
        self.ids.m_atr.text = f"ATR       {e.get('atr_15m', '--')}"
        self.ids.m_sl.text = f"SL        {r.get('stop_loss', '--')}"
        self.ids.m_tp1.text = f"TP1       {tg.get('tp1', '--')}"
        self.ids.m_tp2.text = f"TP2       {tg.get('tp2', '--')}"

    def _refresh_scanner(self):
        grid = self.ids.scanner_grid
        grid.clear_widgets()
        headers = ('SYMBOL', 'PRICE', '24H%', 'SIGNAL', 'CONF')
        for h in headers:
            grid.add_widget(self._scanner_cell(h, C_DIM, bold=True))
        rows = []
        scan = self._read_json('binance_universe_scan.json') or {}
        rows = scan.get('symbols') or scan.get('universe') or []
        if not rows:
            p6 = self._read_json('p6_trade_quality.json') or {}
            for t in (p6.get('trades') or [])[:7]:
                rows.append({
                    'symbol': t.get('symbol', '--'),
                    'price': (t.get('entry') or {}).get('reference_price', '--'),
                    'change': '--',
                    'signal': t.get('direction', 'NEUTRAL'),
                    'conf': t.get('confidence', '--'),
                })
        if not rows:
            for s in ('BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT',
                      'FILUSDT', 'XRPUSDT', 'ADAUSDT'):
                rows.append({'symbol': s, 'price': '--', 'change': '--',
                             'signal': 'NEUTRAL', 'conf': '--'})
        for row in rows[:7]:
            sym = str(row.get('symbol', '--'))
            price = str(row.get('price', '--'))
            chg = str(row.get('change', '--'))
            sig = str(row.get('signal', 'NEUTRAL')).upper()
            conf = str(row.get('conf', '--'))
            sig_color = (
                C_GREEN if sig == 'LONG' else C_RED if sig == 'SHORT' else C_DIM
            )
            grid.add_widget(self._scanner_cell(sym, C_TEXT, bold=True))
            grid.add_widget(self._scanner_cell(price, C_TEXT))
            grid.add_widget(self._scanner_cell(chg, C_DIM))
            grid.add_widget(self._scanner_cell(sig, sig_color, bold=True))
            grid.add_widget(self._scanner_cell(conf, C_DIM))

    def _scanner_cell(self, text, color, bold=False):
        from kivy.uix.label import Label
        return Label(
            text=text, font_size='11sp', bold=bold, color=color,
            halign='left', valign='middle',
        )

    def _refresh_boundary(self):
        ex = (
            (self._read_json('p12_live_execution.json') or {}).get('execution')
            or (self._read_json('p11_full_system_verification.json') or {}).get('execution_boundary')
            or (self._read_json('p10_trade_lifecycle.json') or {}).get('execution_boundary')
            or {}
        )
        if not ex:
            return
        spot  = ex.get('spot_only', False)
        fut   = ex.get('futures_enabled', False)
        wd    = ex.get('withdrawals', True)
        armed = ex.get('bot_armed', False)
        live  = ex.get('live_execution', False)
        stat  = ex.get('status', '--')
        self.ids.ex_spot.text = f"Spot Only        {'ON' if spot else 'OFF'}"
        self.ids.ex_spot.color = C_GREEN if spot else C_RED
        self.ids.ex_fut.text = f"Futures          {'ON' if fut else 'OFF'}"
        self.ids.ex_fut.color = C_RED if fut else C_DIM
        self.ids.ex_with.text = f"Withdrawals      {'LOCKED' if not wd else 'OPEN'}"
        self.ids.ex_with.color = C_GREEN if not wd else C_RED
        self.ids.ex_armed.text = f"Bot Armed        {'YES' if armed else 'NO'}"
        self.ids.ex_armed.color = C_ACCENT if armed else C_DIM
        self.ids.ex_exec.text = f"Live Execution   {'ON' if live else 'OFF'}"
        self.ids.ex_exec.color = C_ACCENT if live else C_DIM
        self.ids.ex_status.text = f"Status           {stat}"

    def _refresh_status(self):
        p12 = self._read_json('p12_live_execution.json') or {}
        p12s = p12.get('status', '--')
        orders = p12.get('orders_placed', 0)
        self.ids.status_line.text = (
            f"State: {'RUNNING' if self.running else 'IDLE'}     "
            f"Orders: {orders}     P12: {p12s}"
        )

    # ---------- Controls ----------
    def start_pipeline(self):
        if self.running:
            return
        self.running = True
        self.ids.pill_status.text = 'RUNNING'
        self.ids.pill_status.color = C_ACCENT
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop_pipeline(self):
        self.running = False
        self.ids.pill_status.text = 'IDLE'
        self.ids.pill_status.color = C_DIM
        if self._stop:
            self._stop.set()

    def _log(self, msg):
        Clock.schedule_once(lambda dt: setattr(
            self.ids.status_line, 'text', f"Status: {msg}"), 0)

    def _run(self):
        try:
            mp = Path(self.app.master_path)
            if not mp.exists():
                self._log(f"master missing: {mp}")
                return
            spec = importlib.util.spec_from_file_location("cmx1_master", str(mp))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.REPORTS = self.reports_dir
            p1 = mod.P1()
            p2 = mod.P2(p1)
            p3 = mod.P3(p2)
            p4 = mod.P4(p3)
            p5 = mod.P5(p4)
            p6 = mod.P6(p5)
            p7 = mod.P7(p6)
            p8 = mod.P8(p7)
            p9 = mod.P9(p8)
            p10 = mod.P10(p9)
            p11 = mod.P11(p10)
            p12 = mod.P12(p11)
            self._log(
                f"done — P7 validated={p7['summary']['validated']} "
                f"P12={p12['status']}"
            )
        except Exception as e:
            self._log(f"error: {e}")
        finally:
            def _done(dt):
                self.running = False
                self.ids.pill_status.text = 'IDLE'
                self.ids.pill_status.color = C_DIM
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
