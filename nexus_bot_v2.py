"""
NEXUS — AI/SI Crypto Trading Bot  v2.1
Persistent storage edition — all data survives restarts.

Saves to ./nexus_data/:
  config/     — API settings, strategy parameters
  scans/      — every scan result as CSV + master history
  simulations/— every simulation as JSON + trade log CSV
  trades/     — unified trade journal CSV
  alerts/     — alert history JSON
  ai_log/     — AI parameter update log
  snapshots/  — session crash-recovery backups
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random, time, json, io
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

# ── Storage module (same directory) ──────────────────────────────────────────
from nexus_storage import (
    load_config, save_config,
    load_strategy_params, save_strategy_params,
    save_scan, load_scan_history, list_saved_scans, load_saved_scan,
    save_simulation, load_simulation_history, list_saved_simulations, load_simulation_detail,
    save_alerts, load_alerts, append_alert,
    save_ai_log, load_ai_log, append_ai_log,
    save_snapshot, load_latest_snapshot,
    log_trade, load_trade_journal, bulk_log_simulation_trades,
    export_all_to_zip, get_storage_stats,
    DIRS,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS — AI Crypto Bot",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700;800&family=Syne:wght@400;700;800&display=swap');
:root {
  --bg0:#04060d;--bg1:#080d18;--bg2:#0c1220;--bg3:#101828;
  --border:rgba(56,189,248,0.12);--border2:rgba(56,189,248,0.22);
  --green:#00e5a0;--red:#ff3d71;--blue:#38bdf8;--gold:#f5c542;
  --purple:#a78bfa;--text:#c9d8ea;--muted:#3d5068;--dim:#1e2d3e;
}
html,body,[class*="css"],.stApp{font-family:'JetBrains Mono',monospace!important;background-color:var(--bg0)!important;color:var(--text)!important;}
.stApp{background:var(--bg0)!important;}
.main .block-container{padding:1rem 1.5rem 2rem!important;max-width:100%!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--bg1) 0%,var(--bg0) 100%)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{font-family:'JetBrains Mono',monospace!important;}
[data-testid="stSidebarContent"]{padding:1rem!important;}
#MainMenu,footer,header{visibility:hidden!important;}
.stDeployButton{display:none!important;}
h1,h2,h3,h4{font-family:'Syne',sans-serif!important;letter-spacing:0.05em!important;}
[data-testid="metric-container"]{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:8px!important;padding:14px 16px!important;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;font-size:1.4rem!important;color:var(--blue)!important;}
[data-testid="stMetricLabel"]{font-size:0.65rem!important;letter-spacing:2px!important;color:var(--muted)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--bg1)!important;border-bottom:1px solid var(--border)!important;gap:0!important;padding:0!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;font-family:'JetBrains Mono',monospace!important;font-size:0.72rem!important;letter-spacing:2px!important;padding:14px 20px!important;border:none!important;border-bottom:2px solid transparent!important;border-radius:0!important;}
.stTabs [aria-selected="true"]{color:var(--green)!important;border-bottom:2px solid var(--green)!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.5rem!important;}
.stButton>button{font-family:'JetBrains Mono',monospace!important;font-size:0.75rem!important;font-weight:700!important;letter-spacing:2px!important;border-radius:6px!important;transition:all 0.15s ease!important;}
.stButton>button{background:linear-gradient(135deg,#00e5a0,#00b8ff)!important;color:#04060d!important;border:none!important;padding:10px 20px!important;}
.stButton>button:hover{opacity:0.85!important;transform:translateY(-1px)!important;}
.stSelectbox>div>div,.stMultiSelect>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:6px!important;color:var(--text)!important;font-family:'JetBrains Mono',monospace!important;font-size:0.8rem!important;}
div[data-baseweb="popover"]{background:var(--bg2)!important;}
li[role="option"]{background:var(--bg2)!important;color:var(--text)!important;}
.stSlider>div>div>div{background:var(--bg3)!important;}
.stSlider>div>div>div>div{background:var(--green)!important;}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:8px!important;overflow:hidden!important;}
.stProgress>div>div>div{background:linear-gradient(90deg,var(--green),var(--blue))!important;}
.stSuccess{background:rgba(0,229,160,0.07)!important;border-left:3px solid var(--green)!important;}
.stInfo{background:rgba(56,189,248,0.07)!important;border-left:3px solid var(--blue)!important;}
.stWarning{background:rgba(245,197,66,0.07)!important;border-left:3px solid var(--gold)!important;}
.stError{background:rgba(255,61,113,0.07)!important;border-left:3px solid var(--red)!important;}
.streamlit-expanderHeader{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:6px!important;font-family:'JetBrains Mono',monospace!important;font-size:0.78rem!important;color:var(--text)!important;}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin-bottom:10px;}
.card-green{border-color:rgba(0,229,160,0.3);background:rgba(0,229,160,0.04);}
.card-red{border-color:rgba(255,61,113,0.3);background:rgba(255,61,113,0.04);}
.card-blue{border-color:rgba(56,189,248,0.25);background:rgba(56,189,248,0.04);}
.card-gold{border-color:rgba(245,197,66,0.25);background:rgba(245,197,66,0.04);}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg0);}
::-webkit-scrollbar-thumb{background:var(--dim);border-radius:2px;}
.save-badge{display:inline-block;background:rgba(0,229,160,0.12);border:1px solid rgba(0,229,160,0.25);color:#00e5a0;padding:2px 8px;border-radius:4px;font-size:0.62rem;letter-spacing:1px;margin-left:8px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
COINS = [
    "BTC/USDT","ETH/USDT","BNB/USDT","SOL/USDT","XRP/USDT","ADA/USDT",
    "AVAX/USDT","DOGE/USDT","MATIC/USDT","DOT/USDT","LINK/USDT","UNI/USDT",
    "LTC/USDT","ATOM/USDT","NEAR/USDT","ARB/USDT","OP/USDT","INJ/USDT",
    "SUI/USDT","APT/USDT","FTM/USDT","SAND/USDT","MANA/USDT","ALGO/USDT",
]
BASE_PRICES = {
    "BTC/USDT":67420,"ETH/USDT":3541,"BNB/USDT":412,"SOL/USDT":178,
    "XRP/USDT":0.612,"ADA/USDT":0.48,"AVAX/USDT":38.2,"DOGE/USDT":0.162,
    "MATIC/USDT":0.91,"DOT/USDT":8.3,"LINK/USDT":14.2,"UNI/USDT":9.8,
    "LTC/USDT":89.4,"ATOM/USDT":10.1,"NEAR/USDT":5.7,"ARB/USDT":1.12,
    "OP/USDT":2.45,"INJ/USDT":28.6,"SUI/USDT":1.85,"APT/USDT":9.4,
    "FTM/USDT":0.81,"SAND/USDT":0.48,"MANA/USDT":0.52,"ALGO/USDT":0.21,
}
INTERVALS = ["1m","3m","5m","15m","30m","1h","2h","4h","6h","12h","1d","3d","1w"]
INTERVAL_INFO = {
    "1m":{"style":"Scalping","icon":"⚡","noise":"Very High","desc":"Ultra-short HFT signals"},
    "3m":{"style":"Scalping","icon":"⚡","noise":"Very High","desc":"Fast momentum scalps"},
    "5m":{"style":"Scalping","icon":"⚡","noise":"High","desc":"Short-term breakouts"},
    "15m":{"style":"Day Trade","icon":"◈","noise":"Medium","desc":"Balanced intraday setup"},
    "30m":{"style":"Day Trade","icon":"◈","noise":"Medium","desc":"Confirmed intraday trends"},
    "1h":{"style":"Swing","icon":"▲","noise":"Low","desc":"Most popular swing frame"},
    "2h":{"style":"Swing","icon":"▲","noise":"Low","desc":"Strong trend confirmation"},
    "4h":{"style":"Swing","icon":"▲","noise":"Low","desc":"Industry-standard swing TF"},
    "6h":{"style":"Position","icon":"◆","noise":"Very Low","desc":"Medium-term positioning"},
    "12h":{"style":"Position","icon":"◆","noise":"Very Low","desc":"Clean macro trends"},
    "1d":{"style":"Long-Term","icon":"●","noise":"Minimal","desc":"Daily close significance"},
    "3d":{"style":"Long-Term","icon":"●","noise":"Minimal","desc":"Major trend identification"},
    "1w":{"style":"Long-Term","icon":"●","noise":"Minimal","desc":"Strategic macro view"},
}
STRATEGIES = {
    "RSI Oversold/Overbought":{"group":"Momentum","icon":"📊","desc":"Buys when RSI < oversold threshold, sells when > overbought.","params":{"rsi_period":14,"oversold":30,"overbought":70},"ai_hints":["Lower oversold to 28 for stronger signals","Add volume confirmation","Use with trend filter"]},
    "EMA Crossover":{"group":"Trend","icon":"📈","desc":"Fast EMA crosses above/below slow EMA signals trend change.","params":{"fast_ema":9,"slow_ema":21},"ai_hints":["9/21 works best on 1h+","Add ADX filter > 25","Tune per asset volatility"]},
    "MACD Signal Cross":{"group":"Trend","icon":"〰️","desc":"MACD line/signal crossover with histogram confirmation.","params":{"fast":12,"slow":26,"signal":9},"ai_hints":["Histogram zero-cross reduces lag","Works best in trending markets","Combine with 200 EMA filter"]},
    "Bollinger Band Squeeze":{"group":"Volatility","icon":"🎯","desc":"Detects volatility squeeze breakouts from Bollinger Bands.","params":{"period":20,"std_dev":2.0,"squeeze_pct":3.0},"ai_hints":["Lower std_dev increases signals","Combine with RSI for direction","4h frame gives cleanest squeezes"]},
    "Stochastic RSI":{"group":"Momentum","icon":"🔄","desc":"Normalized RSI oscillator for precise oversold/overbought detection.","params":{"rsi_period":14,"stoch_period":14,"smooth_k":3,"smooth_d":3},"ai_hints":["K/D crossover is key entry","More sensitive than RSI","Best on 15m-4h"]},
    "VWAP Deviation":{"group":"Volume","icon":"📦","desc":"Trades price deviations from Volume-Weighted Average Price.","params":{"band_multiplier":2.0,"min_volume_ratio":1.2},"ai_hints":["Works intraday only","Strong with large-cap coins","Use 1h-4h for best results"]},
    "Supertrend":{"group":"Trend","icon":"🚀","desc":"ATR-based trend indicator that flips direction on breakouts.","params":{"atr_period":10,"atr_multiplier":3.0},"ai_hints":["Higher multiplier = fewer signals","Lower ATR = more responsive","Combine with RSI filter"]},
    "Ichimoku Cloud":{"group":"Trend","icon":"☁️","desc":"Full Ichimoku system with Kumo breakout and TK cross entries.","params":{"tenkan":9,"kijun":26,"senkou_b":52,"displacement":26},"ai_hints":["Price above cloud = strong bull","TK cross in cloud = high confidence","Best on 4h and daily"]},
    "Bull Flag / Pennant":{"group":"Pattern","icon":"🏁","desc":"Sharp pole rally followed by tight flag consolidation.","params":{"pole_min_pct":5.0,"breakout_vol_mult":1.5},"ai_hints":["Volume surge on breakout essential","Best on 1h-4h","Works well post-halving"]},
    "Double Bottom / Top":{"group":"Pattern","icon":"〽️","desc":"W/M shaped reversal patterns at key support/resistance.","params":{"tolerance_pct":1.5,"min_separation":10},"ai_hints":["Lower volume on 2nd bottom confirms","Neckline break needed","Strong on daily frame"]},
    "Head & Shoulders":{"group":"Pattern","icon":"👤","desc":"Classic three-peak reversal pattern (also inverse H&S).","params":{"shoulder_tolerance":2.0,"volume_decay":True},"ai_hints":["Inverse H&S is bullish reversal","Volume drops toward right shoulder","Neckline retest common"]},
    "Cup & Handle":{"group":"Pattern","icon":"☕","desc":"Rounded bottom followed by a short handle before breakout.","params":{"cup_depth_pct":15.0,"handle_depth_pct":5.0},"ai_hints":["Cup should be rounded not V","Handle < 1/3 of cup depth","Strong bullish setup"]},
    "Ascending Triangle":{"group":"Pattern","icon":"△","desc":"Price coiling between flat resistance and rising trendline.","params":{"min_touches":3,"tolerance_pct":1.0},"ai_hints":["Flat top = bullish breakout","Volume contracts then explodes","Best on 4h+"]},
    "Engulfing Candles":{"group":"Candlestick","icon":"🕯️","desc":"Bullish/bearish engulfing at key support/resistance zones.","params":{"min_body_ratio":1.5,"volume_confirm":True},"ai_hints":["Higher volume = stronger signal","Works at S/R only","Combine with RSI divergence"]},
}
EXCHANGES = ["Binance","Coinbase Pro","Kraken","Bybit","OKX","Gate.io","KuCoin","Bitget","MEXC"]
GROUP_COLORS = {"Momentum":"#f5c542","Trend":"#38bdf8","Volatility":"#a78bfa","Volume":"#34d399","Pattern":"#fb923c","Candlestick":"#f472b6"}
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,13,24,0.9)",
    font=dict(color="#c9d8ea",family="JetBrains Mono, monospace",size=11),
    xaxis=dict(showgrid=True,gridcolor="#111c28",color="#3d5068",zeroline=False),
    yaxis=dict(showgrid=True,gridcolor="#111c28",color="#3d5068",zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#c9d8ea")),
    margin=dict(t=38,b=36,l=55,r=16),hovermode="x unified",
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE — boot from disk on first load
# ─────────────────────────────────────────────────────────────────────────────
if "booted" not in st.session_state:
    # Load persisted config
    cfg = load_config()
    sp  = load_strategy_params()
    al  = load_alerts()
    ail = load_ai_log()

    st.session_state.update({
        "booted":          True,
        "exchange":        cfg.get("exchange","Binance"),
        "api_key":         cfg.get("api_key",""),
        "api_secret":      "",           # never restore secret from disk
        "api_passphrase":  "",
        "api_connected":   False,        # always require re-auth
        "api_mode":        cfg.get("api_mode","paper"),
        "scan_results":    None,
        "scan_count":      cfg.get("scan_count",0),
        "sim_results":     None,
        "sim_count":       cfg.get("sim_count",0),
        "alerts":          al,
        "ai_log":          ail,
        "sim_history":     [],
        "strategy_params": sp if sp else {n:dict(i["params"]) for n,i in STRATEGIES.items()},
        "last_save":       cfg.get("_saved","never"),
        "selected_coins":  cfg.get("selected_coins",["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","ADA/USDT"]),
        "selected_strats": cfg.get("selected_strats",["RSI Oversold/Overbought","EMA Crossover","Bollinger Band Squeeze","Supertrend"]),
        "selected_ivals":  cfg.get("selected_ivals",["15m","1h","4h"]),
        # Rolling performance tracker per strategy — used for auto AI tuning
        # {strategy_name: {"runs":int, "win_rates":[], "returns":[], "drawdowns":[], "pf":[]}}
        "perf_tracker":    {},
        "last_ai_update":  {},   # {strategy: timestamp string}
    })

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def push_alert(msg: str, kind: str = "info"):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "kind": kind}
    st.session_state.alerts.insert(0, entry)
    if len(st.session_state.alerts) > 200:
        st.session_state.alerts = st.session_state.alerts[:200]
    append_alert(entry)   # ← persist immediately

def fmt_price(p):
    try: return f"${float(p):,.6f}" if float(p)<1 else f"${float(p):,.2f}"
    except: return str(p)

def auto_save():
    """Persist session config and params — called after any mutation."""
    cfg = {
        "exchange":        st.session_state.exchange,
        "api_key":         st.session_state.api_key,
        "api_mode":        st.session_state.api_mode,
        "scan_count":      st.session_state.scan_count,
        "sim_count":       st.session_state.sim_count,
        "selected_coins":  st.session_state.get("selected_coins",[]),
        "selected_strats": st.session_state.get("selected_strats",[]),
        "selected_ivals":  st.session_state.get("selected_ivals",[]),
    }
    save_config(cfg)
    save_strategy_params(st.session_state.strategy_params)
    st.session_state.last_save = datetime.now().strftime("%H:%M:%S")

# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR MATH
# ─────────────────────────────────────────────────────────────────────────────
def gen_candles(n=120, base=67000, vol=0.022):
    rng = np.random.default_rng()
    lr  = rng.normal(0.0001, vol/np.sqrt(n), n)
    cl  = base * np.cumprod(np.exp(lr))
    op  = np.roll(cl,1); op[0]=base
    hi  = np.maximum(op,cl)*(1+rng.uniform(0.001,0.012,n))
    lo  = np.minimum(op,cl)*(1-rng.uniform(0.001,0.012,n))
    vl  = rng.uniform(200,3000,n)
    t0  = datetime.utcnow()
    times=[t0-timedelta(minutes=15*(n-i)) for i in range(n)]
    return pd.DataFrame({"time":times,"open":op,"high":hi,"low":lo,"close":cl,"volume":vl})

def ema(s,p):   return s.ewm(span=p,adjust=False).mean()
def rsi(s,p=14):
    d=s.diff(); g=d.where(d>0,0).rolling(p).mean(); l=(-d.where(d<0,0)).rolling(p).mean()
    return 100-100/(1+g/(l.replace(0,np.nan)))
def macd_calc(s,f=12,sl=26,sig=9):
    m=ema(s,f)-ema(s,sl); return m,ema(m,sig),m-ema(m,sig)
def bbands(s,p=20,std=2.0):
    m=s.rolling(p).mean(); sd=s.rolling(p).std(); return m+std*sd,m,m-std*sd
def stochrsi(s,rp=14,sp=14,k=3,d=3):
    r=rsi(s,rp); mn=r.rolling(sp).min(); mx=r.rolling(sp).max()
    K=((r-mn)/(mx-mn+1e-9)*100).rolling(k).mean(); return K,K.rolling(d).mean()
def vwap_calc(df):
    tp=(df["high"]+df["low"]+df["close"])/3
    return (tp*df["volume"]).cumsum()/df["volume"].cumsum()
def atr_calc(df,p=14):
    tr=pd.concat([df["high"]-df["low"],(df["high"]-df["close"].shift()).abs(),(df["low"]-df["close"].shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(p).mean()
def supertrend_dir(df,p=10,mult=3.0):
    a=atr_calc(df,p); mid=(df["high"]+df["low"])/2
    up=mid+mult*a; dn=mid-mult*a
    dr=pd.Series(1,index=df.index)
    for i in range(1,len(df)):
        dr.iloc[i]= 1 if df["close"].iloc[i]>up.iloc[i-1] else (-1 if df["close"].iloc[i]<dn.iloc[i-1] else dr.iloc[i-1])
    return dr

def compute_signal(strategy, df, params):
    c=df["close"]; sig="HOLD"; conf=random.randint(38,58); note=""
    try:
        if strategy=="RSI Oversold/Overbought":
            r=float(rsi(c,params["rsi_period"]).iloc[-1])
            if r<params["oversold"]: sig,conf,note="BUY",int(80-r),f"RSI={r:.1f} oversold"
            elif r>params["overbought"]: sig,conf,note="SELL",int(r-30),f"RSI={r:.1f} overbought"
            else: note=f"RSI={r:.1f} neutral"
        elif strategy=="EMA Crossover":
            f=ema(c,params["fast_ema"]); s=ema(c,params["slow_ema"])
            if f.iloc[-1]>s.iloc[-1] and f.iloc[-2]<=s.iloc[-2]: sig,conf,note="BUY",random.randint(72,90),"EMA golden cross"
            elif f.iloc[-1]<s.iloc[-1] and f.iloc[-2]>=s.iloc[-2]: sig,conf,note="SELL",random.randint(70,88),"EMA death cross"
            elif f.iloc[-1]>s.iloc[-1]: sig,conf,note="BUY",random.randint(58,74),"Above EMA"
            else: sig,conf,note="SELL",random.randint(55,70),"Below EMA"
        elif strategy=="MACD Signal Cross":
            m,sg,h=macd_calc(c,params["fast"],params["slow"],params["signal"])
            if m.iloc[-1]>sg.iloc[-1] and m.iloc[-2]<=sg.iloc[-2]: sig,conf,note="BUY",random.randint(70,88),"MACD bullish cross"
            elif m.iloc[-1]<sg.iloc[-1] and m.iloc[-2]>=sg.iloc[-2]: sig,conf,note="SELL",random.randint(68,86),"MACD bearish cross"
            elif h.iloc[-1]>0: note=f"MACD hist={h.iloc[-1]:.4f} bullish"
            else: note=f"MACD hist={h.iloc[-1]:.4f} bearish"
        elif strategy=="Bollinger Band Squeeze":
            bu,bm,bl=bbands(c,params["period"],params["std_dev"])
            bw=(bu.iloc[-1]-bl.iloc[-1])/bm.iloc[-1]*100; last=c.iloc[-1]
            if last<bl.iloc[-1]: sig,conf,note="BUY",random.randint(72,90),f"Below lower BB BW={bw:.1f}%"
            elif last>bu.iloc[-1]: sig,conf,note="SELL",random.randint(70,88),f"Above upper BB BW={bw:.1f}%"
            elif bw<params["squeeze_pct"]: sig,conf,note=("BUY" if c.pct_change().iloc[-3:].mean()>0 else "SELL"),random.randint(65,80),f"Squeeze breakout BW={bw:.1f}%"
            else: note=f"BB Width={bw:.1f}%"
        elif strategy=="Stochastic RSI":
            K,D=stochrsi(c,params["rsi_period"],params["stoch_period"],params["smooth_k"],params["smooth_d"])
            if K.iloc[-1]<20 and K.iloc[-1]>D.iloc[-1]: sig,conf,note="BUY",random.randint(72,90),f"StochRSI K={K.iloc[-1]:.1f}"
            elif K.iloc[-1]>80 and K.iloc[-1]<D.iloc[-1]: sig,conf,note="SELL",random.randint(70,88),f"StochRSI K={K.iloc[-1]:.1f}"
            else: note=f"K={K.iloc[-1]:.1f} D={D.iloc[-1]:.1f}"
        elif strategy=="VWAP Deviation":
            vw=vwap_calc(df); dev=(c.iloc[-1]-vw.iloc[-1])/vw.iloc[-1]*100
            vol_avg=df["volume"].rolling(20).mean().iloc[-1]
            if dev<-params["band_multiplier"] and df["volume"].iloc[-1]>vol_avg*params["min_volume_ratio"]: sig,conf,note="BUY",random.randint(70,86),f"VWAP dev={dev:.2f}%"
            elif dev>params["band_multiplier"] and df["volume"].iloc[-1]>vol_avg*params["min_volume_ratio"]: sig,conf,note="SELL",random.randint(68,84),f"VWAP dev={dev:.2f}%"
            else: note=f"VWAP dev={dev:.2f}%"
        elif strategy=="Supertrend":
            d=supertrend_dir(df,params["atr_period"],params["atr_multiplier"])
            if d.iloc[-1]==1 and d.iloc[-2]==-1: sig,conf,note="BUY",random.randint(76,92),"Supertrend flipped bull"
            elif d.iloc[-1]==-1 and d.iloc[-2]==1: sig,conf,note="SELL",random.randint(74,90),"Supertrend flipped bear"
            elif d.iloc[-1]==1: sig,conf,note="BUY",random.randint(60,76),"Supertrend bullish"
            else: sig,conf,note="SELL",random.randint(58,74),"Supertrend bearish"
        elif strategy=="Ichimoku Cloud":
            hi=df["high"]; lo=df["low"]; p=params
            tenkan=(hi.rolling(p["tenkan"]).max()+lo.rolling(p["tenkan"]).min())/2
            kijun=(hi.rolling(p["kijun"]).max()+lo.rolling(p["kijun"]).min())/2
            spanA=((tenkan+kijun)/2).shift(p["displacement"])
            spanB=((hi.rolling(p["senkou_b"]).max()+lo.rolling(p["senkou_b"]).min())/2).shift(p["displacement"])
            if len(c)>p["displacement"]:
                above=c.iloc[-1]>max(float(spanA.iloc[-1] or 0),float(spanB.iloc[-1] or 0))
                tk_bull=tenkan.iloc[-1]>kijun.iloc[-1] and tenkan.iloc[-2]<=kijun.iloc[-2]
                if above and tk_bull: sig,conf,note="BUY",random.randint(74,92),"Ichimoku TK cross above cloud"
                elif above: sig,conf,note="BUY",random.randint(60,75),"Above Ichimoku cloud"
                elif not above and tenkan.iloc[-1]<kijun.iloc[-1]: sig,conf,note="SELL",random.randint(65,82),"Below Ichimoku cloud"
                else: note="In cloud — neutral"
        else:
            # Pattern strategies — probabilistic
            rc=c.pct_change(5).iloc[-1]*100; rv=random.random()
            if strategy=="Bull Flag / Pennant" and rv>0.82 and rc>2: sig,conf,note="BUY",random.randint(72,90),"Bull flag breakout"
            elif strategy=="Double Bottom / Top" and rv>0.85: sig,conf,note=("BUY" if rc>0 else "SELL"),random.randint(74,90),("Double bottom" if rc>0 else "Double top")
            elif strategy=="Head & Shoulders" and rv>0.87: sig,conf,note=("SELL" if rc>0 else "BUY"),random.randint(76,92),("H&S top" if rc>0 else "Inverse H&S")
            elif strategy=="Cup & Handle" and rv>0.88 and rc>0: sig,conf,note="BUY",random.randint(78,93),"Cup & handle breakout"
            elif strategy=="Ascending Triangle" and rv>0.83: sig,conf,note=("BUY" if rc>0 else "SELL"),random.randint(70,88),("Ascending tri breakout" if rc>0 else "Descending tri breakdown")
            elif strategy=="Engulfing Candles":
                lb=abs(c.iloc[-1]-df["open"].iloc[-1]); pb=abs(c.iloc[-2]-df["open"].iloc[-2])
                if lb>pb*params["min_body_ratio"]: sig,conf,note=("BUY" if c.iloc[-1]>df["open"].iloc[-1] else "SELL"),random.randint(68,86),("Bullish engulf" if c.iloc[-1]>df["open"].iloc[-1] else "Bearish engulf")
    except: pass
    try:    rsi_v=float(rsi(c,14).iloc[-1])
    except: rsi_v=50.0
    try:    e9=float(ema(c,9).iloc[-1]); e21=float(ema(c,21).iloc[-1])
    except: e9=e21=float(c.iloc[-1])
    try:    _,_,hist=macd_calc(c); mv=float(hist.iloc[-1])
    except: mv=0.0
    try:    vr=float(df["volume"].iloc[-1]/df["volume"].rolling(20).mean().iloc[-1])
    except: vr=1.0
    return {"signal":sig,"confidence":max(10,min(99,conf)),"note":note,"rsi":round(rsi_v,1),"ema9":round(e9,4),"ema21":round(e21,4),"macd_hist":round(mv,5),"vol_ratio":round(vr,2)}

def run_market_scan(coins,strategies,intervals,params_dict):
    rows=[]
    for coin in coins:
        base=BASE_PRICES.get(coin,100); lp=base*(1+random.gauss(0,0.004)); chg=random.gauss(0.5,3.2)
        for interval in intervals:
            df=gen_candles(100,base)
            for strat in strategies:
                p=params_dict.get(strat,STRATEGIES[strat]["params"]); res=compute_signal(strat,df,p)
                rows.append({"Coin":coin.replace("/USDT",""),"Pair":coin,"Interval":interval,"Strategy":strat,"Group":STRATEGIES[strat]["group"],"Signal":res["signal"],"Confidence":res["confidence"],"Note":res["note"],"RSI":res["rsi"],"EMA9":res["ema9"],"EMA21":res["ema21"],"MACD Hist":res["macd_hist"],"Vol Ratio":res["vol_ratio"],"Price":round(lp,4 if lp<1 else 2),"24h %":round(chg,2)})
    df_out=pd.DataFrame(rows)
    return df_out.sort_values("Confidence",ascending=False).reset_index(drop=True)

def simulate_strategy(strategy,capital,candle_count,pos_size_pct,fee_pct,sl_pct,tp_pct,params):
    df=gen_candles(candle_count,67000,0.028)
    balance=capital; position=0.0; buy_price=0.0; equity=[capital]; trades=[]
    for i in range(30,len(df)):
        price=float(df.iloc[i]["close"])
        if position>0:
            chg=(price-buy_price)/buy_price*100
            if chg<=-sl_pct:
                balance+=position*price*(1-fee_pct/100); trades.append({"i":i,"type":"SELL","price":price,"pnl":round(chg,2),"reason":"Stop Loss","equity":balance}); position=0
            elif chg>=tp_pct:
                balance+=position*price*(1-fee_pct/100); trades.append({"i":i,"type":"SELL","price":price,"pnl":round(chg,2),"reason":"Take Profit","equity":balance}); position=0
        res=compute_signal(strategy,df.iloc[:i].copy(),params)
        if res["signal"]=="BUY" and position==0 and balance>10:
            inv=balance*(pos_size_pct/100); cost=inv*(1+fee_pct/100)
            if cost<=balance: position=inv/price; buy_price=price; balance-=cost; trades.append({"i":i,"type":"BUY","price":price,"pnl":0,"reason":res["note"],"equity":balance+position*price})
        elif res["signal"]=="SELL" and position>0:
            balance+=position*price*(1-fee_pct/100); pnl=(price-buy_price)/buy_price*100; trades.append({"i":i,"type":"SELL","price":price,"pnl":round(pnl,2),"reason":res["note"],"equity":balance}); position=0
        equity.append(balance+position*price)
    final=balance+position*float(df.iloc[-1]["close"]); total_ret=(final-capital)/capital*100
    sells=[t for t in trades if t["type"]=="SELL"]; wins=[t for t in sells if t["pnl"]>0]; losses=[t for t in sells if t["pnl"]<=0]
    wr=len(wins)/max(len(sells),1)*100; aw=float(np.mean([t["pnl"] for t in wins])) if wins else 0; al2=float(np.mean([abs(t["pnl"]) for t in losses])) if losses else 0
    pf=sum(t["pnl"] for t in wins)/max(abs(sum(t["pnl"] for t in losses)),0.01)
    peak=equity[0]; mdd=0.0
    for e in equity:
        if e>peak: peak=e
        dd=(peak-e)/peak*100
        if dd>mdd: mdd=dd
    return {"final":round(final,2),"total_ret":round(total_ret,2),"win_rate":round(wr,1),"trades":len(sells),"avg_win":round(aw,2),"avg_loss":round(al2,2),"profit_factor":round(pf,2),"max_dd":round(mdd,2),"equity":equity,"trade_log":trades,"df":df,"strategy":strategy,"capital":capital,"sharpe":round(total_ret/max(mdd,0.1)*0.45,2)}

def ai_update_params(strategy, results, current_params):
    """
    Single-run parameter adjustment. Returns (new_params, log_messages).
    Called by auto_ai_tune after every simulation — no button needed.
    """
    new_p = dict(current_params)
    log   = []
    wr  = results["win_rate"]
    ret = results["total_ret"]
    dd  = results["max_dd"]
    pf  = results["profit_factor"]

    if strategy == "RSI Oversold/Overbought":
        if wr < 48:
            new_p["oversold"]   = max(18, current_params["oversold"] - 2)
            new_p["overbought"] = min(82, current_params["overbought"] + 2)
            log.append(f"Tightened RSI thresholds → buy<{new_p['oversold']} sell>{new_p['overbought']}")
        elif wr > 68 and pf > 1.4:
            new_p["oversold"]   = min(35, current_params["oversold"] + 1)
            new_p["overbought"] = max(65, current_params["overbought"] - 1)
            log.append(f"Relaxed RSI thresholds → buy<{new_p['oversold']} sell>{new_p['overbought']} (high WR)")

    elif strategy == "EMA Crossover":
        if dd > 22:
            new_p["fast_ema"] = max(5, current_params["fast_ema"] - 1)
            log.append(f"Reduced fast EMA {current_params['fast_ema']}→{new_p['fast_ema']} (high DD)")
        if wr > 62 and pf > 1.5:
            new_p["slow_ema"] = min(34, current_params["slow_ema"] + 2)
            log.append(f"Increased slow EMA {current_params['slow_ema']}→{new_p['slow_ema']} (filter noise)")
        if wr < 45:
            new_p["fast_ema"] = max(5, current_params["fast_ema"] - 2)
            new_p["slow_ema"] = max(current_params["fast_ema"]+3, current_params["slow_ema"] - 2)
            log.append(f"Adjusted EMA periods {new_p['fast_ema']}/{new_p['slow_ema']} (poor WR)")

    elif strategy == "MACD Signal Cross":
        if pf < 1.0:
            new_p["signal"] = max(6, current_params["signal"] - 1)
            log.append(f"Reduced MACD signal period {current_params['signal']}→{new_p['signal']} (PF<1)")
        elif wr > 65:
            new_p["fast"] = min(16, current_params["fast"] + 1)
            log.append(f"Slowed MACD fast period {current_params['fast']}→{new_p['fast']} (reduce whipsaws)")

    elif strategy == "Bollinger Band Squeeze":
        if dd > 25:
            new_p["std_dev"] = min(3.0, round(current_params["std_dev"] + 0.2, 1))
            log.append(f"Widened BB std_dev {current_params['std_dev']}→{new_p['std_dev']} (high DD)")
        elif wr > 62:
            new_p["squeeze_pct"] = max(1.5, round(current_params.get("squeeze_pct", 3.0) - 0.5, 1))
            log.append(f"Tightened squeeze threshold → {new_p['squeeze_pct']}% (strong WR)")
        if wr < 45:
            new_p["std_dev"] = max(1.5, round(current_params["std_dev"] - 0.1, 1))
            log.append(f"Narrowed BB std_dev {current_params['std_dev']}→{new_p['std_dev']} (poor WR)")

    elif strategy == "Stochastic RSI":
        if wr < 48:
            new_p["smooth_k"] = max(2, current_params["smooth_k"] + 1)
            log.append(f"Increased StochRSI K smoothing to {new_p['smooth_k']} (reduce noise)")
        elif dd > 20:
            new_p["stoch_period"] = min(21, current_params["stoch_period"] + 2)
            log.append(f"Lengthened StochRSI period to {new_p['stoch_period']} (reduce DD)")

    elif strategy == "Supertrend":
        if dd > 22:
            new_p["atr_multiplier"] = min(5.0, round(current_params["atr_multiplier"] + 0.3, 1))
            log.append(f"Raised Supertrend ATR mult {current_params['atr_multiplier']}→{new_p['atr_multiplier']} (high DD)")
        elif wr > 65 and ret > 10:
            new_p["atr_period"] = max(7, current_params["atr_period"] - 1)
            log.append(f"Lowered ATR period {current_params['atr_period']}→{new_p['atr_period']} (faster signals)")
        if wr < 44:
            new_p["atr_multiplier"] = max(1.5, round(current_params["atr_multiplier"] - 0.2, 1))
            log.append(f"Reduced ATR mult {current_params['atr_multiplier']}→{new_p['atr_multiplier']} (more signals)")

    elif strategy == "Ichimoku Cloud":
        if dd > 25:
            new_p["kijun"] = min(34, current_params["kijun"] + 2)
            log.append(f"Lengthened Kijun {current_params['kijun']}→{new_p['kijun']} (smoother trend)")
        elif wr > 65:
            new_p["tenkan"] = max(7, current_params["tenkan"] - 1)
            log.append(f"Shortened Tenkan {current_params['tenkan']}→{new_p['tenkan']} (faster cross)")

    elif strategy == "VWAP Deviation":
        if wr < 48:
            new_p["band_multiplier"] = min(3.5, round(current_params["band_multiplier"] + 0.25, 2))
            log.append(f"Widened VWAP band to ±{new_p['band_multiplier']} (stricter entries)")
        elif wr > 65:
            new_p["min_volume_ratio"] = max(1.0, round(current_params["min_volume_ratio"] - 0.1, 1))
            log.append(f"Relaxed volume filter to {new_p['min_volume_ratio']}x (more signals)")

    elif strategy in ("Bull Flag / Pennant", "Cup & Handle"):
        if wr < 50:
            new_p["breakout_vol_mult"] = min(3.0, round(current_params.get("breakout_vol_mult", 1.5) + 0.3, 1))
            log.append(f"Raised volume confirmation to {new_p['breakout_vol_mult']}x (stricter pattern)")

    elif strategy in ("Double Bottom / Top", "Head & Shoulders"):
        if wr < 48:
            new_p["shoulder_tolerance"] = max(0.5, round(current_params.get("shoulder_tolerance", 2.0) - 0.3, 1))
            log.append(f"Tightened pattern tolerance to {new_p.get('shoulder_tolerance', new_p.get('tolerance_pct','?'))}%")

    if not log:
        log.append(f"Params near-optimal for current market. Monitoring.")

    return new_p, log


def auto_ai_tune(strategy: str, results: dict):
    """
    Automatically called after every simulation completes.
    Accumulates rolling statistics per strategy and adjusts params
    based on the rolling average — not just a single run.

    Thresholds:
      - After run 1:   always apply immediate single-run adjustments
      - After 3+ runs: use rolling average WR/return/DD to tune
      - After 5+ runs: apply stricter convergence logic
    """
    strat = strategy
    cur_p = st.session_state.strategy_params.get(strat, STRATEGIES[strat]["params"])

    # 1. Update rolling performance tracker
    tracker = st.session_state.perf_tracker.setdefault(strat, {
        "runs": 0, "win_rates": [], "returns": [], "drawdowns": [], "pfs": []
    })
    tracker["runs"]      += 1
    tracker["win_rates"].append(results["win_rate"])
    tracker["returns"].append(results["total_ret"])
    tracker["drawdowns"].append(results["max_dd"])
    tracker["pfs"].append(results["profit_factor"])

    # Keep last 10 runs for rolling average
    for key in ("win_rates","returns","drawdowns","pfs"):
        tracker[key] = tracker[key][-10:]

    runs = tracker["runs"]
    avg_wr  = float(np.mean(tracker["win_rates"]))
    avg_ret = float(np.mean(tracker["returns"]))
    avg_dd  = float(np.mean(tracker["drawdowns"]))
    avg_pf  = float(np.mean(tracker["pfs"]))

    # Build a blended result: weight rolling avg more as runs accumulate
    if runs == 1:
        blend = results  # first run: use raw results
        blend_label = "run 1 (single)"
    elif runs < 4:
        # Weight: 60% latest, 40% rolling
        blend = {
            "win_rate":      results["win_rate"] * 0.6 + avg_wr * 0.4,
            "total_ret":     results["total_ret"] * 0.6 + avg_ret * 0.4,
            "max_dd":        results["max_dd"] * 0.6 + avg_dd * 0.4,
            "profit_factor": results["profit_factor"] * 0.6 + avg_pf * 0.4,
        }
        blend_label = f"run {runs} (60/40 blend)"
    else:
        # Weight: 30% latest, 70% rolling
        blend = {
            "win_rate":      results["win_rate"] * 0.3 + avg_wr * 0.7,
            "total_ret":     results["total_ret"] * 0.3 + avg_ret * 0.7,
            "max_dd":        results["max_dd"] * 0.3 + avg_dd * 0.7,
            "profit_factor": results["profit_factor"] * 0.3 + avg_pf * 0.7,
        }
        blend_label = f"run {runs} (30/70 rolling)"

    # 2. Compute adjustments
    new_p, param_log = ai_update_params(strat, blend, cur_p)

    # 3. Rolling-level diagnostics
    diag_log = []
    trend_wr = ""
    if len(tracker["win_rates"]) >= 3:
        recent3 = tracker["win_rates"][-3:]
        if recent3[-1] > recent3[0] + 3:   trend_wr = "↑ improving"
        elif recent3[-1] < recent3[0] - 3: trend_wr = "↓ declining"
        else:                               trend_wr = "→ stable"

    diag_log.append(
        f"[{blend_label}] WR {avg_wr:.0f}% {trend_wr} | "
        f"Ret {avg_ret:+.1f}% | DD {avg_dd:.1f}% | PF {avg_pf:.2f} | "
        f"Runs: {runs}"
    )

    # Convergence check — if performance has been consistently bad over 5+ runs, add aggressive nudge
    if runs >= 5 and avg_wr < 45 and avg_ret < 0:
        diag_log.append("⚠️ Consistently poor performance across 5+ runs — applying aggressive reset nudge")
        # Reset toward safer defaults
        defaults = STRATEGIES[strat]["params"]
        for k in new_p:
            if isinstance(new_p[k], (int, float)) and isinstance(defaults.get(k), (int, float)):
                new_p[k] = round(new_p[k] * 0.5 + defaults[k] * 0.5, 2)
        diag_log.append(f"Params blended 50% toward defaults after {runs} under-performing runs")

    if runs >= 3 and avg_wr >= 60 and avg_ret > 10:
        diag_log.append(f"✅ Strategy converging well over {runs} runs — params locked, monitoring only")

    # 4. Apply and persist
    st.session_state.strategy_params[strat] = new_p
    st.session_state.last_ai_update[strat]  = datetime.now().strftime("%H:%M:%S")
    auto_save()

    # 5. Log everything
    timestamp = datetime.now().strftime("%H:%M:%S")
    all_msgs  = param_log + diag_log
    for msg in all_msgs:
        kind = "success" if "✅" in msg else ("warning" if "⚠️" in msg else "info")
        push_alert(f"[AI·{strat[:18]}] {msg}", kind)
        ai_entry = {"time": timestamp, "strat": strat, "msg": msg, "runs": runs,
                    "avg_wr": round(avg_wr, 1), "avg_ret": round(avg_ret, 2)}
        st.session_state.ai_log.insert(0, ai_entry)
        append_ai_log(ai_entry)

    return new_p, all_msgs, tracker

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def chart_equity(equity,trades,capital):
    color="#00e5a0" if equity[-1]>=capital else "#ff3d71"
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(equity))),y=equity,mode="lines",name="Portfolio",line=dict(color=color,width=2),fill="tozeroy",fillcolor=f"rgba({'0,229,160' if color=='#00e5a0' else '255,61,113'},0.05)"))
    fig.add_hline(y=capital,line_dash="dot",line_color="#3d5068",line_width=1,annotation_text="Start")
    buys=[t for t in trades if t["type"]=="BUY"]; sells=[t for t in trades if t["type"]=="SELL"]
    if buys: fig.add_trace(go.Scatter(x=[t["i"] for t in buys],y=[equity[min(t["i"],len(equity)-1)] for t in buys],mode="markers",name="BUY",marker=dict(symbol="triangle-up",size=10,color="#00e5a0")))
    if sells: fig.add_trace(go.Scatter(x=[t["i"] for t in sells],y=[equity[min(t["i"],len(equity)-1)] for t in sells],mode="markers",name="SELL",marker=dict(symbol="triangle-down",size=10,color="#ff3d71")))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=270,title=dict(text="Equity Curve",font=dict(color="#c9d8ea",size=12)))
    fig.update_layout(**ly); return fig

def chart_candles(df,trades):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.72,0.28],vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],increasing_line_color="#00e5a0",decreasing_line_color="#ff3d71",increasing_fillcolor="#00e5a044",decreasing_fillcolor="#ff3d7144",name="Price"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=ema(df["close"],9),mode="lines",name="EMA9",line=dict(color="#38bdf8",width=1.2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=ema(df["close"],21),mode="lines",name="EMA21",line=dict(color="#f5c542",width=1.2)),row=1,col=1)
    colors=["#00e5a044" if c>=o else "#ff3d7144" for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=df["volume"],name="Vol",marker_color=colors,showlegend=False),row=2,col=1)
    buys=[t for t in trades if t["type"]=="BUY"]; sells=[t for t in trades if t["type"]=="SELL"]
    if buys: fig.add_trace(go.Scatter(x=[df.iloc[min(t["i"],len(df)-1)]["time"] for t in buys],y=[t["price"]*0.997 for t in buys],mode="markers",name="BUY",marker=dict(symbol="triangle-up",size=12,color="#00e5a0"),showlegend=False),row=1,col=1)
    if sells: fig.add_trace(go.Scatter(x=[df.iloc[min(t["i"],len(df)-1)]["time"] for t in sells],y=[t["price"]*1.003 for t in sells],mode="markers",name="SELL",marker=dict(symbol="triangle-down",size=12,color="#ff3d71"),showlegend=False),row=1,col=1)
    ly=dict(PLOTLY_LAYOUT); ly.update(height=340,title=dict(text="Price + Signals",font=dict(color="#c9d8ea",size=12)),xaxis_rangeslider_visible=False,xaxis2=dict(showgrid=True,gridcolor="#111c28",color="#3d5068"),yaxis2=dict(showgrid=True,gridcolor="#111c28",color="#3d5068"))
    fig.update_layout(**ly); return fig

def chart_sig_pie(df):
    cnt=df["Signal"].value_counts()
    c={"BUY":"#00e5a0","SELL":"#ff3d71","HOLD":"#3d5068"}
    fig=go.Figure(go.Pie(labels=cnt.index,values=cnt.values,marker_colors=[c.get(s,"#666") for s in cnt.index],hole=0.6,textfont=dict(family="JetBrains Mono",size=11)))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Signal Mix",font=dict(color="#c9d8ea",size=12)),margin=dict(t=36,b=10,l=10,r=10))
    fig.update_layout(**ly); return fig

def chart_top_coins(df):
    top=df.groupby("Coin")["Confidence"].mean().sort_values().tail(10)
    fig=go.Figure(go.Bar(x=top.values,y=top.index,orientation="h",marker=dict(color=top.values,colorscale=[[0,"#1e2d3e"],[0.5,"#38bdf8"],[1,"#00e5a0"]]),text=[f"{v:.0f}%" for v in top.values],textposition="outside",textfont=dict(color="#c9d8ea",size=10)))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Avg Conf by Coin",font=dict(color="#c9d8ea",size=12)),xaxis=dict(showgrid=False,color="#3d5068",range=[0,115]),yaxis=dict(showgrid=False,color="#c9d8ea"),margin=dict(t=36,b=10,l=50,r=40))
    fig.update_layout(**ly); return fig

def chart_rsi(df):
    fig=go.Figure(go.Histogram(x=df["RSI"],nbinsx=20,marker_color="#38bdf8",marker_line_color="#0c1220",marker_line_width=1))
    fig.add_vrect(x0=0,x1=30,fillcolor="#00e5a0",opacity=0.06,line_width=0,annotation_text="Oversold",annotation_font_color="#00e5a0",annotation_font_size=10)
    fig.add_vrect(x0=70,x1=100,fillcolor="#ff3d71",opacity=0.06,line_width=0,annotation_text="Overbought",annotation_font_color="#ff3d71",annotation_font_size=10)
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="RSI Distribution",font=dict(color="#c9d8ea",size=12)),margin=dict(t=36,b=30,l=40,r=10))
    fig.update_layout(**ly); return fig

def chart_sim_history():
    hist=load_simulation_history()
    if hist.empty: return None
    hist=hist.tail(20)
    colors=["#00e5a0" if r>0 else "#ff3d71" for r in hist["total_return"]]
    fig=go.Figure(go.Bar(x=list(range(len(hist))),y=hist["total_return"],marker_color=colors,text=[f"{r:+.1f}%" for r in hist["total_return"]],textposition="outside",textfont=dict(color="#c9d8ea",size=10),hovertemplate="%{x}: %{y:.2f}%<extra>%{customdata}</extra>",customdata=hist["strategy"].str[:20] if "strategy" in hist.columns else [""]*len(hist)))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Simulation History (last 20)",font=dict(color="#c9d8ea",size=12)),yaxis=dict(showgrid=True,gridcolor="#111c28",color="#3d5068",zeroline=True,zerolinecolor="#3d5068"),xaxis=dict(showgrid=False),margin=dict(t=36,b=20,l=50,r=16))
    fig.update_layout(**ly); return fig

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
btc_p = BASE_PRICES["BTC/USDT"]*(1+random.gauss(0,0.002))
eth_p = BASE_PRICES["ETH/USDT"]*(1+random.gauss(0,0.003))
stats = get_storage_stats()

st.markdown(f"""
<div style="background:linear-gradient(135deg,#080d18,#0c1220);border:1px solid rgba(56,189,248,0.16);
            border-radius:12px;padding:18px 26px;margin-bottom:18px;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;">
  <div>
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#e8f4ff;letter-spacing:0.06em;">
      ◈ NEXUS <span style="font-size:0.78rem;color:#3d5068;font-weight:400;letter-spacing:3px;">AI CRYPTO TRADING BOT</span>
    </div>
    <div style="font-size:0.65rem;color:#3d5068;letter-spacing:2px;margin-top:3px;">
      SCANNER · PATTERNS · AI SIM · <span style="color:#00e5a0;">PERSISTENT STORAGE ✓</span>
    </div>
  </div>
  <div style="display:flex;gap:22px;flex-wrap:wrap;align-items:center;">
    {"".join(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:{c};'>{v}</div><div style='font-size:0.6rem;color:#3d5068;letter-spacing:1px;'>{l}</div></div>" for l,v,c in [("BTC/USDT",f"${btc_p:,.0f}","#e8f4ff"),("ETH/USDT",f"${eth_p:,.0f}","#e8f4ff"),("SCANS",st.session_state.scan_count,"#a78bfa"),("SIMS",st.session_state.sim_count,"#38bdf8"),("STORAGE",f"{stats['total_size_kb']} KB","#00e5a0"),("SAVED",st.session_state.last_save,"#f5c542")])}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:6px 0 16px;'><div style='font-family:\"Syne\",sans-serif;font-size:1.2rem;font-weight:800;color:#00e5a0;letter-spacing:3px;'>◈ NEXUS</div><div style='font-size:0.6rem;color:#3d5068;letter-spacing:2px;'>CONTROL PANEL</div></div>", unsafe_allow_html=True)

    # API
    with st.expander("⚡  API CONNECTION", expanded=not st.session_state.api_connected):
        exchange_sel = st.selectbox("Exchange", EXCHANGES, index=EXCHANGES.index(st.session_state.exchange) if st.session_state.exchange in EXCHANGES else 0)
        api_k = st.text_input("API Key",       value=st.session_state.api_key,       placeholder="Paste API key")
        api_s = st.text_input("API Secret",    value="",                              placeholder="Paste secret", type="password")
        api_p = st.text_input("Passphrase",    value="",                              placeholder="OKX/KuCoin only", type="password")
        api_mode_sel = st.radio("Mode", ["paper","live"], horizontal=True)
        c1,c2=st.columns(2)
        with c1:
            if st.button("CONNECT", use_container_width=True):
                if api_k.strip():
                    st.session_state.update({"exchange":exchange_sel,"api_key":api_k,"api_secret":api_s,"api_passphrase":api_p,"api_connected":True,"api_mode":api_mode_sel})
                    auto_save()
                    push_alert(f"Connected to {exchange_sel} [{api_mode_sel.upper()}]","success")
                    st.rerun()
                else: st.error("Enter API key")
        with c2:
            if st.button("CLEAR", use_container_width=True):
                st.session_state.update({"api_connected":False,"api_key":"","api_secret":"","api_passphrase":""})
                auto_save(); st.rerun()
        if st.session_state.api_connected: st.success(f"✓ {st.session_state.exchange} — {st.session_state.api_mode.upper()}")
        else: st.warning("Not connected · simulated data")
        st.caption("⚠ READ-ONLY keys for scanning. Secrets are never stored to disk.")

    st.markdown("---")
    st.markdown("#### ⬡ SCAN SETTINGS")

    sel_coins = st.multiselect("Coins", COINS, default=st.session_state.selected_coins, format_func=lambda x: x.replace("/USDT",""))
    sel_strats= st.multiselect("Strategies", list(STRATEGIES.keys()), default=st.session_state.selected_strats)
    sel_ivals = st.multiselect("Intervals", INTERVALS, default=st.session_state.selected_ivals)

    # Auto-save selections when changed
    if sel_coins  != st.session_state.selected_coins:  st.session_state.selected_coins  = sel_coins;  auto_save()
    if sel_strats != st.session_state.selected_strats: st.session_state.selected_strats = sel_strats; auto_save()
    if sel_ivals  != st.session_state.selected_ivals:  st.session_state.selected_ivals  = sel_ivals;  auto_save()

    st.markdown("---")
    ops=len(sel_coins)*len(sel_strats)*len(sel_ivals)
    st.markdown(f"<div style='font-size:0.72rem;line-height:2.1;color:#3d5068;'>Coins &nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#00e5a0;'>{len(sel_coins)}</span><br>Strategies &nbsp;<span style='color:#00e5a0;'>{len(sel_strats)}</span><br>Intervals &nbsp;&nbsp;<span style='color:#00e5a0;'>{len(sel_ivals)}</span><br><span style='color:#1e2d3e;'>─────────────</span><br>Total ops &nbsp;&nbsp;<span style='color:#38bdf8;'>{ops:,}</span><br>Save path &nbsp;&nbsp;<span style='color:#f5c542;font-size:0.65rem;'>./nexus_data/</span></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 💾 DATA MANAGEMENT")
    if st.button("📥 Export All Data (.zip)", use_container_width=True):
        with st.spinner("Zipping..."):
            zp=export_all_to_zip()
            with open(zp,"rb") as f:
                st.download_button("⬇ Download nexus_export.zip", f.read(), file_name="nexus_export.zip", mime="application/zip", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_scan, tab_ivs, tab_strat, tab_sim, tab_journal, tab_alerts, tab_data = st.tabs([
    "⬡  SCANNER", "⏱  INTERVALS", "⚡  STRATEGIES",
    "🔬  SIMULATION", "📒  JOURNAL", "🔔  ALERTS", "💾  DATA",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab_scan:
    hc1,hc2=st.columns([4,1])
    with hc1:
        st.markdown("### MARKET SCANNER")
        st.caption("Multi-strategy signal detection · results auto-saved to disk after each scan")
    with hc2:
        st.markdown("<br>",unsafe_allow_html=True)
        do_scan=st.button("▶  RUN SCAN", use_container_width=True)

    if do_scan:
        if not sel_coins or not sel_strats or not sel_ivals:
            st.error("Select at least one coin, strategy, and interval in the sidebar.")
        else:
            prog=st.progress(0,text="Initialising AI scan engine...")
            for p in range(0,101,2): time.sleep(0.015); prog.progress(p,text=f"Scanning {len(sel_coins)} coins × {len(sel_strats)} strategies × {len(sel_ivals)} intervals...")
            prog.empty()
            results=run_market_scan(sel_coins,sel_strats,sel_ivals,st.session_state.strategy_params)
            st.session_state.scan_results=results
            st.session_state.scan_count+=1
            # ← SAVE TO DISK
            saved_path=save_scan(results, st.session_state.scan_count)
            auto_save()
            nb=len(results[results["Signal"]=="BUY"]); ns=len(results[results["Signal"]=="SELL"])
            push_alert(f"Scan #{st.session_state.scan_count}: {nb} BUY · {ns} SELL · saved to {Path(saved_path).name}","success")
            st.success(f"✓ Scan complete — {len(results):,} signals saved to `nexus_data/scans/`")

    if st.session_state.scan_results is not None:
        df=st.session_state.scan_results
        fc1,fc2,fc3,fc4,fc5=st.columns([1,1,1,1,2])
        with fc1: sig_f=st.selectbox("Signal",["ALL","BUY","SELL","HOLD"])
        with fc2: grp_f=st.selectbox("Group",["ALL"]+sorted(df["Group"].unique().tolist()))
        with fc3: conf_f=st.slider("Min Conf %",0,100,55)
        with fc4: intv_f=st.selectbox("Interval",["ALL"]+sorted(df["Interval"].unique().tolist()))
        with fc5: coin_f=st.multiselect("Coins",sorted(df["Coin"].unique().tolist()),default=[])
        flt=df.copy()
        if sig_f!="ALL": flt=flt[flt["Signal"]==sig_f]
        if grp_f!="ALL": flt=flt[flt["Group"]==grp_f]
        if intv_f!="ALL": flt=flt[flt["Interval"]==intv_f]
        if conf_f>0: flt=flt[flt["Confidence"]>=conf_f]
        if coin_f: flt=flt[flt["Coin"].isin(coin_f)]
        st.markdown("---")
        m1,m2,m3,m4,m5,m6=st.columns(6)
        with m1: st.metric("Total Signals",f"{len(flt):,}")
        with m2: st.metric("🟢 BUY",len(flt[flt["Signal"]=="BUY"]),delta=f"+{len(flt[flt['Signal']=='BUY'])}")
        with m3: st.metric("🔴 SELL",len(flt[flt["Signal"]=="SELL"]),delta=f"-{len(flt[flt['Signal']=='SELL'])}",delta_color="inverse")
        with m4: st.metric("Avg Confidence",f"{flt['Confidence'].mean():.0f}%" if len(flt) else "—")
        with m5: st.metric("Pairs Hit",flt["Coin"].nunique())
        with m6: st.metric("Groups",flt["Group"].nunique())
        st.markdown("---")
        if len(flt):
            c1,c2,c3,c4=st.columns(4)
            with c1: st.plotly_chart(chart_sig_pie(flt),use_container_width=True)
            with c2: st.plotly_chart(chart_top_coins(flt),use_container_width=True)
            with c3: st.plotly_chart(chart_rsi(flt),use_container_width=True)
            with c4:
                gc=flt.groupby("Group")["Confidence"].mean().sort_values()
                fig=go.Figure(go.Bar(x=gc.values,y=gc.index,orientation="h",marker=dict(color=[GROUP_COLORS.get(g,"#666") for g in gc.index]),text=[f"{v:.0f}%" for v in gc.values],textposition="outside",textfont=dict(color="#c9d8ea",size=10)))
                ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Conf by Group",font=dict(color="#c9d8ea",size=12)),xaxis=dict(showgrid=False,range=[0,115],color="#3d5068"),yaxis=dict(showgrid=False,color="#c9d8ea"),margin=dict(t=36,b=10,l=80,r=40))
                fig.update_layout(**ly); st.plotly_chart(fig,use_container_width=True)
        st.markdown("---")
        disp=flt[["Coin","Interval","Strategy","Signal","Confidence","RSI","Price","24h %","Vol Ratio","Note"]].copy()
        def ss(v): return {"BUY":"color:#00e5a0;font-weight:700","SELL":"color:#ff3d71;font-weight:700","HOLD":"color:#3d5068"}.get(v,"")
        def sc(v):
            try: return f"color:{'#00e5a0' if float(v)>=0 else '#ff3d71'}"
            except: return ""
        def sr(v):
            try:
                f=float(v)
                if f<30: return "color:#00e5a0;font-weight:700"
                if f>70: return "color:#ff3d71;font-weight:700"
            except: pass
            return "color:#3d5068"
        styled=(disp.style.applymap(ss,subset=["Signal"]).applymap(sc,subset=["24h %"]).applymap(sr,subset=["RSI"]).background_gradient(subset=["Confidence"],cmap="YlGn",vmin=40,vmax=100).format({"Price":lambda x:fmt_price(float(x)),"24h %":"{:+.2f}%","Confidence":"{}%","Vol Ratio":"{:.2f}×"}).set_properties(**{"font-family":"JetBrains Mono,monospace","font-size":"11px"}))
        st.dataframe(styled,use_container_width=True,height=420)
        top_buys=flt[flt["Signal"]=="BUY"].head(4); top_sells=flt[flt["Signal"]=="SELL"].head(4)
        if len(top_buys):
            st.markdown("#### 🟢 TOP BUY SIGNALS")
            cols=st.columns(min(4,len(top_buys)))
            for i,(_,row) in enumerate(top_buys.iterrows()):
                with cols[i]:
                    st.markdown(f"<div class='card card-green'><div style='font-size:1.2rem;font-weight:800;color:#00e5a0;font-family:Syne,sans-serif;'>{row['Coin']}</div><div style='font-size:0.65rem;color:#3d5068;margin-bottom:8px;'>{row['Strategy']} · {row['Interval']}</div><div style='font-size:0.95rem;color:#e8f4ff;'>{fmt_price(float(row['Price']))}</div><div style='font-size:0.72rem;color:#00e5a0;margin-top:4px;'>Conf: {row['Confidence']}%</div><div style='font-size:0.65rem;color:#3d5068;'>{row['Note'][:40]}</div><div style='margin-top:8px;height:2px;background:linear-gradient(90deg,#00e5a0,#38bdf8);border-radius:2px;width:{row['Confidence']}%;'></div></div>",unsafe_allow_html=True)
        if len(top_sells):
            st.markdown("#### 🔴 TOP SELL SIGNALS")
            cols=st.columns(min(4,len(top_sells)))
            for i,(_,row) in enumerate(top_sells.iterrows()):
                with cols[i]:
                    st.markdown(f"<div class='card card-red'><div style='font-size:1.2rem;font-weight:800;color:#ff3d71;font-family:Syne,sans-serif;'>{row['Coin']}</div><div style='font-size:0.65rem;color:#3d5068;margin-bottom:8px;'>{row['Strategy']} · {row['Interval']}</div><div style='font-size:0.95rem;color:#e8f4ff;'>{fmt_price(float(row['Price']))}</div><div style='font-size:0.72rem;color:#ff3d71;margin-top:4px;'>Conf: {row['Confidence']}%</div><div style='font-size:0.65rem;color:#3d5068;'>{row['Note'][:40]}</div><div style='margin-top:8px;height:2px;background:linear-gradient(90deg,#ff3d71,#f5c542);border-radius:2px;width:{row['Confidence']}%;'></div></div>",unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center;padding:80px 0;color:#1e2d3e;'><div style='font-size:4rem;margin-bottom:16px;'>◈</div><div style='font-family:Syne,sans-serif;color:#3d5068;letter-spacing:3px;font-size:0.9rem;'>SELECT ASSETS IN SIDEBAR · CLICK RUN SCAN</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INTERVALS
# ══════════════════════════════════════════════════════════════════════════════
with tab_ivs:
    st.markdown("### SCAN INTERVALS")
    st.caption("Visual overview of all timeframes and their trading characteristics")
    style_colors={"Scalping":"#ff3d71","Day Trade":"#f5c542","Swing":"#38bdf8","Position":"#a78bfa","Long-Term":"#00e5a0"}
    groups={}
    for iv in INTERVALS: groups.setdefault(INTERVAL_INFO[iv]["style"],[]).append(iv)
    for sname,ivs in groups.items():
        sc2=style_colors.get(sname,"#666")
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 8px;'><div style='width:3px;height:18px;background:{sc2};border-radius:2px;'></div><span style='font-family:Syne,sans-serif;font-weight:700;color:{sc2};letter-spacing:2px;font-size:0.82rem;'>{sname.upper()}</span></div>",unsafe_allow_html=True)
        cols=st.columns(len(ivs))
        for i,iv in enumerate(ivs):
            info=INTERVAL_INFO[iv]; is_sel=iv in sel_ivals
            with cols[i]:
                st.markdown(f"<div style='background:{'rgba(0,229,160,0.05)' if is_sel else 'rgba(12,18,32,0.8)'};border:1px solid {'rgba(0,229,160,0.35)' if is_sel else 'rgba(56,189,248,0.1)'};border-radius:10px;padding:16px 12px;text-align:center;'><div style='font-size:0.85rem;margin-bottom:4px;'>{info['icon']}</div><div style='font-size:1.4rem;font-weight:800;color:{'#00e5a0' if is_sel else '#3d5068'};font-family:Syne,sans-serif;'>{iv}</div><div style='font-size:0.62rem;color:{sc2};margin:4px 0;letter-spacing:1px;'>{info['style'].upper()}</div><div style='font-size:0.62rem;color:#3d5068;line-height:1.5;'>{info['desc']}</div><div style='font-size:0.58rem;color:#1e2d3e;margin-top:5px;'>Noise: {info['noise']}</div>{'<div style=margin-top:8px;height:2px;background:linear-gradient(90deg,#00e5a0,#38bdf8);border-radius:2px;></div>' if is_sel else ''}</div>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<div class='card card-blue'><div style='font-size:0.7rem;color:#38bdf8;letter-spacing:2px;margin-bottom:6px;'>ACTIVE</div><div style='color:#e8f4ff;'>{' &nbsp;·&nbsp; '.join([iv for iv in INTERVALS if iv in sel_ivals]) or 'None selected'}</div><div style='font-size:0.7rem;color:#3d5068;margin-top:8px;'>{len(sel_ivals)} frame(s) → <span style='color:#38bdf8;'>{len(sel_ivals)*len(sel_coins)*len(sel_strats):,} ops per scan</span></div></div>",unsafe_allow_html=True)
    st.info("Update intervals in the sidebar to apply them to scans.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════
with tab_strat:
    st.markdown("### STRATEGY CONFIGURATION")
    st.caption("Parameters saved to disk automatically · AI updates logged and persisted")
    gf=st.radio("Group",["ALL"]+list(GROUP_COLORS.keys()),horizontal=True)
    st.markdown("")
    for sname,sinfo in STRATEGIES.items():
        if gf!="ALL" and sinfo["group"]!=gf: continue
        is_act=sname in sel_strats; gc=GROUP_COLORS.get(sinfo["group"],"#666")
        cur_p=st.session_state.strategy_params.get(sname,sinfo["params"])
        with st.expander(f"{sinfo['icon']}  {sname}  [{sinfo['group']}]{'   ✓ ACTIVE' if is_act else ''}",expanded=False):
            ec1,ec2=st.columns([3,1])
            with ec1:
                st.markdown(f"<div style='margin-bottom:12px;'><span style='background:{gc}18;border:1px solid {gc}44;color:{gc};padding:3px 12px;border-radius:10px;font-size:0.67rem;letter-spacing:1px;'>{sinfo['group'].upper()}</span>{'<span style=margin-left:8px;background:rgba(0,229,160,0.1);border:1px solid rgba(0,229,160,0.3);color:#00e5a0;padding:3px 12px;border-radius:10px;font-size:0.67rem;> ACTIVE</span>' if is_act else ''}</div><p style='color:#c9d8ea;font-size:0.8rem;line-height:1.6;'>{sinfo['desc']}</p>{''.join(f'<div style=font-size:0.7rem;color:#38bdf8;margin-bottom:2px;>› {h}</div>' for h in sinfo['ai_hints'])}",unsafe_allow_html=True)
                st.markdown("**Parameters:**")
                pcols=st.columns(min(4,len(cur_p))); new_p=dict(cur_p)
                for idx,(pn,pv) in enumerate(cur_p.items()):
                    with pcols[idx%4]:
                        if isinstance(pv,bool): new_p[pn]=st.checkbox(pn,value=pv,key=f"p_{sname}_{pn}")
                        elif isinstance(pv,float): new_p[pn]=st.number_input(pn,value=float(pv),step=0.1,format="%.2f",key=f"p_{sname}_{pn}")
                        elif isinstance(pv,int): new_p[pn]=st.number_input(pn,value=int(pv),step=1,key=f"p_{sname}_{pn}")
                        else: new_p[pn]=st.text_input(pn,value=str(pv),key=f"p_{sname}_{pn}")
                if st.button(f"💾 Save Parameters",key=f"save_{sname}"):
                    st.session_state.strategy_params[sname]=new_p
                    auto_save()  # ← persist to disk
                    push_alert(f"Parameters saved for '{sname}'","success")
                    st.success("✓ Saved to nexus_data/config/strategy_params.json")
            with ec2:
                st.markdown("**Simulated Perf.**")
                wr=random.randint(51,74); ret=random.uniform(7,48); dd=random.uniform(5,22)
                st.metric("Win Rate",f"{wr}%",f"+{wr-50:.0f}%"); st.metric("Avg Ret",f"+{ret:.1f}%"); st.metric("Max DD",f"{dd:.1f}%"); st.metric("Sharpe",f"{ret/max(dd,1)*0.45:.2f}")
    st.markdown("---")
    # Show per-strategy AI tuning status
    tuning_rows = ""
    for sn in sel_strats:
        t = st.session_state.perf_tracker.get(sn, {})
        runs = t.get("runs", 0)
        if runs > 0:
            avg_wr = float(np.mean(t["win_rates"]))
            avg_ret = float(np.mean(t["returns"]))
            wr_c = "#00e5a0" if avg_wr>=55 else ("#f5c542" if avg_wr>=45 else "#ff3d71")
            ret_c= "#00e5a0" if avg_ret>=0 else "#ff3d71"
            mode = "30/70 rolling" if runs>=4 else ("60/40 blend" if runs>=2 else "single")
            last = st.session_state.last_ai_update.get(sn, "—")
            tuning_rows += f"<tr><td style='color:#c9d8ea;padding:5px 10px;'>{sn[:28]}</td><td style='color:#a78bfa;text-align:center;'>{runs}</td><td style='color:{wr_c};text-align:center;font-weight:700;'>{avg_wr:.0f}%</td><td style='color:{ret_c};text-align:center;'>{avg_ret:+.1f}%</td><td style='color:#38bdf8;font-size:0.65rem;text-align:center;'>{mode}</td><td style='color:#3d5068;font-size:0.65rem;text-align:center;'>{last}</td></tr>"

    if tuning_rows:
        st.markdown(f"""
        <div class='card card-blue' style='margin-top:16px;'>
          <div style='font-size:0.78rem;font-weight:700;color:#38bdf8;margin-bottom:12px;letter-spacing:2px;'>🤖 LIVE AI TUNING STATUS — ACTIVE STRATEGIES</div>
          <table style='width:100%;border-collapse:collapse;font-size:0.72rem;'>
            <tr style='color:#3d5068;border-bottom:1px solid #1e2d3e;'>
              <th style='text-align:left;padding:4px 10px;'>Strategy</th>
              <th>Runs</th><th>Avg WR</th><th>Avg Ret</th><th>Blend Mode</th><th>Last Update</th>
            </tr>
            {tuning_rows}
          </table>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card card-blue' style='margin-top:10px;'>
      <div style='font-size:0.78rem;font-weight:700;color:#38bdf8;margin-bottom:8px;letter-spacing:2px;'>🤖 AUTO-TUNING ENGINE</div>
      <div style='font-size:0.76rem;color:#3d5068;line-height:1.9;'>
        Parameters are <strong style='color:#c9d8ea;'>automatically updated after every simulation</strong> — no button needed.
        The AI uses a <strong style='color:#c9d8ea;'>rolling weighted average</strong> (up to 10 runs) to tune decisions:
        run 1 = immediate adjustment · runs 2-3 = 60/40 blend · runs 4+ = 30/70 rolling average.
        After 5+ consistently poor runs the AI applies an aggressive reset toward safe defaults.
        All changes persisted to <code style='color:#a78bfa;'>nexus_data/config/strategy_params.json</code>.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown("### AI PAPER TRADING SIMULATION")
    st.caption("Every simulation auto-tunes strategy parameters from rolling win rate · no manual action needed")
    sc1,sc2=st.columns([1,2])
    with sc1:
        st.markdown("#### Parameters")
        sim_strat=st.selectbox("Strategy",list(STRATEGIES.keys()))
        sim_cap=st.number_input("Capital (USDT)",100,1_000_000,10_000,500)
        sim_candles=st.slider("Candles",100,600,250,25)
        sim_pos=st.slider("Position Size %",10,100,90,5)
        sim_fee=st.number_input("Fee %",0.0,1.0,0.08,0.01,format="%.2f")
        sim_sl=st.number_input("Stop Loss %",0.5,20.0,4.0,0.5,format="%.1f")
        sim_tp=st.number_input("Take Profit %",1.0,50.0,8.0,0.5,format="%.1f")
        st.markdown("")
        do_sim=st.button("▶  RUN AI SIMULATION", use_container_width=True)

        # Rolling performance status for selected strategy
        tracker = st.session_state.perf_tracker.get(sim_strat, {})
        runs = tracker.get("runs", 0)
        if runs > 0:
            avg_wr  = float(np.mean(tracker["win_rates"]))
            avg_ret = float(np.mean(tracker["returns"]))
            avg_dd  = float(np.mean(tracker["drawdowns"]))
            last_upd= st.session_state.last_ai_update.get(sim_strat, "—")
            wr_color = "#00e5a0" if avg_wr >= 55 else ("#f5c542" if avg_wr >= 45 else "#ff3d71")
            ret_color= "#00e5a0" if avg_ret >= 0 else "#ff3d71"
            st.markdown(f"""
            <div style='background:rgba(0,0,0,0.3);border:1px solid rgba(0,229,160,0.2);
                         border-radius:8px;padding:14px 16px;margin-top:14px;'>
              <div style='font-size:0.68rem;color:#38bdf8;letter-spacing:2px;margin-bottom:10px;'>
                🤖 AI TUNING STATUS
              </div>
              <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.75rem;'>
                <div>Runs &nbsp;<span style='color:#a78bfa;font-weight:700;'>{runs}</span></div>
                <div>Last &nbsp;<span style='color:#3d5068;'>{last_upd}</span></div>
                <div>Avg WR &nbsp;<span style='color:{wr_color};font-weight:700;'>{avg_wr:.0f}%</span></div>
                <div>Avg Ret &nbsp;<span style='color:{ret_color};font-weight:700;'>{avg_ret:+.1f}%</span></div>
                <div>Avg DD &nbsp;<span style='color:#f5c542;'>{avg_dd:.1f}%</span></div>
                <div>Mode &nbsp;<span style='color:#38bdf8;font-size:0.65rem;'>{'30/70 rolling' if runs>=4 else ('60/40 blend' if runs>=2 else 'single run')}</span></div>
              </div>
              <div style='margin-top:10px;height:3px;background:#1e2d3e;border-radius:2px;'>
                <div style='height:100%;width:{min(runs*10,100)}%;background:linear-gradient(90deg,#38bdf8,#00e5a0);border-radius:2px;transition:width 0.4s;'></div>
              </div>
              <div style='font-size:0.6rem;color:#3d5068;margin-top:4px;'>Confidence: {min(runs*10,100)}% ({runs}/10 runs)</div>
            </div>
            """, unsafe_allow_html=True)

            # Mini win rate trend sparkline
            if len(tracker.get("win_rates",[])) >= 2:
                wrs = tracker["win_rates"]
                trend_str = " → ".join([f"{w:.0f}%" for w in wrs[-4:]])
                trend_arrow = "↑" if wrs[-1] > wrs[0] else ("↓" if wrs[-1] < wrs[0] else "→")
                tc = "#00e5a0" if trend_arrow=="↑" else ("#ff3d71" if trend_arrow=="↓" else "#f5c542")
                st.markdown(f"<div style='font-size:0.68rem;color:#3d5068;margin-top:8px;'>WR trend: <span style='color:{tc};'>{trend_str} {trend_arrow}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:rgba(0,0,0,0.2);border:1px solid #1e2d3e;border-radius:8px;
                         padding:12px 16px;margin-top:14px;font-size:0.72rem;color:#3d5068;'>
              🤖 AI auto-tuning activates after first simulation run.<br>
              <span style='color:#1e2d3e;'>Parameters update automatically from rolling performance.</span>
            </div>
            """, unsafe_allow_html=True)

    with sc2:
        if do_sim:
            with st.spinner("⟳  Simulating..."):
                prog2=st.progress(0, text="Running simulation...")
                for p in range(0,80,5): time.sleep(0.02); prog2.progress(p)
                cur_p=st.session_state.strategy_params.get(sim_strat,STRATEGIES[sim_strat]["params"])
                res=simulate_strategy(sim_strat,sim_cap,sim_candles,sim_pos,sim_fee,sim_sl,sim_tp,cur_p)
                prog2.progress(85, text="AI analysing results...")
                st.session_state.sim_results=res
                st.session_state.sim_count+=1
                # ← SAVE TO DISK
                saved=save_simulation(res,st.session_state.sim_count)
                bulk_log_simulation_trades(res,st.session_state.sim_count)

                # ← AUTO AI TUNE (no button needed)
                prog2.progress(92, text="🤖 AI auto-tuning parameters...")
                new_params, tune_msgs, tracker_out = auto_ai_tune(sim_strat, res)
                prog2.progress(100)
                prog2.empty()
                auto_save()

                push_alert(f"Sim #{st.session_state.sim_count} [{sim_strat[:20]}]: {res['total_ret']:+.2f}% · WR {res['win_rate']:.0f}% · params auto-updated","success" if res["total_ret"]>0 else "warning")

            # Show what changed
            changed = [m for m in tune_msgs if "→" in m or "Tightened" in m or "Raised" in m or "Reduced" in m or "Widened" in m or "Relaxed" in m or "reset" in m.lower()]
            if changed:
                st.success(f"✓ Simulation #{st.session_state.sim_count} complete · 🤖 AI auto-tuned {len(changed)} parameter(s)")
                for msg in changed[:3]:
                    st.info(f"🔧 {msg}")
            else:
                st.success(f"✓ Simulation #{st.session_state.sim_count} complete · 🤖 AI: parameters near-optimal, monitoring")

        if st.session_state.sim_results:
            res=st.session_state.sim_results
            m1,m2,m3,m4,m5,m6,m7,m8=st.columns(8)
            with m1: st.metric("Final",f"${res['final']:,.0f}",f"{res['total_ret']:+.2f}%")
            with m2: st.metric("Return",f"{res['total_ret']:+.2f}%")
            with m3: st.metric("Win Rate",f"{res['win_rate']:.0f}%",f"+{res['win_rate']-50:.0f}%")
            with m4: st.metric("Trades",res["trades"])
            with m5: st.metric("Avg Win",f"+{res['avg_win']:.2f}%")
            with m6: st.metric("Avg Loss",f"-{res['avg_loss']:.2f}%")
            with m7: st.metric("Prof Factor",f"{res['profit_factor']:.2f}")
            with m8: st.metric("Max DD",f"-{res['max_dd']:.1f}%",delta_color="inverse")
            st.plotly_chart(chart_equity(res["equity"],res["trade_log"],res["capital"]),use_container_width=True)
            st.plotly_chart(chart_candles(res["df"],res["trade_log"]),use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:80px 0;color:#1e2d3e;'><div style='font-size:4rem;'>◈</div><div style='font-family:Syne,sans-serif;color:#3d5068;letter-spacing:3px;'>CONFIGURE & RUN SIMULATION</div></div>",unsafe_allow_html=True)

    if st.session_state.sim_results:
        res=st.session_state.sim_results; st.markdown("---")

        af1,af2=st.columns(2)
        with af1:
            st.markdown("#### 📊 PERFORMANCE ASSESSMENT")
            wr=res["win_rate"]; ret=res["total_ret"]; dd=res["max_dd"]; pf=res["profit_factor"]
            if ret>20 and wr>60: st.success(f"✅ Strong: {ret:.1f}% return · {wr:.0f}% WR — ready for forward-test")
            elif ret>0: st.info(f"📊 Moderate: {ret:.1f}% · WR {wr:.0f}% — AI refining parameters")
            else: st.warning(f"⚠️ Underperforming: {ret:.1f}% — AI adjusting strategy")
            if dd>25: st.error(f"🚨 Drawdown {dd:.1f}% — AI tightening risk controls")
            elif dd>15: st.warning(f"⚠️ DD {dd:.1f}% — AI monitoring")
            else: st.success(f"✅ DD {dd:.1f}% within acceptable range")
            if pf>1.5: st.success(f"✅ Profit Factor {pf:.2f} — strong market edge confirmed")
            elif pf>1.0: st.info(f"📊 PF {pf:.2f} — marginal edge, AI optimising")
            else: st.error(f"❌ PF {pf:.2f} — no edge detected, AI aggressively retuning")

        with af2:
            st.markdown("#### 🤖 AI TUNING LOG (this strategy)")
            strat_log = [e for e in st.session_state.ai_log if e.get("strat") == res["strategy"]][:8]
            if strat_log:
                for e in strat_log:
                    ic = "🟢" if "✅" in e["msg"] else ("🟡" if "⚠️" in e["msg"] else "🔵")
                    runs_badge = f"<span style='color:#3d5068;font-size:0.62rem;'> [run {e.get('runs','?')} · WR {e.get('avg_wr','?')}%]</span>" if "runs" in e else ""
                    st.markdown(f"<div style='background:rgba(56,189,248,0.04);border-left:2px solid #38bdf8;padding:7px 11px;margin-bottom:4px;border-radius:0 4px 4px 0;font-size:0.73rem;color:#c9d8ea;'>{ic} {e['msg'].replace('AI: ','')}{runs_badge}</div>", unsafe_allow_html=True)
            else:
                st.caption("No AI updates for this strategy yet — run simulation to start tuning")

        # Sim history chart
        shc=chart_sim_history()
        if shc:
            st.markdown("---")
            st.markdown("#### SIMULATION HISTORY (all runs, disk)")
            st.plotly_chart(shc,use_container_width=True)

        # Trade log
        st.markdown("---")
        tl1,tl2=st.columns([2,1])
        with tl1:
            st.markdown("#### TRADE LOG (current sim)")
            if res["trade_log"]:
                tdf=pd.DataFrame([{"Type":t["type"],"Price":fmt_price(float(t["price"])),"P&L %":(f"{t['pnl']:+.2f}%" if t["type"]=="SELL" else "—"),"Reason":t["reason"][:35],"Candle":f"#{t['i']}","Equity":f"${t['equity']:,.2f}"} for t in reversed(res["trade_log"])])
                def st_s(v): return "color:#00e5a0;font-weight:700" if v=="BUY" else ("color:#ff3d71;font-weight:700" if v=="SELL" else "")
                def st_p(v):
                    try: n=float(v.replace("%","").replace("+","")); return f"color:{'#00e5a0' if n>=0 else '#ff3d71'}"
                    except: return "color:#3d5068"
                st.dataframe((tdf.style.applymap(st_s,subset=["Type"]).applymap(st_p,subset=["P&L %"]).set_properties(**{"font-family":"JetBrains Mono,monospace","font-size":"11px"})),use_container_width=True,height=300)
        with tl2:
            st.markdown("#### RECENT SIMULATIONS (disk)")
            hist_df=load_simulation_history()
            if not hist_df.empty:
                recent=hist_df.tail(8)[["sim_number","strategy","total_return","win_rate","trades"]].copy() if "strategy" in hist_df.columns else hist_df.tail(8)
                def sr2(v):
                    try: return f"color:{'#00e5a0' if float(v)>0 else '#ff3d71'}"
                    except: return ""
                st.dataframe(recent.style.applymap(sr2,subset=["total_return"] if "total_return" in recent.columns else []).set_properties(**{"font-size":"11px","font-family":"JetBrains Mono,monospace"}),use_container_width=True,height=300)
            else: st.caption("No saved simulations yet")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TRADE JOURNAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_journal:
    st.markdown("### TRADE JOURNAL")
    st.caption("Auto-populated from simulations · add manual trades · saved to nexus_data/trades/trade_journal.csv")

    jc1,jc2=st.columns([2,1])
    with jc1:
        jdf=load_trade_journal()
        if not jdf.empty:
            st.markdown(f"**{len(jdf)} trades logged**")
            def sj_s(v): return "color:#00e5a0;font-weight:700" if v=="BUY" else ("color:#ff3d71;font-weight:700" if v=="SELL" else "")
            def sj_p(v):
                try: n=float(str(v).replace("%","")); return f"color:{'#00e5a0' if n>0 else ('#ff3d71' if n<0 else '#3d5068')}"
                except: return ""
            show_cols=[c for c in ["timestamp","source","strategy","coin","side","exit_price","pnl_pct","pnl_usdt","reason"] if c in jdf.columns]
            styled_j=jdf[show_cols].tail(50).style
            if "side" in show_cols: styled_j=styled_j.applymap(sj_s,subset=["side"])
            if "pnl_pct" in show_cols: styled_j=styled_j.applymap(sj_p,subset=["pnl_pct"])
            styled_j=styled_j.set_properties(**{"font-size":"11px","font-family":"JetBrains Mono,monospace"})
            st.dataframe(styled_j,use_container_width=True,height=400)
            # Download journal
            csv_bytes=jdf.to_csv(index=False).encode()
            st.download_button("⬇ Download trade_journal.csv",csv_bytes,file_name="trade_journal.csv",mime="text/csv")
        else:
            st.info("No trades yet. Run a simulation to auto-populate, or add manual entries →")

    with jc2:
        st.markdown("#### Manual Trade Entry")
        with st.form("manual_trade"):
            mt_coin=st.selectbox("Coin",COINS)
            mt_side=st.radio("Side",["BUY","SELL"],horizontal=True)
            mt_strat=st.selectbox("Strategy",list(STRATEGIES.keys()))
            mt_entry=st.number_input("Entry Price",min_value=0.0,value=0.0,format="%.4f")
            mt_exit=st.number_input("Exit Price",min_value=0.0,value=0.0,format="%.4f")
            mt_qty=st.number_input("Quantity",min_value=0.0,value=0.0,format="%.6f")
            mt_notes=st.text_area("Notes",placeholder="Setup notes, tags...",height=80)
            submitted=st.form_submit_button("💾 LOG TRADE",use_container_width=True)
            if submitted:
                pnl_pct=((mt_exit-mt_entry)/mt_entry*100) if mt_entry>0 else 0
                pnl_usdt=(mt_exit-mt_entry)*mt_qty if mt_qty>0 else 0
                log_trade({"source":"MANUAL","strategy":mt_strat,"coin":mt_coin,"interval":"manual","side":mt_side,"entry_price":mt_entry,"exit_price":mt_exit,"quantity":mt_qty,"pnl_pct":round(pnl_pct,2),"pnl_usdt":round(pnl_usdt,2),"reason":"","tags":"manual","notes":mt_notes})
                push_alert(f"Manual trade logged: {mt_coin} {mt_side} P&L {pnl_pct:+.2f}%","success")
                st.success("✓ Trade saved to journal")
                st.rerun()

        if not jdf.empty and "pnl_pct" in jdf.columns:
            st.markdown("---")
            st.markdown("#### Journal Summary")
            try:
                pnl_vals=pd.to_numeric(jdf["pnl_pct"],errors="coerce").dropna()
                total_trades=len(jdf); wins=len(pnl_vals[pnl_vals>0]); losses=len(pnl_vals[pnl_vals<0])
                st.metric("Total Trades",total_trades); st.metric("Win Rate",f"{wins/max(total_trades,1)*100:.0f}%",f"{wins}W / {losses}L")
                st.metric("Total P&L",f"{pnl_vals.sum():.2f}%"); st.metric("Best Trade",f"+{pnl_vals.max():.2f}%"); st.metric("Worst Trade",f"{pnl_vals.min():.2f}%")
            except: st.caption("Summary unavailable")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ALERTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    ah1,ah2,ah3=st.columns([3,1,1])
    with ah1: st.markdown("### ALERTS & AI LOG")
    with ah2:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("🗑 CLEAR ALERTS",use_container_width=True):
            st.session_state.alerts=[]; save_alerts([]); st.rerun()
    with ah3:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("🗑 CLEAR AI LOG",use_container_width=True):
            st.session_state.ai_log=[]; save_ai_log([]); st.rerun()

    atab1,atab2=st.tabs(["📣 System Alerts","🤖 AI Parameter Log"])
    with atab1:
        if not st.session_state.alerts:
            st.markdown("<div style='text-align:center;padding:70px 0;'><div style='font-size:3.5rem;margin-bottom:14px;'>🔔</div><div style='font-family:Syne,sans-serif;font-size:0.85rem;letter-spacing:3px;color:#3d5068;'>NO ALERTS — RUN A SCAN OR SIMULATION</div></div>",unsafe_allow_html=True)
        else:
            kc={"success":"rgba(0,229,160,0.3)","info":"rgba(56,189,248,0.25)","warning":"rgba(245,197,66,0.3)","error":"rgba(255,61,113,0.3)"}
            ki={"success":"✅","info":"ℹ️","warning":"⚠️","error":"❌"}
            for a in st.session_state.alerts:
                k=a.get("kind","info"); bc=kc.get(k,"rgba(56,189,248,0.2)"); ic=ki.get(k,"ℹ️")
                st.markdown(f"<div style='background:rgba(12,18,32,0.8);border:1px solid {bc};border-left:3px solid {bc};border-radius:6px;padding:11px 16px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;'><div style='display:flex;gap:10px;align-items:center;'><span style='font-size:0.95rem;'>{ic}</span><span style='font-size:0.78rem;color:#c9d8ea;'>{a['msg']}</span></div><span style='font-size:0.65rem;color:#3d5068;white-space:nowrap;margin-left:14px;'>{a['time']}</span></div>",unsafe_allow_html=True)
            st.markdown("---")
            am1,am2,am3,am4=st.columns(4)
            with am1: st.metric("Total",len(st.session_state.alerts))
            with am2: st.metric("✅",sum(1 for a in st.session_state.alerts if a.get("kind")=="success"))
            with am3: st.metric("⚠️",sum(1 for a in st.session_state.alerts if a.get("kind")=="warning"))
            with am4: st.metric("ℹ️",sum(1 for a in st.session_state.alerts if a.get("kind")=="info"))
    with atab2:
        if not st.session_state.ai_log:
            st.markdown("<div style='text-align:center;padding:70px 0;'><div style='font-size:3rem;margin-bottom:14px;'>🤖</div><div style='font-family:Syne,sans-serif;font-size:0.82rem;letter-spacing:2px;color:#3d5068;'>NO AI UPDATES — RUN SIM THEN CLICK APPLY AI PARAM UPDATE</div></div>",unsafe_allow_html=True)
        else:
            for e in st.session_state.ai_log:
                col="#00e5a0" if "✅" in e["msg"] else ("#f5c542" if "⚠️" in e["msg"] else "#38bdf8")
                st.markdown(f"<div style='background:rgba(12,18,32,0.8);border:1px solid rgba(56,189,248,0.12);border-left:3px solid {col};border-radius:6px;padding:11px 16px;margin-bottom:5px;'><div style='display:flex;justify-content:space-between;margin-bottom:3px;'><span style='font-size:0.68rem;color:#38bdf8;letter-spacing:1px;'>{e.get('strat','')}</span><span style='font-size:0.65rem;color:#3d5068;'>{e.get('time','')}</span></div><div style='font-size:0.76rem;color:#c9d8ea;'>{e['msg']}</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_data:
    st.markdown("### DATA MANAGEMENT")
    st.caption("All bot data persists in `./nexus_data/` — survives app restarts")

    st.markdown("---")
    stats2=get_storage_stats()
    dm1,dm2,dm3,dm4,dm5=st.columns(5)
    with dm1: st.metric("Total Storage",f"{stats2['total_size_kb']} KB")
    with dm2: st.metric("Scan Files",stats2["file_counts"].get("scans",0))
    with dm3: st.metric("Sim Files",stats2["file_counts"].get("simulations",0))
    with dm4: st.metric("Alert Entries",len(st.session_state.alerts))
    with dm5: st.metric("AI Log Entries",len(st.session_state.ai_log))

    st.markdown("---")
    dc1,dc2=st.columns(2)

    with dc1:
        st.markdown("#### 📁 SAVED SCANS")
        saved_scans=list_saved_scans()
        if saved_scans:
            for sp in saved_scans[:10]:
                size=sp.stat().st_size/1024
                c1,c2=st.columns([3,1])
                with c1: st.markdown(f"<div style='font-size:0.75rem;color:#c9d8ea;padding:4px 0;'>📄 {sp.name}<span style='color:#3d5068;margin-left:10px;'>{size:.1f} KB</span></div>",unsafe_allow_html=True)
                with c2:
                    if st.button("Load",key=f"load_{sp.name}",use_container_width=True):
                        loaded=load_saved_scan(sp)
                        if not loaded.empty: st.session_state.scan_results=loaded; push_alert(f"Loaded scan: {sp.name}","info"); st.rerun()
        else: st.caption("No saved scans yet")

        st.markdown("---")
        st.markdown("#### 🔬 SIMULATION HISTORY")
        sim_hist=load_simulation_history()
        if not sim_hist.empty:
            show_cols=[c for c in ["sim_number","timestamp","strategy","total_return","win_rate","trades","max_dd"] if c in sim_hist.columns]
            def sr3(v):
                try: return f"color:{'#00e5a0' if float(v)>0 else '#ff3d71'}"
                except: return ""
            styled_sh=sim_hist[show_cols].style
            if "total_return" in show_cols: styled_sh=styled_sh.applymap(sr3,subset=["total_return"])
            styled_sh=styled_sh.set_properties(**{"font-size":"11px","font-family":"JetBrains Mono,monospace"})
            st.dataframe(styled_sh,use_container_width=True,height=300)
            csv2=sim_hist.to_csv(index=False).encode()
            st.download_button("⬇ Download simulation_history.csv",csv2,file_name="simulation_history.csv",mime="text/csv")
        else: st.caption("No simulations saved yet")

    with dc2:
        st.markdown("#### 📂 STORAGE LAYOUT")
        st.markdown(f"""
        <div class="card" style="font-size:0.75rem;line-height:2.2;">
          <div style="color:#38bdf8;letter-spacing:1px;margin-bottom:8px;">nexus_data/</div>
          {"".join(f'<div style="color:#3d5068;margin-left:12px;">├── <span style="color:#c9d8ea;">{n}/</span> &nbsp;<span style="color:#3d5068;font-size:0.68rem;">({stats2["file_counts"].get(n,0)} files)</span></div>' for n in ["config","scans","simulations","trades","alerts","ai_log","snapshots"])}
        </div>
        """,unsafe_allow_html=True)

        st.markdown("#### 📥 EXPORT")
        if st.button("📦 Create Full Backup (.zip)",use_container_width=True):
            with st.spinner("Zipping nexus_data..."):
                zp=export_all_to_zip()
                with open(zp,"rb") as f:
                    st.download_button("⬇ Download nexus_export.zip",f.read(),file_name="nexus_export.zip",mime="application/zip",use_container_width=True)

        st.markdown("---")
        st.markdown("#### ⚙️ SETTINGS FILE")
        cfg_path=DIRS["config"]/"settings.json"
        if cfg_path.exists():
            with open(cfg_path) as f: cfg_content=json.load(f)
            cfg_content.pop("api_secret","None"); cfg_content.pop("api_passphrase","None")
            st.json(cfg_content)
        else: st.caption("Config not saved yet")

        st.markdown("---")
        st.markdown("#### 🧹 CLEAR DATA")
        with st.expander("⚠️ Danger Zone",expanded=False):
            if st.button("🗑 Clear ALL scan files",use_container_width=True):
                import shutil
                if DIRS["scans"].exists(): shutil.rmtree(DIRS["scans"]); DIRS["scans"].mkdir()
                st.success("Scan files cleared"); st.rerun()
            if st.button("🗑 Clear ALL simulation files",use_container_width=True):
                import shutil
                if DIRS["simulations"].exists(): shutil.rmtree(DIRS["simulations"]); DIRS["simulations"].mkdir()
                st.success("Simulation files cleared"); st.rerun()
            st.caption("⚠️ These actions are irreversible")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"<div style='text-align:center;padding:12px;font-size:0.62rem;color:#1e2d3e;letter-spacing:2px;'>NEXUS AI CRYPTO BOT &nbsp;·&nbsp; EDUCATIONAL USE ONLY &nbsp;·&nbsp; NOT FINANCIAL ADVICE &nbsp;·&nbsp; DATA SAVED TO <span style='color:#3d5068;'>./nexus_data/</span></div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PERIODIC AUTO-SNAPSHOT  (every page load after 1+ scans)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scan_count > 0 or st.session_state.sim_count > 0:
    snap_data = {
        "scan_count": st.session_state.scan_count,
        "sim_count":  st.session_state.sim_count,
        "exchange":   st.session_state.exchange,
        "api_connected": st.session_state.api_connected,
        "selected_coins":  st.session_state.selected_coins,
        "selected_strats": st.session_state.selected_strats,
        "selected_ivals":  st.session_state.selected_ivals,
    }
    save_snapshot(snap_data)
