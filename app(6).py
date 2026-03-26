#遊戲發想者:胡文馨
#編寫:HLH
#2026/02/27
"""
最強糾察員 v6.3 
"""
import streamlit as st
import random
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
#  常數
# ══════════════════════════════════════════════════════════════════
FOOD_CATS = {
    "蔬菜":     {"pts": 5, "emoji": "🥦", "bg": "#e8f5e9", "border": "#66bb6a"},
    "水果":     {"pts": 5, "emoji": "🍎", "bg": "#fce4ec", "border": "#ef9a9a"},
    "雞肉":     {"pts": 4, "emoji": "🍗", "bg": "#fff3e0", "border": "#ffb74d"},
    "海鮮":     {"pts": 4, "emoji": "🐟", "bg": "#e1f5fe", "border": "#4fc3f7"},
    "蛋豆類":   {"pts": 3, "emoji": "🥚", "bg": "#fffde7", "border": "#f9cc4a"},
    "米飯麵食": {"pts": 3, "emoji": "🍚", "bg": "#efebe9", "border": "#a1887f"},
    "乳品":     {"pts": 2, "emoji": "🥛", "bg": "#e3f2fd", "border": "#90caf9"},
    "堅果":     {"pts": 2, "emoji": "🥜", "bg": "#f1f8e9", "border": "#aed581"},
    "油炸點心": {"pts": 1, "emoji": "🍟", "bg": "#f5f5f5", "border": "#bdbdbd"},
}

FUNC_CARDS = {
    "抽牌+2":   {"emoji": "✨", "bg": "#f3e5f5", "border": "#ce93d8",
                 "desc": "立即多抽 2 張牌"},
    "偷1張":    {"emoji": "🤫", "bg": "#fce4ec", "border": "#ef9a9a",
                 "desc": "隨機從一位玩家偷 1 張手牌"},
}

INIT_HAND         = 5
FOOD_PER_CAT      = 6
FUNC_PER_TYPE     = 5
BALANCED_BONUS    =  10  
IMBALANCE_PENALTY = -10

P_COLORS = [
    {"header": "#FF6B6B", "light": "#fff5f5", "text": "#7d2020"},
    {"header": "#4ECDC4", "light": "#f0fffe", "text": "#004d47"},
    {"header": "#f5c842", "light": "#fffdf0", "text": "#7a6000"},
    {"header": "#A29BFE", "light": "#f5f4ff", "text": "#3a2e8c"},
]

# ══════════════════════════════════════════════════════════════════
#  資料模型
# ══════════════════════════════════════════════════════════════════
@dataclass
class Card:
    kind: str
    cat:  str
    cid:  int
    img:  Optional[str] = None

    @property
    def emoji(self): return FOOD_CATS[self.cat]["emoji"] if self.kind == "food" else FUNC_CARDS[self.cat]["emoji"]
    @property
    def bg(self): return FOOD_CATS[self.cat]["bg"] if self.kind == "food" else FUNC_CARDS[self.cat]["bg"]
    @property
    def border(self): return FOOD_CATS[self.cat]["border"] if self.kind == "food" else FUNC_CARDS[self.cat]["border"]
    @property
    def pts(self): return FOOD_CATS[self.cat]["pts"] if self.kind == "food" else 0
    @property
    def desc(self): return f"+{self.pts} 分" if self.kind == "food" else FUNC_CARDS[self.cat]["desc"]

@dataclass
class Player:
    name:  str
    color: dict
    hand:  List[Card] = field(default_factory=list)
    plate: List[Card] = field(default_factory=list)
    skip_next: bool   = False

    def plate_score(self):
        if not self.plate: return 0
        total = sum(c.pts for c in self.plate)
        cats  = [c.cat for c in self.plate]
        cat_set = set(cats)
        
        has_veg     = bool(cat_set & {"蔬菜", "水果"})
        has_protein = bool(cat_set & {"雞肉", "海鮮", "蛋豆類"})
        has_carb    = bool(cat_set & {"米飯麵食"})
        if has_veg and has_protein and has_carb:
            total += BALANCED_BONUS
            
        for cat in FOOD_CATS:
            cnt = cats.count(cat)
            if cnt >= 3:
                total += IMBALANCE_PENALTY
        return total

    def is_balanced(self):
        cats = {c.cat for c in self.plate}
        return (bool(cats & {"蔬菜","水果"}) and
                bool(cats & {"雞肉","海鮮","蛋豆類"}) and
                bool(cats & {"米飯麵食"}))

# ══════════════════════════════════════════════════════════════════
#  遊戲引擎
# ══════════════════════════════════════════════════════════════════
def build_deck():
    cards, cid = [], 0
    for cat in FOOD_CATS:
        for _ in range(FOOD_PER_CAT):
            cards.append(Card("food", cat, cid)); cid += 1
    for cat in FUNC_CARDS:
        for _ in range(FUNC_PER_TYPE):
            cards.append(Card("func", cat, cid)); cid += 1
    random.shuffle(cards)
    return cards

