"""
最強糾察員 v3 ── 可愛明亮版
熱座模式 | 三種遊戲模式 | 嚴格回合流程
"""
import streamlit as st
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
#  常數
# ══════════════════════════════════════════════════════════════════

# 擴充食物類別（原5類 → 9類）
FOOD_CATS = {
    "蔬菜":     {"pts": 5, "emoji": "🥦", "color": "#2e7d32", "bg": "#e8f5e9", "border": "#66bb6a"},
    "水果":     {"pts": 5, "emoji": "🍎", "color": "#c62828", "bg": "#fce4ec", "border": "#ef9a9a"},
    "雞肉":     {"pts": 4, "emoji": "🍗", "color": "#e65100", "bg": "#fff3e0", "border": "#ffb74d"},
    "海鮮":     {"pts": 4, "emoji": "🐟", "color": "#0277bd", "bg": "#e1f5fe", "border": "#4fc3f7"},
    "蛋豆類":   {"pts": 3, "emoji": "🥚", "color": "#f9a825", "bg": "#fffde7", "border": "#fff176"},
    "米飯麵食": {"pts": 3, "emoji": "🍚", "color": "#6d4c41", "bg": "#efebe9", "border": "#a1887f"},
    "乳品":     {"pts": 2, "emoji": "🥛", "color": "#1565c0", "bg": "#e3f2fd", "border": "#90caf9"},
    "堅果":     {"pts": 2, "emoji": "🥜", "color": "#558b2f", "bg": "#f1f8e9", "border": "#aed581"},
    "油炸點心": {"pts": 1, "emoji": "🍟", "color": "#757575", "bg": "#f5f5f5", "border": "#bdbdbd"},
}

# 均衡餐盤條件（需含以下3大類中的代表）
BALANCED_REQUIRED = {"蔬菜", "水果", "雞肉", "海鮮"}   # 任兩類
BALANCED_FULL = {"蔬菜", "水果", "雞肉", "海鮮", "蛋豆類", "米飯麵食"}  # 六大類齊全

FUNC_CARDS = {
    "抽牌+2":      {"emoji": "✨", "color": "#7b1fa2", "bg": "#f3e5f5", "border": "#ce93d8",
                   "desc": "立即多抽 2 張牌"},
    "偷1張":       {"emoji": "🤫", "color": "#c62828", "bg": "#fce4ec", "border": "#ef9a9a",
                   "desc": "隨機偷另一位玩家 1 張手牌"},
    "丟1張":       {"emoji": "💥", "color": "#ef6c00", "bg": "#fff3e0", "border": "#ffb74d",
                   "desc": "將餐盤中 1 張移至棄牌區"},
    "順時針交換":  {"emoji": "🔄", "color": "#00695c", "bg": "#e0f2f1", "border": "#80cbc4",
                   "desc": "所有玩家手牌順時針傳遞"},
    "暫停":        {"emoji": "⛔", "color": "#4527a0", "bg": "#ede7f6", "border": "#b39ddb",
                   "desc": "指定一位玩家跳過下回合"},
}

INIT_HAND    = 5      # 初始手牌
MAX_HAND     = 6      # 手牌上限
MAX_PLATE    = 5      # 餐盤上限
FOOD_PER_CAT = 6      # 每種食物牌數
FUNC_PER_TYPE= 5      # 每種功能牌數（增加）

BALANCED_BONUS    =  5
IMBALANCE_PENALTY = -10

# 每個玩家的顯示顏色
P_COLORS = [
    {"header": "#FF6B6B", "light": "#fff0f0", "text": "#c62828"},
    {"header": "#4ECDC4", "light": "#e0f7fa", "text": "#006064"},
    {"header": "#FFE66D", "light": "#fffde7", "text": "#f57f17"},
    {"header": "#A29BFE", "light": "#ede7f6", "text": "#4527a0"},
]

