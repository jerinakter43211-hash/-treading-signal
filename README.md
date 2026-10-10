# Trading Signal Android

Kivy prototype that fetches public Binance Spot candles and presents heuristic EMA crossover / RSI context. It does not guarantee profits and is not financial advice.

## Build APK
Open **Actions** → **Build Android APK**. Run workflow if needed. After a successful run, open the run and download the `trading-signal-debug-apk` artifact. Extract it and install the APK on Android.

## Limitations
- APK is not precompiled in this repository; GitHub Actions must succeed first.
- Public Binance API access and internet are required.
- No trading account login or order placement is implemented.
- Signals can be wrong; test with historical data and paper trading before risking money.
