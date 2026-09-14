[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cryptomasterx1
source.dir =.
version = 1.1
requirements = python3,kivy==2.3.1
orientation = portrait
[buildozer]
log_level = 2
[app:android]
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license_agreement = True
android.archs = arm64-v8a
