[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cryptomasterx1.bot
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = core/*,modules/*,state/*
version = 1.1
requirements = python3,kivy==2.3.0,requests,urllib3,charset-normalizer,idna,certifi,python-binance
orientation = portrait
fullscreen = 0
p4a.bootstrap = sdl2
p4a.port = android

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license_agreement = True
android.allow_backup = False
android.archs = arm64-v8a
# FIX FOR AIDL BUG
android.build_tools_version = 33.0.2
p4a.whitelist = libffi,openssl,sqlite3