# ══════════════════════════════════════════════════════════════════
#  資料模型
# ══════════════════════════════════════════════════════════════════
@dataclass
class Card:
    kind: str          # "food" | "func"
    cat:  str
    cid:  int
    img:  Optional[str] = None

    @property
    def emoji(self):
        return FOOD_CATS[self.cat]["emoji"] if self.kind == "food" else FUNC_CARDS[self.cat]["emoji"]
    @property
    def color(self):
        return FOOD_CATS[self.cat]["color"] if self.kind == "food" else FUNC_CARDS[self.cat]["color"]
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
        return f"+{self.pts} 分" if self.kind == "food" else FUNC_CARDS[self.cat]["desc"]


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
        # 簡易均衡加成：包含蔬菜/水果 + 蛋白質類 + 澱粉類 各至少1張
        has_veg    = bool(cat_set & {"蔬菜","水果"})
        has_protein= bool(cat_set & {"雞肉","海鮮","蛋豆類"})
        has_carb   = bool(cat_set & {"米飯麵食"})
        if has_veg and has_protein and has_carb:
            total += BALANCED_BONUS
        # 失衡懲罰：同類超過3張
        for cat in FOOD_CATS:
            if cats.count(cat) > 3:
                total += IMBALANCE_PENALTY
        return total

    def is_balanced(self):
        cats = {c.cat for c in self.plate}
        has_veg     = bool(cats & {"蔬菜","水果"})
        has_protein = bool(cats & {"雞肉","海鮮","蛋豆類"})
        has_carb    = bool(cats & {"米飯麵食"})
        return has_veg and has_protein and has_carb

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
        phase="draw",          # draw → action → (draw → …)
        over=False,
        mode=mode,             # "rounds" | "allcards" | "score"
        mode_val=mode_val,
        last_round=False,
        last_starter=None,
        msg="", msg_type="info",
        events=[],
        round_count=0,         # 完成回合數（每位玩家出完算一輪）
        pending=None,          # 待選目標的功能牌
        showing_transition=False,
        transition_to=None,
    )

def check_end(gs) -> tuple:
    """回傳 (is_over, reason_str)"""
    players = gs["players"]
    mode = gs["mode"]

    if mode == "allcards" and not gs["deck"]:
        return True, "牌堆已抽完！"

    if mode == "rounds":
        if gs["round_count"] >= gs["mode_val"] * len(players):
            return True, f"已完成 {gs['mode_val']} 回合！"

    if mode == "score":
        for p in players:
            if p.plate_score() >= gs["mode_val"]:
                return True, f"🎉 {p.name} 率先達到 {gs['mode_val']} 分！"

    # 均衡觸發最後一輪
    for p in players:
        if p.is_balanced() and not gs["last_round"]:
            gs["last_round"]    = True
            gs["last_starter"]  = gs["turn"]
    if gs["last_round"]:
        nxt = (gs["turn"] + 1) % len(players)
        if nxt == gs["last_starter"]:
            return True, "均衡餐盤達成，最後一輪結束！"
    return False, ""

def advance_turn(gs):
    """結束當前回合，推進到下一位玩家"""
    over, reason = check_end(gs)
    if over:
        gs["over"] = True
        gs["msg"]  = reason
        gs["msg_type"] = "success"
        return

    players = gs["players"]
    n = len(players)
    gs["round_count"] += 1

    # 找下一位未暫停玩家
    nxt = (gs["turn"] + 1) % n
    if players[nxt].skip_next:
        players[nxt].skip_next = False
        gs["events"].append(f"⏸️ {players[nxt].name} 被暫停，跳過本回合！")
        nxt = (nxt + 1) % n

    gs["turn"] = nxt
    gs["phase"] = "draw"
    gs["pending"] = None

    # 手牌超限丟棄
    cur = players[nxt]
    while len(cur.hand) > MAX_HAND:
        c = cur.hand.pop(); gs["discard"].append(c)

    # 觸發換人提示
    gs["showing_transition"] = True
    gs["transition_to"] = nxt
    gs["msg"] = ""
    gs["msg_type"] = "info"


# ── 行動函式 ──────────────────────────────────────────────────────

def action_draw(gs):
    p = gs["players"][gs["turn"]]
    if gs["deck"]:
        c = gs["deck"].pop(); p.hand.append(c)
        gs["msg"] = f"🃏 抽到了 {c.emoji} {c.cat}"
        gs["msg_type"] = "info"
    else:
        gs["msg"] = "牌堆已空！"; gs["msg_type"] = "warning"
    gs["phase"] = "action"

