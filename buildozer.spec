[app]

# (str) Title of your application
title = CryptoMasterX1

# (str) Package name
package.name = cryptomasterx1

# (str) Package domain (needed for android/ios packaging)
package.domain = com.cmx1

# (str) Source code directory
source.dir = .

# (list) Source files to include (comma separated)
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

# (list) List of inclusions using pattern matching
source.include_patterns = main.py,CryptoMasterX1.py,*.py

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy,requests,websocket-client,python-binance,pandas,numpy

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

# (int) Android API level
android.api = 34

# (int) Minimum API level
android.minapi = 21

# (int) Android SDK version
android.sdk = 34

# (str) Android NDK version
android.ndk = 25c

# (bool) Enable AndroidX support
android.use_androidx = True

# (bool) Enable Google Play Services
# android.gms = True

# (str) Log level
log_level = 2

# (bool) Show warning about SDK/NDK versions
android.warn_on_old_sdk = False

# (str) Android application entry point
android.entrypoint = org.kivy.android.PythonActivity

# (list) Android extra Java classes
# android.add_java_class =

# (list) Android extra Java source directories
# android.add_src =

# (str) Android fullscreen
android.fullscreen = 0

# (str) Android window background color
android.window_background_color = #000000

# (str) Supported orientation
android.orientation = portrait

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (str) Path to build directory
build_dir = %(source.dir)s/.buildozer

# (str) Path to bin directory
bin_dir = %(source.dir)s/bin

# (str) Path to Android SDK directory
android_sdk_dir = %(build_dir)s/android/platform/android-sdk

# (str) Path to Android NDK directory
android_ndk_dir = %(build_dir)s/android/platform/android-ndk

# (str) Path to Ant directory
android_ant_dir = %(build_dir)s/android/platform/apache-ant

# (str) Path to Gradle directory
android_gradle_dir = %(build_dir)s/android/platform/gradle