def init_game(names: List[str], mode: str, mode_val: int):
    deck = build_deck()
    players = [Player(n, P_COLORS[i]) for i, n in enumerate(names)]
    for p in players:
        for _ in range(INIT_HAND):
            if deck: p.hand.append(deck.pop())
    return dict(
        players=players, deck=deck, discard=[],
        turn=0, phase="draw_screen", over=False,
        mode=mode, mode_val=mode_val,
        last_round=False, last_starter=None, countdown_turns=None,
        msg="", msg_type="info", events=[], round_count=0,
        pending_hand_idx=None, showing_transition=True, transition_to=0,
        last_drawn_card=None, alert_msg="",
    )

def check_emperor(gs, player_idx):
    p = gs["players"][player_idx]
    if len(p.hand) == 0 and not gs.get("last_round") and gs.get("countdown_turns") is None:
        gs["last_round"] = True
        gs["last_starter"] = player_idx
        gs["events"].append(f"👑 帝王條款發動！{p.name} 打出了最後一張手牌，進入最後一輪！")

def check_end(gs) -> tuple:
    players = gs["players"]
    mode    = gs["mode"]

    if gs.get("countdown_turns") is not None:
        if gs["countdown_turns"] <= 0:
            return True, "最後倒數結束，結算最高分數！"

    if gs.get("last_round"):
        nxt = (gs["turn"] + 1) % len(players)
        if nxt == gs["last_starter"]:
            return True, "帝王條款 / 最後一輪結束，結算分數！"

    if mode == "allcards" and not gs["deck"]:
        return True, "牌堆已抽完，結算最高分數！"

    if mode == "rounds":
        if gs["round_count"] >= gs["mode_val"] * len(players):
            return True, f"已完成 {gs['mode_val']} 回合！"

    if mode == "score":
        for p in players:
            if p.plate_score() >= gs["mode_val"]:
                return True, f"🎉 {p.name} 率先達到 {gs['mode_val']} 分！"
        if not gs["deck"] and all(len(p.hand) == 0 for p in players):
            return True, "牌堆與手牌皆空，但無人達標，以目前最高分結算！"

    return False, ""

def advance_turn(gs):
    if gs.get("countdown_turns") is not None:
        gs["countdown_turns"] -= 1

    over, reason = check_end(gs)
    if over:
        gs["over"], gs["msg"], gs["msg_type"], gs["phase"] = True, reason, "success", "over"
        return

    players = gs["players"]
    n = len(players)
    gs["round_count"] += 1

    nxt = (gs["turn"] + 1) % n
    if players[nxt].skip_next:
        players[nxt].skip_next = False
        gs["events"].append(f"⏸️ {players[nxt].name} 被暫停，跳過本回合！")
        if gs.get("countdown_turns") is not None: 
            gs["countdown_turns"] -= 1  
        nxt = (nxt + 1) % n

    gs["turn"]  = nxt
    gs["phase"] = "draw_screen"
    gs["pending_hand_idx"] = None
    gs["last_drawn_card"]  = None
    gs["showing_transition"] = True
    gs["transition_to"]      = nxt
    gs["msg"]                = ""

# ── 行動函式 ─────────────────────────────────────────────────────
def action_draw(gs):
    p = gs["players"][gs["turn"]]
    if gs["deck"]:
        c = gs["deck"].pop()
        p.hand.append(c)
        gs["last_drawn_card"] = len(p.hand) - 1
        gs["msg"], gs["msg_type"] = f"🃏 抽到了 {c.emoji} {c.cat}", "info"
    else:
        gs["last_drawn_card"] = None
        gs["msg"], gs["msg_type"] = "牌堆已空，請直接進行行動！", "warning"
    gs["phase"] = "action"
    st.session_state.sel = None