def action_place(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand.pop(hand_idx)
    p.plate.append(card)
    gs["msg"] = f"🍽️ 將 {card.emoji} {card.cat} 放入餐盤（+{card.pts}分）"
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
    gs["msg"] = f"🗑️ 棄置 {card.emoji} {card.cat}"
    gs["msg_type"] = "info"
    st.session_state.sel = None
    advance_turn(gs)

def action_use_func(gs, hand_idx):
    p = gs["players"][gs["turn"]]
    card = p.hand[hand_idx]
    func = card.cat

    if func == "抽牌+2":
        p.hand.pop(hand_idx)
        gs["discard"].append(card)
        drawn = []
        for _ in range(2):
            if gs["deck"] and len(p.hand) < MAX_HAND:
                c = gs["deck"].pop(); p.hand.append(c); drawn.append(f"{c.emoji}{c.cat}")
        gs["msg"] = f"✨ 抽牌+2！抽到：{'、'.join(drawn) if drawn else '（牌堆已空）'}"
        gs["msg_type"] = "success"
        st.session_state.sel = None
        advance_turn(gs)

    elif func == "偷1張":
        # 隨機偷：從所有其他有手牌的玩家中隨機選一人，再隨機偷一張
        players = gs["players"]
        targets = [(i, pl) for i, pl in enumerate(players) if i != gs["turn"] and pl.hand]
        if not targets:
            gs["msg"] = "沒有可偷的對象！"; gs["msg_type"] = "warning"
            p.hand.pop(hand_idx); gs["discard"].append(card)
            st.session_state.sel = None
            advance_turn(gs)
        else:
            ti, tp = random.choice(targets)
            stolen = random.choice(tp.hand)
            tp.hand.remove(stolen); p.hand.append(stolen)
            p.hand.pop(hand_idx if hand_idx < len(p.hand) else len(p.hand)-1)
            # 實際上已用掉功能牌並加入偷來的牌，重新整理
            # 修正：先移除功能牌再加偷來的牌
            gs["discard"].append(card)
            gs["msg"] = f"🤫 隨機偷到 {tp.name} 的 {stolen.emoji}{stolen.cat}！"
            gs["msg_type"] = "warning"
            gs["events"].append(f"😱 {p.name} 偷了 {tp.name} 的牌！")
            st.session_state.sel = None
            advance_turn(gs)

    elif func == "順時針交換":
        p.hand.pop(hand_idx); gs["discard"].append(card)
        players = gs["players"]
        saved = [pl.hand[:] for pl in players]
        n = len(players)
        for i, pl in enumerate(players): pl.hand = saved[(i - 1) % n]
        gs["msg"] = "🔄 所有玩家手牌順時針交換！"
        gs["msg_type"] = "warning"
        gs["events"].append("🔄 手牌大輪轉！")
        st.session_state.sel = None
        advance_turn(gs)

    elif func in ("丟1張", "暫停"):
        # 這兩個需要二次選擇，進入 pending 狀態
        gs["pending"] = {"func": func, "hand_idx": hand_idx}
        if func == "丟1張":
            gs["msg"] = "💥 選擇要從餐盤移除的牌"
        else:
            gs["msg"] = "⛔ 選擇要暫停的玩家"
        gs["msg_type"] = "warning"

def resolve_remove_plate(gs, plate_idx):
    p = gs["players"][gs["turn"]]
    pending = gs["pending"]
    # 移除功能牌
    func_card = p.hand[pending["hand_idx"]]
    p.hand.pop(pending["hand_idx"])
    gs["discard"].append(func_card)
    # 移除餐盤牌
    removed = p.plate.pop(plate_idx)
    gs["discard"].append(removed)
    gs["msg"] = f"💥 {removed.emoji}{removed.cat} 從餐盤移除"
    gs["msg_type"] = "info"
    gs["pending"] = None
    st.session_state.sel = None
    advance_turn(gs)

def resolve_pause(gs, target_idx):
    p = gs["players"][gs["turn"]]
    pending = gs["pending"]
    func_card = p.hand[pending["hand_idx"]]
    p.hand.pop(pending["hand_idx"])
    gs["discard"].append(func_card)
    target = gs["players"][target_idx]
    target.skip_next = True
    gs["msg"] = f"⛔ {target.name} 下回合將被暫停！"
    gs["msg_type"] = "warning"
    gs["events"].append(f"⛔ {target.name} 下回合被暫停！")
    gs["pending"] = None
    st.session_state.sel = None
    advance_turn(gs)


# ══════════════════════════════════════════════════════════════════
#  CSS（明亮可愛風）
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Fredoka+One&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}
.stApp {
    background: linear-gradient(145deg, #fdfbff 0%, #fff0fb 35%, #f0fbff 70%, #fffdf0 100%);
    background-attachment: fixed;
}

/* ── 標題 ── */
.main-title {
    font-family: 'Fredoka One', cursive;
    font-size: 2.6rem;
    text-align: center;
    background: linear-gradient(135deg, #FF6B6B 0%, #FFB347 30%, #FFE66D 55%, #4ECDC4 80%, #A29BFE 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rainbowSlide 5s linear infinite;
    margin: 0; padding: 0; line-height: 1.2;
}
@keyframes rainbowSlide { to { background-position: 200% center; } }
.sub-title {
    text-align: center; color: #aaa; font-size: .8rem; letter-spacing: 2px; margin-top: 2px;
}

/* ── 卡牌 ── */
.card {
    border-radius: 16px;
    padding: 10px 6px 8px;
    text-align: center;
    border: 2.5px solid transparent;
    cursor: pointer;
    transition: transform .22s cubic-bezier(.34,1.56,.64,1), box-shadow .2s ease;
    box-shadow: 0 3px 10px rgba(0,0,0,.1);
    position: relative; user-select: none; overflow: hidden;
}
.card::after {
    content: ''; position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,.35), transparent);
    transition: left .4s ease;
}
.card:hover::after { left: 120%; }
.card:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow: 0 14px 28px rgba(0,0,0,.18);
    z-index: 10;
}
.card-selected {
    transform: translateY(-10px) scale(1.07) !important;
    box-shadow: 0 0 0 3px #FFD700, 0 14px 28px rgba(0,0,0,.2) !important;
    border-color: #FFD700 !important;
}
.card-selected::before {
    content: '✓';
    position: absolute; top: 4px; right: 8px;
    font-size: .85rem; font-weight: 900; color: #FFD700;
    text-shadow: 0 1px 3px rgba(0,0,0,.3);
}
.card-emoji { font-size: 1.9rem; line-height: 1; margin-bottom: 3px; }
.card-name  { font-size: .7rem; font-weight: 800; margin-bottom: 2px; }
.card-desc  { font-size: .62rem; font-weight: 600; opacity: .75; }

