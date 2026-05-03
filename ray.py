import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 網頁設定與自動刷新 (15 秒) ---
st.set_page_config(page_title="RAY ETF 隨身戰情室", layout="wide")
st_autorefresh(interval=15 * 1000, key="data_refresh")

# --- 2. 數據庫定義 ---
SETTINGS_FILE = 'settings.json'

CN_NAME_MAP = {
    "2356.TW": "英業達",
    "6160.TW": "欣達",
    "00981A.TW": "主動統一台股增長",
    "0050.TW": "元大台灣50",
    "0056.TW": "元大高股息",
    "00631L.TW": "元大台灣50正2",
    "00878.TW": "國泰永續高股息",
    "00919.TW": "群益台灣精選高息",
    "00927.TW": "群益半導體收益"
}

# 更新 00919 最新配息為 0.78
DIV_CFG = {
    "0050.TW": {"m": [1, 7], "d": "2026-07-16", "v": 1.00}, 
    "0056.TW": {"m": [1, 4, 7, 10], "d": "2026-04-21", "v": 1.00}, 
    "00927.TW": {"m": [1, 4, 7, 10], "d": "2026-04-18", "v": 0.94}, 
    "00878.TW": {"m": [2, 5, 8, 11], "d": "2026-05-19", "v": 0.66},
    "00919.TW": {"m": [3, 6, 9, 12], "d": "2026-06-18", "v": 0.78}, 
    "00981A.TW": {"m": [3, 6, 9, 12], "d": "2026-06-17", "v": 0.41}
}

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings():
    default_data = {"etfs": [
        {"symbol": "0056.TW", "name": "元大高股息", "shares": 25000, "cost": 38.77, "div_val": 1.0},
        {"symbol": "00878.TW", "name": "國泰永續高股息", "shares": 13000, "cost": 23.07, "div_val": 0.66},
        {"symbol": "00919.TW", "name": "群益台灣精選高息", "shares": 12000, "cost": 22.73, "div_val": 0.78},
        {"symbol": "00927.TW", "name": "群益半導體收益", "shares": 20000, "cost": 28.65, "div_val": 0.94},
        {"symbol": "00981A.TW", "name": "主動統一台股增長", "shares": 12000, "cost": 27.77, "div_val": 0.41}
    ]}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                for item in d.get('etfs', []):
                    if item['symbol'] in CN_NAME_MAP: item['name'] = CN_NAME_MAP[item['symbol']]
                    
                    current_div = float(item.get('div_val', 0.0))
                    
                    # 強制升級：如果存檔裡 00919 還是舊的 0.66，自動幫用戶升級為 0.78
                    if item['symbol'] == "00919.TW" and current_div == 0.66:
                        current_div = 0.78
                        
                    # 如果是 0，從資料庫撈取預設值
                    if current_div == 0.0:
                        item['div_val'] = DIV_CFG.get(item['symbol'], {}).get('v', 0.0)
                    else:
                        item['div_val'] = current_div
                return d
        except: return default_data
    return default_data

st.session_state.my_data = load_settings()

# --- 4. 數據抓取 (加入雙重備援機制，防止美股消失) ---
@st.cache_data(ttl=10)
def fetch_market_data(sym, name):
    try:
        tk = yf.Ticker(sym)
        try:
            # 優先使用快速通道
            curr = float(tk.fast_info['lastPrice'])
            prev = float(tk.fast_info['regularMarketPreviousClose'])
        except:
            # 假日或特定指數快速通道失效時，改用歷史 K 線備援
            hist = tk.history(period="5d")
            if len(hist) >= 2:
                curr = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
            else:
                return None
                
        diff = curr - prev
        pct = (diff/prev)*100
        return {"name": name, "price": curr, "diff": diff, "pct": pct, "time": datetime.now().strftime('%H:%M:%S')}
    except: 
        return None

@st.cache_data(ttl=10)
def fetch_night_session():
    try:
        url = "https://tw.stock.yahoo.com/quote/WTX%26"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        price_val = float(soup.select_one('span[class*="Fz(32px)"]').text.replace(',', ''))
        change_text = soup.select_one('span[class*="Fz(20px)"]').text.replace(',', '').strip()
        is_up = "-" not in change_text and "0.00" not in change_text
        display_change = ("+" if is_up and "+" not in change_text else "") + change_text
        return {"name": "台指期(夜)", "price": price_val, "change": display_change, "is_up": is_up, "time": datetime.now().strftime('%H:%M:%S')}
    except: return None

