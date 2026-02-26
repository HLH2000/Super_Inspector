"""
最強糾察員 v4 ── 修正版 (護眼閱讀背景版)
修正：IndexError / 白字 / 抽牌獨立大畫面 / 回合計數邏輯 / 護眼背景調整
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
    "丟1張":    {"emoji": "💥", "bg": "#fff3e0", "border": "#ffb74d",
                 "desc": "將自己餐盤中 1 張移至棄牌區"},
    "順時針交換":{"emoji": "🔄", "bg": "#e0f2f1", "border": "#80cbc4",
                 "desc": "所有玩家手牌順時針傳遞"},
    "暫停":     {"emoji": "⛔", "bg": "#ede7f6", "border": "#b39ddb",
                 "desc": "指定一位玩家跳過下回合"},
}

INIT_HAND     = 5
MAX_HAND      = 6
MAX_PLATE     = 5
FOOD_PER_CAT  = 6
FUNC_PER_TYPE = 5
BALANCED_BONUS    =  5
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
    kind: str   # "food" | "func"
    cat:  str
    cid:  int
    img:  Optional[str] = None

    @property
    def emoji(self):
        return FOOD_CATS[self.cat]["emoji"] if self.kind == "food" else FUNC_CARDS[self.cat]["emoji"]
    @property
    def bg(self):
        return FOOD_CATS[self.cat]["bg"] if self.kind == "food" else FUNC_CARDS[self.cat]["bg"]
    @property
    def border(self):
        return FOOD_CATS[self.cat]["border"] if self.kind == "food" else FUNC_CARDS[self.cat]["border"]
    @property
    def pts(self):
        return FOOD_CATS[self.cat]["pts"] if self.kind == "food" else 0
    @property
    def desc(self):
        if self.kind == "food":
            return f"+{self.pts} 分"
        return FUNC_CARDS[self.cat]["desc"]


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
            if cats.count(cat) > 3:
                total += IMBALANCE_PENALTY
        return total

    def is_balanced(self):
        cats = {c.cat for c in self.plate}
        return (bool(cats & {"蔬菜","水果"}) and
                bool(cats & {"雞肉","海鮮","蛋豆類"}) and
                bool(cats & {"米飯麵食"}))

    def imbalanced_cat(self):
        cats = [c.cat for c in self.plate]
        for cat in FOOD_CATS:
            if cats.count(cat) > 3: return cat
        return None


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
        turn=0,
        phase="draw_screen",
        over=False,
        mode=mode,
        mode_val=mode_val,
        last_round=False,
        last_starter=None,
        msg="", msg_type="info",
        events=[],
        round_count=0,
        pending_hand_idx=None,
        showing_transition=True,
        transition_to=0,
        last_drawn_card=None,
    )

def check_end(gs) -> tuple:
    players = gs["players"]
    mode    = gs["mode"]

    if mode == "allcards" and not gs["deck"]:
        return True, "牌堆已抽完！"

    if mode == "rounds":
        if gs["round_count"] >= gs["mode_val"] * len(players):
            return True, f"已完成 {gs['mode_val']} 回合！"

    if mode == "score":
        for p in players:
            if p.plate_score() >= gs["mode_val"]:
                return True, f"🎉 {p.name} 率先達到 {gs['mode_val']} 分！"

    if mode != "rounds":
        for p in players:
            if p.is_balanced() and not gs["last_round"]:
                gs["last_round"]   = True
                gs["last_starter"] = gs["turn"]
        if gs["last_round"]:
            nxt = (gs["turn"] + 1) % len(players)
            if nxt == gs["last_starter"]:
                return True, "均衡餐盤達成，最後一輪結束！"

    return False, ""

def advance_turn(gs):
    over, reason = check_end(gs)
    if over:
        gs["over"]      = True
        gs["msg"]       = reason
        gs["msg_type"]  = "success"
        gs["phase"]     = "over"
        return

    players = gs["players"]
    n = len(players)
    gs["round_count"] += 1

    nxt = (gs["turn"] + 1) % n
    if players[nxt].skip_next:
        players[nxt].skip_next = False
        gs["events"].append(f"⏸️ {players[nxt].name} 被暫停，跳過本回合！")
        nxt = (nxt + 1) % n

    gs["turn"]  = nxt
    gs["phase"] = "draw_screen"
    gs["pending_hand_idx"] = None
    gs["last_drawn_card"]  = None

    cur = players[nxt]
    while len(cur.hand) > MAX_HAND:
        c = cur.hand.pop()
        gs["discard"].append(c)

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
        gs["msg"]      = f"🃏 抽到了 {c.emoji} {c.cat}"
        gs["msg_type"] = "info"
    else:
        gs["last_drawn_card"] = None
        gs["msg"]      = "牌堆已空！"
        gs["msg_type"] = "warning"
    gs["phase"] = "action"
    st.session_state.sel = None

def action_place(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand.pop(hand_idx)
    p.plate.append(card)
    gs["msg"]      = f"🍽️ 將 {card.emoji} {card.cat} 放入餐盤（+{card.pts}分）"
    gs["msg_type"] = "success"
    if p.is_balanced():
        gs["events"].append(f"🌟 {p.name} 達成均衡餐盤！額外 +{BALANCED_BONUS} 分！")
    imbal = p.imbalanced_cat()
    if imbal:
        gs["events"].append(f"⚠️ {p.name} 的 {imbal} 超過3張，-10分！")
    st.session_state.sel = None
    advance_turn(gs)

def action_discard(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand.pop(hand_idx)
    gs["discard"].append(card)
    gs["msg"]      = f"🗑️ 棄置 {card.emoji} {card.cat}"
    gs["msg_type"] = "info"
    st.session_state.sel = None
    advance_turn(gs)

def action_use_func(gs, hand_idx):
    p    = gs["players"][gs["turn"]]
    card = p.hand[hand_idx]
    func = card.cat

    if func == "抽牌+2":
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        drawn = []
        for _ in range(2):
            if gs["deck"] and len(p.hand) < MAX_HAND:
                c = gs["deck"].pop()
                p.hand.append(c)
                drawn.append(f"{c.emoji}{c.cat}")
        gs["msg"]      = f"✨ 抽牌+2！抽到：{'、'.join(drawn) if drawn else '（牌堆已空）'}"
        gs["msg_type"] = "success"
        st.session_state.sel = None
        advance_turn(gs)

    elif func == "偷1張":
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        players = gs["players"]
        targets = [(i, pl) for i, pl in enumerate(players)
                   if i != gs["turn"] and pl.hand]
        if targets:
            ti, tp    = random.choice(targets)
            stolen    = random.choice(tp.hand)
            tp.hand.remove(stolen)
            if len(p.hand) < MAX_HAND:
                p.hand.append(stolen)
                gs["msg"] = f"🤫 隨機偷到 {tp.name} 的 {stolen.emoji}{stolen.cat}！"
            else:
                gs["discard"].append(stolen)
                gs["msg"] = f"🤫 偷到 {stolen.emoji}{stolen.cat}，但手牌已滿自動棄置"
            gs["msg_type"] = "warning"
            gs["events"].append(f"😱 {p.name} 偷了 {tp.name} 的牌！")
        else:
            gs["msg"]      = "沒有可偷的對象！"
            gs["msg_type"] = "warning"
        st.session_state.sel = None
        advance_turn(gs)

    elif func == "順時針交換":
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        players = gs["players"]
        saved   = [pl.hand[:] for pl in players]
        n       = len(players)
        for i, pl in enumerate(players):
            pl.hand = saved[(i - 1) % n]
        gs["msg"]      = "🔄 所有玩家手牌順時針交換！"
        gs["msg_type"] = "warning"
        gs["events"].append("🔄 手牌大輪轉！")
        st.session_state.sel = None
        advance_turn(gs)

    elif func == "丟1張":
        gs["phase"]            = "pending_remove"
        gs["pending_hand_idx"] = hand_idx
        gs["msg"]              = "💥 請選擇要從餐盤移除的牌"
        gs["msg_type"]         = "warning"
        st.session_state.sel = None

    elif func == "暫停":
        gs["phase"]            = "pending_pause"
        gs["pending_hand_idx"] = hand_idx
        gs["msg"]              = "⛔ 請選擇要暫停的玩家"
        gs["msg_type"]         = "warning"
        st.session_state.sel = None

def resolve_remove_plate(gs, plate_idx):
    p         = gs["players"][gs["turn"]]
    hi        = gs["pending_hand_idx"]
    func_card = p.hand.pop(hi)
    gs["discard"].append(func_card)
    removed   = p.plate.pop(plate_idx)
    gs["discard"].append(removed)
    gs["msg"]      = f"💥 {removed.emoji}{removed.cat} 從餐盤移除"
    gs["msg_type"] = "info"
    gs["pending_hand_idx"] = None
    st.session_state.sel = None
    advance_turn(gs)

def resolve_pause(gs, target_idx):
    p         = gs["players"][gs["turn"]]
    hi        = gs["pending_hand_idx"]
    func_card = p.hand.pop(hi)
    gs["discard"].append(func_card)
    target             = gs["players"][target_idx]
    target.skip_next   = True
    gs["msg"]          = f"⛔ {target.name} 下回合將被暫停！"
    gs["msg_type"]     = "warning"
    gs["events"].append(f"⛔ {target.name} 下回合被暫停！")
    gs["pending_hand_idx"] = None
    st.session_state.sel = None
    advance_turn(gs)


# ══════════════════════════════════════════════════════════════════
#  CSS（護眼閱讀色調，提升文字對比）
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Fredoka+One&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
    color: #1a1a1a !important;
}
/* 👇 修改了這裡：替換成護眼的淺灰藍漸層背景 */
.stApp {
    background: linear-gradient(135deg, #F5F7FA 0%, #E8ECF1 100%);
    background-attachment: fixed;
}

/* ── 標題 ── */
.main-title {
    font-family: 'Fredoka One', cursive;
    font-size: 2.6rem;
    text-align: center;
    background: linear-gradient(135deg, #E65C5C, #E69A2E, #3BB8B0, #8A82E6); /* 稍微調暗漸層色以適應淺色背景 */
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rainbowSlide 5s linear infinite;
    margin: 0; line-height: 1.2;
}
@keyframes rainbowSlide { to { background-position: 200% center; } }
.sub-title {
    text-align: center; color: #666; font-size: .78rem; /* 加深顏色提升對比 */
    letter-spacing: 2px; margin-top: 2px;
}

/* ── 卡牌 ── */
.card {
    border-radius: 14px;
    padding: 10px 6px 8px;
    text-align: center;
    border: 2.5px solid #ddd;
    cursor: pointer;
    transition: transform .22s cubic-bezier(.34,1.56,.64,1), box-shadow .2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,.06); /* 陰影放輕柔 */
    position: relative; user-select: none; overflow: hidden;
}
.card:hover {
    transform: translateY(-7px) scale(1.05);
    box-shadow: 0 12px 26px rgba(0,0,0,.12);
    z-index: 10;
}
.card-selected {
    transform: translateY(-9px) scale(1.07) !important;
    box-shadow: 0 0 0 3px #FFD700, 0 12px 26px rgba(0,0,0,.15) !important;
    border-color: #FFD700 !important;
}
.card-selected::before {
    content: '✓';
    position: absolute; top: 3px; right: 7px;
    font-size: .8rem; font-weight: 900; color: #e6a000;
}
.card-emoji { font-size: 1.85rem; line-height: 1; margin-bottom: 3px; }
.card-name  { font-size: .7rem; font-weight: 800; color: #1a1a1a !important; margin-bottom: 2px; }
.card-desc  { font-size: .62rem; font-weight: 600; color: #444 !important; }

/* ── 大卡牌（抽牌畫面用） ── */
.big-card {
    border-radius: 20px;
    padding: 22px 14px 18px;
    text-align: center;
    border: 3px solid #ddd;
    box-shadow: 0 6px 24px rgba(0,0,0,.08);
}
.big-card-emoji { font-size: 3.5rem; line-height: 1; margin-bottom: 8px; }
.big-card-name  { font-size: 1.1rem; font-weight: 900; color: #1a1a1a !important; }
.big-card-desc  { font-size: .85rem; font-weight: 700; color: #444 !important; margin-top: 4px; }

/* ── 餐盤 ── */
.plate-area {
    background: rgba(255,255,255,.85); /* 調高背景不透明度，讓餐盤在淺灰背景上更凸顯 */
    border: 2.5px dashed #ccc;
    border-radius: 14px; padding: 8px; min-height: 88px;
    backdrop-filter: blur(4px);
}
.plate-balanced {
    border-color: #43a047 !important;
    background: rgba(67,160,71,.08) !important;
    box-shadow: 0 0 18px rgba(67,160,71,.25) !important;
    animation: balGlow 2s ease infinite;
}
@keyframes balGlow {
    0%,100% { box-shadow: 0 0 10px rgba(67,160,71,.2); }
    50%      { box-shadow: 0 0 24px rgba(67,160,71,.45); }
}

/* ── 玩家面板 ── */
.player-header {
    border-radius: 12px 12px 0 0; padding: 7px 12px;
    font-weight: 800; font-size: .88rem;
    display: flex; align-items: center; gap: 7px;
    color: #1a1a1a !important;
}
.active-glow {
    animation: activeGlow 1.8s ease infinite;
}
@keyframes activeGlow {
    0%,100% { box-shadow: 0 0 0 3px #FFD700; }
    50%      { box-shadow: 0 0 0 4px #FFD700, 0 4px 20px rgba(255,215,0,.35); }
}

/* ── 訊息列 ── */
.msg-box {
    border-radius: 10px; padding: 9px 14px;
    font-weight: 700; font-size: .87rem; text-align: center;
    animation: msgPop .3s cubic-bezier(.34,1.56,.64,1);
    margin: 5px 0; color: #1a1a1a !important;
}
@keyframes msgPop {
    from { opacity: 0; transform: scale(.92) translateY(-5px); }
    to   { opacity: 1; transform: scale(1) translateY(0); }
}

/* ── 事件 ticker ── */
.event-item {
    border-radius: 8px; padding: 5px 12px;
    font-weight: 700; font-size: .8rem; color: #4e342e !important;
    background: #FFF9C4; border-left: 3px solid #FFC107;
    margin-bottom: 4px; animation: slideIn .3s ease;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ── 過場換人 banner ── */
.transition-banner {
    border-radius: 24px; padding: 36px 24px; text-align: center;
    background: linear-gradient(135deg, #ffffff, #fffdf0, #fcf4f7); /* 柔和化過場背景 */
    border: 3px solid #FFD700;
    box-shadow: 0 8px 32px rgba(255,215,0,.2);
    animation: bannerPop .5s cubic-bezier(.34,1.56,.64,1);
}
@keyframes bannerPop {
    from { opacity: 0; transform: scale(.75); }
    to   { opacity: 1; transform: scale(1); }
}
.transition-name {
    font-family: 'Fredoka One', cursive;
    font-size: 3.2rem; color: #1a1a1a !important;
    animation: nameBounce 1.2s ease infinite alternate;
    display: inline-block;
}
@keyframes nameBounce {
    from { transform: translateY(0) scale(1); }
    to   { transform: translateY(-8px) scale(1.03); }
}

/* ── 抽牌大畫面 banner ── */
.draw-banner {
    border-radius: 24px; padding: 32px 24px; text-align: center;
    background: linear-gradient(135deg, #f0f7ff, #faf5fc, #f2fbf4); /* 柔和化背景 */
    border: 3px solid #90CAF9;
    box-shadow: 0 8px 32px rgba(100,181,246,.2);
    animation: bannerPop .45s cubic-bezier(.34,1.56,.64,1);
}
.draw-prompt {
    font-family: 'Fredoka One', cursive;
    font-size: 2rem; color: #1a1a1a !important;
    margin-bottom: 6px;
}
.draw-sub {
    font-size: 1rem; color: #555 !important; font-weight: 700;
    margin-bottom: 18px;
}

/* ── 分數徽章 ── */
.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #FFD700, #FFA000);
    color: #1a1a1a !important; border-radius: 20px;
    padding: 2px 12px; font-weight: 900; font-size: .88rem;
    box-shadow: 0 2px 6px rgba(0,0,0,.1);
}

/* ── 排名列 ── */
.rank-item {
    display: flex; align-items: center; gap: 9px;
    padding: 7px 11px; border-radius: 10px; margin-bottom: 5px;
    font-weight: 700; font-size: .83rem;
    box-shadow: 0 2px 7px rgba(0,0,0,.05);
    color: #1a1a1a !important;
}
.rank-bar-wrap { flex: 1; background: #d5d5d5; border-radius: 4px; height: 7px; overflow: hidden; } /* 稍微加深底色軌道 */
.rank-bar { height: 100%; border-radius: 4px; transition: width .7s ease; }

/* ── Phase 指示 ── */
.phase-pill {
    border-radius: 20px; padding: 4px 14px;
    font-weight: 800; font-size: .8rem;
    display: inline-block; color: #1a1a1a !important;
}

/* ── Streamlit 按鈕 ── */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    color: #1a1a1a !important;
    transition: transform .15s ease, box-shadow .15s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(0,0,0,.1) !important;
}
.element-container { margin-bottom: 3px !important; }
div[data-testid="stVerticalBlock"] { gap: 4px; }
</style>
"""

