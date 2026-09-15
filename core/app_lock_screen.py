from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from .app_lock import (
    password_exists,
    create_password,
    verify_password,
)


class AppLockScreen(Screen):

    def __init__(self, on_authenticated=None, **kwargs):
        super().__init__(**kwargs)

        self.on_authenticated = on_authenticated
        self.failed_attempts = 0

        layout = BoxLayout(
            orientation="vertical",
            padding=40,
            spacing=20,
        )

        layout.add_widget(
            Label(
                text="CryptoMasterX1",
                font_size="28sp",
                size_hint_y=None,
                height=60,
            )
        )

        layout.add_widget(
            Label(
                text="APP LOCK",
                font_size="20sp",
                size_hint_y=None,
                height=45,
            )
        )

        self.status = Label(
            text="Enter password",
            size_hint_y=None,
            height=50,
        )

        self.password_input = TextInput(
            password=True,
            multiline=False,
            hint_text="Password",
            size_hint_y=None,
            height=55,
        )

        self.button = Button(
            text="UNLOCK",
            size_hint_y=None,
            height=60,
        )

        self.button.bind(
            on_release=self.authenticate
        )

        layout.add_widget(self.status)
        layout.add_widget(self.password_input)
        layout.add_widget(self.button)

        self.add_widget(layout)

    def authenticate(self, *_args):

        password = self.password_input.text

        if not password:
            self.status.text = "Enter password."
            return

        if not password_exists():

            if len(password) < 8:
                self.status.text = (
                    "Password must be at least 8 characters."
                )
                return

            try:
                create_password(password)
                self.password_input.text = ""
                self.status.text = "Password created."
                self._authenticated()

            except Exception as exc:
                self.status.text = str(exc)

            return

        if verify_password(password):

            self.failed_attempts = 0
            self.password_input.text = ""
            self.status.text = "Unlocked."
            self._authenticated()

        else:

            self.failed_attempts += 1
            self.password_input.text = ""

            self.status.text = (
                f"Invalid password. Attempt {self.failed_attempts}"
            )

    def _authenticated(self):

        if callable(self.on_authenticated):
            self.on_authenticated()
