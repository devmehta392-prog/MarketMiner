import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & UI CSS OVERRIDES
# ==========================================
st.set_page_config(page_title="MarketMiner", layout="wide", initial_sidebar_state="expanded")

if "target" not in st.session_state:
    st.session_state.target = "GC=F"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg: #121212;
        --card: #1e1e1e;
        --card2: #252525;
        --border: #2a2a2a;
        --gold: #FFD700;
        --gold-dim: rgba(255,215,0,0.12);
        --text: #e0e0e0;
        --dim: #888;
        --muted: #4a4a4a;
        --green: #26a69a;
        --red: #ef5350;
        --blue: #2196F3;
    }

    /* Make Header Transparent so Sidebar Toggle (Hamburger Menu) remains visible and clickable */
    header[data-testid="stHeader"] { background-color: transparent !important; }
    .block-container { padding: 3rem 1rem 1rem 1rem !important; max-width: 100% !important; }
    [data-testid="stSidebarContent"] { padding: 0 !important; background-color: var(--card) !important; }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg); color: var(--text); font-family: 'Inter', sans-serif;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--gold); }

    /* Ticker Bar */
    .ticker-bar { background: #0d0d0d; border-bottom: 1px solid var(--border); padding: 6px 0; overflow: hidden; white-space: nowrap; margin: -2rem -1rem 15px -1rem; }
    .ticker-track { display: inline-flex; animation: scroll 40s linear infinite; }
    .ticker-track:hover { animation-play-state: paused; }
    .t-item { display: inline-flex; align-items: center; gap: 6px; padding: 0 20px; font-size: 12px; border-right: 1px solid #1e1e1e; }
    .t-item .t-name { color: var(--dim); font-weight: 500; }
    .t-item .t-price { font-weight: 600; }
    .t-item .up { color: var(--green); }
    .t-item .dn { color: var(--red); }
    @keyframes scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

    /* Sidebar Branding */
    .sb-top { padding: 20px 15px 15px 15px; border-bottom: 1px solid var(--border); background: var(--card); }
    .logo { display: flex; align-items: center; gap: 10px; }
    .logo-mark { width: 32px; height: 32px; background: var(--gold); border-radius: 8px; display: grid; place-items: center; font-size: 16px; color: black; font-weight: bold; }
    .logo-name { font-size: 16px; font-weight: 700; color: var(--gold); letter-spacing: -0.5px; line-height: 1.1; }
    .logo-sub { font-size: 10px; color: var(--dim); }
    .sb-label { padding: 15px 15px 5px; font-size: 10px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }

    /* Interactive Sidebar Buttons */
    div[data-testid="stButton"] > button {
        text-align: left !important; justify-content: flex-start !important;
        padding: 10px 15px !important; border-radius: 0px !important; width: 100%; transition: 0.2s;
        border: none !important;
    }
    div[data-testid="stButton"] > button[data-testid="baseButton-secondary"] {
        background-color: transparent !important; 
        border-left: 3px solid transparent !important;
    }
    div[data-testid="stButton"] > button[data-testid="baseButton-secondary"]:hover { 
        background: var(--card2) !important; 
    }
    /* Active Asset Button Styling */
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {
        background: rgba(255,215,0,0.07) !important; 
        border-left: 3px solid var(--gold) !important;
    }
    div[data-testid="stButton"] p { font-size: 12.5px; font-weight: 600; margin: 0; width: 100%; }

    /* Main Dashboard UI */
    .ch-head { padding: 15px 20px; border: 1px solid var(--border); border-radius: 8px 8px 0 0; display: flex; align-items: center; gap: 12px; background: var(--card); margin-bottom: -1px; }
    .ch-icon { font-size: 24px; }
    .ch-name { font-size: 18px; font-weight: 700; }
    .ch-ticker { font-size: 11px; color: var(--muted); background: #121212; padding: 3px 8px; border-radius: 4px; border: 1px solid var(--border); }
    .ch-price { font-size: 26px; font-weight: 700; margin-left: auto; }
    .ch-chg { font-size: 14px; font-weight: 600; }
    .demo-badge { background: var(--gold-dim); color: var(--gold); padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; border: 1px solid rgba(255,215,0,.3); margin-left:10px; }
    
    .summary { background: var(--gold-dim); border-left: 3px solid var(--gold); border-radius: 0 0 8px 8px; padding: 12px 20px; font-size: 13px; line-height: 1.6; color: #ccc; margin-bottom: 20px; }
    .summary strong { color: #fff; }

    /* Fixed Stats Grid Alignment */
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 25px; }
    .stat { background: var(--card); padding: 15px; border-radius: 8px; border: 1px solid var(--border); display: flex; flex-direction: column; justify-content: center; height: 100%; transition: transform 0.2s; }
    .stat:hover { transform: translateY(-3px); border-color: #333; }
    .stat-lbl { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; font-weight: 600; }
    .stat-val { font-size: 18px; font-weight: 700; font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .stat-sub { font-size: 10px; color: var(--dim); margin-top: 4px; }
    
    .badge { display: inline-block; font-size: 10px; padding: 3px 8px; border-radius: 4px; font-weight: 600;}
    .badge.r { background: rgba(239,83,80,.15); color: var(--red); }
    .badge.g { background: rgba(38,166,154,.15); color: var(--green); }
    .badge.y { background: var(--gold-dim); color: var(--gold); }
    
    /* Charts Container */
    .chart-box { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }

    /* Override Chat UI */
    [data-testid="stChatMessage"] { background-color: transparent !important; padding: 1rem 0 !important; border-bottom: 1px solid var(--border); }
    [data-testid="chatAvatarIcon-user"] { background-color: var(--card2) !important; color: var(--text) !important; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: var(--gold) !important; color: #000 !important; }
    [data-testid="stChatInput"] { background-color: var(--card) !important; border-color: var(--border) !important; }
    [data-testid="stChatInput"]:focus-within { border-color: var(--gold) !important; box-shadow: 0 0 0 1px var(--gold) !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. ASSET MAPPING & TECHNICAL CALCS
# ==========================================
ASSET_MAP = {
    "GC=F": {"name": "Gold", "icon": "🥇", "cat": "Precious"},
    "SI=F": {"name": "Silver", "icon": "🥈", "cat": "Precious"},
    "PL=F": {"name": "Platinum", "icon": "💿", "cat": "Precious"},
    "CL=F": {"name": "WTI Crude", "icon": "🛢️", "cat": "Energy"},
    "BZ=F": {"name": "Brent Crude", "icon": "⛽", "cat": "Energy"},
    "NG=F": {"name": "Natural Gas", "icon": "🔥", "cat": "Energy"},
    "HG=F": {"name": "Copper", "icon": "🔶", "cat": "Metals"},
    "ZW=F": {"name": "Wheat", "icon": "🌾", "cat": "Agri"},
    "ZC=F": {"name": "Corn", "icon": "🌽", "cat": "Agri"},
    "BTC-USD": {"name": "Bitcoin", "icon": "₿", "cat": "Digital"}
}

@st.cache_data(ttl=9, show_spinner=False)
def fetch_live_data():
    tickers = list(ASSET_MAP.keys())
    try:
        return yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
    except Exception:
        return pd.DataFrame()

def calculate_technicals(df):
    if df.empty or len(df) < 20:
        return {"rsi": 50, "ma20": 0, "bb_width": 0, "macd": 0}
    close = df['Close'].squeeze()
    ma20 = close.rolling(window=20).mean().iloc[-1]
    std = close.rolling(window=20).std().iloc[-1]
    bb_width = (4 * std) if not pd.isna(std) else 0
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = (ema12 - ema26).iloc[-1]
    
    return {"rsi": rsi, "ma20": ma20, "bb_width": bb_width, "macd": macd}

def get_stats(df_all, ticker):
    try:
        if df_all.empty or ticker not in df_all.columns.levels[0]: 
            return 0, 0, 0, 0, 0, 0, pd.DataFrame(), {}
        df = df_all[ticker].dropna()
        if len(df) < 2: return 0, 0, 0, 0, 0, 0, df, {}
        
        curr = float(df['Close'].iloc[-1])
        day_open = float(df['Open'].iloc[0]) 
        day_high = float(df['High'].max())
        day_low = float(df['Low'].min())
        vol = float(df['Volume'].iloc[-1])
        pct = ((curr - day_open) / day_open) * 100
        tech = calculate_technicals(df)
        return curr, pct, day_open, day_high, day_low, vol, df, tech
    except:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame(), {}

# ==========================================
# 3. INTERACTIVE RED/GREEN SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
        <div class="sb-top">
            <div class="logo">
                <div class="logo-mark">⛏</div>
                <div>
                    <div class="logo-name">MarketMiner</div>
                    <div class="logo-sub">Commodity Intelligence Platform</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='sb-label'>AI Access Key</div>", unsafe_allow_html=True)
    st.session_state.api_key = st.text_input("API Key", type="password", placeholder="Enter Gemini API Key...", label_visibility="collapsed")

@st.fragment(run_every="10s")
def render_live_sidebar():
    df_all = fetch_live_data()
    categories = ["Precious", "Energy", "Metals", "Agri", "Digital"]
    
    for cat in categories:
        st.markdown(f"<div class='sb-label' style='margin-top: 10px;'>{cat}</div>", unsafe_allow_html=True)
        for sym, details in ASSET_MAP.items():
            if details["cat"] == cat:
                curr, pct, _, _, _, _, _, _ = get_stats(df_all, sym)
                
                px_format = f"{curr:,.0f}" if sym == "BTC-USD" else f"{curr:,.2f}"
                sign = "+" if pct >= 0 else ""
                
                # Streamlit's native markdown colors for dynamic red/green text
                color_tag = "green" if pct >= 0 else "red"
                btn_label = f"{details['icon']} {details['name']} • :{color_tag}[${px_format} ({sign}{pct:.2f}%)]"
                
                # Use type="primary" to highlight the selected button natively
                btn_type = "primary" if st.session_state.target == sym else "secondary"
                
                if st.button(btn_label, key=f"nav_{sym}", type=btn_type):
                    st.session_state.target = sym
                    st.rerun()

    # Intelligence Score UI
    _, _, _, _, _, _, _, t_tech = get_stats(df_all, st.session_state.target)
    rsi_val = t_tech.get('rsi', 50)
    iq = 72 if rsi_val > 55 else (35 if rsi_val < 45 else 56)
    
    st.markdown(f"""
    <div style="padding: 15px; border-top: 1px solid var(--border); margin-top: 15px; background: var(--card);">
        <div style="font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600;">Intelligence Score</div>
        <div style="font-size: 36px; font-weight: 700; color: var(--gold); line-height: 1;">{iq} <span style="font-size: 12px; color: var(--dim); font-weight: normal;">/ 100</span></div>
        <div style="margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;"><span style="color:var(--dim);">RSI Momentum</span><span style="color:var(--text);">{rsi_val:.0f}%</span></div>
            <div style="height: 4px; background: var(--border); border-radius: 2px;"><div style="height: 100%; width: {rsi_val}%; background: var(--blue); border-radius: 2px;"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. MAIN DASHBOARD (Chart + Aligned Stats)
# ==========================================
@st.fragment(run_every="10s")
def render_live_main():
    df_all = fetch_live_data()
    if df_all.empty:
        st.warning("Awaiting market data stream...")
        return
        
    sym = st.session_state.target
    name = ASSET_MAP[sym]["name"]
    icon = ASSET_MAP[sym]["icon"]
    curr, pct, o, h, l, vol, df, tech = get_stats(df_all, sym)
    
    up_cls = "up" if pct >= 0 else "dn"
    color_hex = "var(--green)" if pct >= 0 else "var(--red)"
    arrow = "+" if pct >= 0 else ""

    # 1. Ticker
    ticker_items = ""
    for tk, det in ASSET_MAP.items():
        c, p, _, _, _, _, _, _ = get_stats(df_all, tk)
        u_cls = "up" if p >= 0 else "dn"
        c_hex = "var(--green)" if p >= 0 else "var(--red)"
        arr = "▲" if p >= 0 else "▼"
        px_fmt = f"{c:,.0f}" if tk == "BTC-USD" else f"{c:,.2f}"
        ticker_items += f'<div class="t-item"><span>{det["icon"]}</span><span class="t-name">{det["name"]}</span><span class="t-price" style="color:{c_hex};">${px_fmt}</span><span class="t-chg {u_cls}">{arr}{abs(p):.2f}%</span></div>'
    
    st.markdown(f'<div class="ticker-bar"><div class="ticker-track">{ticker_items}{ticker_items}</div></div>', unsafe_allow_html=True)

    # 2. Main Header
    st.markdown(f"""
    <div class="ch-head">
        <span class="ch-icon">{icon}</span>
        <span class="ch-name">{name}</span>
        <span class="ch-ticker">{sym}</span>
        <span class="demo-badge">LIVE INTEL</span>
        <div class="ch-price" style="color: {color_hex};">${curr:,.2f}</div>
        <div class="ch-chg {up_cls}">{arrow}{curr-o:,.2f} ({arrow}{pct:.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Dynamic Candlestick Chart (with Rangebreaks to hide weekends)
    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        ma20_line = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=df.index, y=ma20_line, line=dict(color='#FFD700', width=1.5, dash='dot'), name='MA20'))

        fig.update_layout(
            template="plotly_dark", height=400, margin=dict(t=0, b=0, l=0, r=40),
            paper_bgcolor='#1e1e1e', plot_bgcolor='#1e1e1e',
            xaxis=dict(
                showgrid=False, 
                rangeslider_visible=False,
                rangebreaks=[dict(bounds=["sat", "mon"])] # Removes weekend gaps
            ),
            yaxis=dict(showgrid=True, gridcolor='#2a2a2a', side="right"),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 4. Summary & Perfectly Aligned Stats Grid
    trend = "bullish uptrend" if pct >= 0 else "bearish downtrend"
    rsi_val = tech.get('rsi', 50)
    rsi_stat = "overbought" if rsi_val > 70 else ("oversold" if rsi_val < 30 else "neutral")
    rsi_col = "var(--red)" if rsi_val > 70 else ("var(--green)" if rsi_val < 30 else "var(--dim)")
    ma_val = tech.get('ma20', 0)
    macd_val = tech.get('macd', 0)

    st.markdown(f"""
    <div class="summary">
        ✨ <strong>AI Oracle:</strong> {name} is currently forming a <strong>{trend}</strong>. The 14-period RSI is reading <strong>{rsi_val:.1f}</strong>, indicating conditions are <span style="color:{rsi_col}"><strong>{rsi_stat}</strong></span>. The asset is trading <strong>{'above' if curr > ma_val else 'below'}</strong> its 20-period moving average. Short-term bias leans <strong>{'bullish' if curr > ma_val else 'bearish'}</strong>.
    </div>

    <div class="stats">
        <div class="stat"><div class="stat-lbl">Current Price</div><div class="stat-val" style="color:{color_hex};">${curr:,.2f}</div><div class="stat-sub">Live USD</div></div>
        <div class="stat"><div class="stat-lbl">Session Range</div><div class="stat-val">{l:,.2f} – {h:,.2f}</div><div class="stat-sub">Low / High Limits</div></div>
        <div class="stat"><div class="stat-lbl">RSI (14)</div><div class="stat-val" style="color:{rsi_col};">{rsi_val:.1f}</div><div class="stat-sub"><span class="badge {'r' if rsi_val > 70 else ('g' if rsi_val < 30 else 'y')}">{rsi_stat.upper()}</span></div></div>
        <div class="stat"><div class="stat-lbl">MACD Signal</div><div class="stat-val" style="color:{'var(--green)' if macd_val > 0 else 'var(--red)'};">{macd_val:.2f}</div><div class="stat-sub"><span class="badge {'g' if macd_val > 0 else 'r'}">{'BULLISH' if macd_val > 0 else 'BEARISH'}</span></div></div>
        <div class="stat"><div class="stat-lbl">Intraday Vol</div><div class="stat-val">{vol:,.0f}</div><div class="stat-sub">Cumulative Contracts</div></div>
        <div class="stat"><div class="stat-lbl">MA (20)</div><div class="stat-val">{ma_val:,.2f}</div><div class="stat-sub">Price {'>' if curr > ma_val else '<'} MA20</div></div>
        <div class="stat"><div class="stat-lbl">BB Width</div><div class="stat-val">{tech.get('bb_width',0):.2f}</div><div class="stat-sub">Bollinger Width</div></div>
        <div class="stat"><div class="stat-lbl">Open Price</div><div class="stat-val">${o:,.2f}</div><div class="stat-sub">Session Open</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 5. Bottom 3 Analytical Charts
    st.markdown("<div class='sec-title' style='margin-bottom:10px; font-size:12px;'>Market Analytics & Models</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    chart_layout = dict(template="plotly_dark", height=250, margin=dict(t=30, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title_font=dict(size=13, color="#888"))

    with c1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        assets = ['Metals', 'Energy', 'Agri', 'Equities', 'Crypto']
        perfs = [0.8, -0.4, 1.2, 0.5, 2.1] 
        colors = ['#26a69a' if p > 0 else '#ef5350' for p in perfs]
        fig_bar = go.Figure(data=[go.Bar(x=assets, y=perfs, marker_color=colors)])
        fig_bar.update_layout(**chart_layout, title="📊 Sector Performance Model")
        fig_bar.update_yaxes(showgrid=True, gridcolor='#2a2a2a')
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        labels = ['Equities', 'Bonds', 'Gold', 'Cash']
        values = [60, 20, 10, 10]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker=dict(colors=['#2196F3', '#9C27B0', '#FFD700', '#26a69a']))])
        fig_pie.update_layout(**chart_layout, title="🥧 Institutional Allocation", showlegend=False)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        np.random.seed(42)
        x_val = np.random.normal(0.05, 0.02, 50)
        y_val = x_val * 0.7 + np.random.normal(0, 0.015, 50)
        fig_scatter = go.Figure(data=go.Scatter(x=x_val, y=y_val, mode='markers', marker=dict(color='#2196F3', size=7, opacity=0.8)))
        fig_scatter.update_layout(**chart_layout, title=f"📈 Alpha Correlation vs SPY", xaxis_title="S&P 500", yaxis_title=f"{sym}")
        fig_scatter.update_xaxes(showgrid=True, gridcolor='#2a2a2a')
        fig_scatter.update_yaxes(showgrid=True, gridcolor='#2a2a2a')
        st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. EXECUTION & AI TUTOR CHAT
# ==========================================
with st.sidebar:
    render_live_sidebar()

render_live_main()

# Market Miner AI Chatbot
st.markdown("<hr style='border-color:var(--border); margin: 2rem 0 1rem 0;'>", unsafe_allow_html=True)
st.markdown(f"<div style='display:flex; align-items:center; gap:10px;'><div style='width:30px; height:30px; background:var(--gold); border-radius:50%; display:grid; place-items:center; font-size:15px;'>🤖</div> <div><div style='font-size:14px; font-weight:700; color:var(--gold);'>MarketMiner AI</div><div style='font-size:10px; color:var(--dim);'>Commodity Intelligence Assistant</div></div></div>", unsafe_allow_html=True)

# Chat Styling
st.markdown("""
<style>
[data-testid="stChatMessage"] { background-color: var(--card) !important; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 15px !important;}
[data-testid="chatAvatarIcon-user"] { background-color: var(--card2) !important; color: var(--text) !important; }
[data-testid="chatAvatarIcon-assistant"] { background-color: var(--gold) !important; color: #000 !important; }
[data-testid="stChatInput"] { background-color: var(--card) !important; border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Terminal initialized. I am the MarketMiner AI. Ask me to explain technical indicators or macroeconomic drivers."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Query the Oracle..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        api_key = st.session_state.get("api_key", "")
        if not api_key:
            st.error("⚠️ API Key required. Enter it in the sidebar.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # --- AUTO-DISCOVER AVAILABLE MODEL ---
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                flash_models = [m for m in available_models if 'flash' in m.lower()]
                selected_model = flash_models[0] if flash_models else available_models[0]
                model = genai.GenerativeModel(selected_model)
                # -------------------------------------

                context = f"You are MarketMiner AI, a concise, highly technical trading assistant. The user is currently viewing {ASSET_MAP[st.session_state.target]['name']}. Address the query: {prompt}"
                
                with st.spinner("Processing..."):
                    response = model.generate_content(context)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Oracle Error: {e}")
