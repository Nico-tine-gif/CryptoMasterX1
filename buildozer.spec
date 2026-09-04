[app]

title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cmx1

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,html,css

# Do not send build artifacts / Gradle artifacts into the APK source tree.
source.exclude_dirs = .git,.github,.buildozer,bin,build,app,.gradle,gradle,archive

version = 1.0.0

requirements = python3,kivy,requests,websocket-client,python-binance

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

android.api = 33
android.sdk = 33
android.minapi = 21
android.ndk = 25b
android.python_version = 3.9

android.accept_sdk_license = True
android.archs = arm64-v8a
android.use_androidx = True
android.allow_backup = True

[buildozer]

log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin
