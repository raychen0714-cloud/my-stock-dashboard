import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import altair as alt

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { fill: red; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; }
    
    .news-box { background-color: #f0f7ff; border-left: 6px solid #4a90e2; padding: 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 1px 1px 4px rgba(0,0,0,0.05); }
    .news-title { font-size: 20px; font-weight: bold; color: #1e3c72; margin-bottom: 15px; display: flex; align-items: center; }
    .news-item { font-size: 16px; color: #333; margin-bottom: 12px; line-height: 1.5; font-weight: 500;}
    .news-item a { text-decoration: none; color: #1e3c72; transition: color 0.2s;}
    .news-item a:hover { text-decoration: underline; color: #d32f2f; }

    /* 雙重雷達 */
    .ex-div-box { background-color: #ffeaea; border: 1.5px solid #e06666; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px; height: 115px; display: flex; flex-direction: column; justify-content: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); overflow-y: auto;}
    .ex-div-title { color: #cc0000; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .ex-div-text { color: #783f04; font-size: 12px; font-weight: bold; line-height: 1.4; }
    
    .pay-div-box { background-color: #fff2cc; border: 1.5px solid #f6b26b; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px; height: 115px; display: flex; flex-direction: column; justify-content: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); overflow-y: auto;}
    .pay-div-title { color: #b45f06; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .pay-div-text { color: #783f04; font-size: 12px; font-weight: bold; line-height: 1.4; }

    /* 三拼損益與領息橫列大看板樣式 */
    .triple-box { background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; padding: 15px; display: flex; flex-wrap: wrap; justify-content: space-around; align-items: center; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.04); gap: 10px; }
    .triple-col { flex: 1 1 30%; min-width: 140px; text-align: center; padding: 10px 0; }
    .triple-title { font-size: 14px; color: #757575; font-weight: bold; margin-bottom: 5px; }
    .triple-val-r { font-size: 28px; font-weight: 900; color: #b71c1c; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-g { font-size: 28px; font-weight: 900; color: #2e7d32; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-gold { font-size: 28px; font-weight: 900; color: #f39c12; font-family: Arial, sans-serif; line-height: 1.1; text-shadow: 1px 1px 2px rgba(243, 156, 18, 0.3); }
    .triple-pct-r { font-size: 14px; font-weight: bold; color: #b71c1c; margin-top: 5px; }
    .triple-pct-g { font-size: 14px; font-weight: bold; color: #2e7d32; margin-top: 5px; }
    .triple-sub-gold { font-size: 12px; font-weight: bold; color: #7f8c8d; margin-top: 5px; }

    /* 閃電特效 */
    @keyframes lightning-strike {
        0% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
        50% { box-shadow: 0 0 40px rgba(255, 235, 59, 1), inset 0 0 25px rgba(255, 235, 59, 0.9); background-color: #ffffe0; border-color: #ffeb3b; transform: scale(1.03); }
        100% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
    }
    .flash-gold-box { background-color: #fffdf5; border-radius: 12px; padding: 15px; border: 2px solid #f1c40f; animation: lightning-strike 0.1s infinite; }

    .alert-high { background-color: #ffebee; border: 2px solid #ef5350; border-left: 8px solid #d32f2f; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #b71c1c; font-size: 16px; font-weight: bold; }
    .alert-low { background-color: #e8f5e9; border: 2px solid #66bb6a; border-left: 8px solid #388e3c; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #1b5e20; font-size: 16px; font-weight: bold; }

    .month-card { background-color: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 10px; border: 1px solid #ced4da; }
    .month-title { font-size: 20px; font-weight: bold; color: #495057; }
    .month-amount { font-size: 28px; font-weight: bold; color: #d9534f; margin: 10px 0; }
    .month-sources { font-size: 14px; color: #6c757d; }
    
    div.stButton > button { font-weight: bold; border-radius: 8px; }

    .upcoming-box { background-color: #fff4e6; border: 1px solid #ffd8a8; border-radius: 8px; padding: 8px 10px; text-align: center; margin-bottom: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); }
    .upcoming-title { color: #d9480f; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .upcoming-item { color: #862e01; font-size: 13px; font-weight: bold; margin-bottom: 2px; }
    .upcoming-price { font-size: 11px; color: #888; }
    
    .calc-box { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px;}
    .calc-title { color: #495057; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    .calc-result-profit { font-size: 24px; font-weight: bold; color: #d32f2f; margin-top: 10px;}
    .calc-result-loss { font-size: 24px; font-weight: bold; color: #388e3c; margin-top: 10px;}
    .calc-result-info { font-size: 14px; color: #6c757d; margin-top: 5px;}
    
    /* 自動更新控制區樣式 */
    .auto-refresh-box { background-color: #f0f7ff; border: 1px solid #cce5ff; border-radius: 8px; padding: 15px; text-align: center; }
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
    # -- 新增清單區 --
    "00631L": "00631L 元大台灣50正2", "00673R": "00673R 期元大S&P原油反1", 
    "00632R": "00632R 元大台灣50反1", "009819": "009819 中信數據及電力", 
    "00712": "00712 復華富時不動產"
}

ACTIVE_ETFS = {
    "00981A": "00981A 主動統一台股增長",
    "00403A": "00403A 主動統一台股升級50",
    "00999A": "00999A 主動野村臺灣動能",
    "00401A": "00401A 主動摩根台灣鑫收",
    # -- 新增清單區 --
    "00992A": "00992A 主動群益科技創新",
    "00400A": "00400A 主動國泰動能高息",
    "00997A": "00997A 主動群益美國增長",
    "00988A": "00988A 主動統一全球創新",
    "00994A": "00994A 主動第一金台股優",
}

ETF_NAME_DB = {**PASSIVE_ETFS, **ACTIVE_ETFS}

DIVIDEND_SCHEDULE = {
    "0050.TW": [1, 7], "0056.TW": [1, 4, 7, 10], "00878.TW": [2, 5, 8, 11],
    "00891.TW": [2, 5, 8, 11], "00919.TW": [3, 6, 9, 12], "00927.TW": [1, 4, 7, 10],
    "00929.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "00940.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
}

DIVIDEND_DB = {
    "0056.TW": {"v": 1.07, "d": "2026-04-16", "p": "2026-05-15"}, 
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
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {
        "etfs": [], 
        "pledge": {"borrowed_amount": 0},
        "watchlist": [] 
    }

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: 
    st.session_state.my_data = load_settings()

if 'watchlist' not in st.session_state.my_data:
    st.session_state.my_data['watchlist'] = []

if 'pledge' not in st.session_state.my_data:
    st.session_state.my_data['pledge'] = {"borrowed_amount": 0}
for etf in st.session_state.my_data['etfs']:
    if 'pledged_shares' not in etf:
        etf['pledged_shares'] = 0.0
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
            "holdings": new_h, "cost": new_c, "alert_high": 0.0, "alert_low": 0.0, "pledged_shares": 0.0
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

def save_edits():
    temp_list = []
    for i, item in enumerate(st.session_state.my_data['etfs']):
        h_val = st.session_state.get(f"edit_h_{i}", item['holdings'])
        c_val = st.session_state.get(f"edit_c_{i}", item['cost'])
        temp_list.append({
            "symbol": item['symbol'],
            "name": item['name'],
            "holdings": h_val,
            "cost": c_val,
            "alert_high": item.get('alert_high', 0.0),
            "alert_low": item.get('alert_low', 0.0),
            "pledged_shares": item.get('pledged_shares', 0.0)
        })
    st.session_state.my_data['etfs'] = temp_list
    save_to_json(st.session_state.my_data)

# --- 自選股 Callback ---
def auto_fill_wl_name():
    raw_sym = st.session_state.get('add_sym_wl', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    if clean_sym:
        st.session_state.add_name_wl = ETF_NAME_DB.get(clean_sym, f"{clean_sym}")
    else:
        st.session_state.add_name_wl = ""

def add_new_wl():
    raw_sym = st.session_state.get('add_sym_wl', '')
    new_name = st.session_state.get('add_name_wl', '')
    clean_symbol = raw_sym.strip().upper().replace(".TW", "")
    if clean_symbol and new_name:
        final_symbol = f"{clean_symbol}.TW"
        if any(x['symbol'] == final_symbol for x in st.session_state.my_data['watchlist']):
            st.warning("該標的已在自選名單中！")
            return
        st.session_state.my_data['watchlist'].append({
            "symbol": final_symbol, "name": new_name
        })
        save_to_json(st.session_state.my_data)
        st.session_state.add_sym_wl = ""
        st.session_state.add_name_wl = ""

def delete_wl(index):
    if 0 <= index < len(st.session_state.my_data['watchlist']):
        st.session_state.my_data['watchlist'].pop(index)
        save_to_json(st.session_state.my_data)

def execute_trade():
    trade_etf_name = st.session_state.calc_selected_etf
    trade_type = st.session_state.calc_trade_type
    trade_shares = st.session_state.calc_trade_shares
    
    for i, item in enumerate(st.session_state.my_data['etfs']):
        if item['name'] == trade_etf_name:
            current_holdings = item['holdings']
            current_cost = item['cost']
            current_price = df[df['名稱'] == trade_etf_name].iloc[0]['現價']
            
            if trade_type == "賣出 (計算已實現損益)":
                actual_sell_shares = min(trade_shares, current_holdings)
                new_holdings = current_holdings - actual_sell_shares
                
                if new_holdings <= 0:
                    st.session_state.my_data['etfs'].pop(i)
                    st.success(f"已全數賣出 {trade_etf_name}，並從庫存中移除！")
                else:
                    item['holdings'] = new_holdings
                    st.success(f"成功賣出 {actual_sell_shares} 張 {trade_etf_name}！庫存剩餘 {new_holdings} 張。")
                    
            elif trade_type == "買進 (計算買入成本與新均價)":
                buy_cost_total = current_price * trade_shares * 1000
                new_total_shares = current_holdings + trade_shares
                new_total_cost_val = (current_cost * current_holdings * 1000) + buy_cost_total
                new_avg_cost = new_total_cost_val / (new_total_shares * 1000) if new_total_shares > 0 else 0
                
                item['holdings'] = new_total_shares
                item['cost'] = round(new_avg_cost, 2)
                st.success(f"成功買進 {trade_shares} 張 {trade_etf_name}！最新均價更新為 ${item['cost']}。")
                
            save_to_json(st.session_state.my_data)
            break

# 初始化按鈕狀態
if 'show_us' not in st.session_state: st.session_state.show_us = False
if 'show_tw' not in st.session_state: st.session_state.show_tw = False
if 'show_calendar' not in st.session_state: st.session_state.show_calendar = False
if 'show_div_db' not in st.session_state: st.session_state.show_div_db = False
if 'show_tech' not in st.session_state: st.session_state.show_tech = False
if 'show_holdings' not in st.session_state: st.session_state.show_holdings = False
if 'show_constituents' not in st.session_state: st.session_state.show_constituents = False 
if 'show_pledge' not in st.session_state: st.session_state.show_pledge = False 

def toggle_us(): st.session_state.show_us = not st.session_state.show_us
def toggle_tw(): st.session_state.show_tw = not st.session_state.show_tw
def toggle_calendar(): st.session_state.show_calendar = not st.session_state.show_calendar
def toggle_div_db(): st.session_state.show_div_db = not st.session_state.show_div_db
def toggle_tech(): st.session_state.show_tech = not st.session_state.show_tech
def toggle_holdings(): st.session_state.show_holdings = not st.session_state.show_holdings
def toggle_constituents(): st.session_state.show_constituents = not st.session_state.show_constituents
def toggle_pledge(): st.session_state.show_pledge = not st.session_state.show_pledge 

# --- 📡 抓取 ETF 焦點新聞 ---
@st.cache_data(ttl=3600)
def fetch_etf_news():
    news_list = []
    today_str = datetime.now().strftime("%m/%d")
    try:
        url = "https://news.google.com/rss/search?q=%E5%8F%B0%E7%81%A3+ETF+%E6%96%B0%E4%B8%8A%E5%B8%82+OR+%E9%85%8D%E6%81%AF+OR+%E6%88%90%E5%88%86%E8%82%A1&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item')[:4]:
                title = item.find('title').text
                if " - " in title: title = title.rsplit(" - ", 1)[0]
                link = item.find('link').text
                news_list.append({"title": f"{today_str} {title}", "link": link})
    except Exception: pass
    
    if not news_list:
        news_list = [
            {"title": f"{today_str} 盤前觀察：半導體龍頭動向 (影響 00927 走勢)", "link": "#"},
            {"title": f"{today_str} 高股息標的篩選：關注 00878、0056 成分股調整", "link": "#"},
            {"title": f"{today_str} 焦點情報：多檔新上市主動式 ETF 展開募集與掛牌", "link": "#"},
            {"title": f"{today_str} 大盤壓力測試：正二 (00631L) 槓桿風險控管建議", "link": "#"}
        ]
    return news_list

# --- 📈 抓取美台股大盤指標 ---
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
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    diff = curr - prev
                    pct = (diff / prev) * 100
                    date_str = hist.index[-1].strftime("%m/%d")
                    res[region][name] = {"price": curr, "diff": diff, "pct": pct, "date": date_str}
            except: pass
    return res

def render_macro_cards(data_dict, region_prefix):
    cols = st.columns(3)
    idx = 0
    for name, data in data_dict.items():
        is_up = data['diff'] >= 0
        color_hex = "#e74c3c" if is_up else "#2ecc71" 
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
        with cols[idx % 3]:
            st.markdown(html, unsafe_allow_html=True)
        idx += 1

# --- 🎯 抓取自選股資料 ---
@st.cache_data(ttl=10)
def fetch_watchlist_data(wl_list):
    if not wl_list: return pd.DataFrame()
    results = []
    for item in wl_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period="2d")
            if hist.empty: continue
            
            rt_curr = tk.fast_info.get('lastPrice')
            curr_p = rt_curr if rt_curr is not None else hist['Close'].iloc[-1]
            
            rt_prev = tk.fast_info.get('previousClose')
            prev_close = rt_prev if rt_prev is not None else (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
            
            diff = curr_p - prev_close
            pct = (diff / prev_close * 100) if prev_close else 0
            status_light = "🔴" if diff > 0 else "🟢" if diff < 0 else "⚪"
            
            results.append({
                "代號": item['symbol'].replace('.TW', ''),
                "名稱": item['name'],
                "現價": round(curr_p, 2),
                "漲跌": round(diff, 2),
                "漲跌幅": f"{pct:+.2f}%",
                "狀態": status_light
            })
        except Exception: continue
    return pd.DataFrame(results)

# --- 🎯 抓取自選股除權息資料 ---
@st.cache_data(ttl=3600)
def fetch_watchlist_dividend(wl_list):
    if not wl_list: return pd.DataFrame()
    results = []
    today = datetime.today()
    for item in wl_list:
        sym = item['symbol']
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period='1y') 
            
            is_announced, div_amount, ex_date, pay_date = False, 0.0, "待官方公告", "待官方公告"
            
            cfg = DIVIDEND_DB.get(sym)
            if cfg:
                div_amount = cfg['v']
                ex_date = cfg['d']
                pay_date = cfg['p']
                is_announced = True
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

            fill_status = "-"
            try:
                divs = tk.dividends
                if not divs.empty and not hist.empty:
                    now_ts = pd.Timestamp.now(tz=divs.index.tzinfo) if divs.index.tzinfo else pd.Timestamp.now()
                    past_divs = divs[divs.index < now_ts].sort_index(ascending=False)
                    
                    if not past_divs.empty:
                        last_ex_date = past_divs.index[0]
                        pre_ex = hist[hist.index < last_ex_date]
                        post_ex = hist[hist.index >= last_ex_date]
                        
                        if not pre_ex.empty and not post_ex.empty:
                            target_price = pre_ex['Close'].iloc[-1]
                            filled = False
                            t_days = 0
                            for d, r in post_ex.iterrows():
                                t_days += 1
                                if r['High'] >= target_price:
                                    fill_status = f"{d.month}/{d.day} 填息完成 ({t_days}天)"
                                    filled = True
                                    break
                            if not filled:
                                fill_status = f"未填息 ({t_days}天)"
            except Exception:
                pass

            months = DIVIDEND_SCHEDULE.get(sym, [])
            freq = "月配息" if len(months)==12 else "季配息" if len(months)==4 else "半年配" if len(months)==2 else "年配息" if len(months)==1 else "未知"

            results.append({
                "類別": "👀 自選",
                "ETF 名稱": item['name'], 
                "配息頻率": freq, 
                "配息月份": "、".join(map(str, months)) + " 月" if months else "未設定",
                "狀態": "✅ 已公告" if is_announced else "⏳ 依前次估算", 
                "除息日": ex_date, 
                "發放日": pay_date, 
                "每股金額": f"${div_amount:.3f}",
                "最新填息紀錄": fill_status
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# --- 4. 核心數據計算 ---
@st.cache_data(ttl=10)
def fetch_data(etf_list):
    if not etf_list: return pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0, [], [], [], {i: {"amount": 0, "sources": []} for i in range(1, 13)}
    results, tech_results = [], []
    total_mkt, total_cost, total_div, total_today_pnl = 0, 0, 0, 0
    radar_ex, radar_pay, price_alerts = [], [], []
    monthly_calendar = {i: {"amount": 0, "sources": []} for i in range(1, 13)} 
    today = datetime.today()

    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period='1y') 
            if hist.empty: continue
            
            rt_curr = tk.fast_info.get('lastPrice')
            curr_p = rt_curr if rt_curr is not None else hist['Close'].iloc[-1]
            
            rt_prev = tk.fast_info.get('previousClose')
            prev_close = rt_prev if rt_prev is not None else (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
            
            rt_dh = tk.fast_info.get('dayHigh')
            day_high = rt_dh if rt_dh is not None else hist['High'].iloc[-1]
            
            rt_dl = tk.fast_info.get('dayLow')
            day_low = rt_dl if rt_dl is not None else hist['Low'].iloc[-1]
            
            rt_vol = tk.fast_info.get('lastVolume')
            vol = rt_vol if rt_vol is not None else hist['Volume'].iloc[-1]
            
            year_high = tk.fast_info.get('yearHigh', 0)
            year_low = tk.fast_info.get('yearLow', 0)

            if curr_p > prev_close:
                status_light = "🔴"
            elif curr_p < prev_close:
                status_light = "🟢"
            else:
                status_light = "⚪"
            display_name = f"{status_light} {item['name']}"

            shares = item['holdings'] * 1000
            mkt_val = shares * curr_p
            cost_val = shares * item['cost']
            
            # 券商真實成本估算 (扣除手續費與證交稅) 
            sell_cost_estimate = mkt_val * 0.00235
            profit = mkt_val - cost_val - sell_cost_estimate
            roi = (profit / cost_val * 100) if cost_val != 0 else 0
            
            # 今日漲跌與損益計算
            today_diff = curr_p - prev_close
            today_profit = shares * today_diff
            today_pct_change = (today_diff / prev_close * 100) if prev_close else 0
            
            total_today_pnl += today_profit
            today_pnl_str = f"+${today_profit:,.0f}" if today_profit >= 0 else f"-${abs(today_profit):,.0f}"
            today_pct_str = f"+{today_pct_change:.2f}%" if today_pct_change >= 0 else f"{today_pct_change:.2f}%"

            a_high = float(item.get('alert_high', 0.0))
            a_low = float(item.get('alert_low', 0.0))
            if a_high > 0 and curr_p >= a_high:
                price_alerts.append({"name": item['name'], "price": curr_p, "target": a_high, "type": "high"})
            if a_low > 0 and curr_p <= a_low:
                price_alerts.append({"name": item['name'], "price": curr_p, "target": a_low, "type": "low"})

            is_announced, div_amount, ex_date, pay_date = False, 0, "待官方公告", "待官方公告"
            
            cfg = DIVIDEND_DB.get(item['symbol'])
            if cfg:
                div_amount = cfg['v']
                ex_date = cfg['d']
                pay_date = cfg['p']
                is_announced = True
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

            est_yield = 0.0
            months_to_pay = DIVIDEND_SCHEDULE.get(item['symbol'], [])
            if len(months_to_pay) > 0 and div_amount > 0 and curr_p > 0:
                est_yield = (div_amount * len(months_to_pay)) / curr_p * 100

            if is_announced:
                ex_date_obj = datetime.strptime(ex_date, '%Y-%m-%d')
                days_diff_ex = (ex_date_obj.date() - today.date()).days
                if 0 <= days_diff_ex <= 20: radar_ex.append({"symbol": item['symbol'].split('.')[0], "date": ex_date, "days": days_diff_ex})
                
                pay_date_obj = datetime.strptime(pay_date, '%Y-%m-%d')
                days_diff_pay = (pay_date_obj.date() - today.date()).days
                if 0 <= days_diff_pay <= 20: radar_pay.append({"symbol": item['symbol'].split('.')[0], "date": pay_date, "amount": shares * div_amount, "days": days_diff_pay})

            if div_amount > 0 and shares > 0:
                explicit_pay_month = None
                if is_announced and pay_date != "待官方公告":
                    explicit_pay_month = datetime.strptime(pay_date, '%Y-%m-%d').month
                    monthly_calendar[explicit_pay_month]["amount"] += (shares * div_amount)
                    if item['name'] not in monthly_calendar[explicit_pay_month]["sources"]:
                        monthly_calendar[explicit_pay_month]["sources"].append(item['name'])

                for m in months_to_pay:
                    pay_m = m + 1 if m < 12 else 1
                    if pay_m != explicit_pay_month:
                        monthly_calendar[pay_m]["amount"] += (shares * div_amount)
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
                            filled = False
                            t_days = 0
                            for d, r in post_ex.iterrows():
                                t_days += 1
                                if r['High'] >= target_price:
                                    fill_status = f"{d.month}/{d.day} 填息完成 ({t_days}天)"
                                    filled = True
                                    break
                            if not filled:
                                fill_status = f"未填息 ({t_days}天)"
            except Exception:
                pass

            total_mkt += mkt_val; total_cost += cost_val; total_div += (shares * div_amount)
            
            results.append({
                "代號": item['symbol'], "名稱": item['name'], "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "市值": mkt_val, "損益": profit, "報酬率": roi,
                "單次預估領息": shares * div_amount, "每股配息": div_amount,
                "最新公告除息日": ex_date, "預估發放日": pay_date, "已公告": is_announced,
                "最新填息紀錄": fill_status 
            })
            
            tech_results.append({
                "ETF 名稱": display_name,
                "股票張數": item['holdings'], 
                "現價": round(curr_p, 2),
                "今日損益": today_pnl_str,
                "今日漲跌幅": today_pct_str, 
                "今日交易量": f"{vol:,.0f}" if vol > 0 else "無資料",
                "預估年化殖利率": f"{est_yield:.2f}%",
                "今日最高/最低": f"${day_high:.2f} / ${day_low:.2f}",
                "52週最高/最低": f"${year_high:.2f} / ${year_low:.2f}",
                "設定高標(停利)": a_high,
                "設定低標(停損)": a_low
            })
            
        except Exception as e: continue
        
    return pd.DataFrame(results), pd.DataFrame(tech_results), total_mkt, total_cost, total_div, total_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar

df, df_tech, g_mkt, g_cost, g_div, g_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar = fetch_data(st.session_state.my_data['etfs'])
macro_data = fetch_macro_data()

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

news_data = fetch_etf_news()
news_html = "<div class='news-box'><div class='news-title'>📰 今日財經焦點</div>"
for news in news_data:
    news_html += f"<div class='news-item'>👉 📍 <a href='{news['link']}' target='_blank'>{news['title']}</a></div>"
news_html += "</div>"
st.markdown(news_html, unsafe_allow_html=True)

st.markdown("### 🗓️ 2026 即將上市 ETF 追蹤")
upcoming_list = [
    {"date": "2026/05/05", "symbol": "00999A", "name": "主動野村臺灣動能", "price": "10.00"},
    {"date": "2026/05/15", "symbol": "00403A", "name": "主動統一台股升級50", "price": "15.00"},
    {"date": "2026/06/05", "symbol": "00401A", "name": "主動摩根台灣鑫收", "price": "15.00"},
]

up_cols = st.columns([1, 1, 1, 3]) 
for i, etf in enumerate(upcoming_list):
    with up_cols[i]:
        st.markdown(f"""
        <div class='upcoming-box'>
            <div class='upcoming-title'>🚀 上市日：{etf['date']}</div>
            <div class='upcoming-item'>{etf['symbol']} {etf['name']}</div>
            <div class='upcoming-price'>發行價：${etf['price']}</div>
        </div>
        """, unsafe_allow_html=True)
st.write("")


if price_alerts:
    for alert in price_alerts:
        if alert['type'] == "high":
            st.markdown(f"<div class='alert-high'>🚨 突破停利高標：【{alert['name']}】 現價 ${alert['price']:.2f} 已突破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-low'>⚠️ 跌破停損低標：【{alert['name']}】 現價 ${alert['price']:.2f} 已跌破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)

st.markdown("### 👾 羅小翔專用：雙重雷達戰情室")
col1, col2, _ = st.columns([1, 1, 1])

with col1:
    if radar_ex:
        radar_ex = sorted(radar_ex, key=lambda x: x['days'])
        ex_content = "".join([f"<div style='margin-bottom: 4px; font-weight:bold;'>標的 {r['symbol']} 將於 {r['date'][5:7]}/{r['date'][8:10]} 除息 (倒數 {r['days']} 天)</div>" for r in radar_ex])
        st.markdown(f"<div class='ex-div-box'><div class='ex-div-title'>⚡ 除息雷達提醒 ⚡</div><div class='ex-div-text'>{ex_content}</div></div>", unsafe_allow_html=True)
    else:
        current_m = datetime.today().month
        next_m = current_m + 1 if current_m < 12 else 1
        this_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if current_m in DIVIDEND_SCHEDULE.get(etf['symbol'], [])]
        next_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if next_m in DIVIDEND_SCHEDULE.get(etf['symbol'], [])]
        
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

# 重新計算總損益
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
c3.metric("全年預估總領息", f"${sum([monthly_calendar[m]['amount'] for m in range(1, 13)]):,.0f}")
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


with cols_btn_r1[0]: st.button(b1_lbl, on_click=toggle_us, type=b1_typ, use_container_width=True)
with cols_btn_r1[1]: st.button(b2_lbl, on_click=toggle_tw, type=b2_typ, use_container_width=True)
with cols_btn_r1[2]: st.button(b3_lbl, on_click=toggle_calendar, type=b3_typ, use_container_width=True)

with cols_btn_r2[0]: st.button(b4_lbl, on_click=toggle_div_db, type=b4_typ, use_container_width=True)
with cols_btn_r2[1]: st.button(b5_lbl, on_click=toggle_tech, type=b5_typ, use_container_width=True)
with cols_btn_r2[2]: st.button(b6_lbl, on_click=toggle_holdings, type=b6_typ, use_container_width=True)

with cols_btn_r3[0]: st.button(b7_lbl, on_click=toggle_constituents, type=b7_typ, use_container_width=True) 
with cols_btn_r3[1]: st.button(b8_lbl, on_click=toggle_pledge, type=b8_typ, use_container_width=True) 

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

# --- 📂 展開除權息 ---
if st.session_state.show_div_db:
    st.markdown("#### 📚 專屬 ETF 與自選股 除權息時程總覽")
    db_list = []
    
    # 處理庫存資料
    if not df.empty:
        for _, row in df.iterrows():
            sym = row['代號']; months = DIVIDEND_SCHEDULE.get(sym, [])
            freq = "月配息" if len(months)==12 else "季配息" if len(months)==4 else "半年配" if len(months)==2 else "年配息" if len(months)==1 else "未知"
            db_list.append({
                "類別": "💼 庫存",
                "ETF 名稱": row['名稱'], 
                "配息頻率": freq, 
                "配息月份": "、".join(map(str, months)) + " 月" if months else "未設定",
                "狀態": "✅ 已公告" if row['已公告'] else "⏳ 依前次估算", 
                "除息日": row['最新公告除息日'], 
                "發放日": row['預估發放日'], 
                "每股金額": f"${row['每股配息']:.3f}",
                "最新填息紀錄": row['最新填息紀錄']
            })
            
    df_port_div = pd.DataFrame(db_list)
    
    # 抓取自選股除權息資料
    df_wl_div = fetch_watchlist_dividend(st.session_state.my_data.get('watchlist', []))
    
    final_div_df = pd.DataFrame()
    if not df_port_div.empty and not df_wl_div.empty:
        final_div_df = pd.concat([df_port_div, df_wl_div], ignore_index=True)
    elif not df_wl_div.empty:
        final_div_df = df_wl_div
    elif not df_port_div.empty:
        final_div_df = df_port_div
        
    if not final_div_df.empty:
        st.dataframe(final_div_df, use_container_width=True, hide_index=True)
    else:
        st.info("目前尚無庫存或自選股，因此無除權息資料可顯示。")
        
    st.write("---")

# --- 📡 展開股價監控 ---
if st.session_state.show_tech:
    if not df.empty:
        st.markdown("#### 📡 庫存價格區間監控與技術分析 (👉 雙擊表格數值設定警報，設 0 代表關閉)")
        
        def color_profit_loss(val):
            if isinstance(val, str):
                if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;' 
                elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;' 
            return ''

        try:
            styled_df_tech = df_tech.style.map(color_profit_loss, subset=['今日損益', '今日漲跌幅'])
        except AttributeError:
            styled_df_tech = df_tech.style.applymap(color_profit_loss, subset=['今日損益', '今日漲跌幅'])

        edited_tech = st.data_editor(
            styled_df_tech,
            column_config={
                "設定高標(停利)": st.column_config.NumberColumn("設定高標(停利)", help="雙擊輸入，超過觸發紅色警報", min_value=0.0, format="%.2f"),
                "設定低標(停損)": st.column_config.NumberColumn("設定低標(停損)", help="雙擊輸入，低於觸發綠色警報", min_value=0.0, format="%.2f"),
                "現價": st.column_config.NumberColumn("現價", format="%.2f"),
                "股票張數": st.column_config.NumberColumn("股票張數", format="%.1f") 
            },
            disabled=["ETF 名稱", "股票張數", "現價", "今日損益", "今日漲跌幅", "今日交易量", "預估年化殖利率", "今日最高/最低", "52週最高/最低"],
            use_container_width=True, hide_index=True
        )

        has_changes = False
        for _, row in edited_tech.iterrows():
            display_name = row['ETF 名稱']
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] in display_name:
                    if etf.get('alert_high', 0.0) != row['設定高標(停利)'] or etf.get('alert_low', 0.0) != row['設定低標(停損)']:
                        etf['alert_high'] = row['設定高標(停利)']
                        etf['alert_low'] = row['設定低標(停損)']
                        has_changes = True
                    break
        if has_changes:
            save_to_json(st.session_state.my_data)
            st.cache_data.clear()
            st.rerun()
    else:
        st.markdown("#### 📡 庫存價格區間監控")
        st.info("目前無庫存標的。")
        
    st.write("---")
    
    # --- 整合在展開股價監控內的自選股區域 ---
    st.markdown("#### 👀 自選股觀察清單")
    st.caption("追蹤您尚未入手、正在觀察的標的")
    
    col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
    with col_w1:
        st.text_input("輸入代碼 (不需手打 .TW)", placeholder="例如: 2330", key="add_sym_wl", on_change=auto_fill_wl_name)
    with col_w2:
        st.text_input("自定義名稱", placeholder="例如: 2330 台積電", key="add_name_wl")
    with col_w3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("➕ 加入名單", key="btn_add_wl", on_click=add_new_wl, use_container_width=True)

    wl_df = fetch_watchlist_data(st.session_state.my_data.get('watchlist', []))
    if not wl_df.empty:
        def color_diff(val):
            if isinstance(val, str) and '%' in val:
                if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;'
                elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;'
            elif isinstance(val, (int, float)):
                if val > 0: return 'color: #d32f2f; font-weight: bold;'
                elif val < 0: return 'color: #388e3c; font-weight: bold;'
            return ''
        
        try:
            styled_wl = wl_df.style.map(color_diff, subset=['漲跌', '漲跌幅'])
        except AttributeError:
            styled_wl = wl_df.style.applymap(color_diff, subset=['漲跌', '漲跌幅'])
            
        st.dataframe(styled_wl, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ 管理與刪除自選股"):
            for i, item in enumerate(st.session_state.my_data['watchlist']):
                cols_wl_del = st.columns([3, 1, 6])
                cols_wl_del[0].markdown(f"📍 **{item['name']}**")
                cols_wl_del[1].button("刪除", key=f"del_wl_{i}", on_click=delete_wl, args=(i,), use_container_width=True)
    else:
        st.info("目前尚無自選股。請在上方輸入代碼新增您的觀察名單！")

    st.write("---")

# --- 📊 展開持股明細 ---
if st.session_state.show_holdings:
    if not df.empty:
        st.markdown("#### 📊 持股動態明細")
        for _, row in df.iterrows():
            p_color = "red" if row['損益'] >= 0 else "green"; roi_str = f"{row['報酬率']:+.2f}%"
            status_badge = "✅ 已公告" if row['已公告'] else "⏳ 依前次估算"
            with st.expander(f"💎 {row['名稱']} | 預估淨報酬: :{p_color}[{roi_str}]", expanded=True):
                col_l, col_m, col_r = st.columns(3)
                with col_l: st.write(f"張數: **{row['張數']}**"); st.write(f"現價: **{row['現價']:.2f}**"); st.caption(f"均價: {row['均價']:.2f}")
                with col_m: st.markdown(f"市值: **${row['市值']:,.0f}**"); st.markdown(f"預估淨利: :{p_color}[**${row['損益']:,.0f}**]")
                with col_r: st.markdown(f"單次領息估算: :orange[**${row['單次預估領息']:,.0f}**]"); st.caption(f"📅 最新除息日: {row['最新公告除息日']} ({status_badge})")
    else:
        st.info("⚠️ 目前尚無持股資料。請至下方「⚙️ 標的管理」新增您的庫存！")
    st.write("---")

# --- 🧩 展開ETF成份股 ---
if st.session_state.show_constituents:
    if not df.empty:
        st.markdown("#### 🧩 專屬庫存 ETF 核心成分股佔比")
        st.caption("已開啟「直接顯示比例」模式。透過圓餅圖檢視成分股，可協助您避免資金過度集中於單一個股，降低系統性風險。")
        
        c_cols = st.columns(3)
        for idx, item in enumerate(st.session_state.my_data['etfs']):
            sym = item['symbol']
            name = item['name']
            
            comp_data = ETF_CONSTITUENTS_DB.get(sym, [{"name": "其他成分股", "weight": 100.0}])
            df_comp = pd.DataFrame(comp_data)
            
            df_comp['label'] = df_comp['weight'].apply(lambda w: f"{w:.1f}%" if w >= 2.0 else "")
            
            base = alt.Chart(df_comp).encode(
                theta=alt.Theta("weight:Q", stack=True),
                color=alt.Color("name:N", 
                                sort=alt.EncodingSortField(field="weight", op="sum", order="descending"), 
                                legend=alt.Legend(title=None, orient="right", labelFontSize=12)),
                tooltip=[
                    alt.Tooltip("name:N", title="成分股"),
                    alt.Tooltip("weight:Q", title="權重 (%)", format=".2f")
                ]
            )
            
            pie = base.mark_arc(outerRadius=100, innerRadius=0)
            
            text = base.mark_text(radius=125, size=13, fontWeight="bold", color="#333333").encode(
                text="label:N"
            )
            
            chart = alt.layer(pie, text).properties(
                height=280
            ).configure_view(strokeWidth=0)
            
            with c_cols[idx % 3]:
                st.markdown(f"<div style='font-weight:900; color:#1e3c72; font-size:16px; margin-bottom:5px; margin-top:15px;'>🛡️ {name}</div>", unsafe_allow_html=True)
                st.altair_chart(chart, use_container_width=True)
    else:
        st.info("⚠️ 目前尚無持股資料。請至下方「⚙️ 標的管理」新增您的庫存！")
    st.write("---")

# --- 🏦 展開質押專區 ---
if st.session_state.show_pledge:
    if not df.empty:
        st.markdown("#### 🏦 股票質押專區 (維持率監控)")
        st.info("💡 股票質押後會從一般券商庫存消失。一般券商（如元大）最高可借出擔保品市值的 60%。請輸入已借入款項，系統將即時監控維持率！")
        
        pledge_data = st.session_state.my_data['pledge']
        borrowed = st.number_input("💸 輸入已向券商借入款項總額 (元)", min_value=0, value=int(pledge_data.get('borrowed_amount', 0)), step=10000)
        
        if borrowed != pledge_data.get('borrowed_amount', 0):
            st.session_state.my_data['pledge']['borrowed_amount'] = borrowed
            save_to_json(st.session_state.my_data)
            st.rerun()

        pledge_df_list = []
        total_pledge_mkt = 0
        total_borrowable = 0
        for item in st.session_state.my_data['etfs']:
            sym = item['symbol']
            name = item['name']
            h_total = item['holdings']
            p_shares = item.get('pledged_shares', 0.0)
            
            try:
                curr_p = df[df['代號'] == sym]['現價'].values[0]
            except:
                curr_p = 0
                
            p_mkt = p_shares * 1000 * curr_p
            p_limit = p_mkt * 0.6  
            total_pledge_mkt += p_mkt
            total_borrowable += p_limit
            
            pledge_df_list.append({
                "ETF 名稱": name,
                "總庫存 (張)": h_total,
                "質押張數": p_shares,
                "現價": round(curr_p, 2),
                "質押市值 (元)": round(p_mkt, 0),
                "可借上限 (60%)": round(p_limit, 0) 
            })
            
        pledge_df = pd.DataFrame(pledge_df_list)
        margin_ratio = (total_pledge_mkt / borrowed * 100) if borrowed > 0 else 0
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("擔保品總市值", f"${total_pledge_mkt:,.0f}")
        col_m2.metric("🎯 總可借款上限 (60%)", f"${total_borrowable:,.0f}")
        col_m3.metric("💸 已借入總額", f"${borrowed:,.0f}")
        
        if borrowed > 0:
            if margin_ratio < 130:
                col_m4.metric("🚨 目前維持率", f"{margin_ratio:.2f}%", "危險：低於 130% 將面臨斷頭", delta_color="inverse")
                st.error("🚨 警告：您的維持率已跌破 130%，請盡速補繳保證金或償還部分借款！")
            elif margin_ratio < 160:
                col_m4.metric("⚠️ 目前維持率", f"{margin_ratio:.2f}%", "注意：市場波動可能導致風險", delta_color="off")
            else:
                col_m4.metric("✅ 目前維持率", f"{margin_ratio:.2f}%", "安全：維持率處於健康水平", delta_color="normal")
        else:
            col_m4.metric("目前維持率", "0.00%")

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
            p_name = row['ETF 名稱']
            new_p_shares = row['質押張數']
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] == p_name and etf.get('pledged_shares', 0.0) != new_p_shares:
                    etf['pledged_shares'] = new_p_shares
                    has_p_changes = True
                    break
        if has_p_changes:
            save_to_json(st.session_state.my_data)
            st.rerun()
    else:
        st.info("⚠️ 目前尚無持股資料，無法進行質押計算。")
    st.write("---")

# 🎯 買賣損益試算面板與執行交易功能
with st.expander("💰 買賣損益試算器", expanded=False):
    st.markdown("<div class='calc-title'>依照即時現價，試算買進或賣出後的損益狀況，並可直接寫入庫存！</div>", unsafe_allow_html=True)
    
    if not df.empty:
        calc_options = [row['名稱'] for _, row in df.iterrows()]
        
        # 建立專屬 session_state 變數，避免執行後數值亂跳
        if 'calc_selected_etf' not in st.session_state: st.session_state.calc_selected_etf = calc_options[0]
        if 'calc_trade_type' not in st.session_state: st.session_state.calc_trade_type = "賣出 (計算已實現損益)"
        if 'calc_trade_shares' not in st.session_state: st.session_state.calc_trade_shares = 1.0
        
        st.selectbox("選擇要操作的庫存標的：", calc_options, key="calc_selected_etf")
        
        target_row = df[df['名稱'] == st.session_state.calc_selected_etf].iloc[0]
        current_price = target_row['現價']
        current_cost = target_row['均價']
        current_holdings = target_row['張數']
        
        st.info(f"📍 **{st.session_state.calc_selected_etf}** | 目前庫存：{current_holdings} 張 | 庫存均價：${current_cost:.2f} | 系統即時現價：${current_price:.2f}")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.radio("交易動作：", ["賣出 (計算已實現損益)", "買進 (計算買入成本與新均價)"], key="calc_trade_type")
        with col_c2:
            st.number_input("輸入交易張數", min_value=0.1, step=1.0, key="calc_trade_shares")
            
        if st.session_state.calc_trade_type == "賣出 (計算已實現損益)":
            trade_shares_display = st.session_state.calc_trade_shares
            if trade_shares_display > current_holdings:
                st.warning(f"⚠️ 賣出張數 ({trade_shares_display}) 大於目前庫存 ({current_holdings})，將以全數出清試算並執行。")
                trade_shares_display = current_holdings
                
            realized_profit = (current_price - current_cost) * trade_shares_display * 1000
            
            st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
            st.write(f"📝 試算賣出 **{trade_shares_display}** 張")
            if realized_profit > 0:
                st.markdown(f"🎉 預估已實現損益 (賺)：<div class='calc-result-profit'>+${realized_profit:,.0f}</div>", unsafe_allow_html=True)
            elif realized_profit < 0:
                st.markdown(f"📉 預估已實現損益 (賠)：<div class='calc-result-loss'>-${abs(realized_profit):,.0f}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"⚖️ 預估已實現損益：<div style='font-size: 24px; font-weight: bold; margin-top: 10px;'>$0</div>", unsafe_allow_html=True)
                
            st.markdown(f"<div class='calc-result-info'>*不含手續費與證交稅，成交價以系統抓取之現價 ${current_price:.2f} 計算</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 🎯 執行按鈕
            st.button("💾 確認賣出並更新庫存", type="primary", use_container_width=True, on_click=execute_trade)
            
        else: # 買進
            trade_shares_display = st.session_state.calc_trade_shares
            buy_cost_total = current_price * trade_shares_display * 1000
            new_total_shares = current_holdings + trade_shares_display
            new_total_cost_val = (current_cost * current_holdings * 1000) + buy_cost_total
            new_avg_cost = new_total_cost_val / (new_total_shares * 1000) if new_total_shares > 0 else 0
            
            st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
            st.write(f"📝 試算買進 **{trade_shares_display}** 張")
            st.markdown(f"💸 預估買入總花費：<div style='font-size: 24px; font-weight: bold; margin-top: 10px;'>${buy_cost_total:,.0f}</div>", unsafe_allow_html=True)
            st.markdown(f"🎯 買入後全新均價：<div style='font-size: 20px; font-weight: bold; color: #1e3c72; margin-top: 10px;'>${new_avg_cost:.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='calc-result-info'>*總庫存將變為 {new_total_shares} 張。不含手續費，成交價以系統抓取之現價 ${current_price:.2f} 計算</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 🎯 執行按鈕
            st.button("💾 確認買進並更新庫存", type="primary", use_container_width=True, on_click=execute_trade)
            
    else:
        st.warning("請先在下方「標的管理」新增庫存，才能進行試算喔！")

st.write("---")

# 🎯 最底層操作列 (手動更新 + 標的管理 + 自動更新開關)
bot_c1, bot_c2, bot_c3 = st.columns([2, 5, 3])

with bot_c1:
    if st.button("🔄 手動重新整理股價", use_container_width=True):
        fetch_data.clear()
        fetch_watchlist_dividend.clear()
        st.rerun()

with bot_c2:
    with st.expander("⚙️ 標的管理 (庫存新增 / 修改 / 刪除)", expanded=True):
        st.markdown("#### ➕ 新增庫存標的 (股票/ETF)")
        
        if "add_name_bot" not in st.session_state: st.session_state.add_name_bot = ""
        if "add_sym_bot" not in st.session_state: st.session_state.add_sym_bot = ""
        if "add_h_bot" not in st.session_state: st.session_state.add_h_bot = 0.0
        if "add_c_bot" not in st.session_state: st.session_state.add_c_bot = 0.0

        st.text_input("輸入代碼 (不需手打 .TW)", placeholder="例如: 00878 或 00981A", key="add_sym_bot", on_change=auto_fill_etf_name)
        st.text_input("自定義名稱", placeholder="例如: 00878 國泰永續高股息", key="add_name_bot")
        
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            st.number_input("張數", step=1.0, key="add_h_bot")
        with col_add2:
            st.number_input("均價", step=0.1, key="add_c_bot")
        
        st.button("確認新增庫存", key="btn_add_bot", use_container_width=True, on_click=add_new_etf_bot)

        if st.session_state.my_data['etfs']:
            st.write("---")
            st.markdown("#### 📝 庫存修改與刪除")
            
            for i, item in enumerate(st.session_state.my_data['etfs']):
                with st.expander(f"📍 {item['name']}"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.number_input("張數", value=float(item['holdings']), step=1.0, key=f"edit_h_{i}")
                    with col_e2:
                        st.number_input("均價", value=float(item['cost']), step=0.1, key=f"edit_c_{i}")

                    st.button(f"🗑️ 刪除 {item['name']}", key=f"del_{i}", on_click=delete_etf, args=(i,), use_container_width=True)

            st.button("💾 儲存所有修改", use_container_width=True, type="primary", on_click=save_edits)

with bot_c3:
    st.markdown("<div class='auto-refresh-box'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ 系統自動更新")
    st.caption("開啟後每 5 秒自動重整抓取最新即時股價")
    
    # 初始化預設狀態
    if 'auto_refresh_mode' not in st.session_state:
        st.session_state.auto_refresh_mode = "❌ NO USE (關閉)"
        
    auto_update = st.radio(
        "即時更新 (每 5 秒)", 
        ["❌ NO USE (關閉)", "✅ USE (開啟)"], 
        key="auto_refresh_mode",
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")
st.markdown("### 📈 持股歷史股價趨勢 (近 30 日)")

current_etfs = [item['symbol'] for item in st.session_state.my_data.get('etfs', [])]

if current_etfs:
    with st.spinner("正在繪製高精度股價戰報..."):
        try:
            price_history = yf.download(current_etfs, period="1mo")['Close']
            
            if len(current_etfs) == 1:
                price_history = price_history.to_frame()
                price_history.columns = [st.session_state.my_data['etfs'][0]['name']]
            else:
                name_map = {item['symbol']: item['name'] for item in st.session_state.my_data['etfs']}
                price_history = price_history.rename(columns=name_map)
            
            df_chart = price_history.reset_index()
            date_col = df_chart.columns[0]
            df_melted = df_chart.melt(id_vars=[date_col], var_name='ETF', value_name='Price')

            chart = alt.Chart(df_melted).mark_line().encode(
                x=alt.X(f'{date_col}:T',
                        axis=alt.Axis(
                            format='%d日',      
                            title=None,
                            grid=False
                        )),
                y=alt.Y('Price:Q',
                        scale=alt.Scale(zero=False), 
                        axis=alt.Axis(
                            title=None,
                            labelFontSize=10,  
                            tickMinStep=1,     
                            tickCount=40,      
                            gridColor='#f0f2f6'
                        )),
                color=alt.Color('ETF:N', legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip(f'{date_col}:T', format='%Y/%m/%d', title='日期'),
                    alt.Tooltip('ETF:N', title='標的'),
                    alt.Tooltip('Price:Q', format='.2f', title='收盤價')
                ]
            ).properties(
                height=450
            ).interactive()

            st.altair_chart(chart, use_container_width=True)
            st.caption("數據來源：Yahoo Finance (近一個月每日收盤價趨勢)")
        except Exception as e:
            st.error(f"圖表產生失敗：{e}")
            st.info("提示：請確認網路連線正常或 ETF 代碼是否正確。")
else:
    st.info("目前庫存中沒有標的。請由上方「標的管理」面板新增您的愛股！")

# 🎯 放在腳本最底層的自動更新執行邏輯
if st.session_state.auto_refresh_mode == "✅ USE (開啟)":
    time.sleep(5)
    fetch_data.clear()
    fetch_watchlist_dividend.clear()
    st.rerun()