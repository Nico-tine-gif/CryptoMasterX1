[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cmx1
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,html,css
version = 1.0.0
requirements = python3,kivy,requests,websocket-client
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 23b
android.accept_sdk_license = True
android.arch = armeabi-v7a
android.use_androidx = True
android.allow_backup = True

[buildozer]
log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin
