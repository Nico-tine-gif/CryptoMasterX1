import threading
import traceback
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout


# ============================================================
# CRYPTOMASTERX1 — EXISTING SECURITY LOCK
# ============================================================

try:
    from core.secure_launcher import check_password_lock
    HAS_LOCK = True
except Exception as exc:
    HAS_LOCK = False
    LOCK_IMPORT_ERROR = str(exc)

    def check_password_lock():
        # FAIL CLOSED.
        # Never allow the UI to start the pipeline when the
        # existing security lock cannot be loaded.
        return False


KV = r"""
#:import dp kivy.metrics.dp

<Dashboard>:

    orientation: "vertical"
    padding: dp(12)
    spacing: dp(8)

    canvas.before:
        Color:
            rgba: 0.035, 0.045, 0.06, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "[b]CryptoMasterX1[/b]"
        markup: True
        font_size: dp(26)
        size_hint_y: None
        height: dp(42)

    Label:
        text: "11-Phase Master Trading System"
        font_size: dp(14)
        size_hint_y: None
        height: dp(25)

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)

        Label:
            text: "SECURITY LOCK"
            font_size: dp(13)

        Label:
            text: root.lock_status
            markup: True
            font_size: dp(15)

    BoxLayout:
        size_hint_y: None
        height: dp(45)
        spacing: dp(8)

        Label:
            text: "SYSTEM"
            font_size: dp(13)

        Label:
            text: root.system_status
            font_size: dp(14)

    BoxLayout:
        size_hint_y: None
        height: dp(45)
        spacing: dp(8)

        Label:
            text: "PIPELINE"
            font_size: dp(13)

        Label:
            text: root.pipeline_status
            font_size: dp(14)

    BoxLayout:
        size_hint_y: None
        height: dp(52)
        spacing: dp(8)

        Button:
            text: "START"
            font_size: dp(16)
            disabled: root.start_disabled
            on_release: root.start_pipeline()

        Button:
            text: "STOP"
            font_size: dp(16)
            on_release: root.stop_pipeline()

    Label:
        text: "MASTER PIPELINE LOG"
        size_hint_y: None
        height: dp(28)
        halign: "left"
        text_size: self.size

    TextInput:
        text: root.log_text
        readonly: True
        multiline: True
        font_size: dp(12)
        background_color: 0.02, 0.025, 0.035, 1
        foreground_color: 0.9, 0.9, 0.9, 1

    Label:
        text: "Security controlled by core.secure_launcher"
        size_hint_y: None
        height: dp(25)
        font_size: dp(11)
"""


