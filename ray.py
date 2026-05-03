import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="RAY ETF 隨身戰情室", layout="wide")
st_autorefresh(interval=15 * 1000, key="data_refresh")

# --- 2. 核心數據管理 ---
SETTINGS_FILE = 'settings.json'

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings():
    default_data = {
        "etfs": [
            {"symbol": "00927.TW", "name": "群益半導體收益", "shares": 20000, "cost": 28.65, "manual_pnl": 22096},
            {"symbol": "0056.TW", "name": "元大高股息", "shares": 25000, "cost": 38.77, "manual_pnl": 50680},
            {"symbol": "00878.TW", "name": "國泰永續高股息", "shares": 13000, "cost": 23.07, "manual_pnl": 29345},
            {"symbol": "00919.TW", "name": "群益台灣精選高息", "shares": 12000, "cost": 22.73, "manual_pnl": 10392},
            {"symbol": "00981A.TW", "name": "主動統一台股增長", "shares": 12000, "cost": 27.77, "manual_pnl": 5246},
            {"symbol": "00631L.TW", "name": "元大台灣50正2", "shares": 13000, "cost": 27.25, "manual_pnl": 16758},
            {"symbol": "0050.TW", "name": "元大台灣50", "shares": 8486, "cost": 37.22, "manual_pnl": 445608}
        ]
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return default_data
    return default_data

if 'my_data' not in st.session_state:
    st.session_state.my_data = load_settings()

# --- 3. 數據資料庫 ---
COMPONENTS_DB = {
    "0050.TW": "台積電(52%), 鴻海(5%), 聯發科(4%)",
    "0056.TW": "聯詠(5%), 聯發科(5%), 鴻海(4%), 聯電(4%)",
    "00878.TW": "聯發科(5%), 聯詠(5%), 廣達(5%), 仁寶(4%)",
    "00919.TW": "長榮(11%), 瑞昱(6%), 聯電(6%), 聯詠(6%)",
    "00927.TW": "台積電(14%), 聯發科(6%), 聯電(6%), 日月光(5%)",
    "00940.TW": "長榮(9%), 聯電(4%), 聯詠(3%), 中信金(3%)",
    "00631L.TW": "台指期槓桿 (追蹤 0050 兩倍績效)",
    "00981A.TW": "台股成長股 (統一投信主動操盤)"
}

DIV_CFG = {
    "0050.TW": {"m": [1, 7], "d": "2026-07-16", "v": 1.00}, 
    "0056.TW": {"m": [1, 4, 7, 10], "d": "2026-04-21", "v": 1.00}, 
    "00927.TW": {"m": [1, 4, 7, 10], "d": "2026-04-18", "v": 0.94}, 
    "00878.TW": {"m": [2, 5, 8, 11], "d": "2026-05-19", "v": 0.66},
    "00919.TW": {"m": [3, 6, 9, 12], "d": "2026-06-18", "v": 0.66}, 
    "00981A.TW": {"m": [3, 6, 9, 12], "d": "2026-06-17", "v": 0.41}
}

# --- 4. 功能核心 ---
def get_market_status():
    if datetime.now().weekday() >= 5: return " (休市)"
    return ""

@st.cache_data(ttl=15)
def fetch_tw_night_session():
    status = get_market_status()
    try:
        url = "https://tw.stock.yahoo.com/quote/WTX%26"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        price_val = float(soup.select_one('span[class*="Fz(32px)"]').text.replace(',', ''))
        change_text = soup.select_one('span[class*="Fz(20px)"]').text.replace(',', '').strip()
        
        # 絕對數值判斷：只要字串不含 "-" 且數值非 0，即為上漲
        is_up = "-" not in change_text and "0.00" not in change_text
        up_time = "05/01" if datetime.now().weekday() >= 5 else datetime.now().strftime('%H:%M')
        return {"name": "台指期(夜)", "price": price_val, "change": change_text, "is_up": is_up, "time": up_time + status}
    except: return None

def get_single_data(sym, name):
    status = get_market_status()
    try:
        tk = yf.Ticker(sym)
        curr = tk.fast_info['lastPrice']
        prev = tk.fast_info['regularMarketPreviousClose']
        diff = curr - prev
        up_time = "05/01" if datetime.now().weekday() >= 5 else datetime.now().strftime('%m/%d %H:%M')
        return {"name": name, "price": curr, "diff": diff, "pct": (diff/prev)*100, "time": up_time + status}
    except: return None

# --- 5. 主介面 ---
st.title("📱 RAY ETF 隨身戰情室")

# 市場指標行
st.markdown("#### 🇺🇸 美股指標 (最後結算: 05/01)")
us_tickers = [("^DJI", "道瓊"), ("^IXIC", "那指"), ("^SOX", "費半"), ("NVDA", "輝達"), ("TSM", "台積電ADR")]
us_cols = st.columns(len(us_tickers))
for i, (sym, name) in enumerate(us_tickers):
    data = get_single_data(sym, name)
    if data:
        color = "#FF0000" if data['diff'] > 0 else "#008000"
        with us_cols[i]:
            st.markdown(f"**{data['name']}** <small style='color:gray;'>{data['time']}</small>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{data['price']:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{data['pct']:+.2f}%</span>", unsafe_allow_html=True)

st.markdown("#### 🇹🇼 台股指標 (最後結算: 05/01)")
tw_tickers = [("^TWII", "台股大盤"), ("2330.TW", "台積電"), ("2454.TW", "聯發科")]
night = fetch_tw_night_session()
tw_cols = st.columns(len(tw_tickers) + (1 if night else 0))
for i, (sym, name) in enumerate(tw_tickers):
    data = get_single_data(sym, name)
    if data:
        color = "#FF0000" if data['diff'] > 0 else "#008000"
        with tw_cols[i]:
            st.markdown(f"**{data['name']}** <small style='color:gray;'>{data['time']}</small>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{data['price']:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{data['pct']:+.2f}%</span>", unsafe_allow_html=True)
if night:
    # 這裡強制判定：只要 is_up 為 True，顏色就是紅色
    n_color = "#FF0000" if night['is_up'] else "#008000"
    with tw_cols[-1]:
        st.markdown(f"**{night['name']}** <small style='color:gray;'>{night['time']}</small>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{night['price']:,.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{n_color}; font-weight:bold;'>{night['change']}</span>", unsafe_allow_html=True)

st.divider()

# 持股細節
df_list = []
t_day_chg, t_pnl, t_annual = 0, 0, 0
for item in st.session_state.my_data['etfs']:
    try:
        tk = yf.Ticker(item['symbol'])
        curr = tk.fast_info['lastPrice']
        prev = tk.fast_info['regularMarketPreviousClose']
        day_chg = (curr - prev) * item['shares']
        t_day_chg += day_chg
        t_pnl += item['manual_pnl']
        cfg = DIV_CFG.get(item['symbol'], {"m": [], "v": 0, "d": "無"})
        t_annual += (cfg['v'] * item['shares'] * len(cfg['m']))
        
        df_list.append({
            "名稱 (代碼)": f"{item['name']} ({item['symbol'].split('.')[0]})", 
            "核心成分股": COMPONENTS_DB.get(item['symbol'], "無"),
            "持有股數": item['shares'],
            "目前現價": curr, 
            "平均成本": item['cost'],
            "今日損益結算": day_chg, 
            "累積損益": item['manual_pnl'], 
            "預計除息日": cfg['d'],
            "領息月份": str(cfg['m']) if cfg['m'] else "無"
        })
    except: continue

# 損益總覽儀表板
dc = "#FF0000" if t_day_chg >= 0 else "#008000"
pc = "#FF0000" if t_pnl >= 0 else "#008000"
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"今日損益結算<br><span style='color:{dc}; font-size:32px; font-weight:bold;'>{t_day_chg:+,.0f} 元</span>", unsafe_allow_html=True)
with c2: st.markdown(f"累積總損益<br><span style='color:{pc}; font-size:32px; font-weight:bold;'>{t_pnl:,.0f} 元</span>", unsafe_allow_html=True)
with c3: st.metric("預估年領股息 (含 0050)", f"{t_annual:,.0f} 元")

