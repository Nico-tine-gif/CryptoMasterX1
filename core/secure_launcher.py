from kivy.uix.screenmanager import ScreenManager

from .app_lock_screen import AppLockScreen


class SecureApplication:

    def __init__(self, application_class):
        self.application_class = application_class

    def start(self):

        application_class = self.application_class
        original_build = application_class.build

        def secure_build(app):

            manager = ScreenManager()

            def authenticated():

                manager.clear_widgets()

                main_screen = original_build(app)

                if main_screen is not None:
                    manager.add_widget(main_screen)

            lock_screen = AppLockScreen(
                name="app_lock",
                on_authenticated=authenticated,
            )

            manager.add_widget(lock_screen)

            return manager

        application_class.build = secure_build

        application = application_class()
        application.run()
