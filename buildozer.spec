[app]

title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cmx1
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,html,css
version = 1.0.0
requirements = python3,kivy==2.1.0,requests,websocket-client,python-binance,pandas,numpy
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.use_androidx = True
android.allow_backup = True

[buildozer]
log_level = 2
build_dir = %(source.dir)s/.buildozer
bin_dir = %(source.dir)s/bin