/* ── 餐盤 ── */
.plate-area {
    background: rgba(255,255,255,.65);
    border: 2.5px dashed #e0e0e0;
    border-radius: 16px; padding: 8px; min-height: 90px;
    backdrop-filter: blur(4px);
    transition: all .4s ease;
}
.plate-balanced {
    border-color: #4CAF50 !important;
    background: rgba(76,175,80,.06) !important;
    box-shadow: 0 0 20px rgba(76,175,80,.3) !important;
    animation: balGlow 2s ease infinite;
}
@keyframes balGlow {
    0%,100% { box-shadow: 0 0 12px rgba(76,175,80,.3); }
    50%      { box-shadow: 0 0 28px rgba(76,175,80,.6); }
}

/* ── 玩家面板 ── */
.player-header {
    border-radius: 12px 12px 0 0; padding: 8px 14px;
    font-weight: 800; font-size: .95rem;
    display: flex; align-items: center; gap: 8px;
}
.active-glow {
    box-shadow: 0 0 0 3px #FFD700, 0 4px 16px rgba(0,0,0,.12) !important;
    animation: activeGlow 1.8s ease infinite;
}
@keyframes activeGlow {
    0%,100% { box-shadow: 0 0 0 3px #FFD700, 0 4px 16px rgba(0,0,0,.1); }
    50%      { box-shadow: 0 0 0 4px #FFD700, 0 4px 24px rgba(255,215,0,.35); }
}

/* ── 訊息列 ── */
.msg-box {
    border-radius: 12px; padding: 10px 16px;
    font-weight: 700; font-size: .88rem; text-align: center;
    animation: msgPop .35s cubic-bezier(.34,1.56,.64,1);
    margin: 6px 0;
}
@keyframes msgPop {
    from { opacity: 0; transform: scale(.9) translateY(-6px); }
    to   { opacity: 1; transform: scale(1) translateY(0); }
}

/* ── 事件 ticker ── */
.event-item {
    border-radius: 8px; padding: 5px 12px; font-weight: 700; font-size: .8rem;
    background: linear-gradient(90deg, #FFF9C4, #FFFDE7);
    border-left: 3px solid #FFC107; margin-bottom: 4px;
    animation: slideIn .3s ease;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ── 換人動畫 ── */
.transition-banner {
    border-radius: 20px; padding: 28px 20px; text-align: center;
    background: linear-gradient(135deg, #fff9c4, #fff3e0, #fce4ec);
    border: 3px solid #FFD700;
    box-shadow: 0 8px 32px rgba(255,215,0,.35);
    animation: bannerPop .5s cubic-bezier(.34,1.56,.64,1);
}
@keyframes bannerPop {
    from { opacity: 0; transform: scale(.7); }
    to   { opacity: 1; transform: scale(1); }
}
.transition-name {
    font-family: 'Fredoka One', cursive;
    font-size: 2.8rem; font-weight: 900;
    animation: nameBounce 1s cubic-bezier(.34,1.56,.64,1) infinite alternate;
}
@keyframes nameBounce {
    from { transform: translateY(0) scale(1); }
    to   { transform: translateY(-6px) scale(1.04); }
}
.arrow-bounce {
    font-size: 2rem; display: inline-block;
    animation: arrowMove .6s ease infinite alternate;
}
@keyframes arrowMove {
    from { transform: translateY(0); } to { transform: translateY(6px); }
}

/* ── Phase 指示 ── */
.phase-indicator {
    border-radius: 20px; padding: 5px 14px; font-weight: 800; font-size: .82rem;
    display: inline-block; letter-spacing: 1px;
}

/* ── 分數 ── */
.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #FFD700, #FFA000);
    color: #333; border-radius: 20px; padding: 2px 12px;
    font-weight: 900; font-size: .9rem;
    box-shadow: 0 2px 6px rgba(0,0,0,.15);
}

/* ── 排名表 ── */
.rank-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-radius: 10px; margin-bottom: 5px;
    font-weight: 700; font-size: .85rem;
    box-shadow: 0 2px 8px rgba(0,0,0,.07);
    transition: all .3s ease;
}
.rank-bar-wrap { flex: 1; background: #eee; border-radius: 4px; height: 7px; overflow: hidden; }
.rank-bar { height: 100%; border-radius: 4px; transition: width .7s ease; }

/* ── 模式選擇 ── */
.mode-card {
    border-radius: 16px; padding: 16px 14px; cursor: pointer;
    border: 3px solid transparent; transition: all .2s ease;
    box-shadow: 0 3px 12px rgba(0,0,0,.1);
}
.mode-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(0,0,0,.15); }
.mode-selected { border-color: #FFD700 !important; box-shadow: 0 0 0 3px #FFD70066, 0 8px 24px rgba(0,0,0,.15) !important; }

/* ── Streamlit 覆蓋 ── */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    transition: transform .15s ease, box-shadow .15s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(0,0,0,.15) !important;
}
div.stSlider { padding-top: 4px; }
.element-container { margin-bottom: 4px !important; }
</style>
"""

MSG_COLORS = {
    "info":    ("#E3F2FD", "#1565C0"),
    "success": ("#E8F5E9", "#2E7D32"),
    "warning": ("#FFF8E1", "#E65100"),
    "error":   ("#FFEBEE", "#C62828"),
}

PHASE_STYLE = {
    "draw":   ("🃏 抽牌階段", "#E3F2FD", "#1565C0"),
    "action": ("⚡ 行動階段", "#FFF8E1", "#E65100"),
}


# ══════════════════════════════════════════════════════════════════
#  共用 HTML 元件
# ══════════════════════════════════════════════════════════════════
def render_card(card: Card, selected=False, small=False) -> str:
    sel_cls = "card-selected" if selected else ""
    e_sz = "1.4rem" if small else "1.9rem"
    n_sz = ".62rem" if small else ".7rem"
    d_sz = ".55rem" if small else ".62rem"
    img = (f'<img src="{card.img}" style="width:52px;height:52px;object-fit:cover;border-radius:10px;margin-bottom:4px;">'
           if card.img and Path(card.img).exists()
           else f'<div class="card-emoji" style="font-size:{e_sz};">{card.emoji}</div>')
    return f"""<div class="card {sel_cls}" style="background:{card.bg};border-color:{card.border};">
        {img}
        <div class="card-name" style="color:{card.color};font-size:{n_sz};">{card.cat}</div>
        <div class="card-desc" style="color:{card.color};font-size:{d_sz};">{card.desc}</div>
    </div>"""

def msg_html(text, mtype="info"):
    bg, tc = MSG_COLORS.get(mtype, MSG_COLORS["info"])
    return f'<div class="msg-box" style="background:{bg};color:{tc};">{text}</div>'

def score_html(score):
    return f'<span class="score-badge">⭐ {score} 分</span>'


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
        for i in range(num):
            defaults = ["玩家一 🔴", "玩家二 🟦", "玩家三 🟡", "玩家四 🟣"]
            n = st.text_input(f"玩家 {i+1} 名稱", value=defaults[i], key=f"pname_{i}")
            names.append(n.strip() or f"玩家{i+1}")

        st.markdown("---")
        st.markdown("### 🎮 遊戲模式")
        mode_pick = st.radio("選擇模式", ["回合模式", "全牌模式", "分數模式"], horizontal=True, key="mode_radio")

        mode_val = 5
        if mode_pick == "回合模式":
            st.markdown("""<div style="background:#e3f2fd;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#1565c0;font-weight:700;">
            🔁 設定每位玩家進行的回合數，達到後分數最高者獲勝
            </div>""", unsafe_allow_html=True)
            mode_val = st.slider("每人回合數", 3, 15, 5, key="round_count_setting")
        elif mode_pick == "全牌模式":
            st.markdown("""<div style="background:#e8f5e9;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#2e7d32;font-weight:700;">
            🃏 抽牌堆出完後結算，分數最高者獲勝（原始模式）
            </div>""", unsafe_allow_html=True)
            mode_val = 0
        elif mode_pick == "分數模式":
            st.markdown("""<div style="background:#fff8e1;border-radius:10px;padding:10px 14px;font-size:.83rem;color:#e65100;font-weight:700;">
            🏁 率先達到目標分數的玩家立即獲勝
            </div>""", unsafe_allow_html=True)
            mode_val = st.slider("目標分數", 10, 60, 25, key="score_target")

        mode_key = {"回合模式": "rounds", "全牌模式": "allcards", "分數模式": "score"}[mode_pick]

    with col_r:
        st.markdown("### 📋 食物牌")
        for cat, info in FOOD_CATS.items():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #f0f0f0;font-size:.82rem;"><span>{info["emoji"]} {cat}</span><span style="color:{info["color"]};font-weight:700;">+{info["pts"]}分 × {FOOD_PER_CAT}張</span></div>', unsafe_allow_html=True)

        st.markdown("**均衡加成** 🌟：餐盤含蔬/果＋蛋白質＋澱粉 **額外 +5**")
        st.markdown("**失衡懲罰** ❌：同類超過3張 **−10分**")

        st.markdown("---")
        st.markdown("### ⚡ 功能牌")
        for func, info in FUNC_CARDS.items():
            st.markdown(f'<div style="font-size:.8rem;padding:3px 0;">{info["emoji"]} <b>{func}</b>（×{FUNC_PER_TYPE}）：{info["desc"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎮 開始遊戲！", use_container_width=True, type="primary"):
            if len(set(names)) < len(names):
                st.error("玩家名稱不能重複！"); return
            st.session_state.gs        = init_game(names, mode_key, mode_val)
            st.session_state.sel       = None
            st.session_state.page      = "game"
            # 顯示第一位玩家提示
            st.session_state.gs["showing_transition"] = True
            st.session_state.gs["transition_to"]      = 0
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  換人過場畫面
# ══════════════════════════════════════════════════════════════════
def page_transition():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    players = gs["players"]
    nxt = gs["transition_to"]
    p   = players[nxt]
    pc  = p.color

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        prev_idx = (nxt - 1) % len(players)
        if gs["round_count"] > 0:
            prev = players[prev_idx]
            st.markdown(f'<div style="text-align:center;color:#aaa;font-size:.9rem;margin-bottom:10px;">✅ {prev.name} 的回合結束</div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="transition-banner">
            <div style="font-size:1rem;color:#888;font-weight:700;margin-bottom:8px;">👇 請將裝置交給</div>
            <div class="transition-name" style="color:{pc['header']};">{p.name}</div>
            <div style="font-size:1rem;color:#888;font-weight:600;margin:8px 0;">的回合開始！</div>
            <div class="arrow-bounce">⬇️</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 顯示事件
        for ev in gs["events"]:
            st.markdown(f'<div class="event-item">📢 {ev}</div>', unsafe_allow_html=True)
        gs["events"].clear()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"▶ 我是 {p.name}，開始我的回合！", use_container_width=True, type="primary"):
            gs["showing_transition"] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  遊戲主頁
# ══════════════════════════════════════════════════════════════════
def page_game():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    players: List[Player] = gs["players"]
    ci  = gs["turn"]
    cur = players[ci]
    sel = st.session_state.get("sel", None)

    # ── 頂部 ─────────────────────────────────────────────────
    h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
    with h1:
        st.markdown('<div class="main-title" style="font-size:1.5rem;text-align:left;">🥗 最強糾察員</div>', unsafe_allow_html=True)
        phase_label, phase_bg, phase_tc = PHASE_STYLE[gs["phase"]]
        st.markdown(f'<span class="phase-indicator" style="background:{phase_bg};color:{phase_tc};">{phase_label}</span>', unsafe_allow_html=True)
    with h2:
        mode_labels = {"rounds":"回合模式","allcards":"全牌模式","score":"分數模式"}
        st.markdown(f'<div style="background:#f5f5f5;border-radius:10px;padding:8px;text-align:center;"><div style="font-size:.65rem;color:#999;">模式</div><div style="font-weight:800;font-size:.82rem;">{mode_labels[gs["mode"]]}</div></div>', unsafe_allow_html=True)
    with h3:
        st.markdown(f'<div style="background:#e3f2fd;border-radius:10px;padding:8px;text-align:center;"><div style="font-size:.65rem;color:#1565c0;">牌堆剩餘</div><div style="font-weight:900;font-size:1.5rem;color:#1565c0;">{len(gs["deck"])}</div></div>', unsafe_allow_html=True)
    with h4:
        top = gs["discard"][-1] if gs["discard"] else None
        lbl = f"{top.emoji} {top.cat}" if top else "（空）"
        st.markdown(f'<div style="background:#fce4ec;border-radius:10px;padding:8px;text-align:center;"><div style="font-size:.65rem;color:#c62828;">棄牌堆頂</div><div style="font-size:.8rem;font-weight:700;color:#c62828;">{lbl}</div></div>', unsafe_allow_html=True)

    # 訊息
    if gs["msg"]:
        st.markdown(msg_html(gs["msg"], gs["msg_type"]), unsafe_allow_html=True)

    st.markdown("---")

    # ── 排名 + 餐盤 ────────────────────────────────────────
    left, right = st.columns([1, 2.5])

    with left:
        st.markdown("**📊 即時排名**")
        ranked = sorted(enumerate(players), key=lambda x: x[1].plate_score(), reverse=True)
        max_sc = max((p.plate_score() for p in players), default=1) or 1
        medals = ["🥇","🥈","🥉","4️⃣"]
        for ri, (pi, p) in enumerate(ranked):
            sc  = p.plate_score()
            pct = max(5, int(sc / max_sc * 100)) if sc > 0 else 5
            is_cur = pi == ci
            bg = f"background:{p.color['light']};border:2px solid {p.color['header']};"
            badge = "▶ " if is_cur else ""
            bal_tag = " ✅" if p.is_balanced() else ""
            skip_tag = " ⏸️" if p.skip_next else ""
            st.markdown(f"""<div class="rank-item" style="{bg}">
                <span>{medals[ri]}</span>
                <span style="flex:1;color:{p.color['text']};font-size:.8rem;">{badge}{p.name}{bal_tag}{skip_tag}</span>
                <div class="rank-bar-wrap"><div class="rank-bar" style="width:{pct}%;background:{p.color['header']};"></div></div>
                <span class="score-badge" style="font-size:.78rem;">{sc}</span>
            </div>""", unsafe_allow_html=True)

        if gs["mode"] == "score":
            st.markdown(f'<div style="font-size:.75rem;text-align:center;color:#888;margin-top:4px;">目標：{gs["mode_val"]} 分</div>', unsafe_allow_html=True)
        elif gs["mode"] == "rounds":
            done = gs["round_count"]
            total = gs["mode_val"] * len(players)
            st.markdown(f'<div style="font-size:.75rem;text-align:center;color:#888;margin-top:4px;">已進行 {done}/{total} 輪</div>', unsafe_allow_html=True)

    with right:
        st.markdown("**🍽️ 各玩家餐盤**")
        pcols = st.columns(len(players))
        for pi, p in enumerate(players):
            with pcols[pi]:
                is_cur = pi == ci
                h_bg = p.color["header"] if is_cur else p.color["light"]
                h_tc = "white" if is_cur else p.color["text"]
                glow  = "active-glow" if is_cur else ""
                bal   = "plate-balanced" if p.is_balanced() else ""
                skip_ico = " ⏸️" if p.skip_next else ""
                act_ico  = " ▶" if is_cur else ""
                st.markdown(f'<div class="player-header {glow}" style="background:{h_bg};color:{h_tc};border-radius:12px 12px 0 0;border:2px solid {p.color["header"]};">{act_ico} {p.name}{skip_ico}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plate-area {bal}">', unsafe_allow_html=True)
                if p.plate:
                    cc = st.columns(min(len(p.plate), 5))
                    for j, c in enumerate(p.plate):
                        with cc[j]:
                            st.markdown(render_card(c, small=True), unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:center;color:#ccc;padding:18px 0;font-size:.8rem;'>空餐盤</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if p.is_balanced():
                    st.markdown(f'<div style="text-align:center;font-size:.72rem;font-weight:800;color:#2e7d32;margin-top:3px;">✅ 均衡 +{BALANCED_BONUS}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 當前玩家手牌 ────────────────────────────────────────
    st.markdown(f'<div style="font-size:1rem;font-weight:800;color:{cur.color["text"]};">🎴 {cur.name} 的手牌（{len(cur.hand)} 張）</div>', unsafe_allow_html=True)

    if cur.hand:
        hcols = st.columns(min(len(cur.hand), 6))
        for i, card in enumerate(cur.hand):
            with hcols[i]:
                is_sel = (sel == i)
                st.markdown(render_card(card, selected=is_sel), unsafe_allow_html=True)
                if gs["phase"] == "action" and not gs["pending"]:
                    btn_lbl = "✓ 已選" if is_sel else "選擇"
                    if st.button(btn_lbl, key=f"hsel_{i}", use_container_width=True):
                        st.session_state.sel = i if not is_sel else None
                        st.rerun()
    else:
        st.info("手牌為空")

    # 選中牌說明
    sel_card = cur.hand[sel] if (sel is not None and sel < len(cur.hand)) else None
    if sel_card and gs["phase"] == "action":
        st.markdown(f'<div style="background:{sel_card.bg};border:2px solid {sel_card.border};border-radius:10px;padding:8px 14px;font-weight:700;color:{sel_card.color};text-align:center;margin:6px 0;">{sel_card.emoji} <b>{sel_card.cat}</b> — {sel_card.desc}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ══ 行動區：嚴格按 phase 只顯示當步 ══
    pending = gs.get("pending")

    # ── Phase 1：抽牌 ────────────────────────────────────────
    if gs["phase"] == "draw":
        st.markdown(msg_html("👇 請抽一張牌", "info"), unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🃏 抽一張牌", use_container_width=True, type="primary"):
                action_draw(gs); st.rerun()

    # ── Phase 2：行動 ────────────────────────────────────────
    elif gs["phase"] == "action":

        # 2a. 等待「丟1張」目標
        if pending and pending["func"] == "丟1張":
            st.markdown(msg_html("👇 選擇要從餐盤移除的牌", "warning"), unsafe_allow_html=True)
            if cur.plate:
                rc = st.columns(min(len(cur.plate), 5))
                for j, c in enumerate(cur.plate):
                    with rc[j]:
                        st.markdown(render_card(c, small=True), unsafe_allow_html=True)
                        if st.button("移除", key=f"rem_{j}", use_container_width=True):
                            resolve_remove_plate(gs, j); st.rerun()
            else:
                st.info("餐盤為空，無法使用")
                if st.button("取消"):
                    gs["pending"] = None; st.rerun()

        # 2b. 等待「暫停」目標
        elif pending and pending["func"] == "暫停":
            st.markdown(msg_html("👇 選擇要暫停的玩家", "warning"), unsafe_allow_html=True)
            targets = [(i, p) for i, p in enumerate(players) if i != ci]
            tc = st.columns(len(targets))
            for idx, (ti, tp) in enumerate(targets):
                with tc[idx]:
                    st.markdown(f'<div style="background:{tp.color["light"]};border:2px solid {tp.color["header"]};border-radius:12px;padding:10px;text-align:center;font-weight:700;color:{tp.color["text"]};">{tp.name}{"（已暫停）" if tp.skip_next else ""}<br><small>{tp.plate_score()} 分</small></div>', unsafe_allow_html=True)
                    if st.button(f"暫停 {tp.name}", key=f"pause_{ti}", use_container_width=True, type="primary"):
                        resolve_pause(gs, ti); st.rerun()

        # 2c. 正常行動：選牌後顯示操作
        else:
            if not sel_card:
                st.markdown(msg_html("👆 先點選一張手牌，再選擇行動", "info"), unsafe_allow_html=True)
            else:
                can_place   = sel_card.kind == "food" and len(cur.plate) < MAX_PLATE
                can_func    = sel_card.kind == "func"
                can_discard = True

                ac = st.columns(3)
                with ac[0]:
                    tip = "" if can_place else ("（餐盤已滿）" if len(cur.plate) >= MAX_PLATE else "（只能放食物牌）")
                    if st.button(f"🍽️ 放入餐盤{tip}", disabled=not can_place, use_container_width=True, type="primary"):
                        action_place(gs, sel); st.rerun()
                with ac[1]:
                    if st.button("✨ 使用功能牌" if can_func else "（非功能牌）", disabled=not can_func, use_container_width=True):
                        action_use_func(gs, sel); st.rerun()
                with ac[2]:
                    if st.button("🗑️ 棄牌", disabled=not can_discard, use_container_width=True):
                        action_discard(gs, sel); st.rerun()

    if gs["last_round"]:
        st.markdown('<div class="event-item" style="border-color:#FF5722;background:#fff3e0;text-align:center;font-size:.85rem;">⚡ 最後一輪！把握機會！</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩️ 返回設定頁"):
        st.session_state.page = "setup"
        if "gs" in st.session_state: del st.session_state.gs
        st.rerun()


# ══════════════════════════════════════════════════════════════════
#  結果頁
# ══════════════════════════════════════════════════════════════════
def page_result():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    players: List[Player] = gs["players"]
    for p in players: p.score = p.plate_score()
    ranked = sorted(players, key=lambda p: p.score, reverse=True)
    winner = ranked[0]
    medals = ["🥇","🥈","🥉","4️⃣"]

    st.markdown('<div class="main-title">🏆 遊戲結束！</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:1.4rem;font-weight:900;color:{winner.color["text"]};margin:8px 0;">🎉 {winner.name} 獲勝！{score_html(winner.score)}</div>', unsafe_allow_html=True)
    st.markdown("---")

    for ri, p in enumerate(ranked):
        cats = {}
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
                    st.markdown(f'<div style="font-size:.8rem;padding:2px 0;">{FOOD_CATS.get(cat,{}).get("emoji","⚡")} {cat} × {cnt} 張 = {pts_per*cnt} 分{"  ❌超量−10" if cnt>3 else ""}</div>', unsafe_allow_html=True)
                if bal_b: st.success(f"✅ 均衡加成 +{bal_b}")
                if imbal: st.error(f"❌ 失衡懲罰 {imbal}")
            with dc2:
                st.markdown(f'<div style="background:{p.color["light"]};border:2px solid {p.color["header"]};border-radius:14px;padding:14px;text-align:center;"><div style="font-size:.7rem;color:#888;">食物基礎</div><div style="font-size:1.6rem;font-weight:900;color:{p.color["text"]};">{raw}</div><div style="font-size:.75rem;color:#888;">{f"+{bal_b} 均衡" if bal_b else ""}{f"  {imbal} 失衡" if imbal else ""}</div><div style="font-size:1.3rem;font-weight:900;color:{p.color["text"]};border-top:1px solid #eee;margin-top:6px;padding-top:6px;">= {p.score} 分</div></div>', unsafe_allow_html=True)

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
    elif gs and gs.get("over"):
        page_result()
    elif gs and gs.get("showing_transition"):
        page_transition()
    else:
        page_game()

if __name__ == "__main__":
    main()