MSG_COLORS = {
    "info":    ("#dbeafe", "#1e3a5f"),
    "success": ("#dcfce7", "#14532d"),
    "warning": ("#fef9c3", "#713f12"),
    "error":   ("#fee2e2", "#7f1d1d"),
}

def msg_html(text, mtype="info"):
    bg, tc = MSG_COLORS.get(mtype, MSG_COLORS["info"])
    return f'<div class="msg-box" style="background:{bg};color:{tc};">{text}</div>'

def score_html(score):
    return f'<span class="score-badge">⭐ {score} 分</span>'

def render_card(card: Card, selected=False, small=False) -> str:
    sel_cls = "card-selected" if selected else ""
    e_sz = "1.4rem" if small else "1.85rem"
    img = (f'<img src="{card.img}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;margin-bottom:3px;">'
           if card.img and Path(card.img).exists()
           else f'<div class="card-emoji" style="font-size:{e_sz};">{card.emoji}</div>')
    return f"""<div class="card {sel_cls}" style="background:{card.bg};border-color:{card.border};">
        {img}
        <div class="card-name">{card.cat}</div>
        <div class="card-desc">{card.desc}</div>
    </div>"""

def render_big_card(card: Card) -> str:
    img = (f'<img src="{card.img}" style="width:90px;height:90px;object-fit:cover;border-radius:12px;margin-bottom:10px;">'
           if card.img and Path(card.img).exists()
           else f'<div class="big-card-emoji">{card.emoji}</div>')
    return f"""<div class="big-card" style="background:{card.bg};border-color:{card.border};">
        {img}
        <div class="big-card-name">{card.cat}</div>
        <div class="big-card-desc">{card.desc}</div>
    </div>"""


