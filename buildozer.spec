[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cryptomasterx1
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.1
requirements = python3,kivy==2.3.1
orientation = portrait
[buildozer]
log_level = 2
[app:android]
android.permissions = INTERNET
android.api = 35
android.minapi = 21
android.ndk = 28c
android.accept_sdk_license_agreement = True
android.archs = arm64-v8a
p4a.bootstrap = sdl2
