import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import altair as alt
import re  

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { fill: red; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; }
    
    .mini-card-container { display: flex; flex-wrap: nowrap; overflow-x: auto; gap: 10px; padding-bottom: 10px; margin-bottom: 25px; }
    .mini-card { min-width: 140px; border: 1px solid #333; border-radius: 8px; padding: 12px 10px; background-color: #212529; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); }
    .mini-title { font-size: 13px; color: #f8f9fa; font-weight: bold; margin-bottom: 6px; }
    .mini-time { font-size: 11px; color: #adb5bd; margin-top: 6px; }
    .mini-price { font-size: 18px; font-weight: 900; margin-bottom: 2px; }
    .mini-pct { font-size: 12px; font-weight: bold; }

    .ex-div-box { background-color: #ffeaea; border: 1.5px solid #e06666; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px; height: 115px; display: flex; flex-direction: column; justify-content: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); overflow-y: auto;}
    .ex-div-title { color: #cc0000; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .ex-div-text { color: #783f04; font-size: 12px; font-weight: bold; line-height: 1.4; }
    
    .pay-div-box { background-color: #fff2cc; border: 1.5px solid #f6b26b; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px; height: 115px; display: flex; flex-direction: column; justify-content: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); overflow-y: auto;}
    .pay-div-title { color: #b45f06; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .pay-div-text { color: #783f04; font-size: 12px; font-weight: bold; line-height: 1.4; }

    .triple-box { background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; padding: 15px; display: flex; flex-wrap: wrap; justify-content: space-around; align-items: center; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.04); gap: 10px; }
    .triple-col { flex: 1 1 30%; min-width: 140px; text-align: center; padding: 10px 0; }
    .triple-title { font-size: 14px; color: #757575; font-weight: bold; margin-bottom: 5px; }
    .triple-val-r { font-size: 28px; font-weight: 900; color: #d32f2f; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-g { font-size: 28px; font-weight: 900; color: #388e3c; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-gold { font-size: 28px; font-weight: 900; color: #f39c12; font-family: Arial, sans-serif; line-height: 1.1; text-shadow: 1px 1px 2px rgba(243, 156, 18, 0.3); }
    .triple-pct-r { font-size: 14px; font-weight: bold; color: #d32f2f; margin-top: 5px; }
    .triple-pct-g { font-size: 14px; font-weight: bold; color: #388e3c; margin-top: 5px; }
    .triple-sub-gold { font-size: 12px; font-weight: bold; color: #7f8c8d; margin-top: 5px; }

    @keyframes lightning-strike {
        0% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
        50% { box-shadow: 0 0 40px rgba(255, 235, 59, 1), inset 0 0 25px rgba(255, 235, 59, 0.9); background-color: #ffffe0; border-color: #ffeb3b; transform: scale(1.03); }
        100% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
    }
    .flash-gold-box { background-color: #fffdf5; border-radius: 12px; padding: 15px; border: 2px solid #f1c40f; animation: lightning-strike 0.1s infinite; }

    .month-card { background-color: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 10px; border: 1px solid #ced4da; }
    .month-title { font-size: 20px; font-weight: bold; color: #495057; }
    .month-amount { font-size: 28px; font-weight: bold; color: #d9534f; margin: 10px 0; }
    .month-sources { font-size: 14px; color: #6c757d; }
    
    div.stButton > button { font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 系統設定與資料庫 ---
SETTINGS_FILE = 'settings.json'

PASSIVE_ETFS = {
    "0050": "0050 元大台灣50", "006208": "006208 富邦台50", "00692": "00692 富邦公司治理", 
    "00850": "00850 元大台灣ESG永續", "00922": "00922 國泰台灣領袖50", "00923": "00923 群益台ESG低碳50",
    "0056": "0056 元大高股息", "00878": "00878 國泰永續高股息", "00713": "00713 元大台灣高息低波",
    "00900": "00900 富邦特選高股息30", "00915": "00915 凱基優選高股息30", "00918": "00918 大華優利高填息30",
    "00919": "00919 群益台灣精選高息", "00929": "00929 復華台灣科技優息", "00936": "00936 台新永續高息中小",
    "00939": "00939 統一台灣高息動能", "00940": "00940 元大台灣價值高息", "00944": "00944 野村趨勢動能高息", 
    "00946": "00946 群益科技高息成長", "0052": "0052 富邦科技", "00881": "00881 國泰台灣5G+", 
    "00891": "00891 中信關鍵半導體", "00892": "00892 富邦台灣半導體", "00927": "00927 群益半導體收益", 
    "00935": "00935 野村臺灣新科技50", "00941": "00941 中信上游半導體", "00893": "00893 國泰智能電動車", 
    "00895": "00895 富邦未來車", "00646": "00646 元大S&P500", "00662": "00662 富邦NASDAQ", 
    "00830": "00830 國泰費城半導體", "00757": "00757 統一FANG+", "00882": "00882 中信中國高股息", 
    "00962": "00962 洲際美國大型龍頭", "00963": "00963 中信全球高股息", "00964": "00964 中信亞太高股息",
    "00679B": "00679B 元大美債20年", "00687B": "00687B 國泰20年美債", "00720B": "00720B 元大投資級公司債",
    "00751B": "00751B 元大AAA至A公司債", "00937B": "00937B 群益ESG投等債20+", "00772B": "00772B 中信高評級公司債",
    "00773B": "00773B 中信優先金融債", "00780B": "00780B 國泰A級金融債", "00795B": "00795B 中信美國公債20年",
    "2330": "2330 台積電", "2454": "2454 聯發科", "2317": "2317 鴻海",
    "2887": "2887 台新金", "2888": "2888 新光金",
    "00631L": "00631L 元大台灣50正2", "00673R": "00673R 期元大S&P原油反1", 
    "00632R": "00632R 元大台灣50反1", "009819": "009819 中信數據及電力", 
    "00712": "00712 復華富時不動產"
}

ACTIVE_ETFS = {
    "00981A": "00981A 主動統一台股增長", "00403A": "00403A 主動統一台股升級50",
    "00999A": "00999A 主動野村臺灣動能", "00401A": "00401A 主動摩根台灣鑫收",
    "00982A": "00982A 主動群益台灣強棒", "00400A": "00400A 主動國泰動能高息",
    "00997A": "00997A 主動群益美國增長", "00988A": "00988A 主動統一全球創新",
    "00994A": "00994A 主動第一金台股優",
}

ETF_NAME_DB = {**PASSIVE_ETFS, **ACTIVE_ETFS}

DIVIDEND_SCHEDULE = {
    "0050.TW": [1, 7], "0056.TW": [1, 4, 7, 10], "00878.TW": [2, 5, 8, 11],
    "00891.TW": [2, 5, 8, 11], "00919.TW": [3, 6, 9, 12], "00927.TW": [1, 4, 7, 10],
    "00929.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "00940.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "2887.TW": [7]
}

DIVIDEND_DB = {
    "0050.TW": {"v": 1.0, "d": "2026-07-16", "p": "2026-08-15"},
    "0056.TW": {"v": 1.0, "d": "2026-04-16", "p": "2026-05-15"}, 
    "00927.TW": {"v": 0.94, "d": "2026-04-18", "p": "2026-05-15"}  
}

ETF_CONSTITUENTS_DB = {
    "0056.TW": [{"name": "鴻海", "weight": 6.5}, {"name": "聯發科", "weight": 5.2}, {"name": "聯詠", "weight": 4.8}, {"name": "中信金", "weight": 4.5}, {"name": "聯電", "weight": 4.1}, {"name": "其他", "weight": 74.9}],
    "00878.TW": [{"name": "聯發科", "weight": 5.5}, {"name": "國泰金", "weight": 5.1}, {"name": "富邦金", "weight": 4.9}, {"name": "廣達", "weight": 4.5}, {"name": "聯電", "weight": 4.2}, {"name": "其他", "weight": 75.8}],
    "00919.TW": [{"name": "長榮", "weight": 11.5}, {"name": "聯電", "weight": 6.2}, {"name": "瑞昱", "weight": 5.8}, {"name": "聯發科", "weight": 5.1}, {"name": "聯詠", "weight": 4.8}, {"name": "其他", "weight": 66.6}],
    "00927.TW": [{"name": "台積電", "weight": 31.2}, {"name": "聯發科", "weight": 15.5}, {"name": "聯電", "weight": 6.5}, {"name": "日月光投控", "weight": 5.8}, {"name": "瑞昱", "weight": 5.2}, {"name": "其他", "weight": 35.8}],
    "00891.TW": [{"name": "台積電", "weight": 30.5}, {"name": "聯發科", "weight": 14.2}, {"name": "聯電", "weight": 6.1}, {"name": "日月光投控", "weight": 5.5}, {"name": "瑞昱", "weight": 5.0}, {"name": "其他", "weight": 38.7}],
    "00929.TW": [{"name": "聯發科", "weight": 9.5}, {"name": "聯電", "weight": 7.2}, {"name": "日月光投控", "weight": 6.8}, {"name": "瑞昱", "weight": 6.5}, {"name": "聯詠", "weight": 6.1}, {"name": "其他", "weight": 63.9}],
    "0050.TW": [{"name": "台積電", "weight": 52.5}, {"name": "鴻海", "weight": 5.5}, {"name": "聯發科", "weight": 4.8}, {"name": "廣達", "weight": 2.1}, {"name": "台達電", "weight": 1.9}, {"name": "其他", "weight": 33.2}],
    "006208.TW": [{"name": "台積電", "weight": 52.6}, {"name": "鴻海", "weight": 5.4}, {"name": "聯發科", "weight": 4.9}, {"name": "廣達", "weight": 2.0}, {"name": "台達電", "weight": 1.8}, {"name": "其他", "weight": 33.3}],
    "00713.TW": [{"name": "統一", "weight": 8.5}, {"name": "台灣大", "weight": 7.2}, {"name": "遠傳", "weight": 6.8}, {"name": "華碩", "weight": 6.1}, {"name": "仁寶", "weight": 5.5}, {"name": "其他", "weight": 65.9}],
    "00940.TW": [{"name": "長榮", "weight": 9.5}, {"name": "聯電", "weight": 6.5}, {"name": "聯發科", "weight": 5.8}, {"name": "中美晶", "weight": 5.2}, {"name": "神基", "weight": 4.8}, {"name": "其他", "weight": 68.2}]
}

def load_settings():
    default_data = {
        "etfs": [
            {"symbol": "0050.TW", "name": "元大台灣50", "holdings": 2.0, "div_holdings": 2.0, "cost": 90.58},
            {"symbol": "0056.TW", "name": "元大高股息", "holdings": 20.0, "div_holdings": 20.0, "cost": 38.87},
            {"symbol": "00878.TW", "name": "國泰永續高股息", "holdings": 21.0, "div_holdings": 21.0, "cost": 24.42},
            {"symbol": "00891.TW", "name": "中信關鍵半導體", "holdings": 8.0, "div_holdings": 8.0, "cost": 33.70},
            {"symbol": "00927.TW", "name": "群益半導體收益", "holdings": 20.0, "div_holdings": 20.0, "cost": 28.65},
            {"symbol": "00981A.TW", "name": "主動統一台股增長", "holdings": 15.0, "div_holdings": 15.0, "cost": 28.10},
            {"symbol": "00982A.TW", "name": "主動群益台灣強棒", "holdings": 5.0, "div_holdings": 5.0, "cost": 22.84} 
        ], 
        "pledge": {"borrowed_amount": 0}
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: 
                data = json.load(f)
                if 'etfs' not in data or not data['etfs']:
                    data['etfs'] = default_data['etfs']
                
                for etf in data['etfs']:
                    if etf.get('symbol') == '00992A.TW' and "強棒" in etf.get('name', ''):
                        etf['symbol'] = '00982A.TW'
                    
                    etf.setdefault('div_holdings', etf.get('holdings', 0.0))
                    etf.setdefault('pledged_shares', 0.0)
                    etf.setdefault('manual_price', 0.0)
                    etf.setdefault('manual_prev_price', 0.0)  
                    etf.setdefault('manual_div', 0.0)
                    etf.setdefault('manual_freq', "")
                    etf.setdefault('manual_months', "")
                    etf.setdefault('manual_ex_date', "")
                    etf.setdefault('manual_pay_date', "")
                return data
        except: pass
    return default_data

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: 
    st.session_state.my_data = load_settings()

if 'pledge' not in st.session_state.my_data:
    st.session_state.my_data['pledge'] = {"borrowed_amount": 0}

for etf in st.session_state.my_data['etfs']:
    if 'div_holdings' not in etf: etf['div_holdings'] = etf.get('holdings', 0.0)
    if 'pledged_shares' not in etf: etf['pledged_shares'] = 0.0
    if 'manual_price' not in etf: etf['manual_price'] = 0.0
    if 'manual_prev_price' not in etf: etf['manual_prev_price'] = 0.0
    if 'manual_div' not in etf: etf['manual_div'] = 0.0
    if 'manual_freq' not in etf: etf['manual_freq'] = ""
    if 'manual_months' not in etf: etf['manual_months'] = ""
    if 'manual_ex_date' not in etf: etf['manual_ex_date'] = ""
    if 'manual_pay_date' not in etf: etf['manual_pay_date'] = ""
save_to_json(st.session_state.my_data)

# --- 🚀 Callback 函數區 ---
def auto_fill_etf_name():
    raw_sym = st.session_state.get('add_sym_bot', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    if clean_sym:
        st.session_state.add_name_bot = ETF_NAME_DB.get(clean_sym, f"{clean_sym} ETF")
    else:
        st.session_state.add_name_bot = ""

def add_new_etf_bot():
    raw_sym = st.session_state.get('add_sym_bot', '')
    new_name = st.session_state.get('add_name_bot', '')
    new_h = st.session_state.get('add_h_bot', 0.0)
    new_c = st.session_state.get('add_c_bot', 0.0)

    clean_symbol = raw_sym.strip().upper().replace(".TW", "")
    if clean_symbol and new_name:
        final_symbol = f"{clean_symbol}.TW" 
        
        st.session_state.my_data['etfs'].append({
            "symbol": final_symbol, "name": new_name, 
            "holdings": new_h, "div_holdings": new_h, "cost": new_c, 
            "pledged_shares": 0.0, "manual_price": 0.0, "manual_prev_price": 0.0,
            "manual_div": 0.0, "manual_freq": "", "manual_months": "", 
            "manual_ex_date": "", "manual_pay_date": ""
        })
        save_to_json(st.session_state.my_data)
        
        st.session_state.add_sym_bot = ""
        st.session_state.add_name_bot = ""
        st.session_state.add_h_bot = 0.0
        st.session_state.add_c_bot = 0.0

def delete_etf(index):
    if 0 <= index < len(st.session_state.my_data['etfs']):
        st.session_state.my_data['etfs'].pop(index)
        save_to_json(st.session_state.my_data)

if 'show_us' not in st.session_state: st.session_state.show_us = False
if 'show_tw' not in st.session_state: st.session_state.show_tw = False
if 'show_calendar' not in st.session_state: st.session_state.show_calendar = False
if 'show_div_db' not in st.session_state: st.session_state.show_div_db = False
if 'show_tech' not in st.session_state: st.session_state.show_tech = False
if 'show_holdings' not in st.session_state: st.session_state.show_holdings = False
if 'show_constituents' not in st.session_state: st.session_state.show_constituents = False 
if 'show_pledge' not in st.session_state: st.session_state.show_pledge = False 
if 'show_history' not in st.session_state: st.session_state.show_history = False 

def toggle_us(): st.session_state.show_us = not st.session_state.show_us
def toggle_tw(): st.session_state.show_tw = not st.session_state.show_tw
def toggle_calendar(): st.session_state.show_calendar = not st.session_state.show_calendar
def toggle_div_db(): st.session_state.show_div_db = not st.session_state.show_div_db
def toggle_tech(): st.session_state.show_tech = not st.session_state.show_tech
def toggle_holdings(): st.session_state.show_holdings = not st.session_state.show_holdings
def toggle_constituents(): st.session_state.show_constituents = not st.session_state.show_constituents
def toggle_pledge(): st.session_state.show_pledge = not st.session_state.show_pledge 
def toggle_history(): st.session_state.show_history = not st.session_state.show_history

@st.cache_data(ttl=60)
def fetch_mini_indices():
    tickers = {
        "那斯達克": "^IXIC", "費半指數": "^SOX", "NASDAQ-100": "^NDX",
        "MICRON (美光)": "MU", "NVIDIA CORP": "NVDA", "台積電 ADR": "TSM",
        "台指近全": "WTX&P" 
    }
    results = []
    for name, sym in tickers.items():
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="5d")
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]; prev = hist['Close'].iloc[-2]
                diff = curr - prev; pct = (diff / prev) * 100
                time_str = hist.index[-1].strftime("%H:%M")
                results.append({"name": name, "price": curr, "diff": diff, "pct": pct, "time": time_str})
        except: pass 
    return results

@st.cache_data(ttl=300) 
def fetch_macro_data():
    tickers = {
        "us": {"道瓊工業": "^DJI", "那斯達克": "^IXIC", "費城半導體": "^SOX", "輝達 NVIDIA": "NVDA", "台積電 ADR": "TSM"},
        "tw": {"台股加權 (大盤)": "^TWII", "台積電 (台股)": "2330.TW", "聯發科 (台股)": "2454.TW", "台指期 (近月)": "WTX&P"} 
    }
    res = {"us": {}, "tw": {}}
    for region, t_dict in tickers.items():
        for name, symbol in t_dict.items():
            try:
                tk = yf.Ticker(symbol)
                hist = tk.history(period="5d")
                if len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]; prev = hist['Close'].iloc[-2]
                    diff = curr - prev; pct = (diff / prev) * 100
                    date_str = hist.index[-1].strftime("%m/%d")
                    res[region][name] = {"price": curr, "diff": diff, "pct": pct, "date": date_str}
            except: pass
    return res

def render_macro_cards(data_dict, region_prefix):
    cols = st.columns(3); idx = 0
    for name, data in data_dict.items():
        is_up = data['diff'] >= 0
        color_hex = "#d32f2f" if is_up else "#388e3c" 
        sign = "+" if is_up else ""
        html = f"""
        <div style="border:1px solid #e0e0e0; border-radius:8px; border-left:6px solid {color_hex}; padding:15px; margin-bottom:15px; background:#fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="color:{color_hex}; font-size:15px; display:flex; align-items:center;">
                    <div style="width:10px; height:10px; border-radius:50%; background-color:{color_hex}; margin-right:6px;"></div>
                    <span style="font-weight:900; margin-right:4px;">{region_prefix}</span> <span style="font-weight:bold;">{name}</span>
                </div>
                <div style="color:#888; font-size:12px;">🕒 {data['date']}</div>
            </div>
            <div style="font-size:26px; font-weight:900; color:#111; margin-bottom:5px;">{data['price']:,.2f}</div>
            <div style="font-size:14px; font-weight:bold; color:{color_hex};">{sign}{data['diff']:,.2f} ({sign}{data['pct']:.2f}%)</div>
        </div>
        """
        with cols[idx % 3]: st.markdown(html, unsafe_allow_html=True)
        idx += 1

# --- 全新功能：抓取歷史區間資料 ---
@st.cache_data(ttl=300)
def fetch_historical_pnl(etfs, start_date, end_date):
    fetch_start = start_date - timedelta(days=10) 
    res = {}
    for etf in etfs:
        try:
            tk = yf.Ticker(etf['symbol'])
            df = tk.history(start=fetch_start, end=end_date + timedelta(days=1))
            if df.empty: continue
            
            df['Pct'] = df['Close'].pct_change() * 100
            
            # 移除時區，避免日期比對或索引出錯
            df.index = df.index.tz_localize(None)
            df['DateObj'] = df.index.date
            
            mask = (df['DateObj'] >= start_date) & (df['DateObj'] <= end_date)
            df_filtered = df.loc[mask].copy()
            
            if not df_filtered.empty:
                # 排序後，強制轉換為 list 寫入
                df_filtered = df_filtered.sort_index(ascending=False)
                
                display_df = pd.DataFrame({
                    '日期': df_filtered.index.strftime('%m/%d').tolist(),
                    '幅(%)': df_filtered['Pct'].fillna(0).tolist()
                })
                
                res[etf['name']] = display_df
        except:
            pass
    return res

# --- 4. 核心數據計算 ---
@st.cache_data(ttl=10)
def fetch_data(etf_list):
    if not etf_list: return pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0, [], [], {i: {"amount": 0, "sources": []} for i in range(1, 13)}
    results, tech_results = [], []
    total_mkt, total_cost, total_div, total_today_pnl = 0, 0, 0, 0
    radar_ex, radar_pay = [], []
    monthly_calendar = {i: {"amount": 0, "sources": []} for i in range(1, 13)} 
    today = datetime.today()

    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period='1y') 
            
            rt_curr = tk.fast_info.get('lastPrice')
            curr_p = rt_curr if rt_curr is not None else (hist['Close'].iloc[-1] if not hist.empty else 0.0)
            
            rt_prev = tk.fast_info.get('previousClose')
            prev_close = rt_prev if rt_prev is not None else (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
            
            rt_dh = tk.fast_info.get('dayHigh')
            day_high = rt_dh if rt_dh is not None else (hist['High'].iloc[-1] if not hist.empty else 0.0)
            
            rt_dl = tk.fast_info.get('dayLow')
            day_low = rt_dl if rt_dl is not None else (hist['Low'].iloc[-1] if not hist.empty else 0.0)
            
            rt_vol = tk.fast_info.get('lastVolume')
            vol = rt_vol if rt_vol is not None else (hist['Volume'].iloc[-1] if not hist.empty else 0.0)
            
            year_high = tk.fast_info.get('yearHigh', 0)
            year_low = tk.fast_info.get('yearLow', 0)

            manual_price = float(item.get('manual_price', 0.0))
            if manual_price > 0:
                curr_p = manual_price
                if prev_close == 0: prev_close = manual_price 
                
            manual_prev = float(item.get('manual_prev_price', 0.0))
            if manual_prev > 0:
                prev_close = manual_prev

            if curr_p == 0: continue 

            if curr_p > prev_close: status_light = "🔴"
            elif curr_p < prev_close: status_light = "🟢"
            else: status_light = "⚪"
            display_name = f"{status_light} {item['name']}"

            # 核心修正：將目前庫存與配息張數獨立計算
            shares = item['holdings'] * 1000
            div_shares = item.get('div_holdings', item['holdings']) * 1000

            mkt_val = shares * curr_p
            cost_val = shares * item['cost']
            
            sell_cost_estimate = mkt_val * 0.00235
            profit = mkt_val - cost_val - sell_cost_estimate
            roi = (profit / cost_val * 100) if cost_val != 0 else 0
            
            today_diff = curr_p - prev_close
            today_pct_change = (today_diff / prev_close * 100) if prev_close else 0
            today_profit = shares * today_diff
            
            total_today_pnl += today_profit
            today_pnl_str = f"+${today_profit:,.0f}" if today_profit >= 0 else f"-${abs(today_profit):,.0f}"
            today_diff_str = f"+{today_diff:.2f}" if today_diff > 0 else f"{today_diff:.2f}"
            today_pct_str = f"+{today_pct_change:.2f}%" if today_pct_change > 0 else f"{today_pct_change:.2f}%"

            is_announced, div_amount, ex_date, pay_date = False, 0, "待官方公告", "待官方公告"
            
            cfg = DIVIDEND_DB.get(item['symbol'])
            if cfg:
                div_amount = cfg['v']; ex_date = cfg['d']; pay_date = cfg['p']; is_announced = True
            else:
                actions = tk.actions
                if not actions.empty:
                    latest = actions.sort_index(ascending=False).head(1)
                    div_amount = float(latest['Dividends'].values[0]) 
                    last_ex_date_obj = latest.index[0].replace(tzinfo=None)
                    if last_ex_date_obj.date() >= today.date():
                        ex_date = last_ex_date_obj.strftime('%Y-%m-%d')
                        pay_date = (last_ex_date_obj + timedelta(days=28)).strftime('%Y-%m-%d') 
                        is_announced = True

            manual_div = float(item.get('manual_div', 0.0))
            manual_freq = str(item.get('manual_freq', "")).strip()
            manual_months_str = str(item.get('manual_months', "")).strip()
            manual_ex_date = str(item.get('manual_ex_date', "")).strip()
            manual_pay_date = str(item.get('manual_pay_date', "")).strip()
            
            if manual_div > 0: div_amount = manual_div

            if manual_ex_date and manual_ex_date.lower() != 'nan':
                ex_date = manual_ex_date
                is_announced = True
            if manual_pay_date and manual_pay_date.lower() != 'nan':
                pay_date = manual_pay_date
                is_announced = True

            months_to_pay = DIVIDEND_SCHEDULE.get(item['symbol'], [])
            if manual_months_str and manual_months_str.lower() != 'nan':
                nums = re.findall(r'\d+', manual_months_str)
                if nums:
                    months_to_pay = [int(n) for n in nums if 1 <= int(n) <= 12]

            if is_announced and ex_date != "待官方公告":
                try:
                    clean_ex = ex_date.replace('/', '-')
                    ex_date_obj = datetime.strptime(clean_ex, '%Y-%m-%d')
                    days_diff_ex = (ex_date_obj.date() - today.date()).days
                    if 0 <= days_diff_ex <= 20: radar_ex.append({"symbol": item['symbol'].split('.')[0], "date": clean_ex, "days": days_diff_ex})
                except: pass
                
            if is_announced and pay_date != "待官方公告":
                try:
                    clean_pay = pay_date.replace('/', '-')
                    pay_date_obj = datetime.strptime(clean_pay, '%Y-%m-%d')
                    days_diff_pay = (pay_date_obj.date() - today.date()).days
                    # 雷達領息一律使用 div_shares 計算
                    if 0 <= days_diff_pay <= 20: radar_pay.append({"symbol": item['symbol'].split('.')[0], "date": clean_pay, "amount": div_shares * div_amount, "days": days_diff_pay})
                except: pass

            if div_amount > 0 and div_shares > 0:
                explicit_pay_month = None
                if is_announced and pay_date != "待官方公告":
                    try:
                        clean_pay = pay_date.replace('/', '-')
                        explicit_pay_month = datetime.strptime(clean_pay, '%Y-%m-%d').month
                        # 月曆預估一律使用 div_shares 計算
                        monthly_calendar[explicit_pay_month]["amount"] += (div_shares * div_amount)
                        if item['name'] not in monthly_calendar[explicit_pay_month]["sources"]:
                            monthly_calendar[explicit_pay_month]["sources"].append(item['name'])
                    except: pass

                for m in months_to_pay:
                    pay_m = m + 1 if m < 12 else 1
                    if pay_m != explicit_pay_month:
                        monthly_calendar[pay_m]["amount"] += (div_shares * div_amount)
                        if item['name'] not in monthly_calendar[pay_m]["sources"]:
                            monthly_calendar[pay_m]["sources"].append(item['name'])

            fill_status = "-"
            try:
                divs = tk.dividends
                if not divs.empty:
                    now_ts = pd.Timestamp.now(tz=divs.index.tzinfo) if divs.index.tzinfo else pd.Timestamp.now()
                    past_divs = divs[divs.index < now_ts].sort_index(ascending=False)
                    if not past_divs.empty:
                        last_ex_date = past_divs.index[0]
                        pre_ex = hist[hist.index < last_ex_date]
                        post_ex = hist[hist.index >= last_ex_date]
                        if not pre_ex.empty and not post_ex.empty:
                            target_price = pre_ex['Close'].iloc[-1]
                            filled = False; t_days = 0
                            for d, r in post_ex.iterrows():
                                t_days += 1
                                if r['High'] >= target_price:
                                    fill_status = f"{d.month}/{d.day} 填息完成 ({t_days}天)"
                                    filled = True; break
                            if not filled: fill_status = f"未填息 ({t_days}天)"
            except: pass
            
            display_freq = "未知"
            if manual_freq and manual_freq.lower() != 'nan': display_freq = manual_freq
            elif len(months_to_pay) == 12: display_freq = "月配息"
            elif len(months_to_pay) == 4: display_freq = "季配息"
            elif len(months_to_pay) == 2: display_freq = "半年配"
            elif len(months_to_pay) == 1: display_freq = "年配息"

            total_mkt += mkt_val; total_cost += cost_val; 
            total_div += (div_shares * div_amount * (len(months_to_pay) if len(months_to_pay)>0 else 1))
            
            results.append({
                "代號": item['symbol'], "名稱": item['name'], 
                "現價/成本": f"{curr_p:.2f} / {item['cost']:.2f}",
                "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "配息張數": item.get('div_holdings', item['holdings']),
                "市值": mkt_val, "損益": profit, "報酬率": roi,
                "單次預估領息": div_shares * div_amount, "每股配息": div_amount,
                "配息頻率": display_freq,
                "配息月份": "、".join(map(str, months_to_pay)) + " 月" if months_to_pay else "未設定",
                "最新公告除息日": ex_date, "預估發放日": pay_date, "已公告": is_announced,
                "最新填息紀錄": fill_status 
            })
            
            tech_results.append({
                "ETF 名稱": display_name, "股票張數": item['holdings'], 
                "現價": curr_p, 
                "今日損益": today_pnl_str,
                "今日漲跌": today_diff_str,
                "今日漲跌幅": today_pct_str,
                "校正昨收價(填0自動)": manual_prev, 
                "今日交易量": f"{vol:,.0f}" if vol > 0 else "無資料",
                "今日最高/最低": f"${day_high:.2f} / ${day_low:.2f}",
                "52週最高/最低": f"${year_high:.2f} / ${year_low:.2f}"
            })
            
        except Exception as e: continue
        
    return pd.DataFrame(results), pd.DataFrame(tech_results), total_mkt, total_cost, total_div, total_today_pnl, radar_ex, radar_pay, monthly_calendar

df, df_tech, g_mkt, g_cost, g_div, g_today_pnl, radar_ex, radar_pay, monthly_calendar = fetch_data(st.session_state.my_data['etfs'])
macro_data = fetch_macro_data()
mini_indices_data = fetch_mini_indices()

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if mini_indices_data:
    mini_html = '<div class="mini-card-container">'
    for d in mini_indices_data:
        is_up = d['diff'] >= 0
        color_hex = "#d32f2f" if is_up else "#388e3c"
        sign = "▲" if is_up else "▼"
        mini_html += f"<div class='mini-card'><div class='mini-title'>{d['name']}</div><div class='mini-price' style='color: {color_hex};'>{d['price']:,.2f}</div><div class='mini-pct' style='color: {color_hex};'>{sign} {abs(d['diff']):.2f} ({abs(d['pct']):.2f}%)</div><div class='mini-time'>🕒 {d['time']}</div></div>"
    mini_html += '</div>'
    st.markdown(mini_html, unsafe_allow_html=True)

st.markdown("### 👾 戰情室專屬：雙重雷達提醒")
col1, col2, _ = st.columns([1, 1, 1])

def get_etf_months(etf):
    manual_m = str(etf.get('manual_months', '')).strip()
    if manual_m and manual_m.lower() != 'nan':
        nums = re.findall(r'\d+', manual_m)
        if nums:
            return [int(n) for n in nums if 1 <= int(n) <= 12]
    return DIVIDEND_SCHEDULE.get(etf['symbol'], [])

with col1:
    if radar_ex:
        radar_ex = sorted(radar_ex, key=lambda x: x['days'])
        ex_content = "".join([f"<div style='margin-bottom: 4px; font-weight:bold;'>標的 {r['symbol']} 將於 {r['date'][5:7]}/{r['date'][8:10]} 除息 (倒數 {r['days']} 天)</div>" for r in radar_ex])
        st.markdown(f"<div class='ex-div-box'><div class='ex-div-title'>⚡ 除息雷達提醒 ⚡</div><div class='ex-div-text'>{ex_content}</div></div>", unsafe_allow_html=True)
    else:
        current_m = datetime.today().month
        next_m = current_m + 1 if current_m < 12 else 1
        
        this_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if current_m in get_etf_months(etf)]
        next_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if next_m in get_etf_months(etf)]
        
        if this_m_etfs:
            msg = f"本月 ({current_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:16px;'>{', '.join(this_m_etfs)}</span><br><span style='font-size:11px; color:#888;'>雷達持續掃描官方公告中...</span>"
        elif next_m_etfs:
            msg = f"下個月 ({next_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:16px;'>{', '.join(next_m_etfs)}</span><br><span style='font-size:11px; color:#888;'>雷達持續掃描官方公告中...</span>"
        else:
            msg = "目前無 20 天內已公告之除息<br><span style='font-size:11px; color:#888;'>近期亦無表定除息標的</span>"
            
        st.markdown(f" <div class='ex-div-box' style='background-color: #f4f6f8; border: 1.5px dashed #adb5bd; box-shadow: none;'><div class='ex-div-title' style='color: #6c757d;'>📡 預測雷達 (等待官方公告)</div><div class='ex-div-text' style='color: #495057;'>{msg}</div></div>", unsafe_allow_html=True)

with col2:
    if radar_pay:
        radar_pay = sorted(radar_pay, key=lambda x: x['days'])
        pay_content = "".join([f"<div style='margin-bottom: 4px; font-weight:bold;'>標的 {r['symbol']} 股息約 ${r['amount']:,.0f} 將於 {r['date'][5:7]}/{r['date'][8:10]} 入帳 (倒數 {r['days']} 天)！</div>" for r in radar_pay])
        st.markdown(f"<div class='pay-div-box'><div class='pay-div-title'>💰 領息雷達提醒 💰</div><div class='pay-div-text'>{pay_content}</div></div>", unsafe_allow_html=True)
    else: 
        st.markdown(f" <div class='pay-div-box' style='background-color: #fafafa; border: 1.5px dashed #ddd;'><div class='pay-div-title' style='color: #888;'>💰 領息雷達提醒 💰</div><div class='pay-div-text' style='color:#666;'>目前無 20 天內領息雷達提示</div></div>", unsafe_allow_html=True)

total_net_profit = df['損益'].sum() if not df.empty else 0
r_total = (total_net_profit / g_cost * 100) if g_cost != 0 else 0
prev_mkt = g_mkt - g_today_pnl
today_pct = (g_today_pnl / prev_mkt * 100) if prev_mkt != 0 else 0

today_val_str = f"+{g_today_pnl:,.0f}" if g_today_pnl >= 0 else f"{g_today_pnl:,.0f}"
today_pct_str = f"+{today_pct:.2f}%" if today_pct >= 0 else f"{today_pct:.2f}%"
today_c_val = "triple-val-r" if g_today_pnl >= 0 else "triple-val-g"
today_c_pct = "triple-pct-r" if g_today_pnl >= 0 else "triple-pct-g"

total_val_str = f"+{total_net_profit:,.0f}" if total_net_profit >= 0 else f"{total_net_profit:,.0f}"
total_pct_str = f"+{r_total:.2f}%" if r_total >= 0 else f"{r_total:.2f}%"
total_c_val = "triple-val-r" if total_net_profit >= 0 else "triple-val-g"
total_c_pct = "triple-pct-r" if total_net_profit >= 0 else "triple-pct-g"

current_month_num = datetime.today().month
current_month_div_amount = monthly_calendar[current_month_num]["amount"]
current_month_div_str = f"${current_month_div_amount:,.0f}"
div_sources = monthly_calendar[current_month_num]["sources"]
if div_sources:
    sources_str = "、".join([s.split(' ')[0] for s in div_sources]) 
    sub_title = f"來自：{sources_str}"
else:
    sub_title = "本月無現金流入預定"

html_triple_pnl = f"""
<div class="triple-box">
    <div class="triple-col">
        <div class="triple-title">今日損益</div>
        <div class="{today_c_val}">{today_val_str}</div>
        <div class="{today_c_pct}">{today_pct_str}</div>
    </div>
    <div class="triple-col">
        <div class="triple-title">累積預估淨損益 (已扣手續費/稅)</div>
        <div class="{total_c_val}">{total_val_str}</div>
        <div class="{total_c_pct}">{total_pct_str}</div>
    </div>
    <div class="triple-col flash-gold-box">
        <div class="triple-title" style="color: #b48608; margin-bottom: 5px;">⚡ {current_month_num} 月預估領息總額</div>
        <div class="triple-val-gold">{current_month_div_str}</div>
        <div class="triple-sub-gold">{sub_title}</div>
    </div>
</div>
"""
st.markdown(html_triple_pnl, unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("股票總市值", f"${g_mkt:,.0f}")
c2.metric("投資總成本", f"${g_cost:,.0f}")
c3.metric("全年預估總領息", f"${g_div:,.0f}")
st.write("---")

# ================================
# 🔥 新增：專屬快速更新張數與成本的區塊 (有小按鈕)
# ================================
with st.expander("🔢 快速修改庫存 (張數/成本) 小按鈕區", expanded=False):
    st.info("💡 「目前庫存」決定你的總市值與損益；「配息張數」專門用來計算你『領息當下』持有的張數，兩者完全分離，修改互不干擾！")
    edit_list = [{
        "ETF 名稱": e['name'], 
        "目前庫存 (張)": float(e['holdings']), 
        "持股均價": float(e['cost']),
        "配息張數 (張)": float(e.get('div_holdings', e['holdings']))
    } for e in st.session_state.my_data['etfs']]
    
    if edit_list:
        quick_edit_df = st.data_editor(
            pd.DataFrame(edit_list),
            column_config={
                "ETF 名稱": st.column_config.TextColumn("ETF 名稱", disabled=True),
                "目前庫存 (張)": st.column_config.NumberColumn("目前庫存 (張)", format="%.2f", step=1.0),
                "持股均價": st.column_config.NumberColumn("持股均價", format="%.2f", step=0.1),
                "配息張數 (張)": st.column_config.NumberColumn("配息張數 (張)", format="%.2f", step=1.0)
            },
            use_container_width=True, hide_index=True
        )
        if st.button("💾 確認更新設定", type="primary"):
            for i, row in quick_edit_df.iterrows():
                st.session_state.my_data['etfs'][i]['holdings'] = float(row['目前庫存 (張)'])
                st.session_state.my_data['etfs'][i]['cost'] = float(row['持股均價'])
                st.session_state.my_data['etfs'][i]['div_holdings'] = float(row['配息張數 (張)'])
            save_to_json(st.session_state.my_data)
            st.cache_data.clear()
            st.rerun()
    else:
        st.write("目前尚無庫存資料，請至下方『標的管理』新增。")
st.write("---")

us_icon = "🌏"
if "us" in macro_data and macro_data["us"]:
    us_up = sum(1 for v in macro_data["us"].values() if v['diff'] >= 0)
    us_down = len(macro_data["us"]) - us_up
    us_icon = "🔴" if us_up >= us_down else "🟢"

tw_icon = "🇹🇼"
if "tw" in macro_data and macro_data["tw"]:
    tw_up = sum(1 for v in macro_data["tw"].values() if v['diff'] >= 0)
    tw_down = len(macro_data["tw"]) - tw_up
    tw_icon = "🔴" if tw_up >= tw_down else "🟢"

cols_btn_r1 = st.columns(3)
cols_btn_r2 = st.columns(3)
cols_btn_r3 = st.columns(3)

b1_lbl, b1_typ = (f"🔽 收起美股指數 {us_icon}", "primary") if st.session_state.show_us else (f"{us_icon} 展開美股指數", "secondary")
b2_lbl, b2_typ = (f"🔽 收起台股指數 {tw_icon}", "primary") if st.session_state.show_tw else (f"{tw_icon} 展開台股指數", "secondary")
b3_lbl, b3_typ = ("🔽 收起每月領息", "primary") if st.session_state.show_calendar else ("📅 展開每月領息", "secondary")

b4_lbl, b4_typ = ("🔽 收起除權息", "primary") if st.session_state.show_div_db else ("📂 展開除權息", "secondary")
b5_lbl, b5_typ = ("🔽 收起股價監控", "primary") if st.session_state.show_tech else ("📡 展開股價監控", "secondary")
b6_lbl, b6_typ = ("🔽 收起持股明細", "primary") if st.session_state.show_holdings else ("📊 展開持股明細", "secondary")

b7_lbl, b7_typ = ("🔽 收起ETF成份股", "primary") if st.session_state.show_constituents else ("🧩 展開ETF成份股", "secondary")
b8_lbl, b8_typ = ("🔽 收起質押專區", "primary") if st.session_state.show_pledge else ("🏦 展開質押專區", "secondary") 
b9_lbl, b9_typ = ("🔽 收起歷史漲跌", "primary") if st.session_state.show_history else ("📈 展開歷史漲跌", "secondary") 

with cols_btn_r1[0]: st.button(b1_lbl, on_click=toggle_us, type=b1_typ, use_container_width=True)
with cols_btn_r1[1]: st.button(b2_lbl, on_click=toggle_tw, type=b2_typ, use_container_width=True)
with cols_btn_r1[2]: st.button(b3_lbl, on_click=toggle_calendar, type=b3_typ, use_container_width=True)

with cols_btn_r2[0]: st.button(b4_lbl, on_click=toggle_div_db, type=b4_typ, use_container_width=True)
with cols_btn_r2[1]: st.button(b5_lbl, on_click=toggle_tech, type=b5_typ, use_container_width=True)
with cols_btn_r2[2]: st.button(b6_lbl, on_click=toggle_holdings, type=b6_typ, use_container_width=True)

with cols_btn_r3[0]: st.button(b7_lbl, on_click=toggle_constituents, type=b7_typ, use_container_width=True) 
with cols_btn_r3[1]: st.button(b8_lbl, on_click=toggle_pledge, type=b8_typ, use_container_width=True) 
with cols_btn_r3[2]: st.button(b9_lbl, on_click=toggle_history, type=b9_typ, use_container_width=True) 

st.write("---")

if st.session_state.show_us and "us" in macro_data and macro_data["us"]:
    st.markdown("#### 🌏 關鍵美股指標")
    render_macro_cards(macro_data["us"], "us")
    st.write("")

if st.session_state.show_tw and "tw" in macro_data and macro_data["tw"]:
    st.markdown("#### 🇹🇼 關鍵台股點數")
    render_macro_cards(macro_data["tw"], "tw")
    st.write("---")

if st.session_state.show_calendar:
    st.markdown("#### 📅 1~12月 預估領息日曆")
    month_options = [f"{m} 月" for m in range(1, 13)]
    default_index = datetime.today().month - 1
    selected_month_str = st.selectbox("請選擇您想查詢的月份：", month_options, index=default_index)
    selected_month = int(selected_month_str.replace(" 月", ""))
    data = monthly_calendar[selected_month]
    sources_text = "、".join(data["sources"]) if data["sources"] else "本月無除息預定"
    amount_text = f"${data['amount']:,.0f}" if data["amount"] > 0 else "$0"
    col_space1, col_center, col_space2 = st.columns([1, 2, 1])
    with col_center:
        st.markdown(f"""
        <div class='month-card'>
            <div class='month-title'>{selected_month} 月預估領息</div>
            <div class='month-amount'>{amount_text}</div>
            <div class='month-sources'>ETF 來源：{sources_text}</div>
        </div>
        """, unsafe_allow_html=True)
    st.write("---")

if st.session_state.show_div_db:
    st.markdown("#### 📚 專屬庫存除權息時程總覽")
    db_list = []
    if not df.empty:
        for _, row in df.iterrows():
            db_list.append({
                "類別": "💼 庫存", "ETF 名稱": row['名稱'], "配息頻率": row['配息頻率'], 
                "配息月份": row['配息月份'], "狀態": "✅ 已公告" if row['已公告'] else "⏳ 依估算或手動", 
                "除息日": row['最新公告除息日'], "發放日": row['預估發放日'], 
                "每股金額": f"${row['每股配息']:.3f}", "最新填息紀錄": row['最新填息紀錄']
            })
            
    df_port_div = pd.DataFrame(db_list)
    if not df_port_div.empty: st.dataframe(df_port_div, use_container_width=True, hide_index=True)
    else: st.info("目前尚無庫存。")
    st.write("---")

if st.session_state.show_tech:
    if not df.empty:
        st.markdown("#### 📡 庫存價格區間監控與技術分析")
        st.info("💡 如果 yfinance 的昨日收盤價不準導致損益有誤差，請直接雙擊下方表格中的 **「校正昨收價」** 欄位輸入正確金額，系統會立刻修正漲跌與 % 數！")
        def color_profit_loss(val):
            if isinstance(val, str):
                if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;' 
                elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;' 
            return ''

        try: styled_df_tech = df_tech.style.map(color_profit_loss, subset=['今日損益', '今日漲跌', '今日漲跌幅'])
        except AttributeError: styled_df_tech = df_tech.style.applymap(color_profit_loss, subset=['今日損益', '今日漲跌', '今日漲跌幅'])

        edited_tech = st.data_editor(
            styled_df_tech,
            column_config={
                "校正昨收價(填0自動)": st.column_config.NumberColumn("校正昨收價(填0自動)", min_value=0.0, format="%.2f"),
                "現價": st.column_config.NumberColumn("現價", format="%.2f"),
                "股票張數": st.column_config.NumberColumn("股票張數", format="%.1f") 
            },
            disabled=["ETF 名稱", "股票張數", "現價", "今日損益", "今日漲跌", "今日漲跌幅", "今日交易量", "今日最高/最低", "52週最高/最低"],
            use_container_width=True, hide_index=True
        )

        has_changes = False
        for _, row in edited_tech.iterrows():
            display_name = row['ETF 名稱']
            new_prev = row['校正昨收價(填0自動)']
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] in display_name:
                    if etf.get('manual_prev_price', 0.0) != new_prev:
                        etf['manual_prev_price'] = new_prev; has_changes = True
                    break
        if has_changes: save_to_json(st.session_state.my_data); st.cache_data.clear(); st.rerun()
    else:
        st.markdown("#### 📡 庫存價格區間監控"); st.info("目前無庫存標的。")
    st.write("---")
    
if st.session_state.show_holdings:
    if not df.empty:
        st.markdown("#### 📊 持股動態明細")
        for _, row in df.iterrows():
            p_color = "red" if row['損益'] >= 0 else "green"; roi_str = f"{row['報酬率']:+.2f}%"
            status_badge = "✅ 已公告" if row['已公告'] else "⏳ 依前次估算"
            with st.expander(f"💎 {row['名稱']} | 預估淨報酬: :{p_color}[{roi_str}]", expanded=True):
                col_l, col_m, col_r = st.columns(3)
                with col_l: 
                    st.write(f"目前庫存: **{row['張數']} 張** (參與配息: **{row['配息張數']} 張**)")
                    st.write(f"現價 / 成本: **{row['現價/成本']}**")
                with col_m: 
                    st.markdown(f"市值: **${row['市值']:,.0f}**")
                    st.markdown(f"預估淨利: :{p_color}[**${row['損益']:,.0f}**]")
                with col_r: 
                    st.markdown(f"單次領息估算: :orange[**${row['單次預估領息']:,.0f}**]")
                    st.caption(f"📅 最新除息日: {row['最新公告除息日']} ({status_badge})")
    else: st.info("⚠️ 目前尚無持股資料。請至下方「⚙️ 標的管理」新增您的庫存！")
    st.write("---")

if st.session_state.show_constituents:
    if not df.empty:
        st.markdown("#### 🧩 專屬庫存 ETF 核心成分股佔比")
        
        c_cols = st.columns(3)
        for idx, item in enumerate(st.session_state.my_data['etfs']):
            sym = item['symbol']
            name = item['name']
            
            comp_data = ETF_CONSTITUENTS_DB.get(sym, [{"name": "其他成分股", "weight": 100.0}])
            df_comp = pd.DataFrame(comp_data)
            df_comp['label'] = df_comp['weight'].apply(lambda w: f"{w:.1f}%" if w >= 2.0 else "")
            
            base = alt.Chart(df_comp).encode(
                theta=alt.Theta("weight:Q", stack=True),
                color=alt.Color("name:N", sort=alt.EncodingSortField(field="weight", op="sum", order="descending"), legend=alt.Legend(title=None, orient="right", labelFontSize=12)),
                tooltip=[alt.Tooltip("name:N", title="成分股"), alt.Tooltip("weight:Q", title="權重 (%)", format=".2f")]
            )
            
            pie = base.mark_arc(outerRadius=100, innerRadius=0)
            text = base.mark_text(radius=125, size=13, fontWeight="bold", color="#333333").encode(text="label:N")
            chart = alt.layer(pie, text).properties(height=280).configure_view(strokeWidth=0)
            
            with c_cols[idx % 3]:
                st.markdown(f"<div style='font-weight:900; color:#1e3c72; font-size:16px; margin-bottom:5px; margin-top:15px;'>🛡️ {name}</div>", unsafe_allow_html=True)
                st.altair_chart(chart, use_container_width=True)
    else: st.info("⚠️ 目前尚無持股資料。請至下方「⚙️ 標的管理」新增您的庫存！")
    st.write("---")

if st.session_state.show_pledge:
    if not df.empty:
        st.markdown("#### 🏦 股票質押專區 (維持率監控)")
        
        pledge_data = st.session_state.my_data['pledge']
        borrowed = st.number_input("💸 輸入已向券商借入款項總額 (元)", min_value=0, value=int(pledge_data.get('borrowed_amount', 0)), step=10000)
        
        if borrowed != pledge_data.get('borrowed_amount', 0):
            st.session_state.my_data['pledge']['borrowed_amount'] = borrowed; save_to_json(st.session_state.my_data); st.rerun()

        pledge_df_list = []
        total_pledge_mkt = 0; total_borrowable = 0
        for item in st.session_state.my_data['etfs']:
            sym = item['symbol']; name = item['name']; h_total = item['holdings']; p_shares = item.get('pledged_shares', 0.0)
            try: curr_p = df[df['代號'] == sym]['現價'].values[0]
            except: curr_p = 0
                
            p_mkt = p_shares * 1000 * curr_p
            p_limit = p_mkt * 0.6  
            total_pledge_mkt += p_mkt; total_borrowable += p_limit
            
            pledge_df_list.append({
                "ETF 名稱": name, "總庫存 (張)": h_total, "質押張數": p_shares,
                "現價": round(curr_p, 2), "質押市值 (元)": round(p_mkt, 0), "可借上限 (60%)": round(p_limit, 0) 
            })
            
        pledge_df = pd.DataFrame(pledge_df_list)
        margin_ratio = (total_pledge_mkt / borrowed * 100) if borrowed > 0 else 0
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("擔保品總市值", f"${total_pledge_mkt:,.0f}")
        col_m2.metric("🎯 總可借款上限 (60%)", f"${total_borrowable:,.0f}")
        col_m3.metric("💸 已借入總額", f"${borrowed:,.0f}")
        
        if borrowed > 0:
            if margin_ratio < 130: col_m4.metric("🚨 目前維持率", f"{margin_ratio:.2f}%", "危險：低於 130% 將面臨斷頭", delta_color="inverse")
            elif margin_ratio < 160: col_m4.metric("⚠️ 目前維持率", f"{margin_ratio:.2f}%", "注意：市場波動可能導致風險", delta_color="off")
            else: col_m4.metric("✅ 目前維持率", f"{margin_ratio:.2f}%", "安全：維持率處於健康水平", delta_color="normal")
        else: col_m4.metric("目前維持率", "0.00%")

        st.write("👇 **請雙擊下方表格的「質押張數」欄位，設定您已向券商質押的庫存：**")
        edited_pledge = st.data_editor(
            pledge_df,
            column_config={
                "質押張數": st.column_config.NumberColumn("質押張數 (雙擊編輯)", min_value=0.0, step=1.0, format="%.1f"),
                "現價": st.column_config.NumberColumn("現價", format="%.2f"),
                "質押市值 (元)": st.column_config.NumberColumn("質押市值 (元)", format="%.0f"),
                "可借上限 (60%)": st.column_config.NumberColumn("可借上限 (60%)", format="%.0f") 
            },
            disabled=["ETF 名稱", "總庫存 (張)", "現價", "質押市值 (元)", "可借上限 (60%)"],
            use_container_width=True, hide_index=True
        )
        
        has_p_changes = False
        for _, row in edited_pledge.iterrows():
            p_name = row['ETF 名稱']; new_p_shares = row['質押張數']
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] == p_name and etf.get('pledged_shares', 0.0) != new_p_shares:
                    etf['pledged_shares'] = new_p_shares; has_p_changes = True; break
        if has_p_changes: save_to_json(st.session_state.my_data); st.rerun()
    else: st.info("⚠️ 目前尚無持股資料，無法進行質押計算。")
    st.write("---")

# ================================
# 🔥 全新橫向卡片式功能區：每日歷史漲跌追蹤
# ================================
if st.session_state.show_history:
    if not df.empty:
        st.markdown("#### 📅 庫存歷史走勢洞察 (網格小卡片檢視)")
        col_d1, col_d2, col_d3 = st.columns([1, 1, 2])
        with col_d1: start_d = st.date_input("開始日期", datetime.today().date() - timedelta(days=14))
        with col_d2: end_d = st.date_input("結束日期", datetime.today().date())
        
        st.caption("提示：已將傳統表格改為「上日期、下漲幅」的橫向動態方塊，空間不夠會自動換到第二行，一目瞭然！")
        
        hist_dict = fetch_historical_pnl(st.session_state.my_data['etfs'], start_d, end_d)
        
        if hist_dict:
            for name, d_df in hist_dict.items():
                # 繪製每個 ETF 的專屬標題
                st.markdown(f"<div style='font-size:16px; font-weight:900; color:#1e3c72; margin-bottom:8px; border-left: 4px solid #1e3c72; padding-left: 8px;'>{name}</div>", unsafe_allow_html=True)
                
                # 開啟一個橫向的彈性容器 (Flexbox)
                cards_html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 25px;'>"
                
                for _, row in d_df.iterrows():
                    date_str = row['日期']
                    pct = row['幅(%)']
                    
                    if pd.isna(pct):
                        pct = 0.0
                        
                    if pct > 0:
                        color = "#d32f2f"  # 紅色
                        sign = "+"
                    elif pct < 0:
                        color = "#388e3c"  # 綠色
                        sign = ""
                    else:
                        color = "#7f8c8d"  # 灰色
                        sign = ""
                        
                    # 每個日期的獨立小方塊 (完全移除縮排避免 Markdown 解析為 Code block)
                    cards_html += "<div style='border: 1px solid #ddd; border-radius: 6px; padding: 4px 6px; text-align: center; min-width: 65px; background-color: #fff; box-shadow: 1px 1px 2px rgba(0,0,0,0.05);'>"
                    cards_html += f"<div style='font-size: 11px; color: #888; border-bottom: 1px dashed #eee; padding-bottom: 2px; margin-bottom: 3px;'>{date_str}</div>"
                    cards_html += f"<div style='font-size: 13px; font-weight: 900; color: {color};'>{sign}{pct:.2f}%</div>"
                    cards_html += "</div>"
                
                # 關閉彈性容器
                cards_html += "</div>"
                
                # 一次性輸出這整列 ETF 的 HTML
                st.markdown(cards_html, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 查無歷史資料，請確認日期區間是否正確。")
    else: st.info("目前尚無持股資料。")
    st.write("---")

with st.expander("⚙️ 標的管理 (庫存新增 / 刪除)", expanded=False):
    st.markdown("#### ➕ 新增庫存標的 (股票/ETF)")
    
    if "add_name_bot" not in st.session_state: st.session_state.add_name_bot = ""
    if "add_sym_bot" not in st.session_state: st.session_state.add_sym_bot = ""
    if "add_h_bot" not in st.session_state: st.session_state.add_h_bot = 0.0
    if "add_c_bot" not in st.session_state: st.session_state.add_c_bot = 0.0

    st.text_input("輸入代碼 (不需手打 .TW)", placeholder="例如: 00878", key="add_sym_bot", on_change=auto_fill_etf_name)
    st.text_input("自定義名稱", placeholder="例如: 00878 國泰永續高股息", key="add_name_bot")
    
    col_add1, col_add2 = st.columns(2)
    with col_add1: st.number_input("張數", step=1.0, key="add_h_bot")
    with col_add2: st.number_input("均價", step=0.1, key="add_c_bot")
    
    st.button("確認新增庫存", key="btn_add_bot", use_container_width=True, on_click=add_new_etf_bot)

    if st.session_state.my_data['etfs']:
        st.write("---")
        st.markdown("#### 📝 庫存刪除")
        for i, item in enumerate(st.session_state.my_data['etfs']):
            cols_del = st.columns([3, 1])
            cols_del[0].markdown(f"📍 **{item['name']}**")
            cols_del[1].button("🗑️ 刪除", key=f"del_{i}", on_click=delete_etf, args=(i,), use_container_width=True)

st.write("---")

# ================================
# 🔥 手動校正專區 (包含配息頻率、月份、日期)
# ================================
with st.expander("✏️ 手動校正專區 (包含配息頻率、月份、日期)", expanded=True):
    st.info("💡 如果系統抓的配息時間有落差，請直接在這裡手動填寫。日期請填 YYYY-MM-DD (例: 2026-05-15 或 2026/05/15)。現價與昨收價填 0 代表自動抓取。")
    
    ov_list = []
    for item in st.session_state.my_data['etfs']:
        ov_list.append({
            "名稱": item['name'],
            "強制現價(0=自動)": float(item.get('manual_price', 0.0)),
            "手動昨收價(0=自動)": float(item.get('manual_prev_price', 0.0)),
            "每股配息": float(item.get('manual_div', 0.0)),
            "除息日(YYYY-MM-DD)": str(item.get('manual_ex_date', "")),
            "發放日(YYYY-MM-DD)": str(item.get('manual_pay_date', "")),
            "配息頻率(例:季配)": str(item.get('manual_freq', "")),
            "配息月份(自動過濾)": str(item.get('manual_months', ""))
        })
        
    edited_ov = st.data_editor(
        pd.DataFrame(ov_list),
        column_config={
            "名稱": st.column_config.TextColumn("ETF 名稱", disabled=True),
            "強制現價(0=自動)": st.column_config.NumberColumn("強制現價(0=自動)", format="%.2f"),
            "手動昨收價(0=自動)": st.column_config.NumberColumn("手動昨收價(0=自動)", format="%.2f"),
            "每股配息": st.column_config.NumberColumn("每股配息", format="%.3f"),
            "除息日(YYYY-MM-DD)": st.column_config.TextColumn("除息日(YYYY-MM-DD)"),
            "發放日(YYYY-MM-DD)": st.column_config.TextColumn("發放日(YYYY-MM-DD)"),
            "配息頻率(例:季配)": st.column_config.TextColumn("配息頻率(例:季配)"),
            "配息月份(自動過濾)": st.column_config.TextColumn("配息月份(自動過濾)")
        },
        use_container_width=True, hide_index=True
    )
    
    if st.button("💾 確認儲存配息與現價", type="primary"):
        for i, row in edited_ov.iterrows():
            st.session_state.my_data['etfs'][i]['manual_price'] = float(row.get('強制現價(0=自動)', 0.0))
            st.session_state.my_data['etfs'][i]['manual_prev_price'] = float(row.get('手動昨收價(0=自動)', 0.0))
            st.session_state.my_data['etfs'][i]['manual_div'] = float(row.get('每股配息', 0.0))
            
            ex_str = str(row.get('除息日(YYYY-MM-DD)', ""))
            st.session_state.my_data['etfs'][i]['manual_ex_date'] = ex_str.strip() if ex_str.lower() != 'nan' else ""

            pay_str = str(row.get('發放日(YYYY-MM-DD)', ""))
            st.session_state.my_data['etfs'][i]['manual_pay_date'] = pay_str.strip() if pay_str.lower() != 'nan' else ""

            freq_str = str(row.get('配息頻率(例:季配)', ""))
            st.session_state.my_data['etfs'][i]['manual_freq'] = freq_str.strip() if freq_str.lower() != 'nan' else ""
            
            month_str = str(row.get('配息月份(自動過濾)', ""))
            st.session_state.my_data['etfs'][i]['manual_months'] = month_str.strip() if month_str.lower() != 'nan' else ""
            
        save_to_json(st.session_state.my_data)
        st.cache_data.clear()
        st.rerun()

st.write("---")

bot_col1, bot_col2, bot_col3 = st.columns([2, 3, 5])

with bot_col1:
    if st.button("🔄 手動重整股價", use_container_width=True):
        fetch_data.clear(); fetch_historical_pnl.clear(); st.rerun()

with bot_col2:
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    is_auto_on = (st.session_state.get('auto_refresh_mode') == "✅ 開啟")
    auto_refresh_toggle = st.toggle("⚡ 開啟自動更新 (每 5 秒重整)", value=is_auto_on)
    st.session_state.auto_refresh_mode = "✅ 開啟" if auto_refresh_toggle else "❌ NO USE (關閉)"

with bot_col3:
    pass

# 🎯 單一自動更新執行邏輯
if st.session_state.get('auto_refresh_mode') == "✅ 開啟":
    time.sleep(5)
    fetch_data.clear()
    fetch_historical_pnl.clear()
    st.rerun()