# ══════════════════════════════════════════════════════════════════
#  共用側邊排名（用於 action 頁）
# ══════════════════════════════════════════════════════════════════
def render_ranking(players, ci, gs):
    ranked  = sorted(enumerate(players), key=lambda x: x[1].plate_score(), reverse=True)
    max_sc  = max((p.plate_score() for p in players), default=1) or 1
    medals  = ["🥇","🥈","🥉","4️⃣"]
    for ri, (pi, p) in enumerate(ranked):
        sc  = p.plate_score()
        pct = max(5, int(sc / max_sc * 100)) if sc > 0 else 5
        is_cur = pi == ci
        bg   = f"background:{p.color['light']};border:2px solid {p.color['header']};"
        cur_mark  = "▶ " if is_cur else ""
        bal_mark  = " ✅" if p.is_balanced() else ""
        skip_mark = " ⏸️" if p.skip_next else ""
        st.markdown(f"""<div class="rank-item" style="{bg}">
            <span>{medals[ri]}</span>
            <span style="flex:1;">{cur_mark}{p.name}{bal_mark}{skip_mark}</span>
            <div class="rank-bar-wrap">
              <div class="rank-bar" style="width:{pct}%;background:{p.color['header']};"></div>
            </div>
            {score_html(sc)}
        </div>""", unsafe_allow_html=True)

    if gs["mode"] == "score":
        st.markdown(f'<div style="font-size:.73rem;text-align:center;color:#666;margin-top:4px;">🏁 目標：{gs["mode_val"]} 分</div>', unsafe_allow_html=True)
    elif gs["mode"] == "rounds":
        done  = gs["round_count"]
        total = gs["mode_val"] * len(players)
        pct   = int(done / total * 100) if total else 0
        st.markdown(f'<div style="font-size:.73rem;text-align:center;color:#666;margin-top:4px;">🔁 回合進度 {done}/{total}</div>', unsafe_allow_html=True)
        st.progress(min(pct, 100))