# --- 5. 主介面 ---
st.title("📱 RAY ETF 隨身戰情室")

# 除息提醒區域
reminders = []
today = datetime.now()
for item in st.session_state.my_data['etfs']:
    cfg = DIV_CFG.get(item['symbol'])
    if cfg and cfg["d"] != "無":
        try:
            div_date = datetime.strptime(cfg["d"], "%Y-%m-%d")
            days_left = (div_date - today).days
            if 0 <= days_left <= 15:
                reminders.append(f"🚨 **{item['name']}** 將於 **{div_date.strftime('%m/%d')}** 除息 (倒數 {days_left} 天)")
        except: pass

if reminders:
    st.markdown("""<style>@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } } .blink-alert { animation: blink 1.5s infinite; background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 2px solid white; font-weight: bold; }</style>""", unsafe_allow_html=True)
    for r in reminders: st.markdown(f'<div class="blink-alert">{r}</div>', unsafe_allow_html=True)

st.caption(f"最後同步：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每 15 秒更新)")

# 指標行 (加入防消失機制)
us_cols = st.columns(5)
us_tickers = [("^DJI", "道瓊"), ("^IXIC", "那指"), ("^SOX", "費半"), ("NVDA", "輝達"), ("TSM", "台積電ADR")]
for i, (sym, name) in enumerate(us_tickers):
    with us_cols[i]:
        data = fetch_market_data(sym, name)
        if data:
            color = "#FF0000" if data['diff'] > 0 else "#008000"
            st.markdown(f"**{data['name']}** <small style='color:gray;'>{data['time']}</small>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{data['price']:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{data['diff']:+,.2f} ({data['pct']:+.2f}%)</span>", unsafe_allow_html=True)
        else:
            # 如果連備援機制都抓不到，顯示錯誤但保留排版
            st.markdown(f"**{name}**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:gray; font-size:14px;'>無資料/連線異常</span>", unsafe_allow_html=True)

tw_cols = st.columns(4)
tw_tickers = [("^TWII", "台股大盤"), ("2330.TW", "台積電"), ("2454.TW", "聯發科")]
night = fetch_night_session()
for i, (sym, name) in enumerate(tw_tickers):
    with tw_cols[i]:
        data = fetch_market_data(sym, name)
        if data:
            color = "#FF0000" if data['diff'] > 0 else "#008000"
            st.markdown(f"**{data['name']}** <small style='color:gray;'>{data['time']}</small>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{data['price']:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{data['diff']:+,.2f} ({data['pct']:+.2f}%)</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**{name}**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:gray; font-size:14px;'>無資料/連線異常</span>", unsafe_allow_html=True)

if night:
    n_color = "#FF0000" if night['is_up'] else "#008000"
    with tw_cols[-1]:
        st.markdown(f"**{night['name']}** <small style='color:gray;'>{night['time']}</small>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:18px; font-weight:bold;'>{night['price']:,.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{n_color}; font-weight:bold;'>{night['change']}</span>", unsafe_allow_html=True)

st.divider()

# --- 持股表格 ---
df_list = []
total_day_pnl, total_auto_pnl, total_div = 0, 0, 0
for item in st.session_state.my_data['etfs']:
    try:
        tk = yf.Ticker(item['symbol'])
        curr = tk.fast_info['lastPrice']
        prev = tk.fast_info['regularMarketPreviousClose']
        day_pnl = (curr - prev) * item['shares']
        auto_pnl = (curr - item['cost']) * item['shares']
        
        div_single = float(item.get('div_val', 0.0))
        cfg = DIV_CFG.get(item['symbol'], {"m": [], "v": 0.0, "d": "無"})
        freq = len(cfg['m']) if cfg['m'] else (1 if div_single > 0 else 0)
        item_annual_div = div_single * item['shares'] * freq
        
        total_day_pnl += day_pnl; total_auto_pnl += auto_pnl; total_div += item_annual_div
        df_list.append({"名稱 (代碼)": f"{item['name']} ({item['symbol'].split('.')[0]})", "持有股數": item['shares'], "目前現價": curr, "平均成本": item['cost'], "今日損益": day_pnl, "累積自動損益": auto_pnl, "單次配息額": div_single, "預估年領息額": item_annual_div, "預計除息日": cfg['d'], "領息月": str(cfg['m'])})
    except: continue

