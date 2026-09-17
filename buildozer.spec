[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cryptomasterx1.bot

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = core/**,modules/**,state/**,reports/**

version = 1.1

requirements = python3,kivy

orientation = portrait
fullscreen = 0

p4a.bootstrap = sdl2
p4a.port = android
p4a.whitelist = libffi,openssl,sqlite3

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True
android.build_tools_version = 33.0.2

[buildozer]
log_level = 2
warn_on_root = 1

