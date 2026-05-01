import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 隨身戰情室", layout="wide")
st_autorefresh(interval=15 * 1000, key="data_refresh")

# --- 2. 核心數據管理 ---
SETTINGS_FILE = 'settings.json'

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings():
    default_data = {
        "etfs": [
            {"symbol": "0056.TW", "name": "元大高股息", "shares": 25000, "cost": 38.77, "manual_pnl": 50680},
            {"symbol": "00927.TW", "name": "群益半導體收益", "shares": 20000, "cost": 28.65, "manual_pnl": 22096},
            {"symbol": "00878.TW", "name": "國泰永續高股息", "shares": 13000, "cost": 23.07, "manual_pnl": 29345},
            {"symbol": "00919.TW", "name": "群益台灣精選高息", "shares": 12000, "cost": 22.73, "manual_pnl": 10392},
            {"symbol": "0050.TW", "name": "元大台灣50", "shares": 2000, "cost": 90.50, "manual_pnl": -592},
            {"symbol": "00981A.TW", "name": "主動統一台股增長", "shares": 12000, "cost": 27.77, "manual_pnl": 5246},
            {"symbol": "00631L.TW", "name": "元大台灣50正2", "shares": 13000, "cost": 27.25, "manual_pnl": 16758}
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

# --- 3. 計算核心 ---
@st.cache_data(ttl=10)
def fetch_monitor_data():
    tickers = {"WTX=F": "台指期夜盤", "^NDX": "那斯達克", "^SOX": "費城半導體", "NVDA": "輝達 NVIDIA", "TSM": "台積電 ADR"}
    monitor_results = []
    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            info = tk.fast_info
            curr = info['lastPrice']
            prev = info['regularMarketPreviousClose']
            if curr == 0 or curr is None: continue 
            diff = curr - prev
            pct = (diff / prev) * 100 if prev != 0 else 0
            monitor_results.append({"名稱": name, "現價": round(curr, 2), "點數漲跌": diff, "漲跌幅": pct})
        except: continue
    return monitor_results

@st.cache_data(ttl=10)
def fetch_analysis(etf_list):
    if not etf_list: return pd.DataFrame(), 0, 0, 0, {}, 0, []
    res, t_mkt, t_pnl, t_cost, annual_total = [], 0, 0, 0, 0
    m_stats = {f"{m}月": {"total": 0, "detail": []} for m in range(1, 13)}
    reminders = []
    today = datetime.now()
    
    # 核心除息配置 (只要符合此代號就會自動提醒)
    div_cfg = {
        "0050.TW": {"m": [1, 7], "d": "2026-01-22", "v": 1.39},
        "0056.TW": {"m": [1, 4, 7, 10], "d": "2026-04-21", "v": 1.00}, 
        "00927.TW": {"m": [1, 4, 7, 10], "d": "2026-04-18", "v": 0.94},
        "00878.TW": {"m": [2, 5, 8, 11], "d": "2026-05-19", "v": 0.66},
        "00919.TW": {"m": [3, 6, 9, 12], "d": "2026-03-18", "v": 0.66}, 
        "00981A.TW": {"m": [3, 6, 9, 12], "d": "2026-03-17", "v": 0.41},
        "00631L.TW": {"m": [], "d": "無", "v": 0.0}
    }
    
    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            curr_p = tk.fast_info['lastPrice']
            cfg = div_cfg.get(item['symbol'], {"m": [], "d": "無", "v": 0.0})
            
            # 25 天內自動發動雷達提醒
            if cfg["d"] != "無":
                div_date = datetime.strptime(cfg["d"], "%Y-%m-%d")
                days_diff = (div_date - today).days
                if 0 <= days_diff <= 25: 
                    reminders.append({"code": item['symbol'].split('.')[0], "date": div_date.strftime("%m/%d")})
            
            cash = cfg['v'] * item['shares']
            for m in cfg["m"]:
                m_stats[f"{m}月"]["total"] += cash
                m_stats[f"{m}月"]["detail"].append({"code": item['symbol'].split('.')[0], "amount": cash})
                annual_total += cash
            
            t_mkt += (item['shares'] * curr_p)
            t_pnl += item['manual_pnl']
            t_cost += (item['shares'] * item['cost'])
            
            res.append({
                "代號名稱": f"{item['symbol'].split('.')[0]} {item['name']}", 
                "現價": round(curr_p, 2), "市值": round(item['shares'] * curr_p, 0), 
                "損益": item['manual_pnl'], "張數": f"{int(item['shares']/1000)}張",
                "預估配息": f"${cfg['v']:.2f}" if cfg['v'] > 0 else "無", "除息日": cfg["d"],
                "has_div": 1 if cfg['v'] > 0 else 0
            })
        except: continue
    return pd.DataFrame(res).sort_values(by="has_div", ascending=False).drop(columns=["has_div"]), t_mkt, t_pnl, t_cost, m_stats, annual_total, reminders

# --- 4. 介面呈現 ---
st.title("📱 ETF 隨身戰情室")

# --- 🚨 除息雷達提醒 (25天閃爍) ---
df, g_mkt, g_pnl, g_cost, g_months, g_annual, g_reminders = fetch_analysis(st.session_state.my_data['etfs'])

st.markdown("""
    <style>
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .blink-box { animation: blink 1s linear infinite; background-color: #fee2e2; padding: 18px; border-radius: 12px; margin-bottom: 15px; border: 2px solid #f87171; }
    </style>
""", unsafe_allow_html=True)

if g_reminders:
    for r in g_reminders:
        st.markdown(f"""
            <div class="blink-box">
                <span style='font-size: 24px;'>💰 🚨</span> 
                <b style='color: #b91c1c; font-size: 20px;'> 除息雷達提醒：</b> 
                <span style='color: #b91c1c; font-size: 20px;'>您庫存中的 {r['code']} ({r['date']}) 即將在近期除息！</span>
            </div>
        """, unsafe_allow_html=True)

# 🌙 全球夜盤監測
monitor_data = fetch_monitor_data()
if monitor_data:
    st.subheader("🌙 全球夜盤監測")
    cols = st.columns(len(monitor_data))
    for i, d in enumerate(monitor_data):
        with cols[i]: st.metric(label=d['名稱'], value=f"{d['現價']}", delta=f"{d['點數漲跌']:+.2f} ({d['漲跌幅']:+.2f}%)", delta_color="inverse")
st.divider()

# 總損益看板
p_col = "#FF0000" if g_pnl >= 0 else "#008000"
roi = (g_pnl / g_cost * 100) if g_cost != 0 else 0
st.markdown(f"<div style='background-color:#f0f2f6; padding:20px; border-radius:15px; text-align:center;'><p style='margin:0; color:#666;'>未實現總損益</p><h1 style='color:{p_col}; margin:0; font-size:55px;'>${g_pnl:,.0f}</h1><p style='margin:0; font-weight:bold; color:{p_col};'>報酬率：{roi:+.2f}%</p></div>", unsafe_allow_html=True)
st.divider()

# 📊 即時明細 (欄位重排：張數移至損益後)
st.subheader("📊 即時資產明細表")
if not df.empty:
    st.dataframe(
        df.style.format({"現價":"{:.2f}","市值":"{:,.0f}","損益":"{:,.0f}"})
        .map(lambda x: f'color:{"red" if isinstance(x, (int,float)) and x>0 else "green" if isinstance(x, (int,float)) and x<0 else "black"};font-weight:bold;', subset=['損益']),
        use_container_width=True, hide_index=True
    )

st.divider()

# 全年領息預估
st.subheader("🗓️ 全年領息預估 (按月)")
for m_name in [f"{m}月" for m in range(1, 13)]:
    data = g_months[m_name]
    if data["total"] > 0:
        with st.container():
            st.info(f"**{m_name} 領息總計：${data['total']:,.0f}**")
            for d in data["detail"]: st.write(f"  └ {d['code']}： :green[+${d['amount']:,.0f}]")
    else: st.write(f"**{m_name}**： :gray[$0]")

st.success(f"### 💰 全年度預計領息總額： ${g_annual:,.0f}")
st.divider()

# 🛠 管理資產與手動新增
with st.expander("🛠 資產管理 (編輯、刪除、手動新增)"):
    updated_list, to_delete_idx = [], -1
    
    # --- A. 編輯現有標的 ---
    st.markdown("### 📝 編輯與刪除")
    for i, item in enumerate(st.session_state.my_data.get('etfs', [])):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: st.write(f"**{item['name']}** ({item['symbol']})")
        with c2: s = st.number_input(f"股數", value=int(item['shares']), key=f"s_{i}", step=1000)
        with c3: c = st.number_input(f"成本", value=float(item['cost']), key=f"c_{i}")
        p = st.number_input(f"損益修正額", value=int(item['manual_pnl']), key=f"p_{i}")
        updated_list.append({"symbol": item['symbol'], "name": item['name'], "shares": s, "cost": c, "manual_pnl": p})
        if st.button(f"🗑️ 刪除標的", key=f"del_{i}"): to_delete_idx = i
        st.divider()
    
    # --- B. 手動新增標的 ---
    st.markdown("### ➕ 手動新增標的")
    with st.container():
        new_c1, new_c2 = st.columns(2)
        with new_c1: new_symbol = st.text_input("代號 (例: 00940.TW)", key="new_sym")
        with new_c2: new_name = st.text_input("名稱 (例: 元大臺灣價值高息)", key="new_name")
        new_c3, new_c4, new_c5 = st.columns(3)
        with new_c3: new_shares = st.number_input("持有股數", value=1000, step=1000, key="new_sh")
        with new_c4: new_cost = st.number_input("買進成本", value=10.0, key="new_co")
        with new_c5: new_pnl = st.number_input("手動損益修正", value=0, key="new_pn")
        
        if st.button("🚀 確定新增標的"):
            if new_symbol and new_name:
                st.session_state.my_data['etfs'].append({
                    "symbol": new_symbol, "name": new_name, 
                    "shares": new_shares, "cost": new_cost, "manual_pnl": new_pnl
                })
                save_to_json(st.session_state.my_data)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("代號與名稱不能為空喔！")

    # 執行刪除或更新
    if to_delete_idx != -1:
        st.session_state.my_data['etfs'].pop(to_delete_idx)
        save_to_json(st.session_state.my_data)
        st.rerun()
    if st.button("💾 儲存所有編輯內容"):
        st.session_state.my_data['etfs'] = updated_list
        save_to_json(st.session_state.my_data)
        st.cache_data.clear()
        st.rerun()

st.caption(f"最後更新：{datetime.now().strftime('%H:%M:%S')}")