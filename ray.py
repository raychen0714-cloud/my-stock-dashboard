import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# --- 1. 網頁設定與自動刷新 (15 秒) ---
st.set_page_config(page_title="RAY ETF 隨身戰情室", layout="wide")
st_autorefresh(interval=15 * 1000, key="data_refresh")

# --- 2. 數據庫定義 ---
SETTINGS_FILE = 'settings.json'
TRADES_FILE = 'trades.json'
TW_TZ = pytz.timezone('Asia/Taipei')

CN_NAME_MAP = {
    "2356.TW": "英業達", "6160.TWO": "欣達", "00981A.TW": "主動統一台股增長",
    "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00631L.TW": "元大台灣50正2",
    "00878.TW": "國泰永續高股息", "00919.TW": "群益台灣精選高息", "00927.TW": "群益半導體收益"
}

DIV_CFG = {
    "0050.TW": {"m": [1, 7], "d": "2026-07-16", "pay_d": "2026-08-14", "v": 3.00}, 
    "0056.TW": {"m": [1, 4, 7, 10], "d": "2026-04-21", "pay_d": "2026-05-15", "v": 1.00}, 
    "00927.TW": {"m": [1, 4, 7, 10], "d": "2026-04-18", "pay_d": "2026-05-13", "v": 0.94}, 
    "00878.TW": {"m": [2, 5, 8, 11], "d": "2026-05-19", "pay_d": "2026-06-12", "v": 0.66},
    "00919.TW": {"m": [3, 6, 9, 12], "d": "2026-06-18", "pay_d": "2026-07-15", "v": 0.78}, 
    "00981A.TW": {"m": [3, 6, 9, 12], "d": "2026-06-17", "pay_d": "2026-07-14", "v": 0.41}
}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if "pay_adj" not in d: d["pay_adj"] = {}
                # 確保歷史配息欄位存在
                for e in d.get("etfs", []):
                    if "hist_div" not in e: e["hist_div"] = 0.0
                return d
        except: pass
    return {"etfs": [], "pay_adj": {}}

def load_trades():
    if os.path.exists(TRADES_FILE):
        try:
            with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return []

st.session_state.my_data = load_settings()
st.session_state.my_trades = load_trades()

# --- 3. 數據抓取 ---
@st.cache_data(ttl=5)
def fetch_market_data(sym):
    try:
        tk = yf.Ticker(sym)
        m_raw = tk.fast_info.get('last_trade_timestamp')
        t_str = datetime.fromtimestamp(m_raw, tz=pytz.utc).astimezone(TW_TZ).strftime('%m/%d %H:%M') if m_raw else datetime.now(TW_TZ).strftime('%m/%d %H:%M')
        curr, prev = float(tk.fast_info['lastPrice']), float(tk.fast_info['regularMarketPreviousClose'])
        return {"price": curr, "diff": curr - prev, "pct": ((curr - prev)/prev)*100, "market_time": t_str}
    except: return None

@st.cache_data(ttl=5)
def fetch_night_session():
    try:
        url = "https://tw.stock.yahoo.com/quote/WTX%26"
        soup = BeautifulSoup(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).text, 'html.parser')
        p = float(soup.select_one('span[class*="Fz(32px)"]').text.replace(',', ''))
        c = soup.select_one('span[class*="Fz(20px)"]').text.replace(',', '').strip()
        t = soup.select_one('span[class*="C(#6e7780)"]').text.replace('更新', '').strip()
        return {"price": p, "change": c, "market_time": t}
    except: return None

# --- 4. 主介面 ---
st.title("📱 RAY ETF 隨身戰情室")

# A. 領息預報單與歷史累計
today = datetime.now(TW_TZ)
st.subheader(f"📅 {today.month} 月份領息預報單")

pay_list = [{"name": e['name'], "pay_d": datetime.strptime(DIV_CFG[e['symbol']]["pay_d"], "%Y-%m-%d").strftime('%m/%d'), "shares": e['shares'], "v": e['div_val']} for e in st.session_state.my_data['etfs'] if e['symbol'] in DIV_CFG and datetime.strptime(DIV_CFG[e['symbol']]["pay_d"], "%Y-%m-%d").month == today.month]

c_m1, c_m2 = st.columns([1, 2])
with c_m1:
    # 1. 本月預估
    this_month_total = 0
    for p in pay_list:
        stored_s = st.session_state.my_data["pay_adj"].get(p['name'], int(p['shares']))
        this_month_total += int(stored_s) * p['v']
    st.metric("本月預計領息總額", f"{this_month_total:,.0f} 元")
    
    # 2. 歷史累計 (圖片圈選處)
    total_hist_div = sum(e.get("hist_div", 0) for e in st.session_state.my_data['etfs'])
    st.markdown("---")
    st.metric("🏦 歷史領息總累計", f"{total_hist_div:,.0f} 元", help="所有持股從過去到現在已領取的配息總和")

