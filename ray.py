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

# --- 3. 數據抓取核心 ---

# 🌟 暴力爬蟲：專門對付抓不到的台指期夜盤
@st.cache_data(ttl=15)
def fetch_tw_night_session():
    name = "🌙 台指期 (夜盤)"
    try:
        # 直接爬取 Yahoo 奇摩股市台版網頁
        url = "https://tw.stock.yahoo.com/quote/WTX%26"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 尋找網頁中顯示價格的大字體 span
        price_tags = soup.find_all("span", class_=lambda c: c and "Fz(32px)" in c)
        diff_tags = soup.find_all("span", class_=lambda c: c and "Fz(20px)" in c)
        
        if price_tags and diff_tags:
            curr = float(price_tags[0].text.replace(',', ''))
            diff_text = diff_tags[0].text.replace(',', '').strip()
            
            # 判斷是漲是跌
            if "▼" in diff_text or "-" in diff_text:
                diff = -float(diff_text.replace('▼', '').replace('-', '').strip())
            elif "▲" in diff_text or "+" in diff_text:
                diff = float(diff_text.replace('▲', '').replace('+', '').strip())
            else:
                diff = 0.0
                
            prev = curr - diff
            pct = (diff / prev) * 100 if prev != 0 else 0
            return {"name": name, "price": curr, "diff": diff, "pct": pct, "error": False}
    except Exception as e:
        print(f"夜盤爬取失敗: {e}")
    
    return {"name": name, "price": 0, "diff": 0, "pct": 0, "error": True}

@st.cache_data(ttl=10)
def fetch_market_data():
    # 美股五大指標
    us_tickers = {
        "^DJI": "🇺🇸 道瓊工業", 
        "^IXIC": "🇺🇸 那斯達克", 
        "^SOX": "🇺🇸 費城半導體",
        "NVDA": "🟢 輝達 NVIDIA",
        "TSM": "🔴 台積電 ADR"
    }
    # 台股指標 (大盤 + 台積電 + 聯發科)
    tw_tickers = {
        "^TWII": "🇹🇼 台股加權 (大盤)",
        "2330.TW": "🔴 台積電 (台股)",
        "2454.TW": "🔵 聯發科 (台股)"
    }

    def get_data(tickers):
        results = []
        for sym, name in tickers.items():
            try:
                tk = yf.Ticker(sym)
                hist = tk.history(period="5d")
                if len(hist) >= 2:
                    curr = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[-2])
                else:
                    info = tk.fast_info
                    curr = float(info.get('lastPrice', 0))
                    prev = float(info.get('regularMarketPreviousClose', curr))
                
                if curr > 0:
                    diff = curr - prev
                    pct = (diff / prev) * 100 if prev != 0 else 0
                    results.append({"name": name, "price": curr, "diff": diff, "pct": pct, "error": False})
                else:
                    results.append({"name": name, "price": 0, "diff": 0, "pct": 0, "error": True})
            except:
                results.append({"name": name, "price": 0, "diff": 0, "pct": 0, "error": True})
        return results

    us_data = get_data(us_tickers)
    tw_data = get_data(tw_tickers)
    
    # 將暴力爬蟲抓到的夜盤資料，塞進台股板塊的最後一個
    night_data = fetch_tw_night_session()
    tw_data.append(night_data)

    return us_data, tw_data

@st.cache_data(ttl=10)
def fetch_analysis(etf_list):
    if not etf_list: return pd.DataFrame(), 0, 0, 0, {}, 0, [], 0
    res, t_mkt, t_pnl, t_cost, t_day_change, annual_total = [], 0, 0, 0, 0, 0
    m_stats = {f"{m}月": {"total": 0, "detail": []} for m in range(1, 13)}
    reminders, today = [], datetime.now()
    
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
            hist = tk.history(period="2d")
            if len(hist) >= 2:
                curr_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
            else:
                curr_p = tk.fast_info.get('lastPrice', item['cost'])
                prev_p = tk.fast_info.get('regularMarketPreviousClose', curr_p)
                
            day_chg = (curr_p - prev_p) * item['shares']
            
            cfg = div_cfg.get(item['symbol'], {"m": [], "d": "無", "v": 0.0})
            if cfg["d"] != "無" and 0 <= (datetime.strptime(cfg["d"], "%Y-%m-%d") - today).days <= 25:
                reminders.append({"code": item['symbol'].split('.')[0], "date": datetime.strptime(cfg["d"], "%Y-%m-%d").strftime("%m/%d")})
            
            cash = cfg['v'] * item['shares']
            for m in cfg["m"]:
                m_stats[f"{m}月"]["total"] += cash
                m_stats[f"{m}月"]["detail"].append({"code": item['symbol'].split('.')[0], "amount": cash})
                annual_total += cash
            
            t_mkt += (item['shares'] * curr_p)
            t_pnl += item['manual_pnl']
            t_cost += (item['shares'] * item['cost'])
            t_day_change += day_chg
            
            res.append({"代號名稱": f"{item['symbol'].split('.')[0]} {item['name']}", "現價": round(curr_p, 2), "今日漲跌": day_chg, "累積損益": item['manual_pnl'], "張數": f"{int(item['shares']/1000)}張", "市值": round(item['shares'] * curr_p, 0), "除息日": cfg["d"], "has_div": 1 if cfg['v'] > 0 else 0})
        except: continue
    return pd.DataFrame(res).sort_values(by="has_div", ascending=False).drop(columns=["has_div"]), t_mkt, t_pnl, t_cost, m_stats, annual_total, reminders, t_day_change

