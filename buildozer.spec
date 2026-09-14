[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cryptomasterx1
source.dir =.
source.include_exts = py,png,jpg,kv,json,txt,env
version = 1.1
requirements = python3,kivy==2.3.1,requests,python-binance,websocket-client,python-dotenv
orientation = portrait
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 37.0.0
android.accept_sdk_license_agreement = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