if df_list:
    st.dataframe(pd.DataFrame(df_list).style.format({
        "目前現價": "{:.2f}", "平均成本": "{:.2f}", "今日損益結算": "{:+,.0f}", "累積損益": "{:,.0f}", "持有股數": "{:,.0f}"
    }).map(lambda x: f'color: {"#FF0000" if x >= 0 else "#008000"}; font-weight: bold;' if isinstance(x, (int, float)) else '', subset=["今日損益結算", "累積損益"]), use_container_width=True, hide_index=True)

with st.expander("🛠 資產管理修正"):
    updated = []
    for i, item in enumerate(st.session_state.my_data['etfs']):
        col = st.columns([2, 1, 1, 1, 0.5])
        with col[0]: st.write(f"**{item['name']}**")
        with col[1]: s = st.number_input(f"股數", value=int(item['shares']), key=f"s_{i}")
        with col[2]: c = st.number_input(f"成本", value=float(item['cost']), key=f"c_{i}")
        with col[3]: p = st.number_input(f"修正損益", value=int(item['manual_pnl']), key=f"p_{i}")
        with col[4]: 
            if st.button("🗑️", key=f"del_{i}"): continue
        updated.append({"symbol": item['symbol'], "name": item['name'], "shares": s, "cost": c, "manual_pnl": p})
    if st.button("💾 儲存所有修正"):
        st.session_state.my_data['etfs'] = updated
        save_to_json(st.session_state.my_data); st.rerun()