with c_m2:
    if pay_list:
        for p in pay_list:
            stored_s = st.session_state.my_data["pay_adj"].get(p['name'], int(p['shares']))
            r_box, r_btn = st.columns([5, 1])
            adj_s = r_box.number_input(f"調整 {p['name']} 領息股數 ({p['pay_d']} 入帳)", value=int(stored_s), step=1000, key=f"pay_adj_{p['name']}")
            if r_btn.button("💾", key=f"sv_{p['name']}"):
                st.session_state.my_data["pay_adj"][p['name']] = adj_s
                save_json(SETTINGS_FILE, st.session_state.my_data); st.rerun()
            st.write(f"💰 入帳預告：**{adj_s * p['v']:,.0f}** 元")
    else:
        st.info("本月尚無領息紀錄")

st.divider()

# B. 市場看板
cols = st.columns(5)
us_tickers = [("^DJI", "道瓊"), ("^IXIC", "那指"), ("^SOX", "費半"), ("NVDA", "輝達"), ("TSM", "台積電ADR")]
for i, (sym, name) in enumerate(us_tickers):
    d = fetch_market_data(sym)
    if d:
        clr = "#FF0000" if d['diff'] > 0 else "#008000"
        cols[i].markdown(f"**{name}** <small style='color:gray;'>{d['market_time']}</small><br><span style='font-size:18px; font-weight:bold;'>{d['price']:,.2f}</span><br><span style='color:{clr}; font-weight:bold;'>{d['diff']:+,.2f} ({d['pct']:+.2f}%)</span>", unsafe_allow_html=True)

tw_cols = st.columns(4); tw_tickers = [("^TWII", "台股大盤"), ("2330.TW", "台積電"), ("2454.TW", "聯發科")]
for i, (sym, name) in enumerate(tw_tickers):
    d = fetch_market_data(sym)
    if d:
        clr = "#FF0000" if d['diff'] > 0 else "#008000"
        tw_cols[i].markdown(f"**{name}** <small style='color:gray;'>{d['market_time']}</small><br><span style='font-size:18px; font-weight:bold;'>{d['price']:,.2f}</span><br><span style='color:{clr}; font-weight:bold;'>{d['diff']:+,.2f} ({d['pct']:+.2f}%)</span>", unsafe_allow_html=True)
n = fetch_night_session()
if n: tw_cols[-1].markdown(f"**台指期(夜)** <small style='color:gray;'>{n['market_time']}</small><br><span style='font-size:18px; font-weight:bold;'>{n['price']:,.2f}</span><br><span style='color:red; font-weight:bold;'>{n['change']}</span>", unsafe_allow_html=True)

st.divider()

# C. 持股表格
df_list = []; t_day, t_acc, t_div = 0, 0, 0
for item in st.session_state.my_data['etfs']:
    try:
        tk = yf.Ticker(item['symbol'])
        c, p = float(tk.fast_info['lastPrice']), float(tk.fast_info['regularMarketPreviousClose'])
        d_pnl, a_pnl, d_pct = (c - p) * item['shares'], (c - item['cost']) * item['shares'], ((c - p) / p) * 100
        a_div = item['div_val'] * item['shares'] * (len(DIV_CFG.get(item['symbol'], {}).get('m', [])) or 1)
        t_day += d_pnl; t_acc += a_pnl; t_div += a_div
        df_list.append({
            "標的": f"{item['symbol'].split('.')[0]} {item['name']}", 
            "持有股數": item['shares'], "平均成本": item['cost'], "目前現價": c, 
            "漲跌 (%)": d_pct, "今日損益": d_pnl, "累積損益": a_pnl, 
            "單次配息": item['div_val'], "預估年領息": a_div,
            "除息日": DIV_CFG.get(item['symbol'], {}).get('d', '無')
        })
    except: continue

st.subheader("📈 核心持股現況")
met_col1, met_col2, met_col3 = st.columns(3)
met_col1.metric("今日帳面損益", f"{t_day:+,.0f} 元")
met_col2.metric("累積帳面總損益", f"{t_acc:+,.0f} 元")
met_col3.metric("預估年領總股息", f"{t_div:,.0f} 元")