class Dashboard(BoxLayout):

    system_status = StringProperty("READY")
    pipeline_status = StringProperty("STOPPED")
    lock_status = StringProperty("[b]CHECKING...[/b]")
    log_text = StringProperty("")
    start_disabled = BooleanProperty(True)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.pipeline_module = None
        self.pipeline_instance = None
        self.pipeline_thread = None
        self.stop_requested = False
        self.lock_authenticated = False

        self.log("CryptoMasterX1 dashboard started.")
        self.log("Checking existing security lock.")

        self.check_security_lock()
        self.load_pipeline()

    # ========================================================
    # LOG
    # ========================================================

    def log(self, message):

        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"

        def update(_dt):

            lines = self.log_text.splitlines()
            lines.append(line)

            if len(lines) > 300:
                lines = lines[-300:]

            self.log_text = "\n".join(lines)

        Clock.schedule_once(update, 0)

    # ========================================================
    # STATUS
    # ========================================================

    def set_system_status(self, value):

        Clock.schedule_once(
            lambda _dt: setattr(
                self,
                "system_status",
                value,
            ),
            0,
        )

    def set_pipeline_status(self, value):

        Clock.schedule_once(
            lambda _dt: setattr(
                self,
                "pipeline_status",
                value,
            ),
            0,
        )

    def set_lock_status(self, value):

        Clock.schedule_once(
            lambda _dt: setattr(
                self,
                "lock_status",
                value,
            ),
            0,
        )

    # ========================================================
    # SECURITY LOCK
    # ========================================================

    def check_security_lock(self):

        if not HAS_LOCK:

            self.lock_authenticated = False
            self.start_disabled = True

            self.set_lock_status(
                "[b]LOCK ERROR[/b]"
            )

            self.set_system_status(
                "SECURITY ERROR"
            )

            self.log(
                "SECURITY LOCK IMPORT FAILED."
            )

            self.log(
                f"Reason: {LOCK_IMPORT_ERROR}"
            )

            self.log(
                "START BLOCKED — FAIL CLOSED."
            )

            return False

        try:

            result = check_password_lock()

            if result:

                self.lock_authenticated = True
                self.start_disabled = False

                self.set_lock_status(
                    "[b]UNLOCKED[/b]"
                )

                self.set_system_status(
                    "READY"
                )

                self.log(
                    "Security lock accepted."
                )

                self.log(
                    "START enabled."
                )

                return True

            self.lock_authenticated = False
            self.start_disabled = True

            self.set_lock_status(
                "[b]LOCKED[/b]"
            )

            self.set_system_status(
                "LOCKED"
            )

            self.log(
                "Security lock is active."
            )

            self.log(
                "START blocked."
            )

            return False

        except Exception as exc:

            self.lock_authenticated = False
            self.start_disabled = True

            self.set_lock_status(
                "[b]LOCK ERROR[/b]"
            )

            self.set_system_status(
                "SECURITY ERROR"
            )

            self.log(
                f"Security lock error: {exc}"
            )

            self.log(
                traceback.format_exc()
            )

            self.log(
                "START BLOCKED — FAIL CLOSED."
            )

            return False

    # ========================================================
    # PIPELINE LOADING
    # ========================================================

    def load_pipeline(self):

        try:

            from core import master_pipeline

            self.pipeline_module = master_pipeline

            self.log(
                "core.master_pipeline loaded."
            )

            return master_pipeline

        except Exception as exc:

            self.pipeline_module = None

            self.set_system_status(
                "PIPELINE ERROR"
            )

            self.log(
                f"Pipeline import failed: {exc}"
            )

            self.log(
                traceback.format_exc()
            )

            return None

    # ========================================================
    # START
    # ========================================================

    def start_pipeline(self):

        # ----------------------------------------------------
        # SECURITY CHECK — ALWAYS FIRST
        # ----------------------------------------------------

        if not self.check_security_lock():

            self.log(
                "START DENIED by security lock."
            )

            return

        if self.pipeline_thread:

            if self.pipeline_thread.is_alive():

                self.log(
                    "Pipeline is already running."
                )

                return

        self.stop_requested = False

        self.set_pipeline_status(
            "STARTING"
        )

        self.log(
            "Starting CryptoMasterX1 master pipeline."
        )

        self.pipeline_thread = threading.Thread(
            target=self.pipeline_worker,
            daemon=True,
        )

        self.pipeline_thread.start()

    # ========================================================
    # PIPELINE WORKER
    # ========================================================

    def pipeline_worker(self):

        try:

            if self.pipeline_module is None:

                if self.load_pipeline() is None:

                    self.set_pipeline_status(
                        "ERROR"
                    )

                    return

            pipeline = self.pipeline_module

            # ------------------------------------------------
            # module.run()
            # ------------------------------------------------

            if hasattr(
                pipeline,
                "run",
            ) and callable(
                pipeline.run
            ):

                self.set_pipeline_status(
                    "RUNNING"
                )

                self.log(
                    "Using master_pipeline.run()."
                )

                result = pipeline.run()

                self.log(
                    f"Pipeline result: {result!r}"
                )

            # ------------------------------------------------
            # module.main()
            # ------------------------------------------------

            elif hasattr(
                pipeline,
                "main",
            ) and callable(
                pipeline.main
            ):

                self.set_pipeline_status(
                    "RUNNING"
                )

                self.log(
                    "Using master_pipeline.main()."
                )

                result = pipeline.main()

                self.log(
                    f"Pipeline result: {result!r}"
                )

            # ------------------------------------------------
            # MasterPipeline class
            # ------------------------------------------------

            elif hasattr(
                pipeline,
                "MasterPipeline",
            ):

                self.set_pipeline_status(
                    "RUNNING"
                )

                self.log(
                    "MasterPipeline class detected."
                )

                self.pipeline_instance = (
                    pipeline.MasterPipeline()
                )

                if not hasattr(
                    self.pipeline_instance,
                    "run",
                ):

                    raise RuntimeError(
                        "MasterPipeline has no run() method."
                    )

                result = (
                    self.pipeline_instance.run()
                )

                self.log(
                    f"Pipeline result: {result!r}"
                )

            else:

                raise RuntimeError(
                    "No supported master pipeline "
                    "entry point found."
                )

            if self.stop_requested:

                self.set_pipeline_status(
                    "STOPPED"
                )

            else:

                self.set_pipeline_status(
                    "COMPLETED"
                )

        except Exception as exc:

            self.set_pipeline_status(
                "ERROR"
            )

            self.log(
                f"Pipeline exception: {exc}"
            )

            self.log(
                traceback.format_exc()
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop_pipeline(self):

        self.stop_requested = True

        self.log(
            "Stop requested."
        )

        try:

            target = self.pipeline_instance

            if target is not None:

                if hasattr(
                    target,
                    "stop",
                ) and callable(
                    target.stop
                ):

                    target.stop()

                    self.log(
                        "Pipeline stop() called."
                    )

                    self.set_pipeline_status(
                        "STOPPED"
                    )

                    return

                if hasattr(
                    target,
                    "request_stop",
                ) and callable(
                    target.request_stop
                ):

                    target.request_stop()

                    self.log(
                        "Pipeline request_stop() called."
                    )

                    self.set_pipeline_status(
                        "STOPPED"
                    )

                    return

            module = self.pipeline_module

            if module is not None:

                if hasattr(
                    module,
                    "stop",
                ) and callable(
                    module.stop
                ):

                    module.stop()

                    self.log(
                        "Module stop() called."
                    )

                    self.set_pipeline_status(
                        "STOPPED"
                    )

                    return

                if hasattr(
                    module,
                    "request_stop",
                ) and callable(
                    module.request_stop
                ):

                    module.request_stop()

                    self.log(
                        "Module request_stop() called."
                    )

                    self.set_pipeline_status(
                        "STOPPED"
                    )

                    return

            self.log(
                "No stop API exposed by pipeline."
            )

            self.set_pipeline_status(
                "STOP REQUESTED"
            )

        except Exception as exc:

            self.log(
                f"Stop error: {exc}"
            )

            self.log(
                traceback.format_exc()
            )

            self.set_pipeline_status(
                "STOP ERROR"
            )


class CryptoMasterX1App(App):

    title = "CryptoMasterX1"

    def build(self):

        Builder.load_string(KV)

        return Dashboard()


if __name__ == "__main__":

    CryptoMasterX1App().run()
