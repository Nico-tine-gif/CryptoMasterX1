[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cryptomasterx1.bot
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = core/*,modules/*,state/*
version = 1.1
requirements = python3,kivy,requests,python-binance
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license_agreement = True
android.archs = arm64-v8a
android.allow_backup = False
p4a.bootstrap = sdl2
