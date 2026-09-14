name: CryptoMasterX1 - Build APK
on:
  push:
    branches: [main]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: "17" }
      - uses: android-actions/setup-android@v3
      - name: Fix SDK 37.0.0 license bug
        shell: bash
        run: |
          set -eux
          SDK="$HOME/.buildozer/android/platform/android-sdk"
          mkdir -p "$SDK/cmdline-tools"
          cp -r $ANDROID_HOME/cmdline-tools $SDK/ || true
          yes | sdkmanager --licenses || true
          yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --sdk_root="$SDK" --licenses || true
          sdkmanager "build-tools;37.0.0" "build-tools;35.0.0" "platform-tools" "platforms;android-33"
          $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --sdk_root="$SDK" "build-tools;37.0.0" "build-tools;35.0.0" "platform-tools" "platforms;android-33"
          ls $SDK/build-tools/
          test -x $SDK/build-tools/37.0.0/aidl
          ls $ANDROID_HOME/build-tools/
      - name: Create Binance.env
        shell: bash
        env:
          BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
          BINANCE_API_SECRET: ${{ secrets.BINANCE_API_SECRET }}
        run: |
          cat >.env <<EOF
          BINANCE_SPOT=true
          BINANCE_TESTNET=true
          PAPER_MODE=false
          ALLOW_LIVE=true
          EXECUTION_AUTHORIZED=true
          ORDER_SUBMISSION=true
          LIVE_EXECUTION=true
          BOT_ARMED=yes
          WITHDRAWALS=False
          MAX_POSITION_USDT=10
          BINANCE_API_KEY=$BINANCE_API_KEY
          BINANCE_API_SECRET=$BINANCE_API_SECRET
          EOF
          cat.env | grep -v KEY
      - name: Install Buildozer
        run: |
          pip install -U pip
          pip install buildozer cython==0.29.36
          pip install https://github.com/kivy/python-for-android/archive/master.zip -U
      - name: Build APK
        run: buildozer android debug
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: CryptoMasterX1-APK
          path: bin/*.apk