dc, pc = ("#FF0000" if total_day_pnl >= 0 else "#008000"), ("#FF0000" if total_auto_pnl >= 0 else "#008000")
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"今日估計損益<br><span style='color:{dc}; font-size:32px; font-weight:bold;'>{total_day_pnl:+,.0f} 元</span>", unsafe_allow_html=True)
with c2: st.markdown(f"累積自動總損益<br><span style='color:{pc}; font-size:32px; font-weight:bold;'>{total_auto_pnl:+,.0f} 元</span>", unsafe_allow_html=True)
with c3: st.markdown(f"預估年領股息<br><span style='font-size:32px; font-weight:bold;'>{total_div:,.0f} 元</span>", unsafe_allow_html=True)

if df_list:
    st.dataframe(pd.DataFrame(df_list).style.format({"目前現價": "{:.2f}", "平均成本": "{:.2f}", "今日損益": "{:+,.0f}", "累積自動損益": "{:+,.0f}", "持有股數": "{:,.0f}", "單次配息額": "{:.2f}", "預估年領息額": "{:,.0f}"}).map(lambda x: f'color: {"#FF0000" if x >= 0 else "#008000"}; font-weight: bold;' if isinstance(x, (int, float)) else '', subset=["今日損益", "累積自動損益"]), use_container_width=True, hide_index=True)

# --- 🛠 帳戶管理 ---
with st.expander("🛠 帳戶管理"):
    a_col = st.columns([2, 1, 1, 1, 1])
    raw_id = a_col[0].text_input("輸入代碼 (例: 2356)", key="add_id_final")
    a_s = a_col[1].number_input("股數", min_value=0, step=1000, key="add_s_final")
    a_c = a_col[2].number_input("成本", min_value=0.0, step=0.1, key="add_c_final")
    a_d = a_col[3].number_input("配息額", min_value=0.0, step=0.01, key="add_d_final")
    if a_col[4].button("確認新增"):
        if raw_id:
            raw_id = raw_id.strip().upper()
            test_syms = [raw_id] if "." in raw_id else [f"{raw_id}.TW", f"{raw_id}.TWO"]
            found = None
            for sym in test_syms:
                try:
                    tk = yf.Ticker(sym); _ = tk.fast_info['lastPrice']
                    url = f"https://tw.stock.yahoo.com/quote/{sym}"
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
                    soup = BeautifulSoup(res.text, 'html.parser'); h1 = soup.select_one('h1')
                    name = h1.text if h1 else tk.info.get('shortName', sym)
                    found = {"symbol": sym, "name": name, "shares": a_s, "cost": a_c, "div_val": a_d}
                    break
                except: continue
            if found: st.session_state.my_data['etfs'].append(found); save_to_json(st.session_state.my_data); st.rerun()

    st.divider()
    updated = []; delete_idx = None
    for i, item in enumerate(st.session_state.my_data['etfs']):
        u_key = f"{item['symbol']}_{i}_vfinal"
        row = st.columns([2, 1, 1, 1, 0.5])
        with row[0]: st.write(f"**{item['name']}**")
        s = row[1].number_input("股數", value=int(item['shares']), key=f"s_{u_key}")
        c = row[2].number_input("成本", value=float(item['cost']), key=f"c_{u_key}")
        d = row[3].number_input("配息", value=float(item.get('div_val', 0.0)), key=f"d_{u_key}")
        if row[4].button("🗑️", key=f"del_{u_key}"): delete_idx = i
        updated.append({"symbol": item['symbol'], "name": item['name'], "shares": s, "cost": c, "div_val": d})
    if delete_idx is not None: st.session_state.my_data['etfs'].pop(delete_idx); save_to_json(st.session_state.my_data); st.rerun()
    if st.button("💾 儲存並同步變更"): st.session_state.my_data['etfs'] = updated; save_to_json(st.session_state.my_data); st.rerun()