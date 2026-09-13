[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cryptomasterx1
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_patterns =.buildozer,bin,__pycache__,*.pyc,.git
version = 1.1
requirements = python3,kivy==2.3.1,pillow,requests,urllib3,certifi
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 35
android.minapi = 21
android.ndk = 25b
android.sdk = 35
android.accept_sdk_license_agreement = True
android.archs = arm64-v8a
p4a.bootstrap = sdl2
p4a.branch = master