def action_place(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand.pop(hand_idx)
    p.plate.append(card)
    gs["msg"], gs["msg_type"] = f"🍽️ 將 {card.emoji} {card.cat} 放入餐盤（+{card.pts}分）", "success"
    
    should_alert = False
    if p.is_balanced():
        if gs["mode"] == "first_plate" and gs.get("countdown_turns") is None:
            # ⭐ 核心修正：+1 保證換人時不會吃到贏家未來的回合扣打，讓每個人都有完整 N 輪
            gs["countdown_turns"] = (gs["mode_val"] * len(gs["players"])) + 1
            gs["events"].append(f"🚨 {p.name} 首位達成均衡餐盤！進入最後 {gs['mode_val']} 輪倒數！")
            gs["alert_msg"] = f"玩家 {p.name} 率先完成了均衡餐盤！遊戲正式進入最後 {gs['mode_val']} 輪倒數！"
            gs["phase"] = "alert_first_plate"
            should_alert = True
        else:
            gs["events"].append(f"🌟 {p.name} 達成均衡餐盤！額外 +{BALANCED_BONUS} 分！")
            
    if p.plate.count(card.cat) == 3:
        gs["events"].append(f"⚠️ {p.name} 的 {card.cat} 達到 3 張，扣 10 分！")
        
    st.session_state.sel = None
    
    if should_alert:
        return  

    check_emperor(gs, gs["turn"])
    advance_turn(gs)

def action_discard(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand.pop(hand_idx)
    gs["discard"].append(card)
    gs["msg"], gs["msg_type"] = f"🗑️ 棄置 {card.emoji} {card.cat}", "info"
    st.session_state.sel = None
    check_emperor(gs, gs["turn"])
    advance_turn(gs)

def action_use_func(gs, hand_idx):
    p    = gs["players"][gs["turn"]]
    card = p.hand[hand_idx]
    func = card.cat
    players = gs["players"]

    if func == "抽牌+2":
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        if not gs["deck"]:
            gs["msg"], gs["msg_type"] = "✨ 抽牌+2！但牌堆已空無牌可抽，卡片失效！", "error"
            check_emperor(gs, gs["turn"])
            advance_turn(gs)
            return

        drawn = []
        for _ in range(2):
            if gs["deck"]:
                c = gs["deck"].pop()
                p.hand.append(c)
                drawn.append(f"{c.emoji}{c.cat}")
        gs["msg"], gs["msg_type"] = f"✨ 抽牌+2！抽到：{'、'.join(drawn)}", "success"
        st.session_state.sel = None
        gs["phase"] = "confirm_draw"
        check_emperor(gs, gs["turn"])

    elif func == "偷1張":
        targets = [(i, pl) for i, pl in enumerate(players) if i != gs["turn"] and pl.hand]
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        if not targets:
            gs["msg"], gs["msg_type"] = "🤫 偷1張！但對手皆無手牌，卡片失效！", "error"
            check_emperor(gs, gs["turn"])
            advance_turn(gs)
            return
            
        ti, tp    = random.choice(targets)
        stolen    = random.choice(tp.hand)
        tp.hand.remove(stolen)
        p.hand.append(stolen)
        gs["msg"], gs["msg_type"] = f"🤫 隨機偷到 {tp.name} 的 {stolen.emoji}{stolen.cat}！", "success"
        gs["events"].append(f"😱 {p.name} 偷了 {tp.name} 的牌！")
        st.session_state.sel = None
        check_emperor(gs, gs["turn"])
        advance_turn(gs)





# ══════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Fredoka+One&display=swap');

html, body, p, div, span, h1, h2, h3, h4, h5, h6, label, input, button, a, li, ul, ol, strong, b, i, em, mark, small, del, ins, sub, sup {
    color: #000000 !important; 
    font-family: 'Nunito', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #a0a5aa 0%, #cfd4d8 20%, #8a9095 50%, #c4c9cd 80%, #767b80 100%);
    background-attachment: fixed;
}

div[data-baseweb="base-input"], div[data-baseweb="input"] {
    background-color: #ffffff !important; border: 2px solid #555 !important; border-radius: 8px !important;
}
input {
    background-color: transparent !important; color: #000000 !important; font-weight: 900 !important;
    -webkit-text-fill-color: #000000 !important;
}

summary {
    background-color: rgba(255, 255, 255, 0.85) !important; border-radius: 10px !important;
    border: 2px solid #888 !important; margin-bottom: 8px !important;
}
summary p { font-weight: 900 !important; font-size: 1.15rem !important; }
summary svg { fill: #000000 !important; color: #000000 !important; }

.main-title {
    font-family: 'Fredoka One', cursive; font-size: 2.8rem; text-align: center;
    background: linear-gradient(135deg, #cc2e2e, #b87100, #1b857e, #554dbe); 
    background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: rainbowSlide 5s linear infinite; margin: 0; line-height: 1.2;
}
@keyframes rainbowSlide { to { background-position: 200% center; } }
.sub-title { text-align: center; font-size: .9rem; font-weight: 900; letter-spacing: 2px; margin-top: 2px; }

.card {
    border-radius: 16px; padding: 14px 8px 12px; text-align: center; border: 3px solid #ccc;
    cursor: pointer; transition: transform .2s cubic-bezier(.34,1.56,.64,1), box-shadow .2s ease;
    box-shadow: 0 4px 10px rgba(0,0,0,.2); position: relative; user-select: none; overflow: hidden;
    margin-top: 15px; margin-bottom: 10px;
}
.card:hover { transform: translateY(-8px) scale(1.05); box-shadow: 0 12px 26px rgba(0,0,0,.3); z-index: 10; }
.card-selected {
    transform: translateY(-10px) scale(1.07) !important;
    box-shadow: 0 0 0 4px #FFD700, 0 12px 26px rgba(0,0,0,.4) !important;
    border-color: #FFD700 !important; background-color: #FFFDE7 !important; 
}
.card-selected::before { content: '⭐'; position: absolute; top: 4px; right: 5px; font-size: 1.1rem; }
.card-emoji { font-size: 2.2rem; line-height: 1.1; margin-bottom: 5px; } 
.card-name  { font-size: 0.9rem; font-weight: 900; margin-bottom: 3px; }
.card-desc  { font-size: 0.75rem; font-weight: 900; }

.plate-area {
    background: rgba(255, 255, 255, 0.75); border: 3px solid #888; border-top: none;       
    border-radius: 0 0 14px 14px; padding: 10px; min-height: 90px;
    backdrop-filter: blur(4px); margin-bottom: 10px;
}
.plate-balanced {
    border-color: #2e7d32 !important; background: rgba(67,160,71,.2) !important;
    box-shadow: 0 0 18px rgba(67,160,71,.4) !important; animation: balGlow 2s ease infinite;
}
@keyframes balGlow { 0%,100% { box-shadow: 0 0 10px rgba(67,160,71,.3); } 50% { box-shadow: 0 0 24px rgba(67,160,71,.6); } }

.player-header {
    border-radius: 12px 12px 0 0; padding: 10px 12px; font-weight: 900; font-size: 1rem; 
    display: flex; align-items: center; gap: 7px; 
}
.active-glow { animation: activeGlow 1.8s ease infinite; }
@keyframes activeGlow { 0%,100% { box-shadow: 0 0 0 3px #FFD700; } 50% { box-shadow: 0 0 0 6px #FFD700, 0 4px 24px rgba(255,215,0,.6); } }

.msg-box {
    border-radius: 12px; padding: 12px 16px; font-weight: 900; font-size: 1.1rem; text-align: center;
    animation: msgPop .3s cubic-bezier(.34,1.56,.64,1); margin: 8px 0; border: 3px solid rgba(0,0,0,0.2);
}
@keyframes msgPop { from { opacity: 0; transform: scale(.92) translateY(-5px); } to { opacity: 1; transform: scale(1) translateY(0); } }

.event-item {
    border-radius: 8px; padding: 8px 12px; font-weight: 900; font-size: .95rem; 
    background: #FFF9C4; border-left: 4px solid #FFC107; margin-bottom: 6px; animation: slideIn .3s ease;
}
@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }

.stButton > button {
    background-color: #ffffff !important; border: 3px solid #777 !important; border-radius: 14px !important;
    padding: 8px 10px !important; transition: transform .15s ease, box-shadow .15s ease, background-color .2s !important;
}
.stButton > button p { font-size: 1.15rem !important; font-weight: 900 !important; }
.stButton > button:hover { background-color: #FFFDE7 !important; border-color: #FFD700 !important; transform: translateY(-3px) !important; box-shadow: 0 6px 18px rgba(0,0,0,.2) !important; }
div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #FF6B6B, #FF8E53) !important; border: 3px solid #D64545 !important; box-shadow: 0 4px 12px rgba(230,92,92,.4) !important; }
div[data-testid="stButton"] > button[kind="primary"] p { font-size: 1.25rem !important; text-shadow: none !important; }
.element-container { margin-bottom: 8px !important; }
div[data-testid="stVerticalBlock"] { gap: 10px; }
</style>
"""

def msg_html(text, mtype="info"):
    bg = {"info": "#dbeafe", "success": "#dcfce7", "warning": "#fef9c3", "error": "#fee2e2"}.get(mtype, "#dbeafe")
    return f'<div class="msg-box" style="background:{bg};">{text}</div>'

def score_html(score): return f'<span class="score-badge" style="display:inline-block; background:#FFD700; border:2px solid #b89b00; font-weight:900; padding:2px 10px; border-radius:20px;">⭐ {score} 分</span>'

def render_card(card: Card, selected=False, small=False) -> str:
    sel_cls = "card-selected" if selected else ""
    e_sz = "1.7rem" if small else "2.2rem"
    return f'<div class="card {sel_cls}" style="background:{card.bg};border-color:{card.border};"><div class="card-emoji" style="font-size:{e_sz};">{card.emoji}</div><div class="card-name">{card.cat}</div><div class="card-desc">{card.desc}</div></div>'

def render_ranking(players, ci, gs):
    ranked  = sorted(enumerate(players), key=lambda x: x[1].plate_score(), reverse=True)
    max_sc  = max((p.plate_score() for p in players), default=1) or 1
    medals  = ["🥇","🥈","🥉","4️⃣"]
    for ri, (pi, p) in enumerate(ranked):
        sc  = p.plate_score()
        pct = max(5, int(sc / max_sc * 100)) if sc > 0 else 5
        bg = f"background:#ffffff; border:3px solid {p.color['header']};"
        st.markdown(f'<div style="{bg} display:flex; align-items:center; gap:9px; padding:8px 12px; border-radius:12px; margin-bottom:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15);"><span style="font-size: 1.3rem;">{medals[ri]}</span><span style="flex:1; font-size: 1.05rem; font-weight: 900;">{"▶ " if pi==ci else ""}{p.name}{" ✅" if p.is_balanced() else ""}{" ⏸️" if p.skip_next else ""}</span><div style="flex: 1; background: #ddd; border-radius: 6px; height: 12px; overflow: hidden; border:1px solid #aaa;"><div style="height: 100%; border-radius: 6px; width:{pct}%; background:{p.color["header"]};"></div></div>{score_html(sc)}</div>', unsafe_allow_html=True)

    if gs["mode"] == "score":
        st.markdown(f'<div style="font-size:1rem;text-align:center;font-weight:900;margin-top:10px;">🏁 目標：{gs["mode_val"]} 分</div>', unsafe_allow_html=True)
    elif gs["mode"] == "rounds":
        done, total = gs["round_count"], gs["mode_val"] * len(players)
        st.markdown(f'<div style="font-size:1rem;text-align:center;font-weight:900;margin-top:10px;">🔁 回合進度 {done}/{total}</div>', unsafe_allow_html=True)
        st.progress(min(int(done / total * 100) if total else 0, 100))

# ══════════════════════════════════════════════════════════════════
#  設定頁
# ══════════════════════════════════════════════════════════════════
def page_setup():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="main-title">🥗 最強糾察員</div><div class="sub-title">NUTRITION BATTLE CARD GAME</div><br>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown("### 👥 玩家設定")
        num = st.slider("玩家人數", 2, 4, 2, key="setup_num")
        names = [st.text_input(f"玩家 {i+1} 名稱", value=["玩家一 🔴", "玩家二 🟦", "玩家三 🟡", "玩家四 🟣"][i]).strip() or f"玩家{i+1}" for i in range(num)]

        st.markdown("---")
        st.markdown("### 🎮 遊戲模式")
        mode_pick = st.radio("", ["🔁 回合模式", "🃏 全牌模式", "🏁 分數模式", "🥇 最先一盤"], horizontal=True, label_visibility="collapsed")
        mode_val = 0
        if "回合模式" in mode_pick:
            st.markdown('<div style="background:#dbeafe;border:2px solid #90caf9;border-radius:10px;padding:12px;font-weight:900;">每位玩家進行設定回合數結算高分獲勝</div>', unsafe_allow_html=True)
            mode_val, mode_key = st.slider("每人回合數", 3, 15, 5), "rounds"
        elif "全牌模式" in mode_pick:
            st.markdown('<div style="background:#dcfce7;border:2px solid #81c784;border-radius:10px;padding:12px;font-weight:900;">牌堆抽完後結算，分數最高者獲勝</div>', unsafe_allow_html=True)
            mode_key = "allcards"
        elif "分數模式" in mode_pick:
            st.markdown('<div style="background:#fff9c4;border:2px solid #fff176;border-radius:10px;padding:12px;font-weight:900;">率先達到目標分數的玩家立即獲勝</div>', unsafe_allow_html=True)
            mode_val, mode_key = st.slider("目標分數", 10, 80, 30), "score"
        else:
            st.markdown('<div style="background:#ffccbc;border:2px solid #ff8a65;border-radius:10px;padding:12px;font-weight:900;">有人達成均衡餐盤後啟動全場最後 N 輪倒數！</div>', unsafe_allow_html=True)
            mode_val, mode_key = st.slider("觸發後倒數輪數 (N)", 1, 5, 1), "first_plate"

    with col_r:
        st.markdown("### 🍱 食物牌（每種 ×6 張）")
        for cat, info in FOOD_CATS.items():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:2px solid #aaa;font-weight:900;"><span>{info["emoji"]} {cat}</span><span style="color:#b71c1c !important;">+{info["pts"]} 分</span></div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:10px 0;font-weight:900;">🌟 均衡加成（蔬果+蛋白+澱粉）<b style="color:#1b5e20 !important;">+10 分</b></div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#b71c1c !important;font-weight:900;">❌ 任一食物種類達到 3 張 <b style="color:#b71c1c !important;">−10 分</b>（所有食物皆適用，多種違規可累加）</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎮 開始遊戲！", use_container_width=True, type="primary"):
            if len(set(names)) < len(names): st.error("玩家名稱不能重複！"); return
            st.session_state.gs = init_game(names, mode_key, mode_val)
            st.session_state.sel = None; st.session_state.page = "game"; st.rerun()

# ══════════════════════════════════════════════════════════════════
#  過場、抽牌與警報頁
# ══════════════════════════════════════════════════════════════════
def page_transition():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    p = gs["players"][gs["transition_to"]]
    st.session_state.sel = None
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        for ev in gs["events"]: st.markdown(f'<div class="event-item">📢 {ev}</div>', unsafe_allow_html=True)
        gs["events"].clear()
        st.markdown(f'<div style="border-radius:24px; padding:36px 24px; text-align:center; background:#ffffff; border:5px solid #FFD700; box-shadow: 0 10px 30px rgba(0,0,0,0.3);"><div style="font-size:1.5rem;font-weight:900;margin-bottom:12px;">👇 請將裝置交給</div><div style="font-family:\'Fredoka One\',cursive; font-size:4.5rem; color:{p.color["header"]} !important;">{p.name}</div><div style="font-size:1.4rem;font-weight:900;margin:16px 0 10px;">準備開始你的回合！</div></div><br>', unsafe_allow_html=True)
        if st.button(f"✅ 我是 {p.name}，準備好了！", use_container_width=True, type="primary"):
            gs["showing_transition"] = False; st.rerun()

def page_alert_first_plate():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    st.markdown(f'<div style="border-radius:24px; padding:50px 24px; text-align:center; background:#ffccbc; border:10px solid #d84315; box-shadow:0 10px 30px rgba(0,0,0,0.5); margin-top:5vh;"><div style="font-size:6rem; margin-bottom:20px;">🚨</div><div style="font-family:\'Fredoka One\',cursive; font-size:3.5rem; font-weight:900; margin-bottom:20px;">均衡餐盤達成！</div><div style="font-size:1.8rem; font-weight:900; background:#fff9c4; border: 4px solid #fbc02d; padding: 30px; border-radius: 16px;">{gs.get("alert_msg", "")}</div></div><br><br>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("✅ 收到！全軍備戰，繼續遊戲！", use_container_width=True, type="primary"):
            gs["phase"] = "action"
            check_emperor(gs, gs["turn"])
            advance_turn(gs)
            st.rerun()

def page_draw():
    st.markdown(CSS, unsafe_allow_html=True)
    gs, ci = st.session_state.gs, st.session_state.gs["turn"]
    cur = gs["players"][ci]
    st.markdown('<div class="main-title" style="font-size:2rem;">🥗 最強糾察員</div><br>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        st.markdown(f'<div style="border-radius:24px; padding:36px 24px; text-align:center; background:#ffffff; border:5px solid #90CAF9; box-shadow:0 10px 30px rgba(0,0,0,0.2);"><div style="font-family:\'Fredoka One\',cursive; font-size:3rem;">🎴 {cur.name} 的回合</div><div style="font-size:1.3rem; font-weight:900; margin-bottom:20px;">牌堆剩餘 <b>{len(gs["deck"])}</b> 張</div></div><br>', unsafe_allow_html=True)
        if gs["deck"]:
            st.markdown("""
<style>
div[data-testid="stButton"].draw-btn > button {
    background: linear-gradient(135deg, #FF6B35, #F7C59F, #FF6B35) !important;
    background-size: 200% auto !important;
    animation: drawPulse 1.8s ease-in-out infinite, drawShine 3s linear infinite !important;
    border: 4px solid #c94a00 !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 28px rgba(255,107,53,0.55), 0 2px 0 #c94a00 !important;
    padding: 22px 10px !important;
    margin: 8px 0 !important;
    transform: scale(1.04) !important;
}
div[data-testid="stButton"].draw-btn > button p {
    font-size: 2rem !important;
    font-weight: 900 !important;
    letter-spacing: 6px !important;
    color: #ffffff !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
}
div[data-testid="stButton"].draw-btn > button:hover {
    transform: scale(1.08) translateY(-4px) !important;
    box-shadow: 0 14px 36px rgba(255,107,53,0.7) !important;
}
@keyframes drawPulse {
    0%,100% { box-shadow: 0 8px 28px rgba(255,107,53,0.55), 0 2px 0 #c94a00; }
    50%      { box-shadow: 0 12px 42px rgba(255,107,53,0.85), 0 2px 0 #c94a00, 0 0 0 8px rgba(255,107,53,0.2); }
}
@keyframes drawShine {
    to { background-position: 200% center; }
}
</style>
""", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="draw-btn">', unsafe_allow_html=True)
                if st.button("🃏  抽  一  張  牌", use_container_width=True, type="primary", key="draw_main_btn"): action_draw(gs); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg_html("牌堆已空！直接進入行動階段", "warning"), unsafe_allow_html=True)
            if st.button("⚡ 直接行動", use_container_width=True, type="primary"): gs["phase"] = "action"; st.rerun()
        
        st.markdown(f'<div style="font-size:1.2rem;font-weight:900;margin-bottom:10px;text-align:center;background:rgba(255,255,255,0.8);border-radius:8px;padding:5px;">📋 目前手牌（{len(cur.hand)} 張）</div>', unsafe_allow_html=True)
        if cur.hand:
            hc = st.columns(min(len(cur.hand), 6) or 1)
            for i, card in enumerate(cur.hand):
                with hc[i % 6]: st.markdown(render_card(card, small=True), unsafe_allow_html=True)
    with c3:
        st.markdown("**📊 目前排名**")
        render_ranking(gs["players"], ci, gs)

# ══════════════════════════════════════════════════════════════════
#  行動主頁
# ══════════════════════════════════════════════════════════════════
def page_action():
    st.markdown(CSS, unsafe_allow_html=True)
    gs, ci, phase = st.session_state.gs, st.session_state.gs["turn"], st.session_state.gs["phase"]
    players, cur = gs["players"], gs["players"][ci]

    sel = st.session_state.get("sel", None)
    if sel is not None and (not cur.hand or sel >= len(cur.hand)): st.session_state.sel = sel = None

    h1, h2, h3 = st.columns([3, 1, 1])
    with h1:
        st.markdown('<div class="main-title" style="font-size:1.8rem;text-align:left;">🥗 最強糾察員</div>', unsafe_allow_html=True)
        lbl, pbg = {"action":("⚡ 行動階段 — 選擇一張牌","#fff59d"), "confirm_draw":("✨ 確認手牌","#a5d6a7")}.get(phase, ("⚡ 行動階段", "#fff59d"))
        st.markdown(f'<span style="display:inline-block; background:{pbg}; border:3px solid #333; font-weight:900; padding:6px 16px; border-radius:20px;">{lbl}</span>', unsafe_allow_html=True)
    with h2: st.markdown(f'<div style="background:#ffffff;border:4px solid #42a5f5;border-radius:12px;padding:8px;text-align:center;font-weight:900;box-shadow:0 2px 6px rgba(0,0,0,0.1);">牌堆<br><span style="font-size:1.8rem;">{len(gs["deck"])}</span></div>', unsafe_allow_html=True)
    with h3: st.markdown(f'<div style="background:#ffffff;border:4px solid #ef5350;border-radius:12px;padding:8px;text-align:center;font-weight:900;box-shadow:0 2px 6px rgba(0,0,0,0.1);">棄牌<br><span style="font-size:1.8rem;">{gs["discard"][-1].emoji if gs["discard"] else "—"}</span></div>', unsafe_allow_html=True)

    if gs["msg"]: st.markdown(msg_html(gs["msg"], gs["msg_type"]), unsafe_allow_html=True)
    st.markdown("---")

    left, right = st.columns([1, 2.8])
    with left:
        st.markdown("**📊 即時排名**")
        render_ranking(players, ci, gs)
        if gs.get("countdown_turns") is not None:
            left_r = (gs["countdown_turns"] + len(players) - 1) // len(players)
            st.markdown(f'<div class="event-item" style="border-color:#d84315;background:#ffccbc;text-align:center;">🚨 倒數：剩餘 {left_r} 輪！</div>', unsafe_allow_html=True)
        elif gs.get("last_round"):
            st.markdown('<div class="event-item" style="border-color:#d84315;background:#ffccbc;text-align:center;">⚡ 最後一輪！</div>', unsafe_allow_html=True)

    with right:
        st.markdown("**🍽️ 各玩家餐盤**")
        pcols = st.columns(len(players))
        for pi, p in enumerate(players):
            with pcols[pi]:
                st.markdown(f'<div style="{"border-right: 3px dashed #777; padding-right: 15px;" if pi < len(players)-1 else "padding-right: 5px;"} height: 100%;">', unsafe_allow_html=True)
                is_cur = pi == ci
                st.markdown(f'<div class="player-header {"active-glow" if is_cur else ""}" style="background:{p.color["header"] if is_cur else "#ffffff"};border:4px solid {p.color["header"]};border-bottom:none;"><span style="font-weight:900;">{"▶ " if is_cur else ""}{p.name}{" ⏸️" if p.skip_next else ""}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plate-area {"plate-balanced" if p.is_balanced() else ""}">', unsafe_allow_html=True)
                if p.plate:
                    cc = st.columns(min(len(p.plate), 5) or 1)
                    for j, c in enumerate(p.plate):
                        with cc[j % 5]: st.markdown(render_card(c, small=True), unsafe_allow_html=True)
                else: st.markdown("<div style='text-align:center;padding:25px 0;font-weight:900;'>🈳 空</div>", unsafe_allow_html=True)
                st.markdown("</div>" + (f'<div style="text-align:center;font-weight:900;color:#1b5e20 !important;background:#c8e6c9;border-radius:6px;border:2px solid #4caf50;">✅ 均衡 +{BALANCED_BONUS}</div>' if p.is_balanced() else "") + "</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f'<div style="font-size:1.3rem; font-weight:900; background:#ffffff; border-radius:12px; padding:8px 16px; display:inline-block; border:4px solid {cur.color["header"]}; margin-bottom:20px; box-shadow:0 4px 10px rgba(0,0,0,0.15);">🎴 {cur.name} 的手牌（{len(cur.hand)} 張）</div>', unsafe_allow_html=True)

        if cur.hand:
            n_cols = min(len(cur.hand), 6) or 1
            hcols  = st.columns(n_cols)
            last_drawn = gs.get("last_drawn_card")
            for i, card in enumerate(cur.hand):
                with hcols[i % n_cols]:
                    is_sel, is_new = (sel == i), (last_drawn is not None and i == last_drawn)
                    if is_new: st.markdown('<div style="text-align:center;font-size:.9rem;font-weight:900;margin-bottom:6px;background:#bbdefb;border:2px solid #1976d2;border-radius:6px;">🆕 剛抽到</div>', unsafe_allow_html=True)
                    st.markdown(render_card(card, selected=is_sel), unsafe_allow_html=True)
                    if phase == "action":
                        if st.button("⭐ 已選" if is_sel else "選擇", key=f"hsel_{i}", use_container_width=True):
                            st.session_state.sel = i if not is_sel else None; st.rerun()
        else: st.info("手牌為空")

        sel_card = cur.hand[sel] if (sel is not None and sel < len(cur.hand)) else None
        if sel_card and phase == "action":
            st.markdown(f'<div style="background:{sel_card.bg};border:4px solid {sel_card.border};border-radius:16px;padding:16px;font-weight:900;font-size:1.25rem;text-align:center;margin:15px 0;box-shadow:0 6px 15px rgba(0,0,0,0.15);">{sel_card.emoji} <b>{sel_card.cat}</b> — {sel_card.desc}</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    if phase == "confirm_draw":
        st.markdown(msg_html("✨ 抽牌完畢！請看一眼確認你新抽到的手牌後，點擊下方按鈕結束回合", "success"), unsafe_allow_html=True)
        if st.button("✅ 我確認完畢，換下一位", use_container_width=True, type="primary"): advance_turn(gs); st.rerun()

    elif phase == "action":
        if not sel_card: st.markdown(msg_html("👆 請先點選一張手牌，再選擇下方行動", "info"), unsafe_allow_html=True)
        else:
            can_place, can_func = sel_card.kind == "food", sel_card.kind == "func"
            ac = st.columns(3)
            with ac[0]:
                if st.button(f"🍽️ 放入餐盤", disabled=not can_place, use_container_width=True, type="primary"): action_place(gs, sel); st.rerun()
            with ac[1]:
                if st.button("✨ 使用功能牌" if can_func else "（請選功能牌）", disabled=not can_func, use_container_width=True, type="primary"): action_use_func(gs, sel); st.rerun()
            with ac[2]:
                if st.button("🗑️ 丟掉不用", use_container_width=True): action_discard(gs, sel); st.rerun()

# ══════════════════════════════════════════════════════════════════
#  結果頁
# ══════════════════════════════════════════════════════════════════
def page_result():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    for p in gs["players"]: p.score = p.plate_score()
    ranked, medals = sorted(gs["players"], key=lambda p: p.score, reverse=True), ["🥇","🥈","🥉","4️⃣"]

    st.markdown('<div class="main-title">🏆 遊戲結束！</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:2rem;font-weight:900;margin:16px 0;background:rgba(255,255,255,0.6);border-radius:20px;padding:10px;">🎉 {ranked[0].name} 獲勝！<br>{score_html(ranked[0].score)}</div>', unsafe_allow_html=True)
    st.markdown("---")

    for ri, p in enumerate(ranked):
        cats = {}
        for c in p.plate: cats[c.cat] = cats.get(c.cat, 0) + 1
        raw, bal_b = sum(c.pts for c in p.plate), BALANCED_BONUS if p.is_balanced() else 0
        imbal = sum(IMBALANCE_PENALTY for cat, cnt in cats.items() if cnt >= 3)

        with st.expander(f"{medals[ri]} {p.name}  ── {p.score} 分", expanded=(ri == 0)):
            dc1, dc2 = st.columns([2, 1])
            with dc1:
                st.markdown(f"**餐盤：** {' '.join(c.emoji for c in p.plate) or '空'}", unsafe_allow_html=True)
                for cat, cnt in cats.items():
                    pts_per, em = FOOD_CATS.get(cat, {}).get("pts", 0), FOOD_CATS.get(cat, {}).get("emoji", "")
                    st.markdown(f'<div style="font-size:1.1rem;font-weight:900;padding:4px 0;">{em} {cat} × {cnt} 張 = <span style="color:#c62828 !important;">{pts_per*cnt} 分</span></div>', unsafe_allow_html=True)
                if bal_b: 
                    st.markdown(f'<div style="background:#b9f6ca; border:3px solid #00c853; padding:8px 12px; border-radius:8px; font-weight:900; font-size:1.1rem; margin-bottom:5px;">✅ 均衡加成 +{bal_b}</div>', unsafe_allow_html=True)
                if imbal: 
                    st.markdown(f'<div style="background:#ffcdd2; border:3px solid #d50000; padding:8px 12px; border-radius:8px; font-weight:900; font-size:1.1rem; margin-bottom:5px;">❌ 失衡懲罰 {imbal}</div>', unsafe_allow_html=True)
            
            with dc2:
                bal_str = f'<div style="background:#b9f6ca; border:2px solid #00c853; border-radius:6px; padding:4px 8px; margin-top:5px; font-weight:900;">+{bal_b} 均衡</div>' if bal_b else ''
                imbal_str = f'<div style="background:#ffcdd2; border:2px solid #d50000; border-radius:6px; padding:4px 8px; margin-top:5px; font-weight:900;">{imbal} 失衡</div>' if imbal else ''
                
                st.markdown(f'<div style="background:#ffffff;border:4px solid {p.color["header"]};border-radius:16px;padding:16px;text-align:center;box-shadow:0 6px 15px rgba(0,0,0,0.15);"><div style="font-weight:900;">食物基礎</div><div style="font-size:2.2rem;font-weight:900;">{raw}</div><div style="font-weight:900; margin:10px 0;">{bal_str}{imbal_str}</div><div style="font-size:1.8rem;font-weight:900;color:#c62828 !important;border-top:3px solid #ccc;margin-top:10px;padding-top:10px;">= {p.score} 分</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 返回主畫面", use_container_width=True, type="primary"):
            st.session_state.page = "setup"; del st.session_state.gs; st.rerun()

def main():
    st.set_page_config(page_title="最強糾察員", page_icon="🥗", layout="wide", initial_sidebar_state="collapsed")
    if "page" not in st.session_state: st.session_state.page = "setup"
    if "sel"  not in st.session_state: st.session_state.sel  = None
    gs = st.session_state.get("gs")
    if st.session_state.page == "setup": page_setup(); return
    if not gs: st.session_state.page = "setup"; st.rerun(); return
    if gs.get("over") or gs.get("phase") == "over": page_result(); return
    if gs.get("showing_transition"): page_transition(); return
    if gs.get("phase") == "alert_first_plate": page_alert_first_plate(); return
    if gs.get("phase", "draw_screen") == "draw_screen": page_draw()
    else: page_action()

if __name__ == "__main__": main()
