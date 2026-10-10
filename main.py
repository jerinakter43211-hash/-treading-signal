import json, threading, urllib.request
from datetime import datetime, timezone
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button

API = "https://api.binance.com/api/v3/klines"

def candles(symbol, interval):
    url = f"{API}?symbol={symbol}&interval={interval}&limit=100"
    req = urllib.request.Request(url, headers={"User-Agent": "TradingSignalDemo/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        rows = json.loads(r.read().decode())
    return [(float(x[4]), int(x[6])) for x in rows]

def ema(vals, period):
    if len(vals) < period: return []
    k = 2 / (period + 1)
    out = [sum(vals[:period]) / period]
    for x in vals[period:]: out.append(x*k + out[-1]*(1-k))
    return out

def rsi(vals, period=14):
    if len(vals) <= period: return None
    diffs = [vals[i]-vals[i-1] for i in range(1,len(vals))]
    gain = sum(max(x,0) for x in diffs[:period])/period
    loss = sum(max(-x,0) for x in diffs[:period])/period
    for x in diffs[period:]:
        gain = (gain*(period-1)+max(x,0))/period
        loss = (loss*(period-1)+max(-x,0))/period
    return 100.0 if loss == 0 else 100 - 100/(1+gain/loss)

def analyze(vals):
    f, s = ema(vals,12), ema(vals,26)
    if len(f)<2 or len(s)<2: return "WAIT", "Not enough candle history"
    # Align EMA series to their shared final candles.
    offset = len(f)-len(s)
    f = f[offset:] if offset > 0 else f
    s = s[-len(f):]
    r = rsi(vals)
    if len(f)<2 or r is None: return "WAIT", "Not enough indicator data"
    prev, curr = f[-2]-s[-2], f[-1]-s[-1]
    if prev <= 0 < curr and r < 70: return "BUY", f"EMA bullish crossover; RSI {r:.1f}"
    if prev >= 0 > curr and r > 30: return "SELL", f"EMA bearish crossover; RSI {r:.1f}"
    return "WAIT", f"No confirmed crossover; RSI {r:.1f}"

class TradingSignalApp(App):
    title = "Trading Signal"
    def build(self):
        self.symbol, self.interval = "BTCUSDT", "1h"
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        root.add_widget(Label(text="TRADING SIGNAL", font_size="24sp", size_hint_y=None, height=dp(44)))
        pair = Spinner(text=self.symbol, values=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"), size_hint_y=None, height=dp(48))
        pair.bind(text=lambda _,v: setattr(self,"symbol",v)); root.add_widget(pair)
        tf = Spinner(text=self.interval, values=("5m","15m","1h","4h","1d"), size_hint_y=None, height=dp(48))
        tf.bind(text=lambda _,v: setattr(self,"interval",v)); root.add_widget(tf)
        self.signal = Label(text="WAIT", font_size="40sp", bold=True); root.add_widget(self.signal)
        self.info = Label(text="Tap refresh to fetch public market data.", halign="center")
        self.info.bind(size=lambda w,s: setattr(w,"text_size",s)); root.add_widget(self.info)
        self.price = Label(text="Last close: —", size_hint_y=None, height=dp(30)); root.add_widget(self.price)
        btn = Button(text="Refresh market data", size_hint_y=None, height=dp(48))
        btn.bind(on_release=self.refresh); root.add_widget(btn)
        root.add_widget(Label(text="Educational only. Signals may be wrong; no profit is guaranteed.", font_size="12sp", size_hint_y=None, height=dp(40)))
        Clock.schedule_once(lambda dt:self.refresh(), 1)
        return root
    def refresh(self,*_):
        self.signal.text="LOADING..."; self.info.text="Fetching latest candles…"
        threading.Thread(target=self.load,daemon=True).start()
    def load(self):
        try:
            data=candles(self.symbol,self.interval); vals=[x[0] for x in data]
            sig,reason=analyze(vals); price=vals[-1]
            stamp=datetime.fromtimestamp(data[-1][1]/1000,tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            Clock.schedule_once(lambda dt:self.show(sig,reason,price,stamp),0)
        except Exception as e:
            msg=str(e)[:120]; Clock.schedule_once(lambda dt:self.error(msg),0)
    def show(self,sig,reason,price,stamp):
        self.signal.text=sig
        self.signal.color={"BUY":(0.1,0.8,0.2,1),"SELL":(0.95,0.2,0.2,1)}.get(sig,(1,0.7,0.1,1))
        self.info.text=f"{self.symbol} · {self.interval}\n{reason}\nLast candle: {stamp}"
        self.price.text=f"Last close: {price:,.4f}"
    def error(self,msg):
        self.signal.text="WAIT"; self.signal.color=(1,0.7,0.1,1)
        self.info.text="Could not fetch market data. Check internet and retry.\n"+msg

if __name__ == "__main__": TradingSignalApp().run()
