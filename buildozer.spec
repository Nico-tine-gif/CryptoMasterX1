[app]

title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = com.cmx1

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

version = 2.0

requirements = python3,kivy==2.3.0,requests,python-dotenv

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE

android.api = 33
android.minapi = 24
android.ndk = 27c
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
