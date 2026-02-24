"""
NEXUS — AI/SI Crypto Trading Bot
Streamlit Cloud Edition — GitHub deployment ready

Storage strategy for Streamlit Cloud (no persistent disk):
  • All data lives in st.session_state (survives tab changes, lost on full refresh)
  • Export/Import full session as JSON for manual backup
  • Scan results and sim history kept in session lists (last 50 each)
  • Strategy params auto-saved to session and exportable
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random, time, json, io
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS — AI Crypto Bot",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
:root {
  --bg:       #f8fafc;
  --surface:  #ffffff;
  --surface2: #f1f5f9;
  --border:   #e2e8f0;
  --border2:  #cbd5e1;
  --text:     #0f172a;
  --text2:    #334155;
  --muted:    #64748b;
  --light:    #94a3b8;
  --green:    #059669;
  --green-bg: #ecfdf5;
  --green-b:  #a7f3d0;
  --red:      #dc2626;
  --red-bg:   #fef2f2;
  --red-b:    #fecaca;
  --blue:     #2563eb;
  --blue-bg:  #eff6ff;
  --blue-b:   #bfdbfe;
  --amber:    #d97706;
  --amber-bg: #fffbeb;
  --amber-b:  #fde68a;
  --purple:   #7c3aed;
}

/* Base */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
.main .block-container { padding: 1.5rem 2rem 3rem !important; max-width: 100% !important; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarContent"] { padding: 1.25rem !important; }

/* Hide chrome */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }

/* Typography */
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif !important;
  color: var(--text) !important;
  font-weight: 700 !important;
}
p, li, span, div { color: var(--text2); }

/* Metrics */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 16px 18px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.4rem !important;
  color: var(--blue) !important;
  font-weight: 600 !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.7rem !important;
  letter-spacing: 1px !important;
  color: var(--muted) !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-bottom: 2px solid var(--border) !important;
  gap: 0 !important;
  padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  padding: 12px 20px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--blue) !important;
  border-bottom: 2px solid var(--blue) !important;
  font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

/* Buttons */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  background: var(--blue) !important;
  color: #ffffff !important;
  border: none !important;
  padding: 10px 20px !important;
  box-shadow: 0 1px 3px rgba(37,99,235,0.3) !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  background: #1d4ed8 !important;
  box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
  transform: translateY(-1px) !important;
}

/* Inputs */
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.85rem !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
div[data-baseweb="popover"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 10px 25px rgba(0,0,0,0.12) !important;
}
li[role="option"] {
  background: var(--surface) !important;
  color: var(--text) !important;
  font-size: 0.85rem !important;
}
li[role="option"]:hover { background: var(--blue-bg) !important; }

/* Slider */
.stSlider > div > div > div { background: var(--border) !important; }
.stSlider > div > div > div > div { background: var(--blue) !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

/* Progress */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--blue), var(--purple)) !important;
  border-radius: 99px !important;
}

/* Alerts */
.stSuccess {
  background: var(--green-bg) !important;
  border-left: 4px solid var(--green) !important;
  border-radius: 0 8px 8px 0 !important;
  color: #065f46 !important;
}
.stInfo {
  background: var(--blue-bg) !important;
  border-left: 4px solid var(--blue) !important;
  border-radius: 0 8px 8px 0 !important;
  color: #1e40af !important;
}
.stWarning {
  background: var(--amber-bg) !important;
  border-left: 4px solid var(--amber) !important;
  border-radius: 0 8px 8px 0 !important;
  color: #78350f !important;
}
.stError {
  background: var(--red-bg) !important;
  border-left: 4px solid var(--red) !important;
  border-radius: 0 8px 8px 0 !important;
  color: #7f1d1d !important;
}

/* Expanders */
.streamlit-expanderHeader {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
}

/* Cards */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.card-green  { border-color: var(--green-b)  !important; background: var(--green-bg)  !important; }
.card-red    { border-color: var(--red-b)    !important; background: var(--red-bg)    !important; }
.card-blue   { border-color: var(--blue-b)   !important; background: var(--blue-bg)   !important; }
.card-amber  { border-color: var(--amber-b)  !important; background: var(--amber-bg)  !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* Radio & Checkbox */
.stRadio label, .stCheckbox label { color: var(--text) !important; font-size: 0.85rem !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
  background: var(--surface) !important;
  color: var(--blue) !important;
  border: 1px solid var(--blue-b) !important;
  box-shadow: none !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background: var(--blue-bg) !important;
  transform: translateY(-1px) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--surface2) !important;
  border: 2px dashed var(--border2) !important;
  border-radius: 10px !important;
}

/* Caption */
.stCaption { color: var(--muted) !important; font-size: 0.78rem !important; }

/* Code */
code { background: var(--surface2) !important; color: var(--blue) !important; border-radius: 4px !important; padding: 1px 5px !important; }
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
    "RSI Oversold/Overbought":    {"group":"Momentum",   "icon":"📊","desc":"Buys RSI<oversold, sells RSI>overbought.",        "params":{"rsi_period":14,"oversold":30,"overbought":70},"ai_hints":["Lower oversold for stronger signals","Add volume confirmation","Use with trend filter"]},
    "EMA Crossover":              {"group":"Trend",       "icon":"📈","desc":"Fast EMA crosses above/below slow EMA.",          "params":{"fast_ema":9,"slow_ema":21},"ai_hints":["9/21 best on 1h+","Add ADX>25 filter","Tune per volatility"]},
    "MACD Signal Cross":          {"group":"Trend",       "icon":"〰️","desc":"MACD/signal line crossover entries.",            "params":{"fast":12,"slow":26,"signal":9},"ai_hints":["Histogram zero-cross reduces lag","Best in trending markets","Combine with 200 EMA"]},
    "Bollinger Band Squeeze":     {"group":"Volatility",  "icon":"🎯","desc":"Volatility squeeze breakout detection.",          "params":{"period":20,"std_dev":2.0,"squeeze_pct":3.0},"ai_hints":["Lower std_dev = more signals","Combine RSI for direction","4h best for squeezes"]},
    "Stochastic RSI":             {"group":"Momentum",   "icon":"🔄","desc":"Normalized RSI for oversold/overbought precision.","params":{"rsi_period":14,"stoch_period":14,"smooth_k":3,"smooth_d":3},"ai_hints":["K/D crossover = entry","More sensitive than RSI","Best 15m-4h"]},
    "VWAP Deviation":             {"group":"Volume",      "icon":"📦","desc":"Trade price deviations from VWAP.",              "params":{"band_multiplier":2.0,"min_volume_ratio":1.2},"ai_hints":["Intraday reset only","Best large-caps","1h-4h ideal"]},
    "Supertrend":                 {"group":"Trend",       "icon":"🚀","desc":"ATR-based trend with directional flips.",         "params":{"atr_period":10,"atr_multiplier":3.0},"ai_hints":["Higher mult = fewer signals","Lower ATR = more responsive","Combine RSI filter"]},
    "Ichimoku Cloud":             {"group":"Trend",       "icon":"☁️","desc":"Full Ichimoku: cloud, TK cross, Kijun bounce.",  "params":{"tenkan":9,"kijun":26,"senkou_b":52,"displacement":26},"ai_hints":["Above cloud = bull","TK cross = high conf","Best 4h+"]},
    "Bull Flag / Pennant":        {"group":"Pattern",     "icon":"🏁","desc":"Sharp pole + tight flag consolidation.",          "params":{"pole_min_pct":5.0,"breakout_vol_mult":1.5},"ai_hints":["Volume surge required","Best 1h-4h","Post-halving works well"]},
    "Double Bottom / Top":        {"group":"Pattern",     "icon":"〽️","desc":"W/M reversal at key support/resistance.",        "params":{"tolerance_pct":1.5,"min_separation":10},"ai_hints":["Lower vol on 2nd bottom","Neckline break confirms","Strong on daily"]},
    "Head & Shoulders":           {"group":"Pattern",     "icon":"👤","desc":"Three-peak reversal (also inverse H&S).",         "params":{"shoulder_tolerance":2.0,"volume_decay":True},"ai_hints":["Inverse = bullish","Volume drops right shoulder","Neckline retest common"]},
    "Cup & Handle":               {"group":"Pattern",     "icon":"☕","desc":"Rounded base + handle before breakout.",           "params":{"cup_depth_pct":15.0,"handle_depth_pct":5.0},"ai_hints":["Rounded not V-shaped","Handle < 1/3 cup","Strong bull setup"]},
    "Ascending Triangle":         {"group":"Pattern",     "icon":"△","desc":"Flat resistance + rising trendline coil.",         "params":{"min_touches":3,"tolerance_pct":1.0},"ai_hints":["Flat top = bull breakout","Volume contracts","Best 4h+"]},
    "Engulfing Candles":          {"group":"Candlestick", "icon":"🕯️","desc":"Bull/bear engulfing at S/R zones.",             "params":{"min_body_ratio":1.5,"volume_confirm":True},"ai_hints":["High volume = stronger","At S/R only","Combine RSI divergence"]},
}
EXCHANGES = ["Binance","Coinbase Pro","Kraken","Bybit","OKX","Gate.io","KuCoin","Bitget","MEXC"]
GROUP_COLORS = {"Momentum":"#d97706","Trend":"#2563eb","Volatility":"#7c3aed","Volume":"#059669","Pattern":"#ea580c","Candlestick":"#db2777"}
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
    font=dict(color="#334155", family="Inter, sans-serif", size=12),
    xaxis=dict(showgrid=True, gridcolor="#e2e8f0", color="#64748b", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", color="#64748b", zeroline=False),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", font=dict(color="#334155"), bordercolor="#e2e8f0", borderwidth=1),
    margin=dict(t=40, b=36, l=55, r=20), hovermode="x unified",
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#e2e8f0", font=dict(color="#0f172a")),
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "exchange":"Binance","api_key":"","api_secret":"","api_passphrase":"",
    "api_connected":False,"api_mode":"paper",
    "scan_results":None,"scan_count":0,
    "sim_results":None,"sim_count":0,
    "scan_history":[],       # list of dicts — last 50 scan summaries
    "sim_history":[],        # list of dicts — last 50 sim summaries
    "alerts":[],             # list of dicts
    "ai_log":[],             # list of dicts
    "trade_journal":[],      # list of dicts
    "strategy_params":None,
    "perf_tracker":{},       # rolling per-strategy performance
    "last_ai_update":{},
    "selected_coins":["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","ADA/USDT","AVAX/USDT","LINK/USDT"],
    "selected_strats":["RSI Oversold/Overbought","EMA Crossover","Bollinger Band Squeeze","Supertrend"],
    "selected_ivals":["15m","1h","4h"],
}
for k,v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.strategy_params is None:
    st.session_state.strategy_params = {n:dict(i["params"]) for n,i in STRATEGIES.items()}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def push_alert(msg:str, kind:str="info"):
    st.session_state.alerts.insert(0,{"time":datetime.now().strftime("%H:%M:%S"),"msg":msg,"kind":kind})
    if len(st.session_state.alerts)>200: st.session_state.alerts=st.session_state.alerts[:200]

def fmt_price(p):
    try: return f"${float(p):,.6f}" if float(p)<1 else f"${float(p):,.2f}"
    except: return str(p)

def session_to_json() -> str:
    """Export all session data to JSON string for download."""
    export = {
        "exported_at": datetime.now().isoformat(),
        "version": "2.1",
        "strategy_params": st.session_state.strategy_params,
        "perf_tracker":    st.session_state.perf_tracker,
        "scan_history":    st.session_state.scan_history[-50:],
        "sim_history":     st.session_state.sim_history[-50:],
        "alerts":          st.session_state.alerts[:100],
        "ai_log":          st.session_state.ai_log[:100],
        "trade_journal":   st.session_state.trade_journal[:500],
        "settings": {
            "exchange":        st.session_state.exchange,
            "api_mode":        st.session_state.api_mode,
            "selected_coins":  st.session_state.selected_coins,
            "selected_strats": st.session_state.selected_strats,
            "selected_ivals":  st.session_state.selected_ivals,
            "scan_count":      st.session_state.scan_count,
            "sim_count":       st.session_state.sim_count,
        }
    }
    return json.dumps(export, indent=2, default=str)

def session_from_json(data: dict):
    """Restore session from imported JSON."""
    if "strategy_params" in data: st.session_state.strategy_params = data["strategy_params"]
    if "perf_tracker"    in data: st.session_state.perf_tracker    = data["perf_tracker"]
    if "scan_history"    in data: st.session_state.scan_history    = data["scan_history"]
    if "sim_history"     in data: st.session_state.sim_history     = data["sim_history"]
    if "alerts"          in data: st.session_state.alerts          = data["alerts"]
    if "ai_log"          in data: st.session_state.ai_log          = data["ai_log"]
    if "trade_journal"   in data: st.session_state.trade_journal   = data["trade_journal"]
    if "settings" in data:
        s = data["settings"]
        for k in ("exchange","api_mode","selected_coins","selected_strats","selected_ivals","scan_count","sim_count"):
            if k in s: st.session_state[k] = s[k]

# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR MATH
# ─────────────────────────────────────────────────────────────────────────────
def gen_candles(n=120,base=67000,vol=0.022):
    rng=np.random.default_rng()
    lr=rng.normal(0.0001,vol/np.sqrt(n),n)
    cl=base*np.cumprod(np.exp(lr)); op=np.roll(cl,1); op[0]=base
    hi=np.maximum(op,cl)*(1+rng.uniform(0.001,0.012,n))
    lo=np.minimum(op,cl)*(1-rng.uniform(0.001,0.012,n))
    vl=rng.uniform(200,3000,n)
    t0=datetime.now()
    return pd.DataFrame({"time":[t0-timedelta(minutes=15*(n-i)) for i in range(n)],"open":op,"high":hi,"low":lo,"close":cl,"volume":vl})

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
        dr.iloc[i]=1 if df["close"].iloc[i]>up.iloc[i-1] else(-1 if df["close"].iloc[i]<dn.iloc[i-1] else dr.iloc[i-1])
    return dr

def compute_signal(strategy,df,params):
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
            else: note=f"MACD hist={'pos' if h.iloc[-1]>0 else 'neg'}"
        elif strategy=="Bollinger Band Squeeze":
            bu,bm,bl=bbands(c,params["period"],params["std_dev"])
            bw=(bu.iloc[-1]-bl.iloc[-1])/bm.iloc[-1]*100; last=c.iloc[-1]
            if last<bl.iloc[-1]: sig,conf,note="BUY",random.randint(72,90),f"Below lower BB BW={bw:.1f}%"
            elif last>bu.iloc[-1]: sig,conf,note="SELL",random.randint(70,88),f"Above upper BB BW={bw:.1f}%"
            elif bw<params.get("squeeze_pct",3.0): sig,conf,note=("BUY" if c.pct_change().iloc[-3:].mean()>0 else "SELL"),random.randint(65,80),f"Squeeze breakout BW={bw:.1f}%"
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
    try: rsi_v=float(rsi(c,14).iloc[-1])
    except: rsi_v=50.0
    try: e9=float(ema(c,9).iloc[-1]); e21=float(ema(c,21).iloc[-1])
    except: e9=e21=float(c.iloc[-1])
    try: _,_,hist=macd_calc(c); mv=float(hist.iloc[-1])
    except: mv=0.0
    try: vr=float(df["volume"].iloc[-1]/df["volume"].rolling(20).mean().iloc[-1])
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
    return pd.DataFrame(rows).sort_values("Confidence",ascending=False).reset_index(drop=True)

def simulate_strategy(strategy,capital,candle_count,pos_size_pct,fee_pct,sl_pct,tp_pct,params):
    df=gen_candles(candle_count,67000,0.028)
    balance=capital; position=0.0; buy_price=0.0; equity=[capital]; trades=[]
    for i in range(30,len(df)):
        price=float(df.iloc[i]["close"])
        if position>0:
            chg=(price-buy_price)/buy_price*100
            if chg<=-sl_pct: balance+=position*price*(1-fee_pct/100); trades.append({"i":i,"type":"SELL","price":price,"pnl":round(chg,2),"reason":"Stop Loss","equity":balance}); position=0
            elif chg>=tp_pct: balance+=position*price*(1-fee_pct/100); trades.append({"i":i,"type":"SELL","price":price,"pnl":round(chg,2),"reason":"Take Profit","equity":balance}); position=0
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

# ─────────────────────────────────────────────────────────────────────────────
# AI AUTO-TUNING  (fires automatically after every simulation)
# ─────────────────────────────────────────────────────────────────────────────
def ai_update_params(strategy, results, current_params):
    new_p=dict(current_params); log=[]
    wr=results["win_rate"]; ret=results["total_ret"]; dd=results["max_dd"]; pf=results["profit_factor"]
    if strategy=="RSI Oversold/Overbought":
        if wr<48: new_p["oversold"]=max(18,current_params["oversold"]-2); new_p["overbought"]=min(82,current_params["overbought"]+2); log.append(f"Tightened RSI → buy<{new_p['oversold']} sell>{new_p['overbought']}")
        elif wr>68 and pf>1.4: new_p["oversold"]=min(35,current_params["oversold"]+1); new_p["overbought"]=max(65,current_params["overbought"]-1); log.append(f"Relaxed RSI → buy<{new_p['oversold']} sell>{new_p['overbought']}")
    elif strategy=="EMA Crossover":
        if dd>22: new_p["fast_ema"]=max(5,current_params["fast_ema"]-1); log.append(f"Reduced fast EMA {current_params['fast_ema']}→{new_p['fast_ema']}")
        if wr>62 and pf>1.5: new_p["slow_ema"]=min(34,current_params["slow_ema"]+2); log.append(f"Increased slow EMA {current_params['slow_ema']}→{new_p['slow_ema']}")
        if wr<45: new_p["fast_ema"]=max(5,current_params["fast_ema"]-2); log.append(f"Adjusted EMA fast {new_p['fast_ema']} (poor WR)")
    elif strategy=="MACD Signal Cross":
        if pf<1.0: new_p["signal"]=max(6,current_params["signal"]-1); log.append(f"Reduced MACD signal {current_params['signal']}→{new_p['signal']}")
        elif wr>65: new_p["fast"]=min(16,current_params["fast"]+1); log.append(f"Slowed MACD fast {current_params['fast']}→{new_p['fast']}")
    elif strategy=="Bollinger Band Squeeze":
        if dd>25: new_p["std_dev"]=min(3.0,round(current_params["std_dev"]+0.2,1)); log.append(f"Widened BB std_dev {current_params['std_dev']}→{new_p['std_dev']}")
        elif wr>62: new_p["squeeze_pct"]=max(1.5,round(current_params.get("squeeze_pct",3.0)-0.5,1)); log.append(f"Tightened squeeze threshold → {new_p['squeeze_pct']}%")
        if wr<45: new_p["std_dev"]=max(1.5,round(current_params["std_dev"]-0.1,1)); log.append(f"Narrowed BB std_dev {current_params['std_dev']}→{new_p['std_dev']}")
    elif strategy=="Stochastic RSI":
        if wr<48: new_p["smooth_k"]=max(2,current_params["smooth_k"]+1); log.append(f"Increased StochRSI K smoothing → {new_p['smooth_k']}")
        elif dd>20: new_p["stoch_period"]=min(21,current_params["stoch_period"]+2); log.append(f"Lengthened StochRSI period → {new_p['stoch_period']}")
    elif strategy=="Supertrend":
        if dd>22: new_p["atr_multiplier"]=min(5.0,round(current_params["atr_multiplier"]+0.3,1)); log.append(f"Raised ATR mult {current_params['atr_multiplier']}→{new_p['atr_multiplier']}")
        elif wr>65 and ret>10: new_p["atr_period"]=max(7,current_params["atr_period"]-1); log.append(f"Lowered ATR period {current_params['atr_period']}→{new_p['atr_period']}")
        if wr<44: new_p["atr_multiplier"]=max(1.5,round(current_params["atr_multiplier"]-0.2,1)); log.append(f"Reduced ATR mult → {new_p['atr_multiplier']}")
    elif strategy=="Ichimoku Cloud":
        if dd>25: new_p["kijun"]=min(34,current_params["kijun"]+2); log.append(f"Lengthened Kijun {current_params['kijun']}→{new_p['kijun']}")
        elif wr>65: new_p["tenkan"]=max(7,current_params["tenkan"]-1); log.append(f"Shortened Tenkan {current_params['tenkan']}→{new_p['tenkan']}")
    elif strategy=="VWAP Deviation":
        if wr<48: new_p["band_multiplier"]=min(3.5,round(current_params["band_multiplier"]+0.25,2)); log.append(f"Widened VWAP band → ±{new_p['band_multiplier']}")
        elif wr>65: new_p["min_volume_ratio"]=max(1.0,round(current_params["min_volume_ratio"]-0.1,1)); log.append(f"Relaxed volume filter → {new_p['min_volume_ratio']}x")
    elif strategy in ("Bull Flag / Pennant","Cup & Handle"):
        if wr<50: new_p["breakout_vol_mult"]=min(3.0,round(current_params.get("breakout_vol_mult",1.5)+0.3,1)); log.append(f"Raised volume mult → {new_p['breakout_vol_mult']}x")
    if not log: log.append("Params near-optimal — monitoring")
    return new_p, log

def auto_ai_tune(strategy:str, results:dict):
    """Runs automatically after every simulation. No button needed."""
    cur_p = st.session_state.strategy_params.get(strategy, STRATEGIES[strategy]["params"])
    tracker = st.session_state.perf_tracker.setdefault(strategy,{"runs":0,"win_rates":[],"returns":[],"drawdowns":[],"pfs":[]})
    tracker["runs"]+=1
    tracker["win_rates"].append(results["win_rate"])
    tracker["returns"].append(results["total_ret"])
    tracker["drawdowns"].append(results["max_dd"])
    tracker["pfs"].append(results["profit_factor"])
    for k in ("win_rates","returns","drawdowns","pfs"): tracker[k]=tracker[k][-10:]

    runs=tracker["runs"]
    avg_wr=float(np.mean(tracker["win_rates"])); avg_ret=float(np.mean(tracker["returns"]))
    avg_dd=float(np.mean(tracker["drawdowns"])); avg_pf=float(np.mean(tracker["pfs"]))

    # Blend: run1=raw, 2-3=60/40, 4+=30/70 rolling
    if runs==1:   blend=results; label="run 1 (direct)"
    elif runs<4:  blend={"win_rate":results["win_rate"]*0.6+avg_wr*0.4,"total_ret":results["total_ret"]*0.6+avg_ret*0.4,"max_dd":results["max_dd"]*0.6+avg_dd*0.4,"profit_factor":results["profit_factor"]*0.6+avg_pf*0.4}; label=f"run {runs} (60/40)"
    else:         blend={"win_rate":results["win_rate"]*0.3+avg_wr*0.7,"total_ret":results["total_ret"]*0.3+avg_ret*0.7,"max_dd":results["max_dd"]*0.3+avg_dd*0.7,"profit_factor":results["profit_factor"]*0.3+avg_pf*0.7}; label=f"run {runs} (30/70)"

    new_p, param_log = ai_update_params(strategy, blend, cur_p)

    # Rolling diagnostics
    diag=[]
    if len(tracker["win_rates"])>=3:
        w=tracker["win_rates"]; arr="↑" if w[-1]>w[0]+3 else("↓" if w[-1]<w[0]-3 else "→")
        diag.append(f"[{label}] Avg WR {avg_wr:.0f}% {arr} | Ret {avg_ret:+.1f}% | DD {avg_dd:.1f}% | PF {avg_pf:.2f}")
    else:
        diag.append(f"[{label}] WR {results['win_rate']:.0f}% | Ret {results['total_ret']:+.1f}% | DD {results['max_dd']:.1f}%")

    # Aggressive reset after 5+ consistently poor runs
    if runs>=5 and avg_wr<45 and avg_ret<0:
        defaults=STRATEGIES[strategy]["params"]
        for k in new_p:
            if isinstance(new_p[k],(int,float)) and isinstance(defaults.get(k),(int,float)):
                new_p[k]=round(new_p[k]*0.5+defaults[k]*0.5,2)
        diag.append(f"⚠️ 5+ poor runs — params reset 50% toward defaults")

    if runs>=3 and avg_wr>=60 and avg_ret>10:
        diag.append(f"✅ Converging well over {runs} runs — params stabilising")

    # Apply
    st.session_state.strategy_params[strategy]=new_p
    st.session_state.last_ai_update[strategy]=datetime.now().strftime("%H:%M:%S")

    ts=datetime.now().strftime("%H:%M:%S")
    all_msgs=param_log+diag
    for msg in all_msgs:
        kind="success" if "✅" in msg else("warning" if "⚠️" in msg else "info")
        push_alert(f"[AI·{strategy[:18]}] {msg}",kind)
        entry={"time":ts,"strat":strategy,"msg":msg,"runs":runs,"avg_wr":round(avg_wr,1),"avg_ret":round(avg_ret,2)}
        st.session_state.ai_log.insert(0,entry)
    if len(st.session_state.ai_log)>500: st.session_state.ai_log=st.session_state.ai_log[:500]
    return new_p, all_msgs, tracker

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def chart_equity(equity,trades,capital):
    color="#059669" if equity[-1]>=capital else "#ff3d71"
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(equity))),y=equity,mode="lines",name="Portfolio",line=dict(color=color,width=2),fill="tozeroy",fillcolor=f"rgba({'5,150,105' if color=='#00e5a0' else '220,38,38'},0.05)"))
    fig.add_hline(y=capital,line_dash="dot",line_color="#64748b",line_width=1,annotation_text="Start")
    buys=[t for t in trades if t["type"]=="BUY"]; sells=[t for t in trades if t["type"]=="SELL"]
    if buys: fig.add_trace(go.Scatter(x=[t["i"] for t in buys],y=[equity[min(t["i"],len(equity)-1)] for t in buys],mode="markers",name="BUY",marker=dict(symbol="triangle-up",size=10,color="#059669")))
    if sells: fig.add_trace(go.Scatter(x=[t["i"] for t in sells],y=[equity[min(t["i"],len(equity)-1)] for t in sells],mode="markers",name="SELL",marker=dict(symbol="triangle-down",size=10,color="#dc2626")))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=270,title=dict(text="Equity Curve",font=dict(color="#0f172a",size=13,family="Inter")))
    fig.update_layout(**ly); return fig

def chart_candles(df,trades):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.72,0.28],vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],increasing_line_color="#059669",decreasing_line_color="#dc2626",name="Price"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=ema(df["close"],9),mode="lines",name="EMA9",line=dict(color="#2563eb",width=1.5)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=ema(df["close"],21),mode="lines",name="EMA21",line=dict(color="#d97706",width=1.5)),row=1,col=1)
    colors=["rgba(5,150,105,0.25)" if c>=o else "rgba(220,38,38,0.2)" for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=df["volume"],name="Vol",marker_color=colors,showlegend=False),row=2,col=1)
    buys=[t for t in trades if t["type"]=="BUY"]; sells=[t for t in trades if t["type"]=="SELL"]
    if buys: fig.add_trace(go.Scatter(x=[df.iloc[min(t["i"],len(df)-1)]["time"] for t in buys],y=[t["price"]*0.997 for t in buys],mode="markers",marker=dict(symbol="triangle-up",size=12,color="#059669"),showlegend=False),row=1,col=1)
    if sells: fig.add_trace(go.Scatter(x=[df.iloc[min(t["i"],len(df)-1)]["time"] for t in sells],y=[t["price"]*1.003 for t in sells],mode="markers",marker=dict(symbol="triangle-down",size=12,color="#dc2626"),showlegend=False),row=1,col=1)
    ly=dict(PLOTLY_LAYOUT); ly.update(height=320,title=dict(text="Price + Signals",font=dict(color="#0f172a",size=13,family="Inter")),xaxis_rangeslider_visible=False,xaxis2=dict(showgrid=True,gridcolor="#e2e8f0",color="#64748b"),yaxis2=dict(showgrid=True,gridcolor="#e2e8f0",color="#64748b"))
    fig.update_layout(**ly); return fig

def chart_sig_pie(df):
    cnt=df["Signal"].value_counts(); c={"BUY":"#059669","SELL":"#dc2626","HOLD":"#94a3b8"}
    fig=go.Figure(go.Pie(labels=cnt.index,values=cnt.values,marker_colors=[c.get(s,"#666") for s in cnt.index],hole=0.6,textfont=dict(family="JetBrains Mono",size=11)))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Signal Mix",font=dict(color="#0f172a",size=13,family="Inter")),margin=dict(t=36,b=10,l=10,r=10))
    fig.update_layout(**ly); return fig

def chart_top_coins(df):
    top=df.groupby("Coin")["Confidence"].mean().sort_values().tail(10)
    fig=go.Figure(go.Bar(x=top.values,y=top.index,orientation="h",marker=dict(color=top.values,colorscale=[[0,"#e2e8f0"],[0.5,"#60a5fa"],[1,"#059669"]]),text=[f"{v:.0f}%" for v in top.values],textposition="outside",textfont=dict(color="#334155",size=10)))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Avg Conf by Coin",font=dict(color="#0f172a",size=13,family="Inter")),xaxis=dict(showgrid=False,color="#64748b",range=[0,115]),yaxis=dict(showgrid=False,color="#334155"),margin=dict(t=36,b=10,l=50,r=40))
    fig.update_layout(**ly); return fig

def chart_rsi(df):
    fig=go.Figure(go.Histogram(x=df["RSI"],nbinsx=20,marker_color="#2563eb",marker_line_color="#0c1220",marker_line_width=1))
    fig.add_vrect(x0=0,x1=30,fillcolor="#059669",opacity=0.06,line_width=0,annotation_text="Oversold",annotation_font_color="#059669",annotation_font_size=10)
    fig.add_vrect(x0=70,x1=100,fillcolor="#dc2626",opacity=0.06,line_width=0,annotation_text="Overbought",annotation_font_color="#dc2626",annotation_font_size=10)
    ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="RSI Distribution",font=dict(color="#0f172a",size=13,family="Inter")),margin=dict(t=36,b=30,l=40,r=10))
    fig.update_layout(**ly); return fig

def chart_sim_history():
    if len(st.session_state.sim_history)<2: return None
    h=st.session_state.sim_history[-20:]
    colors=["#059669" if r["return"]>0 else "#dc2626" for r in h]
    fig=go.Figure(go.Bar(x=list(range(len(h))),y=[r["return"] for r in h],marker_color=colors,text=[f"{r['return']:+.1f}%" for r in h],textposition="outside",textfont=dict(color="#334155",size=10),customdata=[r["strategy"][:20] for r in h],hovertemplate="%{customdata}: %{y:.2f}%<extra></extra>"))
    ly=dict(PLOTLY_LAYOUT); ly.update(height=220,title=dict(text="Simulation History",font=dict(color="#0f172a",size=13,family="Inter")),yaxis=dict(showgrid=True,gridcolor="#e2e8f0",color="#64748b",zeroline=True,zerolinecolor="#64748b"),xaxis=dict(showgrid=False),margin=dict(t=36,b=20,l=50,r=16))
    fig.update_layout(**ly); return fig

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
btc_p=BASE_PRICES["BTC/USDT"]*(1+random.gauss(0,0.002))
eth_p=BASE_PRICES["ETH/USDT"]*(1+random.gauss(0,0.003))
ai_runs_total=sum(t.get("runs",0) for t in st.session_state.perf_tracker.values())

st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;
            padding:20px 28px;margin-bottom:20px;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
  <div>
    <div style="font-family:'Inter',sans-serif;font-size:1.5rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em;">
      ◈ NEXUS
      <span style="font-size:0.72rem;color:#94a3b8;font-weight:500;letter-spacing:0.05em;margin-left:8px;">AI CRYPTO TRADING BOT</span>
    </div>
    <div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;">
      Scanner · Patterns ·
      <span style="color:#059669;font-weight:600;">Auto AI Tuning ✓</span>
    </div>
  </div>
  <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">
    {"".join(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:{c};font-family:JetBrains Mono,monospace;'>{v}</div><div style='font-size:0.62rem;color:#94a3b8;letter-spacing:0.5px;margin-top:2px;'>{l}</div></div>" for l,v,c in [("BTC/USDT",f"${btc_p:,.0f}","#0f172a"),("ETH/USDT",f"${eth_p:,.0f}","#0f172a"),("SCANS",st.session_state.scan_count,"#7c3aed"),("SIMS",st.session_state.sim_count,"#2563eb"),("AI RUNS",ai_runs_total,"#059669"),("ALERTS",len(st.session_state.alerts),"#d97706")])}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:8px 0 18px;'><div style='font-size:1.25rem;font-weight:800;color:#0f172a;letter-spacing:-0.01em;'>◈ NEXUS</div><div style='font-size:0.68rem;color:#94a3b8;letter-spacing:1px;margin-top:2px;'>CONTROL PANEL</div></div>", unsafe_allow_html=True)

    with st.expander("⚡  API CONNECTION", expanded=not st.session_state.api_connected):
        exchange_sel=st.selectbox("Exchange",EXCHANGES,index=EXCHANGES.index(st.session_state.exchange) if st.session_state.exchange in EXCHANGES else 0)
        api_k=st.text_input("API Key",value=st.session_state.api_key,placeholder="Paste API key")
        api_s=st.text_input("API Secret",value="",placeholder="Paste secret",type="password")
        api_p=st.text_input("Passphrase",value="",placeholder="OKX/KuCoin only",type="password")
        api_mode_sel=st.radio("Mode",["paper","live"],horizontal=True)
        c1,c2=st.columns(2)
        with c1:
            if st.button("CONNECT",use_container_width=True):
                if api_k.strip(): st.session_state.update({"exchange":exchange_sel,"api_key":api_k,"api_secret":api_s,"api_passphrase":api_p,"api_connected":True,"api_mode":api_mode_sel}); push_alert(f"Connected to {exchange_sel} [{api_mode_sel.upper()}]","success"); st.rerun()
                else: st.error("Enter API key")
        with c2:
            if st.button("CLEAR",use_container_width=True): st.session_state.update({"api_connected":False,"api_key":"","api_secret":"","api_passphrase":""}); st.rerun()
        if st.session_state.api_connected: st.success(f"✓ {st.session_state.exchange} — {st.session_state.api_mode.upper()}")
        else: st.warning("Not connected · simulated data")
        st.caption("⚠ API secrets are NOT stored — re-enter on each session. Use READ-ONLY keys for scanning.")

    st.markdown("---")
    st.markdown("#### ⬡ SCAN SETTINGS")
    sel_coins=st.multiselect("Coins",COINS,default=st.session_state.selected_coins,format_func=lambda x:x.replace("/USDT",""))
    sel_strats=st.multiselect("Strategies",list(STRATEGIES.keys()),default=st.session_state.selected_strats)
    sel_ivals=st.multiselect("Intervals",INTERVALS,default=st.session_state.selected_ivals)

    if sel_coins  != st.session_state.selected_coins:  st.session_state.selected_coins  = sel_coins
    if sel_strats != st.session_state.selected_strats: st.session_state.selected_strats = sel_strats
    if sel_ivals  != st.session_state.selected_ivals:  st.session_state.selected_ivals  = sel_ivals

    st.markdown("---")
    ops=len(sel_coins)*len(sel_strats)*len(sel_ivals)
    st.markdown(f"<div style='font-size:0.72rem;line-height:2.1;color:#64748b;'>Coins &nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#059669;'>{len(sel_coins)}</span><br>Strategies &nbsp;<span style='color:#059669;'>{len(sel_strats)}</span><br>Intervals &nbsp;&nbsp;<span style='color:#059669;'>{len(sel_ivals)}</span><br><span style='color:#94a3b8;'>─────────────</span><br>Total ops &nbsp;&nbsp;<span style='color:#2563eb;'>{ops:,}</span></div>",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 💾 SESSION DATA")
    st.caption("Streamlit Cloud has no persistent disk. Export your session to keep data between refreshes.")

    # Export — generate bytes once, key ensures button refreshes correctly
    try:
        _export_bytes = session_to_json().encode("utf-8")
        _export_name  = f"nexus_session_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        st.download_button(
            label="⬇ Export Session (.json)",
            data=_export_bytes,
            file_name=_export_name,
            mime="application/json",
            use_container_width=True,
            key="sidebar_export_btn",
        )
    except Exception as _ex:
        st.error(f"Export error: {_ex}")

    st.markdown("")

    # Import
    st.caption("Restore a previous session:")
    uploaded = st.file_uploader(
        "Import .json",
        type=["json"],
        label_visibility="collapsed",
        key="sidebar_import_uploader",
    )
    if uploaded is not None:
        try:
            raw = uploaded.read()
            data = json.loads(raw.decode("utf-8"))
            session_from_json(data)
            push_alert(f"Session restored from {uploaded.name}", "success")
            st.success("✓ Session imported!")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_scan,tab_ivs,tab_strat,tab_sim,tab_journal,tab_alerts = st.tabs([
    "⬡  SCANNER","⏱  INTERVALS","⚡  STRATEGIES","🔬  SIMULATION","📒  JOURNAL","🔔  ALERTS",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab_scan:
    hc1,hc2=st.columns([4,1])
    with hc1: st.markdown("### MARKET SCANNER"); st.caption("Multi-strategy · auto AI-tuned parameters · export results anytime")
    with hc2: st.markdown("<br>",unsafe_allow_html=True); do_scan=st.button("▶  RUN SCAN",use_container_width=True)

    if do_scan:
        if not sel_coins or not sel_strats or not sel_ivals: st.error("Select at least one coin, strategy, and interval.")
        else:
            prog=st.progress(0,text="Scanning markets...")
            for p in range(0,101,2): time.sleep(0.012); prog.progress(p)
            prog.empty()
            results=run_market_scan(sel_coins,sel_strats,sel_ivals,st.session_state.strategy_params)
            st.session_state.scan_results=results
            st.session_state.scan_count+=1
            nb=len(results[results["Signal"]=="BUY"]); ns=len(results[results["Signal"]=="SELL"])
            st.session_state.scan_history.insert(0,{"scan":st.session_state.scan_count,"time":datetime.now().strftime("%H:%M:%S"),"signals":len(results),"buy":nb,"sell":ns,"coins":results["Coin"].nunique()})
            if len(st.session_state.scan_history)>50: st.session_state.scan_history=st.session_state.scan_history[:50]
            push_alert(f"Scan #{st.session_state.scan_count}: {nb} BUY · {ns} SELL · {results['Coin'].nunique()} coins","success")
            st.success(f"✓ Scan complete — {len(results):,} signals · use ⬇ Export in sidebar to save")

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
        with m1: st.metric("Total",f"{len(flt):,}")
        with m2: st.metric("🟢 BUY",len(flt[flt["Signal"]=="BUY"]),delta=f"+{len(flt[flt['Signal']=='BUY'])}")
        with m3: st.metric("🔴 SELL",len(flt[flt["Signal"]=="SELL"]),delta=f"-{len(flt[flt['Signal']=='SELL'])}",delta_color="inverse")
        with m4: st.metric("Avg Conf",f"{flt['Confidence'].mean():.0f}%" if len(flt) else "—")
        with m5: st.metric("Pairs",flt["Coin"].nunique())
        with m6: st.metric("Groups",flt["Group"].nunique())
        st.markdown("---")
        if len(flt):
            c1,c2,c3,c4=st.columns(4)
            with c1: st.plotly_chart(chart_sig_pie(flt),use_container_width=True)
            with c2: st.plotly_chart(chart_top_coins(flt),use_container_width=True)
            with c3: st.plotly_chart(chart_rsi(flt),use_container_width=True)
            with c4:
                gc=flt.groupby("Group")["Confidence"].mean().sort_values()
                fig=go.Figure(go.Bar(x=gc.values,y=gc.index,orientation="h",marker=dict(color=[GROUP_COLORS.get(g,"#666") for g in gc.index]),text=[f"{v:.0f}%" for v in gc.values],textposition="outside",textfont=dict(color="#334155",size=10)))
                ly=dict(PLOTLY_LAYOUT); ly.update(height=230,title=dict(text="Conf by Group",font=dict(color="#0f172a",size=13,family="Inter")),xaxis=dict(showgrid=False,range=[0,115],color="#64748b"),yaxis=dict(showgrid=False,color="#334155"),margin=dict(t=36,b=10,l=80,r=40))
                fig.update_layout(**ly); st.plotly_chart(fig,use_container_width=True)
        st.markdown("---")
        disp=flt[["Coin","Interval","Strategy","Signal","Confidence","RSI","Price","24h %","Vol Ratio","Note"]].copy()
        def ss(v): return {"BUY":"color:#059669;font-weight:700","SELL":"color:#dc2626;font-weight:700","HOLD":"color:#64748b"}.get(v,"")
        def sc(v):
            try: return f"color:{'#00e5a0' if float(v)>=0 else '#ff3d71'}"
            except: return ""
        def sr(v):
            try:
                f=float(v)
                if f<30: return "color:#059669;font-weight:700"
                if f>70: return "color:#dc2626;font-weight:700"
            except: pass
            return "color:#64748b"
        def conf_bg(v):
            try:
                n=float(v)
                if n>=80: return "background:#dcfce7;color:#166534;font-weight:600"
                if n>=65: return "background:#d1fae5;color:#065f46"
                if n>=50: return "background:#fef9c3;color:#713f12"
                return "background:#fee2e2;color:#7f1d1d"
            except: return ""
        styled=(disp.style
            .map(ss,subset=["Signal"])
            .map(sc,subset=["24h %"])
            .map(sr,subset=["RSI"])
            .map(conf_bg,subset=["Confidence"])
            .format({"Price":lambda x:fmt_price(float(x)),"24h %":"{:+.2f}%","Confidence":"{}%","Vol Ratio":"{:.2f}×"})
            .set_properties(**{"font-family":"Inter,sans-serif","font-size":"12px"}))
        st.dataframe(styled,use_container_width=True,height=420)

        # Download scan CSV
        _scan_csv = flt.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download scan results (.csv)",
            data=_scan_csv,
            file_name=f"nexus_scan_{st.session_state.scan_count}.csv",
            mime="text/csv",
            key=f"scan_dl_{st.session_state.scan_count}",
        )

        top_buys=flt[flt["Signal"]=="BUY"].head(4); top_sells=flt[flt["Signal"]=="SELL"].head(4)
        if len(top_buys):
            st.markdown("#### 🟢 TOP BUY SIGNALS")
            cols=st.columns(min(4,len(top_buys)))
            for i,(_,row) in enumerate(top_buys.iterrows()):
                with cols[i]: st.markdown(f"<div class='card card-green'><div style='font-size:1.2rem;font-weight:800;color:#059669;font-family:Syne,sans-serif;'>{row['Coin']}</div><div style='font-size:0.65rem;color:#64748b;margin-bottom:8px;'>{row['Strategy']} · {row['Interval']}</div><div style='font-size:0.95rem;color:#0f172a;'>{fmt_price(float(row['Price']))}</div><div style='font-size:0.72rem;color:#059669;margin-top:4px;'>Conf: {row['Confidence']}%</div><div style='font-size:0.65rem;color:#64748b;'>{row['Note'][:40]}</div><div style='margin-top:8px;height:2px;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;width:{row['Confidence']}%;'></div></div>",unsafe_allow_html=True)
        if len(top_sells):
            st.markdown("#### 🔴 TOP SELL SIGNALS")
            cols=st.columns(min(4,len(top_sells)))
            for i,(_,row) in enumerate(top_sells.iterrows()):
                with cols[i]: st.markdown(f"<div class='card card-red'><div style='font-size:1.2rem;font-weight:800;color:#dc2626;font-family:Syne,sans-serif;'>{row['Coin']}</div><div style='font-size:0.65rem;color:#64748b;margin-bottom:8px;'>{row['Strategy']} · {row['Interval']}</div><div style='font-size:0.95rem;color:#0f172a;'>{fmt_price(float(row['Price']))}</div><div style='font-size:0.72rem;color:#dc2626;margin-top:4px;'>Conf: {row['Confidence']}%</div><div style='font-size:0.65rem;color:#64748b;'>{row['Note'][:40]}</div><div style='margin-top:8px;height:2px;background:linear-gradient(90deg,#dc2626,#d97706);border-radius:2px;width:{row['Confidence']}%;'></div></div>",unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center;padding:80px 0;color:#94a3b8;'><div style='font-size:4rem;margin-bottom:16px;'>◈</div><div style='font-family:Syne,sans-serif;color:#64748b;letter-spacing:0.5px;'>SELECT ASSETS IN SIDEBAR · CLICK RUN SCAN</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INTERVALS
# ══════════════════════════════════════════════════════════════════════════════
with tab_ivs:
    st.markdown("### SCAN INTERVALS")
    style_colors={"Scalping":"#ff3d71","Day Trade":"#f5c542","Swing":"#38bdf8","Position":"#a78bfa","Long-Term":"#00e5a0"}
    groups={}
    for iv in INTERVALS: groups.setdefault(INTERVAL_INFO[iv]["style"],[]).append(iv)
    for sname,ivs in groups.items():
        sc2=style_colors.get(sname,"#666")
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 8px;'><div style='width:3px;height:18px;background:{sc2};border-radius:2px;'></div><span style='font-family:Syne,sans-serif;font-weight:700;color:{sc2};letter-spacing:2px;font-size:0.82rem;'>{sname.upper()}</span></div>",unsafe_allow_html=True)
        cols=st.columns(len(ivs))
        for i,iv in enumerate(ivs):
            info=INTERVAL_INFO[iv]; is_sel=iv in sel_ivals
            with cols[i]: st.markdown(f"<div style='background:{'rgba(5,150,105,0.05)' if is_sel else 'rgba(12,18,32,0.8)'};border:1px solid {'rgba(5,150,105,0.35)' if is_sel else 'rgba(37,99,235,0.15)'};border-radius:10px;padding:16px 12px;text-align:center;'><div style='font-size:0.85rem;margin-bottom:4px;'>{info['icon']}</div><div style='font-size:1.4rem;font-weight:800;color:{'#00e5a0' if is_sel else '#3d5068'};font-family:Syne,sans-serif;'>{iv}</div><div style='font-size:0.62rem;color:{sc2};margin:4px 0;letter-spacing:1px;'>{info['style'].upper()}</div><div style='font-size:0.62rem;color:#64748b;line-height:1.5;'>{info['desc']}</div>{'<div style=margin-top:8px;height:2px;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;></div>' if is_sel else ''}</div>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<div class='card card-blue'><div style='font-size:0.7rem;color:#2563eb;letter-spacing:2px;margin-bottom:6px;'>ACTIVE</div><div style='color:#0f172a;'>{' &nbsp;·&nbsp; '.join([iv for iv in INTERVALS if iv in sel_ivals]) or 'None'}</div><div style='font-size:0.7rem;color:#64748b;margin-top:8px;'>{len(sel_ivals)} frame(s) → <span style='color:#2563eb;'>{len(sel_ivals)*len(sel_coins)*len(sel_strats):,} ops per scan</span></div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════
with tab_strat:
    st.markdown("### STRATEGY CONFIGURATION")
    st.caption("Parameters auto-update from rolling simulation win rate — no manual intervention needed")
    gf=st.radio("Group",["ALL"]+list(GROUP_COLORS.keys()),horizontal=True)
    st.markdown("")
    for sname,sinfo in STRATEGIES.items():
        if gf!="ALL" and sinfo["group"]!=gf: continue
        is_act=sname in sel_strats; gc=GROUP_COLORS.get(sinfo["group"],"#666")
        cur_p=st.session_state.strategy_params.get(sname,sinfo["params"])
        t=st.session_state.perf_tracker.get(sname,{}); runs=t.get("runs",0)
        ai_badge=f" &nbsp;🤖 {runs} runs" if runs>0 else ""
        with st.expander(f"{sinfo['icon']}  {sname}  [{sinfo['group']}]{'  ✓' if is_act else ''}{ai_badge}",expanded=False):
            ec1,ec2=st.columns([3,1])
            with ec1:
                st.markdown(f"<div style='margin-bottom:10px;'><span style='background:{gc}18;border:1px solid {gc}44;color:{gc};padding:3px 12px;border-radius:10px;font-size:0.67rem;letter-spacing:1px;'>{sinfo['group'].upper()}</span>{'<span style=margin-left:8px;background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.3);color:#059669;padding:3px 12px;border-radius:10px;font-size:0.67rem;> ACTIVE</span>' if is_act else ''}</div><p style='color:#0f172a;font-size:0.8rem;line-height:1.6;'>{sinfo['desc']}</p>{''.join(f'<div style=font-size:0.7rem;color:#2563eb;margin-bottom:2px;>› {h}</div>' for h in sinfo['ai_hints'])}",unsafe_allow_html=True)
                st.markdown("**Current Parameters (AI auto-tuned):**")
                pcols=st.columns(min(4,len(cur_p))); new_p=dict(cur_p)
                for idx,(pn,pv) in enumerate(cur_p.items()):
                    with pcols[idx%4]:
                        if isinstance(pv,bool): new_p[pn]=st.checkbox(pn,value=pv,key=f"p_{sname}_{pn}")
                        elif isinstance(pv,float): new_p[pn]=st.number_input(pn,value=float(pv),step=0.1,format="%.2f",key=f"p_{sname}_{pn}")
                        elif isinstance(pv,int): new_p[pn]=st.number_input(pn,value=int(pv),step=1,key=f"p_{sname}_{pn}")
                        else: new_p[pn]=st.text_input(pn,value=str(pv),key=f"p_{sname}_{pn}")
                if st.button(f"💾 Save Manual Override",key=f"save_{sname}"):
                    st.session_state.strategy_params[sname]=new_p; push_alert(f"Manual params saved for '{sname}'","success"); st.success("Saved!")
            with ec2:
                if runs>0:
                    avg_wr=float(np.mean(t["win_rates"])); avg_ret=float(np.mean(t["returns"]))
                    wr_c="#00e5a0" if avg_wr>=55 else("#f5c542" if avg_wr>=45 else "#ff3d71")
                    ret_c="#00e5a0" if avg_ret>=0 else "#ff3d71"
                    last=st.session_state.last_ai_update.get(sname,"—")
                    mode="30/70" if runs>=4 else("60/40" if runs>=2 else "direct")
                    st.markdown(f"""<div style='background:#f1f5f9;border:1px solid rgba(5,150,105,0.15);border-radius:8px;padding:12px;'>
                    <div style='font-size:0.65rem;color:#2563eb;letter-spacing:1px;margin-bottom:8px;'>🤖 AI TUNING</div>
                    <div style='font-size:0.72rem;margin-bottom:4px;'>Runs <span style='color:#7c3aed;font-weight:700;'>{runs}</span></div>
                    <div style='font-size:0.72rem;margin-bottom:4px;'>Avg WR <span style='color:{wr_c};font-weight:700;'>{avg_wr:.0f}%</span></div>
                    <div style='font-size:0.72rem;margin-bottom:4px;'>Avg Ret <span style='color:{ret_c};'>{avg_ret:+.1f}%</span></div>
                    <div style='font-size:0.65rem;color:#64748b;'>Mode: {mode} blend</div>
                    <div style='font-size:0.62rem;color:#64748b;'>Updated: {last}</div>
                    <div style='margin-top:8px;height:2px;background:#e2e8f0;border-radius:2px;'><div style='height:100%;width:{min(runs*10,100)}%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;'></div></div>
                    </div>""",unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;font-size:0.72rem;color:#64748b;'>🤖 AI tuning starts after first simulation run</div>",unsafe_allow_html=True)

    # Live tuning status table for active strategies
    rows=""
    for sn in sel_strats:
        t=st.session_state.perf_tracker.get(sn,{}); r=t.get("runs",0)
        if r>0:
            aw=float(np.mean(t["win_rates"])); ar=float(np.mean(t["returns"]))
            wc="#00e5a0" if aw>=55 else("#f5c542" if aw>=45 else "#ff3d71"); rc="#00e5a0" if ar>=0 else "#ff3d71"
            mode="30/70" if r>=4 else("60/40" if r>=2 else "direct")
            rows+=f"<tr><td style='color:#0f172a;padding:5px 10px;'>{sn[:26]}</td><td style='color:#7c3aed;text-align:center;'>{r}</td><td style='color:{wc};text-align:center;font-weight:700;'>{aw:.0f}%</td><td style='color:{rc};text-align:center;'>{ar:+.1f}%</td><td style='color:#2563eb;font-size:0.65rem;text-align:center;'>{mode}</td></tr>"
    if rows:
        st.markdown("---")
        st.markdown(f"<div class='card card-blue'><div style='font-size:0.75rem;font-weight:700;color:#2563eb;margin-bottom:10px;letter-spacing:2px;'>🤖 LIVE AI TUNING — ACTIVE STRATEGIES</div><table style='width:100%;border-collapse:collapse;font-size:0.72rem;'><tr style='color:#64748b;border-bottom:1px solid #1e2d3e;'><th style='text-align:left;padding:4px 10px;'>Strategy</th><th>Runs</th><th>Avg WR</th><th>Avg Ret</th><th>Blend</th></tr>{rows}</table></div>",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='card card-blue'><div style='font-size:0.75rem;font-weight:700;color:#2563eb;margin-bottom:8px;letter-spacing:2px;'>🤖 AUTO-TUNING ENGINE</div><div style='font-size:0.75rem;color:#64748b;line-height:1.9;'>Parameters update <strong style='color:#0f172a;'>automatically after every simulation</strong>. Uses rolling weighted average (10 runs): run 1 = direct · runs 2-3 = 60/40 blend · runs 4+ = 30/70 rolling. After 5+ consistently poor runs → aggressive reset to safe defaults. Manual overrides always respected.</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown("### AI PAPER TRADING SIMULATION")
    st.caption("Auto-tunes parameters from rolling win rate immediately after each run")
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
        do_sim=st.button("▶  RUN AI SIMULATION",use_container_width=True)

        # AI tuning status panel
        tracker=st.session_state.perf_tracker.get(sim_strat,{})
        runs=tracker.get("runs",0)
        if runs>0:
            avg_wr=float(np.mean(tracker["win_rates"])); avg_ret=float(np.mean(tracker["returns"]))
            avg_dd=float(np.mean(tracker["drawdowns"])); last_upd=st.session_state.last_ai_update.get(sim_strat,"—")
            wr_c="#00e5a0" if avg_wr>=55 else("#f5c542" if avg_wr>=45 else "#ff3d71")
            ret_c="#00e5a0" if avg_ret>=0 else "#ff3d71"
            # WR trend
            wrs=tracker["win_rates"]; arr="↑" if len(wrs)>=2 and wrs[-1]>wrs[0] else("↓" if len(wrs)>=2 and wrs[-1]<wrs[0] else "→")
            tc="#00e5a0" if arr=="↑" else("#ff3d71" if arr=="↓" else "#f5c542")
            mode="30/70 rolling" if runs>=4 else("60/40 blend" if runs>=2 else "single run")
            st.markdown(f"""
            <div style='background:#f1f5f9;border:1px solid rgba(5,150,105,0.2);border-radius:8px;padding:14px 16px;margin-top:14px;'>
              <div style='font-size:0.68rem;color:#2563eb;letter-spacing:2px;margin-bottom:10px;'>🤖 AI TUNING STATUS</div>
              <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.73rem;'>
                <div>Runs <span style='color:#7c3aed;font-weight:700;'>{runs}</span></div>
                <div>Updated <span style='color:#64748b;font-size:0.65rem;'>{last_upd}</span></div>
                <div>Avg WR <span style='color:{wr_c};font-weight:700;'>{avg_wr:.0f}%</span> <span style='color:{tc};'>{arr}</span></div>
                <div>Avg Ret <span style='color:{ret_c};font-weight:700;'>{avg_ret:+.1f}%</span></div>
                <div>Avg DD <span style='color:#d97706;'>{avg_dd:.1f}%</span></div>
                <div style='font-size:0.62rem;color:#2563eb;'>{mode}</div>
              </div>
              <div style='margin-top:10px;height:3px;background:#e2e8f0;border-radius:2px;'>
                <div style='height:100%;width:{min(runs*10,100)}%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;'></div>
              </div>
              <div style='font-size:0.6rem;color:#64748b;margin-top:3px;'>AI confidence: {min(runs*10,100)}% ({runs}/10 runs)</div>
            </div>
            """,unsafe_allow_html=True)
            if len(wrs)>=2: st.markdown(f"<div style='font-size:0.68rem;color:#64748b;margin-top:6px;'>WR trend: <span style='color:{tc};'>{' → '.join([f'{w:.0f}%' for w in wrs[-4:]])} {arr}</span></div>",unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;margin-top:14px;font-size:0.72rem;color:#64748b;'>🤖 AI auto-tuning starts after first run</div>",unsafe_allow_html=True)

    with sc2:
        if do_sim:
            with st.spinner("⟳  Simulating..."):
                prog2=st.progress(0,text="Running simulation...")
                for p in range(0,80,4): time.sleep(0.02); prog2.progress(p)
                cur_p=st.session_state.strategy_params.get(sim_strat,STRATEGIES[sim_strat]["params"])
                res=simulate_strategy(sim_strat,sim_cap,sim_candles,sim_pos,sim_fee,sim_sl,sim_tp,cur_p)
                st.session_state.sim_results=res
                st.session_state.sim_count+=1
                prog2.progress(85,text="🤖 AI auto-tuning parameters...")
                time.sleep(0.2)
                # ← AUTO AI TUNE — fires automatically
                new_params,tune_msgs,_=auto_ai_tune(sim_strat,res)
                prog2.progress(100); prog2.empty()

                # Add to sim history
                st.session_state.sim_history.insert(0,{"strategy":sim_strat,"return":round(res["total_ret"],2),"win_rate":round(res["win_rate"],1),"trades":res["trades"],"max_dd":round(res["max_dd"],1),"time":datetime.now().strftime("%H:%M:%S")})
                if len(st.session_state.sim_history)>50: st.session_state.sim_history=st.session_state.sim_history[:50]

                # Auto-log trades to journal
                for t in res["trade_log"]:
                    if t["type"]=="SELL":
                        st.session_state.trade_journal.insert(0,{"time":datetime.now().strftime("%H:%M:%S"),"source":f"SIM#{st.session_state.sim_count}","strategy":sim_strat,"side":t["type"],"price":round(t["price"],4),"pnl":t["pnl"],"reason":t["reason"][:40]})
                if len(st.session_state.trade_journal)>500: st.session_state.trade_journal=st.session_state.trade_journal[:500]

                push_alert(f"Sim #{st.session_state.sim_count} [{sim_strat[:18]}]: {res['total_ret']:+.2f}% · WR {res['win_rate']:.0f}% · params auto-updated","success" if res["total_ret"]>0 else "warning")

            changed=[m for m in tune_msgs if any(x in m for x in ["→","Tightened","Raised","Reduced","Widened","Relaxed","reset","blend"])]
            if changed:
                st.success(f"✓ Simulation #{st.session_state.sim_count} complete · 🤖 AI auto-tuned {len(changed)} parameter(s)")
                for msg in changed[:3]: st.info(f"🔧 {msg}")
            else:
                st.success(f"✓ Simulation #{st.session_state.sim_count} complete · 🤖 AI: near-optimal, monitoring")

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
            st.markdown("<div style='text-align:center;padding:80px 0;'><div style='font-size:4rem;color:#94a3b8;'>◈</div><div style='font-family:Syne,sans-serif;color:#64748b;letter-spacing:0.5px;font-size:0.9rem;'>CONFIGURE & RUN SIMULATION</div></div>",unsafe_allow_html=True)

    if st.session_state.sim_results:
        res=st.session_state.sim_results; st.markdown("---")
        af1,af2=st.columns(2)
        with af1:
            st.markdown("#### 📊 PERFORMANCE")
            wr=res["win_rate"]; ret=res["total_ret"]; dd=res["max_dd"]; pf=res["profit_factor"]
            if ret>20 and wr>60: st.success(f"✅ Strong: {ret:.1f}% · WR {wr:.0f}% — ready for forward-test")
            elif ret>0: st.info(f"📊 Moderate: {ret:.1f}% · WR {wr:.0f}% — AI refining")
            else: st.warning(f"⚠️ Underperforming: {ret:.1f}% — AI adjusting params")
            if dd>25: st.error(f"🚨 DD {dd:.1f}% — AI tightening risk")
            elif dd>15: st.warning(f"⚠️ DD {dd:.1f}% — monitoring")
            else: st.success(f"✅ DD {dd:.1f}% acceptable")
            if pf>1.5: st.success(f"✅ PF {pf:.2f} — strong edge")
            elif pf>1.0: st.info(f"📊 PF {pf:.2f} — marginal edge")
            else: st.error(f"❌ PF {pf:.2f} — AI aggressively retuning")
        with af2:
            st.markdown("#### 🤖 AI TUNING LOG")
            strat_log=[e for e in st.session_state.ai_log if e.get("strat")==res["strategy"]][:8]
            if strat_log:
                for e in strat_log:
                    ic="🟢" if "✅" in e["msg"] else("🟡" if "⚠️" in e["msg"] else "🔵")
                    rb=f"<span style='color:#64748b;font-size:0.6rem;'> [run {e.get('runs','?')} · WR {e.get('avg_wr','?')}%]</span>" if "runs" in e else ""
                    st.markdown(f"<div style='background:#eff6ff;border-left:2px solid #2563eb;padding:7px 11px;margin-bottom:4px;border-radius:0 4px 4px 0;font-size:0.72rem;color:#0f172a;'>{ic} {e['msg']}{rb}</div>",unsafe_allow_html=True)
            else:
                st.caption("No AI updates yet — run simulation to start tuning")

        # Sim history chart
        shc=chart_sim_history()
        if shc:
            st.markdown("---"); st.plotly_chart(shc,use_container_width=True)

        # Trade log + journal link
        st.markdown("---")
        st.markdown("#### TRADE LOG (current sim)")
        if res["trade_log"]:
            tdf=pd.DataFrame([{"Type":t["type"],"Price":fmt_price(float(t["price"])),"P&L %":(f"{t['pnl']:+.2f}%" if t["type"]=="SELL" else "—"),"Reason":t["reason"][:35],"Candle":f"#{t['i']}","Equity":f"${t['equity']:,.2f}"} for t in reversed(res["trade_log"])])
            def st_s(v): return "color:#059669;font-weight:700" if v=="BUY" else("color:#dc2626;font-weight:700" if v=="SELL" else "")
            def st_p(v):
                try: n=float(v.replace("%","").replace("+","")); return f"color:{'#00e5a0' if n>=0 else '#ff3d71'}"
                except: return "color:#64748b"
            st.dataframe((tdf.style.map(st_s,subset=["Type"]).map(st_p,subset=["P&L %"]).set_properties(**{"font-family":"Inter,sans-serif","font-size":"12px"})),use_container_width=True,height=280)
            _tlog_csv = tdf.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download trade log (.csv)",
                data=_tlog_csv,
                file_name=f"nexus_trades_sim{st.session_state.sim_count}.csv",
                mime="text/csv",
                key=f"tlog_dl_{st.session_state.sim_count}",
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — JOURNAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_journal:
    st.markdown("### TRADE JOURNAL")
    st.caption("Auto-populated from simulations · add manual trades · export to CSV")
    jc1,jc2=st.columns([2,1])
    with jc1:
        if st.session_state.trade_journal:
            jdf=pd.DataFrame(st.session_state.trade_journal)
            def sj_s(v): return "color:#059669;font-weight:700" if v=="BUY" else("color:#dc2626;font-weight:700" if v=="SELL" else "")
            def sj_p(v):
                try: n=float(str(v)); return f"color:{'#00e5a0' if n>0 else('#ff3d71' if n<0 else '#3d5068')}"
                except: return ""
            show_cols=[c for c in ["time","source","strategy","side","price","pnl","reason"] if c in jdf.columns]
            styled_j=jdf[show_cols].head(100).style
            if "side" in show_cols: styled_j=styled_j.map(sj_s,subset=["side"])
            if "pnl" in show_cols: styled_j=styled_j.map(sj_p,subset=["pnl"])
            styled_j=styled_j.set_properties(**{"font-size":"12px","font-family":"Inter,sans-serif"})
            st.dataframe(styled_j,use_container_width=True,height=380)
            _jrnl_csv = jdf.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download journal (.csv)",
                data=_jrnl_csv,
                file_name="nexus_trade_journal.csv",
                mime="text/csv",
                key="journal_dl_btn",
            )
        else:
            st.info("No trades yet. Run a simulation to auto-populate.")
    with jc2:
        st.markdown("#### Manual Trade Entry")
        with st.form("manual_trade"):
            mt_coin=st.selectbox("Coin",COINS)
            mt_side=st.radio("Side",["BUY","SELL"],horizontal=True)
            mt_strat=st.selectbox("Strategy",list(STRATEGIES.keys()))
            mt_entry=st.number_input("Entry Price",min_value=0.0,value=0.0,format="%.4f")
            mt_exit=st.number_input("Exit Price",min_value=0.0,value=0.0,format="%.4f")
            mt_notes=st.text_area("Notes",height=70)
            if st.form_submit_button("💾 LOG TRADE",use_container_width=True):
                pnl=round((mt_exit-mt_entry)/mt_entry*100,2) if mt_entry>0 else 0
                st.session_state.trade_journal.insert(0,{"time":datetime.now().strftime("%H:%M:%S"),"source":"MANUAL","strategy":mt_strat,"side":mt_side,"price":mt_exit,"pnl":pnl,"reason":mt_notes[:40]})
                push_alert(f"Manual trade: {mt_coin} {mt_side} P&L {pnl:+.2f}%","success")
                st.success("✓ Logged"); st.rerun()
        if st.session_state.trade_journal:
            try:
                pnls=[t["pnl"] for t in st.session_state.trade_journal if isinstance(t.get("pnl"),(int,float))]
                wins=[p for p in pnls if p>0]
                st.markdown("---"); st.markdown("#### Summary")
                st.metric("Total Trades",len(pnls)); st.metric("Win Rate",f"{len(wins)/max(len(pnls),1)*100:.0f}%",f"{len(wins)}W/{len(pnls)-len(wins)}L")
                st.metric("Total P&L",f"{sum(pnls):.2f}%"); st.metric("Best",f"+{max(pnls):.2f}%"); st.metric("Worst",f"{min(pnls):.2f}%")
            except: pass

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ALERTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    ah1,ah2,ah3=st.columns([3,1,1])
    with ah1: st.markdown("### ALERTS & AI LOG")
    with ah2:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("🗑 CLEAR ALERTS",use_container_width=True): st.session_state.alerts=[]; st.rerun()
    with ah3:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("🗑 CLEAR AI LOG",use_container_width=True): st.session_state.ai_log=[]; st.rerun()

    atab1,atab2=st.tabs(["📣 System Alerts","🤖 AI Tuning Log"])
    with atab1:
        if not st.session_state.alerts:
            st.markdown("<div style='text-align:center;padding:70px 0;'><div style='font-size:3.5rem;margin-bottom:14px;'>🔔</div><div style='font-family:Syne,sans-serif;font-size:0.85rem;letter-spacing:0.5px;color:#64748b;'>NO ALERTS YET</div></div>",unsafe_allow_html=True)
        else:
            kc={"success":"rgba(5,150,105,0.3)","info":"rgba(37,99,235,0.3)","warning":"rgba(217,119,6,0.4)","error":"rgba(220,38,38,0.3)"}
            ki={"success":"✅","info":"ℹ️","warning":"⚠️","error":"❌"}
            for a in st.session_state.alerts:
                k=a.get("kind","info"); bc=kc.get(k,"rgba(37,99,235,0.25)"); ic=ki.get(k,"ℹ️")
                st.markdown(f"<div style='background:#ffffff;border:1px solid {bc};border-left:3px solid {bc};border-radius:6px;padding:10px 15px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;'><div style='display:flex;gap:10px;align-items:center;'><span>{ic}</span><span style='font-size:0.77rem;color:#0f172a;'>{a['msg']}</span></div><span style='font-size:0.62rem;color:#64748b;white-space:nowrap;margin-left:12px;'>{a['time']}</span></div>",unsafe_allow_html=True)
            st.markdown("---")
            am1,am2,am3=st.columns(3)
            with am1: st.metric("Total",len(st.session_state.alerts))
            with am2: st.metric("✅",sum(1 for a in st.session_state.alerts if a.get("kind")=="success"))
            with am3: st.metric("⚠️",sum(1 for a in st.session_state.alerts if a.get("kind")=="warning"))
    with atab2:
        if not st.session_state.ai_log:
            st.markdown("<div style='text-align:center;padding:70px 0;'><div style='font-size:3rem;margin-bottom:14px;'>🤖</div><div style='font-family:Syne,sans-serif;font-size:0.82rem;letter-spacing:2px;color:#64748b;'>NO AI UPDATES YET — RUN A SIMULATION</div></div>",unsafe_allow_html=True)
        else:
            for e in st.session_state.ai_log[:50]:
                col="#00e5a0" if "✅" in e["msg"] else("#f5c542" if "⚠️" in e["msg"] else "#38bdf8")
                rb=f"<span style='color:#64748b;font-size:0.6rem;'> · run {e.get('runs','?')} · WR {e.get('avg_wr','?')}%</span>" if "runs" in e else ""
                st.markdown(f"<div style='background:#ffffff;border-left:3px solid {col};border-radius:0 6px 6px 0;padding:10px 14px;margin-bottom:4px;'><div style='display:flex;justify-content:space-between;'><span style='font-size:0.68rem;color:#2563eb;'>{e.get('strat','')}</span><span style='font-size:0.62rem;color:#64748b;'>{e.get('time','')} {rb}</span></div><div style='font-size:0.75rem;color:#0f172a;margin-top:3px;'>{e['msg']}</div></div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div style='text-align:center;padding:10px;font-size:0.62rem;color:#94a3b8;letter-spacing:2px;'>NEXUS AI CRYPTO BOT · EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE · EXPORT SESSION TO SAVE DATA</div>",unsafe_allow_html=True)
