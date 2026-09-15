[app]
title = CryptoMasterX1
package.name = cryptomasterx1
package.domain = org.cryptomaster
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Critical core compilation requirements including your async networking modules
requirements = python3,ccxt,motor,aiohttp,asyncio,setuptools

orientation = portrait
fullscreen = 1

# Android specific configurations and permissions mapping
android.permissions = INTERNET, NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.private_storage = True

# Native operational lifecycle and background persistence properties
android.wakelock = True
android.entrypoint = main.py

[buildozer]
log_level = 2
warn_on_root = 1