if df_list:
    st.dataframe(pd.DataFrame(df_list).style.format({"目前現價": "{:.2f}", "平均成本": "{:.2f}", "漲跌 (%)": "{:+.2f}%", "今日損益": "{:+,.0f}", "累積損益": "{:+,.0f}", "持有股數": "{:,.0f}", "單次配息": "{:.2f}", "預估年領息": "{:,.0f}"}).map(lambda x: f'color: {"#FF0000" if x >= 0 else "#008000"}; font-weight: bold;' if isinstance(x, (int, float)) else '', subset=["漲跌 (%)", "今日損益", "累積損益"]), use_container_width=True, hide_index=True)

st.divider()

# D. 今日對帳單
st.subheader("📑 今日買賣成交對帳單")
c_t1, c_t2 = st.columns([1, 3])
with c_t1:
    with st.form("trade_form"):
        t_target = st.selectbox("標的", [f"{e['symbol']} {e['name']}" for e in st.session_state.my_data['etfs']])
        t_action = st.radio("動作", ["賣出", "買進"], horizontal=True)
        t_price = st.number_input("成交價", value=0.0, step=0.01)
        t_qty = st.number_input("成交股數", value=0, step=1000)
        if st.form_submit_button("✅ 新增紀錄"):
            target_etf = next(e for e in st.session_state.my_data['etfs'] if t_target.startswith(e['symbol']))
            val = (t_price - target_etf['cost']) * t_qty if t_action == "賣出" else - (t_price * t_qty)
            st.session_state.my_trades.append({"時間": datetime.now(TW_TZ).strftime('%H:%M'), "標的": target_etf['name'], "動作": t_action, "成交價": t_price, "股數": t_qty, "損益": val})
            save_json(TRADES_FILE, st.session_state.my_trades); st.rerun()

with c_t2:
    if st.session_state.my_trades:
        sum_p = sum(t['損益'] for t in st.session_state.my_trades if t.get('動作') == "賣出")
        st.write(f"今日賣出實現總損益：**{sum_p:+,.0f} 元**")
        h = st.columns([0.8, 1.5, 0.8, 1, 1, 1.2, 0.5])
        h[0].write("**時間**"); h[1].write("**標的**"); h[2].write("**動作**"); h[3].write("**成交價**"); h[4].write("**股數**"); h[5].write("**損益**")
        for idx, tr in enumerate(st.session_state.my_trades):
            r = st.columns([0.8, 1.5, 0.8, 1, 1, 1.2, 0.5])
            r[0].write(tr.get('時間', '--')); r[1].write(tr.get('標的', '--')); r[2].write(tr.get('動作', '--')); r[3].write(f"{tr.get('成交價',0):.2f}"); r[4].write(f"{tr.get('股數',0):,}")
            sv = tr.get('損益', 0); clr = "red" if sv >= 0 else "green"
            r[5].markdown(f"<span style='color:{clr}; font-weight:bold;'>{sv:+,.0f}</span>", unsafe_allow_html=True)
            if r[6].button("🗑️", key=f"dt_{idx}"):
                st.session_state.my_trades.pop(idx); save_json(TRADES_FILE, st.session_state.my_trades); st.rerun()
    else: st.info("尚無今日買賣紀錄")

# E. 帳戶管理 (增加「歷史配息總計」輸入欄位)
st.divider()
with st.expander("🛠 帳戶與庫存管理"):
    upd = []; d_idx = None
    for i, item in enumerate(st.session_state.my_data['etfs']):
        r = st.columns([1.5, 1, 1, 1, 1, 0.5])
        r[0].write(f"**{item['name']}**")
        s = r[1].number_input("持有股數", value=int(item['shares']), key=f"s_{i}")
        c = r[2].number_input("平均成本", value=float(item['cost']), key=f"c_{i}")
        d = r[3].number_input("單次配息", value=float(item['div_val']), key=f"d_{i}")
        h_d = r[4].number_input("已領總配息", value=float(item.get('hist_div', 0)), key=f"hd_{i}")
        if r[5].button("🗑️", key=f"del_{i}"): d_idx = i
        upd.append({"symbol": item['symbol'], "name": item['name'], "shares": s, "cost": c, "div_val": d, "hist_div": h_d})
    if d_idx is not None: st.session_state.my_data['etfs'].pop(d_idx); save_json(SETTINGS_FILE, st.session_state.my_data); st.rerun()
    if st.button("💾 永久儲存庫存變更"): 
        st.session_state.my_data['etfs'] = upd
        save_json(SETTINGS_FILE, st.session_state.my_data); st.rerun()