# --- 自定義卡片 UI 渲染器 (台股紅綠習慣) ---
def render_custom_card(data):
    if data.get('error') or data['price'] == 0:
        b_color, p_str, c_str = "#e5e7eb", "讀取中...", "連線異常或無資料"
        html = f"""
        <div style="background-color: #f9fafb; border-radius: 10px; padding: 15px; margin-bottom: 15px; border: 1px dashed #d1d5db; border-left: 6px solid {b_color};">
            <div style="font-size: 14px; color: #9ca3af; font-weight: bold; margin-bottom: 5px;">{data['name']}</div>
            <div style="font-size: 20px; font-weight: bold; color: #d1d5db; margin-bottom: 5px;">{p_str}</div>
            <div style="font-size: 12px; color: #9ca3af;">{c_str}</div>
        </div>
        """
    else:
        if data['diff'] >= 0:
            b_color, p_str, c_str = "#ef4444", f"{data['price']:,.2f}", f"+{data['diff']:,.2f} (+{data['pct']:.2f}%)"
        else:
            b_color, p_str, c_str = "#22c55e", f"{data['price']:,.2f}", f"{data['diff']:,.2f} ({data['pct']:.2f}%)"
            
        html = f"""
        <div style="background-color: white; border-radius: 10px; padding: 15px; margin-bottom: 15px; border: 1px solid #e5e7eb; border-left: 6px solid {b_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 14px; color: #6b7280; font-weight: bold; margin-bottom: 5px;">{data['name']}</div>
            <div style="font-size: 28px; font-weight: 900; color: #111827; margin-bottom: 5px;">{p_str}</div>
            <div style="font-size: 14px; font-weight: bold; color: {b_color};">{c_str}</div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)

# --- 4. 介面呈現 ---
st.title("📱 ETF 隨身戰情室")

# 🚨 除息閃爍雷達
df, g_mkt, g_pnl, g_cost, g_months, g_annual, g_reminders, g_day_change = fetch_analysis(st.session_state.my_data['etfs'])
st.markdown("""<style>@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } } .blink-box { animation: blink 1s linear infinite; background-color: #fee2e2; padding: 18px; border-radius: 12px; margin-bottom: 20px; border: 2px solid #f87171; }</style>""", unsafe_allow_html=True)

if g_reminders:
    for r in g_reminders:
        st.markdown(f'<div class="blink-box"><span style="font-size: 24px;">💰 🚨</span> <b style="color: #b91c1c; font-size: 20px;"> 除息雷達：</b> <span style="color: #b91c1c; font-size: 20px;">{r["code"]} ({r["date"]}) 近期除息！</span></div>', unsafe_allow_html=True)

us_data, tw_data = fetch_market_data()

# 🌎 美股五大指標
st.markdown("### 🌎 關鍵美股指標")
r1_col1, r1_col2, r1_col3 = st.columns(3)
with r1_col1: render_custom_card(us_data[0]) # 道瓊
with r1_col2: render_custom_card(us_data[1]) # 那斯達克
with r1_col3: render_custom_card(us_data[2]) # 費半

r2_col1, r2_col2, r2_col3 = st.columns(3)
with r2_col1: render_custom_card(us_data[3]) # NVDA
with r2_col2: render_custom_card(us_data[4]) # TSM
with r2_col3: st.write("") # 為了排版美觀留空

# 🇹🇼 台股四大指標
st.markdown("### 🇹🇼 關鍵台股點數")
r3_col1, r3_col2 = st.columns(2)
with r3_col1: render_custom_card(tw_data[0]) # 加權大盤
with r3_col2: render_custom_card(tw_data[1]) # 台積電

r4_col1, r4_col2 = st.columns(2)
with r4_col1: render_custom_card(tw_data[2]) # 聯發科
with r4_col2: render_custom_card(tw_data[3]) # 台指期夜盤 (暴力爬蟲版)

st.divider()

# 💰 損益看板
p_col = "#ef4444" if g_pnl >= 0 else "#22c55e"
d_col = "#ef4444" if g_day_change >= 0 else "#22c55e"
c1, c2 = st.columns(2)
with c1: st.markdown(f"<div style='background-color:#f8fafc; padding:20px; border-radius:15px; text-align:center;'>今日損益<h2 style='color:{d_col}; margin:0; font-size: 32px;'>${g_day_change:+,.0f}</h2></div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div style='background-color:#f8fafc; padding:20px; border-radius:15px; text-align:center;'>累積總損益<h2 style='color:{p_col}; margin:0; font-size: 32px;'>${g_pnl:,.0f}</h2></div>", unsafe_allow_html=True)

st.divider()

# 📊 庫存明細
if not df.empty:
    st.dataframe(
        df.style.format({"現價":"{:.2f}","市值":"{:,.0f}","累積損益":"{:,.0f}","今日漲跌":"{:+,.0f}"})
        .map(lambda x: f'color:{"red" if (isinstance(x, (int,float)) and x>0) or str(x).startswith("+") else "green" if (isinstance(x, (int,float)) and x<0) or str(x).startswith("-") else "black"};font-weight:bold;', subset=['累積損益', '今日漲跌']), 
        use_container_width=True, hide_index=True
    )

# 🗓️ 配息預估
st.divider()
st.subheader("🗓️ 全年領息預估")
for m_name in [f"{m}月" for m in range(1, 13)]:
    data = g_months[m_name]
    if data["total"] > 0:
        with st.container():
            st.info(f"**{m_name} 領息總計：${data['total']:,.0f}**")
            for d in data["detail"]: st.write(f"  └ {d['code']}： :green[+${d['amount']:,.0f}]")

st.divider()

# 🛠️ 資產管理區塊
with st.expander("🛠 資產管理 (編輯/新增)"):
    updated_list, to_delete_idx = [], -1
    for i, item in enumerate(st.session_state.my_data.get('etfs', [])):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: st.write(f"**{item['name']} ({item['symbol'].replace('.TW', '')})**")
        with c2: s = st.number_input(f"股數", value=int(item['shares']), key=f"s_{i}", step=1000)
        with c3: c = st.number_input(f"成本", value=float(item['cost']), key=f"c_{i}")
        p = st.number_input(f"損益修正", value=int(item['manual_pnl']), key=f"p_{i}")
        updated_list.append({"symbol": item['symbol'], "name": item['name'], "shares": s, "cost": c, "manual_pnl": p})
        if st.button(f"🗑️ 刪除", key=f"del_{i}"): to_delete_idx = i
        st.markdown("---")
    
    st.markdown("### ➕ 手動新增標的")
    nc1, nc2 = st.columns(2)
    with nc1: n_sym = st.text_input("代號 (加上.TW)", key="n_sym", placeholder="例如: 00940.TW")
    with nc2: n_name = st.text_input("標的名稱", key="n_name", placeholder="例如: 元大台灣價值高息")
    nc3, nc4, nc5 = st.columns(3)
    with nc3: n_sh = st.number_input("股數", value=1000, step=1000, key="n_sh")
    with nc4: n_co = st.number_input("成本", value=10.0, key="n_co")
    with nc5: n_pnl = st.number_input("起始損益", value=0, key="n_pnl")
    
    if st.button("🚀 確定新增"):
        if n_sym and n_name:
            st.session_state.my_data['etfs'].append({"symbol": n_sym, "name": n_name, "shares": n_sh, "cost": n_co, "manual_pnl": n_pnl})
            save_to_json(st.session_state.my_data)
            st.cache_data.clear()
            st.rerun()

    if to_delete_idx != -1:
        st.session_state.my_data['etfs'].pop(to_delete_idx)
        save_to_json(st.session_state.my_data)
        st.cache_data.clear()
        st.rerun()

    if st.button("💾 儲存所有變更", type="primary"):
        st.session_state.my_data['etfs'] = updated_list
        save_to_json(st.session_state.my_data)
        st.cache_data.clear()
        st.rerun()