# ══════════════════════════════════════════════════════════════════
#  設定頁
# ══════════════════════════════════════════════════════════════════
def page_setup():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="main-title">🥗 最強糾察員</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">NUTRITION BATTLE CARD GAME</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown("### 👥 玩家設定")
        num = st.slider("玩家人數", 2, 4, 2, key="setup_num")
        names = []
        defaults = ["玩家一 🔴", "玩家二 🟦", "玩家三 🟡", "玩家四 🟣"]
        for i in range(num):
            n = st.text_input(f"玩家 {i+1} 名稱", value=defaults[i], key=f"pname_{i}")
            names.append(n.strip() or f"玩家{i+1}")

        st.markdown("---")
        st.markdown("### 🎮 遊戲模式")
        mode_pick = st.radio("", ["🔁 回合模式", "🃏 全牌模式", "🏁 分數模式"],
                             horizontal=True, key="mode_radio", label_visibility="collapsed")

        mode_val = 0
        if "回合模式" in mode_pick:
            st.markdown('<div style="background:#dbeafe;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#1e3a5f;font-weight:700;">每位玩家進行設定回合數，結束後分數最高者獲勝</div>', unsafe_allow_html=True)
            mode_val  = st.slider("每人回合數", 3, 15, 5, key="rv")
            mode_key  = "rounds"
        elif "全牌模式" in mode_pick:
            st.markdown('<div style="background:#dcfce7;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#14532d;font-weight:700;">牌堆抽完後結算，分數最高者獲勝（經典模式）</div>', unsafe_allow_html=True)
            mode_key  = "allcards"
        else:
            st.markdown('<div style="background:#fef9c3;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#713f12;font-weight:700;">率先達到目標分數的玩家立即獲勝</div>', unsafe_allow_html=True)
            mode_val  = st.slider("目標分數", 10, 80, 30, key="sv")
            mode_key  = "score"

    with col_r:
        st.markdown("### 🍱 食物牌（每種 ×6 張）")
        for cat, info in FOOD_CATS.items():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #ddd;font-size:.82rem;color:#1a1a1a;"><span>{info["emoji"]} {cat}</span><span style="font-weight:800;">+{info["pts"]} 分</span></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.8rem;padding:6px 0;color:#1a1a1a;font-weight:700;">🌟 均衡加成（蔬/果＋蛋白＋澱粉 各至少1張）<b>+5</b></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.8rem;color:#c62828;font-weight:700;">❌ 同類超過3張 <b>−10 分</b></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⚡ 功能牌（每種 ×5 張）")
        for func, info in FUNC_CARDS.items():
            st.markdown(f'<div style="font-size:.8rem;padding:3px 0;color:#1a1a1a;">{info["emoji"]} <b>{func}</b>：{info["desc"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎮 開始遊戲！", use_container_width=True, type="primary"):
            if len(set(names)) < len(names):
                st.error("玩家名稱不能重複！"); return
            gs = init_game(names, mode_key, mode_val)
            st.session_state.gs   = gs
            st.session_state.sel  = None
            st.session_state.page = "game"
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  換人過場頁
# ══════════════════════════════════════════════════════════════════
def page_transition():
    st.markdown(CSS, unsafe_allow_html=True)
    gs      = st.session_state.gs
    players = gs["players"]
    nxt     = gs["transition_to"]
    p       = players[nxt]
    pc      = p.color

    prev_idx = (nxt - 1) % len(players)
    prev     = players[prev_idx]

    st.session_state.sel = None

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if gs["round_count"] > 0:
            st.markdown(f'<div style="text-align:center;color:#666;font-size:.92rem;font-weight:700;margin-bottom:12px;">✅ {prev.name} 的回合結束</div>', unsafe_allow_html=True)

        for ev in gs["events"]:
            st.markdown(f'<div class="event-item">📢 {ev}</div>', unsafe_allow_html=True)
        gs["events"].clear()

        st.markdown(f"""<div class="transition-banner">
            <div style="font-size:1.1rem;color:#555;font-weight:800;margin-bottom:10px;">
                👇 請將裝置交給
            </div>
            <div class="transition-name" style="color:{pc['text']};">{p.name}</div>
            <div style="font-size:1.05rem;color:#555;font-weight:700;margin:10px 0 6px;">
                準備開始你的回合！
            </div>
            <div style="font-size:1.8rem;">🎮</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"✅ 我是 {p.name}，準備好了！開始！", use_container_width=True, type="primary"):
            gs["showing_transition"] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  抽牌大畫面
# ══════════════════════════════════════════════════════════════════
def page_draw():
    st.markdown(CSS, unsafe_allow_html=True)
    gs      = st.session_state.gs
    players = gs["players"]
    ci      = gs["turn"]
    cur     = players[ci]
    pc      = cur.color

    st.markdown('<div class="main-title" style="font-size:1.5rem;">🥗 最強糾察員</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        mode_lbl = {"rounds":"回合模式","allcards":"全牌模式","score":"分數模式"}[gs["mode"]]
        st.markdown(f'<div style="text-align:center;font-size:.8rem;color:#666;margin-bottom:10px;">🃏 牌堆剩 {len(gs["deck"])} 張 ｜ {mode_lbl}</div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="draw-banner">
            <div class="draw-prompt">🎴 {cur.name} 的回合</div>
            <div class="draw-sub">牌堆剩餘 <b>{len(gs["deck"])}</b> 張，請點按抽牌</div>
            <div style="font-size:4rem;margin:10px 0;animation:nameBounce 1.2s ease infinite alternate;display:inline-block;">🃏</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if gs["deck"]:
            if st.button("🃏  抽  一  張  牌", use_container_width=True, type="primary"):
                action_draw(gs)
                st.rerun()
        else:
            st.markdown(msg_html("牌堆已空！直接進入行動階段", "warning"), unsafe_allow_html=True)
            if st.button("⚡ 直接行動", use_container_width=True, type="primary"):
                gs["phase"] = "action"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f'<div style="font-size:.82rem;font-weight:800;color:#555;margin-bottom:6px;">📋 目前手牌（{len(cur.hand)} 張）</div>', unsafe_allow_html=True)
        if cur.hand:
            hc = st.columns(min(len(cur.hand), 6))
            for i, card in enumerate(cur.hand):
                with hc[i]:
                    st.markdown(render_card(card, small=True), unsafe_allow_html=True)

    with c3:
        st.markdown("**📊 目前排名**")
        render_ranking(players, ci, gs)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩️ 返回設定頁", key="back_draw"):
        st.session_state.page = "setup"
        if "gs" in st.session_state: del st.session_state.gs
        st.rerun()


# ══════════════════════════════════════════════════════════════════
#  行動主頁（抽完牌後）
# ══════════════════════════════════════════════════════════════════
def page_action():
    st.markdown(CSS, unsafe_allow_html=True)
    gs      = st.session_state.gs
    players = gs["players"]
    ci      = gs["turn"]
    cur     = players[ci]
    pc      = cur.color
    phase   = gs["phase"]

    sel = st.session_state.get("sel", None)
    if sel is not None and (not cur.hand or sel >= len(cur.hand)):
        st.session_state.sel = None
        sel = None

    h1, h2, h3 = st.columns([3, 1, 1])
    with h1:
        st.markdown(f'<div class="main-title" style="font-size:1.4rem;text-align:left;">🥗 最強糾察員</div>', unsafe_allow_html=True)
        phase_map = {
            "action":         ("⚡ 行動階段 — 選擇一張牌",   "#fef9c3", "#713f12"),
            "pending_remove": ("💥 丟1張 — 選擇餐盤中要移除的牌", "#fee2e2", "#7f1d1d"),
            "pending_pause":  ("⛔ 暫停 — 選擇要暫停的玩家",      "#ede7f6", "#4527a0"),
        }
        lbl, pbg, ptc = phase_map.get(phase, ("⚡ 行動階段", "#fef9c3","#713f12"))
        st.markdown(f'<span class="phase-pill" style="background:{pbg};color:{ptc};">{lbl}</span>', unsafe_allow_html=True)
    with h2:
        st.markdown(f'<div style="background:#e3f2fd;border-radius:10px;padding:7px;text-align:center;font-size:.7rem;color:#1e3a5f;font-weight:800;">牌堆<br><span style="font-size:1.4rem;">{len(gs["deck"])}</span></div>', unsafe_allow_html=True)
    with h3:
        top = gs["discard"][-1] if gs["discard"] else None
        lbl2 = f"{top.emoji}" if top else "—"
        st.markdown(f'<div style="background:#fce4ec;border-radius:10px;padding:7px;text-align:center;font-size:.7rem;color:#7d2020;font-weight:800;">棄牌頂<br><span style="font-size:1.4rem;">{lbl2}</span></div>', unsafe_allow_html=True)

    if gs["msg"]:
        st.markdown(msg_html(gs["msg"], gs["msg_type"]), unsafe_allow_html=True)

    st.markdown("---")

    left, right = st.columns([1, 2.8])

    with left:
        st.markdown("**📊 即時排名**")
        render_ranking(players, ci, gs)

        st.markdown("<br>", unsafe_allow_html=True)
        if gs["last_round"]:
            st.markdown('<div class="event-item" style="border-color:#FF5722;background:#fff3e0;text-align:center;">⚡ 最後一輪！</div>', unsafe_allow_html=True)

    with right:
        st.markdown("**🍽️ 各玩家餐盤**")
        pcols = st.columns(len(players))
        for pi, p in enumerate(players):
            with pcols[pi]:
                is_cur  = pi == ci
                h_bg    = p.color["header"] if is_cur else p.color["light"]
                h_style = f"background:{h_bg};border:2px solid {p.color['header']};{'border-bottom:none;' if is_cur else ''}"
                glow    = "active-glow" if is_cur else ""
                bal     = "plate-balanced" if p.is_balanced() else ""
                skip_ic = " ⏸️" if p.skip_next else ""
                act_ic  = " ▶" if is_cur else ""
                st.markdown(f'<div class="player-header {glow}" style="{h_style}">{act_ic} {p.name}{skip_ic}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plate-area {bal}">', unsafe_allow_html=True)
                if p.plate:
                    cc = st.columns(min(len(p.plate), 5))
                    for j, c in enumerate(p.plate):
                        with cc[j]:
                            st.markdown(render_card(c, small=True), unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:center;color:#bbb;padding:16px 0;font-size:.78rem;'>空餐盤</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if p.is_balanced():
                    st.markdown(f'<div style="text-align:center;font-size:.7rem;font-weight:800;color:#2e7d32;margin-top:3px;">✅ 均衡 +{BALANCED_BONUS}</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.markdown(f'<div style="font-size:.95rem;font-weight:800;color:{pc["text"]};">🎴 {cur.name} 的手牌（{len(cur.hand)} 張）</div>', unsafe_allow_html=True)

        if cur.hand:
            n_cols = min(len(cur.hand), 6)
            hcols  = st.columns(n_cols)
            last_drawn = gs.get("last_drawn_card")
            for i, card in enumerate(cur.hand):
                with hcols[i % n_cols]:
                    is_sel = (sel == i)
                    is_new = (last_drawn is not None and i == last_drawn)
                    if is_new:
                        st.markdown('<div style="text-align:center;font-size:.65rem;color:#1565c0;font-weight:800;margin-bottom:2px;">剛抽到 ↓</div>', unsafe_allow_html=True)
                    st.markdown(render_card(card, selected=is_sel), unsafe_allow_html=True)
                    if phase == "action":
                        btn_lbl = "✓ 已選" if is_sel else "選擇"
                        if st.button(btn_lbl, key=f"hsel_{i}", use_container_width=True):
                            st.session_state.sel = i if not is_sel else None
                            st.rerun()
        else:
            st.info("手牌為空")

        sel = st.session_state.get("sel", None)
        sel_card = cur.hand[sel] if (sel is not None and sel < len(cur.hand)) else None
        if sel_card and phase == "action":
            st.markdown(f'<div style="background:{sel_card.bg};border:2px solid {sel_card.border};border-radius:10px;padding:8px 14px;font-weight:700;color:#1a1a1a;text-align:center;margin:5px 0;">{sel_card.emoji} <b>{sel_card.cat}</b> — {sel_card.desc}</div>', unsafe_allow_html=True)

    st.markdown("---")

    if phase == "pending_remove":
        st.markdown(msg_html("👇 點選要從餐盤中移除的牌", "error"), unsafe_allow_html=True)
        if cur.plate:
            rc = st.columns(min(len(cur.plate), 5))
            for j, c in enumerate(cur.plate):
                with rc[j]:
                    st.markdown(render_card(c), unsafe_allow_html=True)
                    if st.button(f"💥 移除", key=f"rem_{j}", use_container_width=True):
                        resolve_remove_plate(gs, j); st.rerun()
        else:
            st.info("餐盤為空，無法使用此功能")
            if st.button("取消"):
                gs["phase"] = "action"; gs["pending_hand_idx"] = None; st.rerun()

    elif phase == "pending_pause":
        st.markdown(msg_html("👇 選擇要讓哪位玩家下回合暫停", "warning"), unsafe_allow_html=True)
        targets = [(i, p) for i, p in enumerate(players) if i != ci]
        tc = st.columns(len(targets))
        for idx, (ti, tp) in enumerate(targets):
            with tc[idx]:
                st.markdown(f'<div style="background:{tp.color["light"]};border:2px solid {tp.color["header"]};border-radius:12px;padding:10px;text-align:center;font-weight:700;color:#1a1a1a;">{tp.name}{"（已暫停）" if tp.skip_next else ""}<br><small style="color:#555;">{tp.plate_score()} 分</small></div>', unsafe_allow_html=True)
                if st.button(f"⛔ 暫停 {tp.name}", key=f"pause_{ti}", use_container_width=True, type="primary"):
                    resolve_pause(gs, ti); st.rerun()

    elif phase == "action":
        if not sel_card:
            st.markdown(msg_html("👆 請先點選一張手牌，再選擇下方行動", "info"), unsafe_allow_html=True)
        else:
            can_place   = sel_card.kind == "food" and len(cur.plate) < MAX_PLATE
            can_func    = sel_card.kind == "func"

            place_tip   = ""
            if not can_place:
                place_tip = "（餐盤已滿）" if len(cur.plate) >= MAX_PLATE else "（功能牌不能放入餐盤）"

            ac = st.columns(3)
            with ac[0]:
                if st.button(f"🍽️ 放入餐盤{place_tip}", disabled=not can_place,
                             use_container_width=True, type="primary"):
                    action_place(gs, sel); st.rerun()
            with ac[1]:
                if st.button("✨ 使用功能牌" if can_func else "（請選功能牌）",
                             disabled=not can_func, use_container_width=True):
                    action_use_func(gs, sel); st.rerun()
            with ac[2]:
                if st.button("🗑️ 棄牌（丟棄不用）", use_container_width=True):
                    action_discard(gs, sel); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩️ 返回設定頁", key="back_action"):
        st.session_state.page = "setup"
        if "gs" in st.session_state: del st.session_state.gs
        st.rerun()


# ══════════════════════════════════════════════════════════════════
#  結果頁
# ══════════════════════════════════════════════════════════════════
def page_result():
    st.markdown(CSS, unsafe_allow_html=True)
    gs      = st.session_state.gs
    players = gs["players"]
    for p in players: p.score = p.plate_score()
    ranked  = sorted(players, key=lambda p: p.score, reverse=True)
    winner  = ranked[0]
    medals  = ["🥇","🥈","🥉","4️⃣"]

    st.markdown('<div class="main-title">🏆 遊戲結束！</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:1.35rem;font-weight:900;color:{winner.color["text"]};margin:8px 0;">🎉 {winner.name} 獲勝！{score_html(winner.score)}</div>', unsafe_allow_html=True)
    st.markdown("---")

    for ri, p in enumerate(ranked):
        cats  = {}
        for c in p.plate: cats[c.cat] = cats.get(c.cat, 0) + 1
        raw   = sum(c.pts for c in p.plate)
        bal_b = BALANCED_BONUS if p.is_balanced() else 0
        imbal = sum(IMBALANCE_PENALTY for cat, cnt in cats.items() if cnt > 3)
        plate_em = " ".join(c.emoji for c in p.plate) or "空"

        with st.expander(f"{medals[ri]} {p.name}  ── {p.score} 分", expanded=(ri == 0)):
            dc1, dc2 = st.columns([2, 1])
            with dc1:
                st.write(f"**餐盤：** {plate_em}")
                for cat, cnt in cats.items():
                    pts_per = FOOD_CATS.get(cat, {}).get("pts", 0)
                    over    = "  ❌ 超量 −10" if cnt > 3 else ""
                    em      = FOOD_CATS.get(cat, {}).get("emoji", "")
                    st.markdown(f'<div style="font-size:.82rem;padding:2px 0;color:#1a1a1a;">{em} {cat} × {cnt} 張 = {pts_per*cnt} 分{over}</div>', unsafe_allow_html=True)
                if bal_b: st.success(f"✅ 均衡加成 +{bal_b}")
                if imbal: st.error(f"❌ 失衡懲罰 {imbal}")
            with dc2:
                st.markdown(f"""<div style="background:{p.color['light']};border:2px solid {p.color['header']};border-radius:14px;padding:14px;text-align:center;">
                    <div style="font-size:.7rem;color:#666;">食物基礎</div>
                    <div style="font-size:1.6rem;font-weight:900;color:{p.color['text']};">{raw}</div>
                    <div style="font-size:.75rem;color:#777;">{f'+{bal_b} 均衡' if bal_b else ''}{'  '+str(imbal)+' 失衡' if imbal else ''}</div>
                    <div style="font-size:1.3rem;font-weight:900;color:{p.color['text']};border-top:1px solid #ddd;margin-top:6px;padding-top:6px;">= {p.score} 分</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 再玩一局", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            if "gs" in st.session_state: del st.session_state.gs
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  入口點
# ══════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="最強糾察員",
        page_icon="🥗",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    if "page" not in st.session_state: st.session_state.page = "setup"
    if "sel"  not in st.session_state: st.session_state.sel  = None

    gs = st.session_state.get("gs")

    if st.session_state.page == "setup":
        page_setup()
        return

    if not gs:
        st.session_state.page = "setup"
        st.rerun()
        return

    if gs.get("over") or gs.get("phase") == "over":
        page_result()
        return

    if gs.get("showing_transition"):
        page_transition()
        return

    phase = gs.get("phase", "draw_screen")
    if phase == "draw_screen":
        page_draw()
    else:
        page_action()

if __name__ == "__main__":
    main()
