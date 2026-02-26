import streamlit as st
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# ─── 常數設定 ───────────────────────────────────────────────────
FOOD_CATEGORIES = {
    "蔬菜水果": {"points": 5, "color": "#4CAF50", "emoji": "🥦", "bg": "#E8F5E9"},
    "蛋白質":   {"points": 4, "color": "#F44336", "emoji": "🍗", "bg": "#FFEBEE"},
    "澱粉":     {"points": 3, "color": "#FF9800", "emoji": "🍚", "bg": "#FFF3E0"},
    "乳品":     {"points": 2, "color": "#2196F3", "emoji": "🥛", "bg": "#E3F2FD"},
    "油炸與點心":{"points": 1, "color": "#9E9E9E", "emoji": "🍟", "bg": "#F5F5F5"},
}

FUNCTION_CARDS = {
    "抽牌+2":    {"emoji": "🃏", "color": "#9C27B0", "bg": "#F3E5F5", "desc": "立即再抽2張牌"},
    "偷1張":     {"emoji": "🤏", "color": "#E91E63", "bg": "#FCE4EC", "desc": "從任意玩家手牌偷取1張"},
    "丟1張":     {"emoji": "🗑️", "color": "#795548", "bg": "#EFEBE9", "desc": "將自己餐盤中1張牌移至棄牌區"},
    "順時針交換手牌":{"emoji": "🔄", "color": "#00BCD4", "bg": "#E0F7FA", "desc": "所有玩家手牌順時針傳遞"},
    "暫停":      {"emoji": "⏸️", "color": "#607D8B", "bg": "#ECEFF1", "desc": "指定一位玩家跳過下回合"},
}

MAX_HAND = 5
MAX_PLATE = 4
BALANCED_BONUS = 5
IMBALANCE_PENALTY = -10
BALANCED_TYPES = {"蔬菜水果", "蛋白質", "澱粉"}

# ─── 資料結構 ──────────────────────────────────────────────────
@dataclass
class Card:
    card_type: str   # "food" or "function"
    category: str    # e.g. "蔬菜水果" or "抽牌+2"
    card_id: int
    image_path: Optional[str] = None  # 未來可加 .jpg 路徑

    def display_name(self):
        return self.category

    def get_emoji(self):
        if self.card_type == "food":
            return FOOD_CATEGORIES[self.category]["emoji"]
        return FUNCTION_CARDS[self.category]["emoji"]

    def get_color(self):
        if self.card_type == "food":
            return FOOD_CATEGORIES[self.category]["color"]
        return FUNCTION_CARDS[self.category]["color"]

    def get_bg(self):
        if self.card_type == "food":
            return FOOD_CATEGORIES[self.category]["bg"]
        return FUNCTION_CARDS[self.category]["bg"]

    def get_points(self):
        if self.card_type == "food":
            return FOOD_CATEGORIES[self.category]["points"]
        return 0

@dataclass
class Player:
    name: str
    hand: List[Card] = field(default_factory=list)
    plate: List[Card] = field(default_factory=list)
    score: int = 0
    skip_next: bool = False

    def plate_score(self):
        if not self.plate:
            return 0
        total = sum(c.get_points() for c in self.plate)
        categories = [c.category for c in self.plate]
        cat_set = set(categories)
        # 均衡加分
        if BALANCED_TYPES.issubset(cat_set):
            total += BALANCED_BONUS
        # 飲食失衡懲罰
        for cat in FOOD_CATEGORIES:
            if categories.count(cat) > 3:
                total += IMBALANCE_PENALTY
        return total

    def is_balanced(self):
        cats = {c.category for c in self.plate}
        return BALANCED_TYPES.issubset(cats)

# ─── 遊戲引擎 ──────────────────────────────────────────────────
def build_deck():
    cards = []
    cid = 0
    # 食物牌：每類5張
    for cat in FOOD_CATEGORIES:
        for _ in range(5):
            cards.append(Card("food", cat, cid))
            cid += 1
    # 功能牌：每種3張
    for func in FUNCTION_CARDS:
        for _ in range(3):
            cards.append(Card("function", func, cid))
            cid += 1
    random.shuffle(cards)
    return cards

def init_game(player_names: List[str]):
    deck = build_deck()
    players = [Player(name) for name in player_names]
    # 發初始手牌
    for p in players:
        for _ in range(3):
            if deck:
                p.hand.append(deck.pop())
    return {
        "players": players,
        "deck": deck,
        "discard": [],
        "current_turn": 0,
        "phase": "draw",       # draw → action → end
        "game_over": False,
        "winner": None,
        "last_round": False,
        "last_round_starter": None,
        "message": "遊戲開始！",
        "message_type": "info",
        "pending_function": None,  # {"func": ..., "player_idx": ...}
        "skipped_players": [],
    }

def check_game_end(gs):
    """檢查遊戲結束條件"""
    if not gs["deck"]:
        return True, "抽牌堆已抽完！"
    for p in gs["players"]:
        if p.is_balanced() and not gs["last_round"]:
            gs["last_round"] = True
            gs["last_round_starter"] = gs["current_turn"]
            return False, f"🎯 {p.name} 完成均衡餐盤！最後一輪開始！"
    if gs["last_round"]:
        cur = gs["current_turn"]
        starter = gs["last_round_starter"]
        # 如果已繞回 starter 前一位，結束
        next_idx = (cur + 1) % len(gs["players"])
        if next_idx == starter:
            return True, "最後一輪結束！"
    return False, ""

def calculate_scores(gs):
    for p in gs["players"]:
        p.score = p.plate_score()

def get_winner(gs):
    calculate_scores(gs)
    players = gs["players"]
    return max(players, key=lambda p: p.score)

# ─── CSS 樣式 ──────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap');

    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }

    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FF6B6B, #FFE66D, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        animation: titlePulse 3s ease-in-out infinite;
    }
    @keyframes titlePulse {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }

    .game-card {
        border-radius: 12px;
        padding: 12px 10px;
        text-align: center;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.25s cubic-bezier(.4,0,.2,1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        user-select: none;
    }
    .game-card:hover {
        transform: translateY(-6px) scale(1.04);
        box-shadow: 0 8px 24px rgba(0,0,0,0.22);
        border-color: #FFD700;
    }
    .game-card.selected {
        transform: translateY(-8px) scale(1.06);
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 3px #FFD70080, 0 8px 24px rgba(0,0,0,0.22);
    }

    .card-emoji { font-size: 2rem; line-height: 1.2; }
    .card-name { font-size: 0.78rem; font-weight: 700; margin-top: 4px; }
    .card-points { font-size: 0.68rem; opacity: 0.8; }

    .plate-zone {
        background: linear-gradient(135deg, #FFFDE7, #FFF9C4);
        border: 2px dashed #FFC107;
        border-radius: 16px;
        padding: 12px;
        min-height: 110px;
    }

    .player-header {
        border-radius: 12px;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }

    .msg-box {
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
        text-align: center;
        margin: 8px 0;
        animation: fadeSlideIn 0.4s ease;
    }
    @keyframes fadeSlideIn {
        from { opacity:0; transform: translateY(-10px); }
        to { opacity:1; transform: translateY(0); }
    }

    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg,#FFD700,#FFA000);
        color: #222;
        border-radius: 20px;
        padding: 2px 12px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }

    .deck-counter {
        background: linear-gradient(135deg,#1a1a2e,#16213e);
        color: #FFD700;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        font-weight: 700;
    }

    .balanced-glow {
        animation: balancedGlow 1.5s ease-in-out infinite;
    }
    @keyframes balancedGlow {
        0%,100% { box-shadow: 0 0 8px #4CAF50; }
        50% { box-shadow: 0 0 24px #4CAF50, 0 0 48px #4CAF5060; }
    }

    .action-btn > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.2s !important;
    }

    .stButton > button:hover { transform: scale(1.04); }
    </style>
    """, unsafe_allow_html=True)

# ─── 卡牌渲染 ──────────────────────────────────────────────────
def render_card_html(card: Card, selected=False, size="normal"):
    sel_class = "selected" if selected else ""
    fs_emoji = "2rem" if size == "normal" else "1.5rem"
    fs_name = "0.78rem" if size == "normal" else "0.68rem"
    img_html = ""
    # 若未來有圖檔
    if card.image_path and Path(card.image_path).exists():
        img_html = f'<img src="{card.image_path}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;margin-bottom:4px;">'
    else:
        img_html = f'<div class="card-emoji" style="font-size:{fs_emoji}">{card.get_emoji()}</div>'

    return f"""
    <div class="game-card {sel_class}"
         style="background:{card.get_bg()};border-color:{card.get_color()}20;">
        {img_html}
        <div class="card-name" style="color:{card.get_color()};font-size:{fs_name};">{card.display_name()}</div>
        <div class="card-points" style="color:{card.get_color()};">{f'+{card.get_points()}分' if card.card_type=="food" else FUNCTION_CARDS[card.category]["desc"][:8]}</div>
    </div>
    """

# ─── 主畫面 ────────────────────────────────────────────────────
def show_setup():
    st.markdown('<div class="main-title">🥗 最強糾察員</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;'>健康飲食卡牌對戰遊戲</p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("👥 玩家設定")
        num_players = st.slider("玩家人數", 2, 4, 2)
        names = []
        for i in range(num_players):
            n = st.text_input(f"玩家 {i+1} 名稱", value=f"玩家{i+1}", key=f"pname_{i}")
            names.append(n)

    with col2:
        st.subheader("📋 遊戲規則")
        rules = [
            ("🥦 蔬菜水果", "+5分"),
            ("🍗 蛋白質", "+4分"),
            ("🍚 澱粉", "+3分"),
            ("🥛 乳品", "+2分"),
            ("🍟 油炸與點心", "+1分"),
            ("⚖️ 均衡餐盤(蔬果+蛋白+澱粉)", "+5額外"),
            ("❌ 超過3張同類", "-10分"),
        ]
        for name, pts in rules:
            st.markdown(f"`{pts}` {name}")

    st.markdown("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎮 開始遊戲！", use_container_width=True, type="primary"):
            if len(set(names)) < len(names):
                st.error("玩家名稱不能重複！")
            else:
                st.session_state.gs = init_game(names)
                st.session_state.setup = False
                st.session_state.selected_hand_idx = None
                st.rerun()

def show_game():
    gs = st.session_state.gs
    players: List[Player] = gs["players"]
    cur_idx = gs["current_turn"]
    cur_player = players[cur_idx]

    # 頂部狀態列
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.markdown(f'<div class="main-title" style="font-size:1.4rem;">🥗 最強糾察員</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""<div class="deck-counter">
            🃏 牌堆<br><span style="font-size:1.5rem;">{len(gs["deck"])}</span>
        </div>""", unsafe_allow_html=True)
    with cols[2]:
        discard_top = gs["discard"][-1] if gs["discard"] else None
        label = f"{discard_top.get_emoji()} {discard_top.display_name()}" if discard_top else "空"
        st.markdown(f"""<div class="deck-counter" style="background:linear-gradient(135deg,#2d1b69,#11998e);">
            🗂️ 棄牌<br><span style="font-size:0.9rem;">{label}</span>
        </div>""", unsafe_allow_html=True)

    # 訊息框
    msg = gs.get("message", "")
    mtype = gs.get("message_type", "info")
    colors = {"info": "#E3F2FD,#1565C0", "success": "#E8F5E9,#2E7D32",
              "warning": "#FFF3E0,#E65100", "error": "#FFEBEE,#C62828"}
    bg, tc = colors.get(mtype, colors["info"]).split(",")
    if msg:
        st.markdown(f'<div class="msg-box" style="background:{bg};color:{tc};">{msg}</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # 所有玩家餐盤概覽
    st.subheader("🍽️ 餐盤總覽")
    pcols = st.columns(len(players))
    for i, p in enumerate(players):
        with pcols[i]:
            is_cur = (i == cur_idx)
            bal = p.is_balanced()
            glow = "balanced-glow" if bal else ""
            skip_mark = " ⏸️" if p.skip_next else ""
            header_bg = "#FFD700" if is_cur else "#F0F0F0"
            header_tc = "#222" if is_cur else "#555"
            st.markdown(f"""<div class="player-header" style="background:{header_bg};color:{header_tc};">
                {'▶ ' if is_cur else ''}{p.name}{skip_mark}
                <span class="score-badge" style="float:right;">{p.plate_score()}分</span>
            </div>""", unsafe_allow_html=True)

            st.markdown(f'<div class="plate-zone {glow}">', unsafe_allow_html=True)
            if p.plate:
                card_cols = st.columns(min(len(p.plate), 4))
                for j, card in enumerate(p.plate):
                    with card_cols[j % 4]:
                        st.markdown(render_card_html(card, size="small"), unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align:center;color:#aaa;font-size:0.8rem;'>空餐盤</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if bal:
                st.markdown("<p style='text-align:center;font-size:0.8rem;color:#2E7D32;font-weight:700;'>✅ 均衡餐盤！</p>", unsafe_allow_html=True)

    st.markdown("---")

    # 當前玩家手牌區
    st.subheader(f"🎴 {cur_player.name} 的手牌 ({gs['phase']}階段)")

    sel = st.session_state.get("selected_hand_idx", None)

    if cur_player.hand:
        hand_cols = st.columns(min(len(cur_player.hand), 5))
        for i, card in enumerate(cur_player.hand):
            with hand_cols[i]:
                is_sel = (sel == i)
                st.markdown(render_card_html(card, selected=is_sel), unsafe_allow_html=True)
                btn_label = f"{'✓ ' if is_sel else ''}選擇"
                if st.button(btn_label, key=f"hand_sel_{i}", use_container_width=True):
                    st.session_state.selected_hand_idx = i if not is_sel else None
                    st.rerun()
    else:
        st.info("手牌為空")

    st.markdown("---")

    # 行動按鈕區
    st.subheader("⚡ 行動")
    sel_card = cur_player.hand[sel] if (sel is not None and sel < len(cur_player.hand)) else None

    if gs["phase"] == "draw":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🃏 抽一張牌", use_container_width=True, type="primary"):
                action_draw(gs, cur_player)
                st.rerun()

    elif gs["phase"] == "action":
        action_cols = st.columns(3)
        with action_cols[0]:
            can_place = sel_card and sel_card.card_type == "food" and len(cur_player.plate) < MAX_PLATE
            if st.button(f"🍽️ 放入餐盤", disabled=not can_place, use_container_width=True, type="primary"):
                action_place(gs, cur_player, sel)
                st.rerun()

        with action_cols[1]:
            can_use = sel_card and sel_card.card_type == "function"
            if st.button(f"✨ 使用功能牌", disabled=not can_use, use_container_width=True):
                action_function(gs, cur_player, sel, players)
                st.rerun()

        with action_cols[2]:
            can_discard = sel_card is not None
            if st.button(f"🗑️ 棄牌", disabled=not can_discard, use_container_width=True):
                action_discard(gs, cur_player, sel)
                st.rerun()

        # 若選了牌，顯示說明
        if sel_card:
            info_bg = sel_card.get_bg()
            info_tc = sel_card.get_color()
            if sel_card.card_type == "food":
                desc = f"放入餐盤得 +{sel_card.get_points()} 分"
            else:
                desc = FUNCTION_CARDS[sel_card.category]["desc"]
            st.markdown(f"""<div style="background:{info_bg};color:{info_tc};border-radius:8px;padding:8px 14px;font-weight:600;text-align:center;">
                {sel_card.get_emoji()} {sel_card.display_name()} — {desc}
            </div>""", unsafe_allow_html=True)

        # 功能牌：偷牌目標選擇
        if gs.get("pending_function") == "偷1張":
            st.markdown("### 選擇要偷牌的對象")
            target_cols = st.columns(len(players) - 1)
            tc_idx = 0
            for i, p in enumerate(players):
                if i == cur_idx:
                    continue
                with target_cols[tc_idx]:
                    if p.hand:
                        if st.button(f"偷 {p.name} 的牌", key=f"steal_{i}"):
                            stolen = random.choice(p.hand)
                            p.hand.remove(stolen)
                            cur_player.hand.append(stolen)
                            gs["pending_function"] = None
                            gs["message"] = f"🤏 {cur_player.name} 從 {p.name} 偷到了 {stolen.get_emoji()}{stolen.display_name()}！"
                            gs["message_type"] = "warning"
                            end_turn(gs, players)
                            st.rerun()
                    else:
                        st.write(f"{p.name} 手牌為空")
                tc_idx += 1

        # 功能牌：暫停目標
        if gs.get("pending_function") == "暫停":
            st.markdown("### 選擇要暫停的玩家")
            for i, p in enumerate(players):
                if i == cur_idx:
                    continue
                if st.button(f"暫停 {p.name}", key=f"pause_{i}"):
                    p.skip_next = True
                    gs["pending_function"] = None
                    gs["message"] = f"⏸️ {p.name} 下回合被暫停！"
                    gs["message_type"] = "warning"
                    end_turn(gs, players)
                    st.rerun()

        # 功能牌：丟餐盤牌
        if gs.get("pending_function") == "丟1張":
            st.markdown("### 選擇要從餐盤移除的牌")
            if cur_player.plate:
                plate_sel_cols = st.columns(len(cur_player.plate))
                for i, card in enumerate(cur_player.plate):
                    with plate_sel_cols[i]:
                        st.markdown(render_card_html(card, size="small"), unsafe_allow_html=True)
                        if st.button(f"移除", key=f"remove_plate_{i}"):
                            removed = cur_player.plate.pop(i)
                            gs["discard"].append(removed)
                            gs["pending_function"] = None
                            gs["message"] = f"🗑️ {removed.get_emoji()}{removed.display_name()} 從餐盤移至棄牌區"
                            gs["message_type"] = "info"
                            end_turn(gs, players)
                            st.rerun()
            else:
                st.info("餐盤為空，無法使用此功能")
                if st.button("取消"):
                    gs["pending_function"] = None
                    st.rerun()

def show_gameover():
    gs = st.session_state.gs
    players = gs["players"]
    calculate_scores(gs)
    winner = get_winner(gs)

    st.markdown('<div class="main-title">🏆 遊戲結束！</div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;color:#FFD700;'>🎉 {winner.name} 獲勝！</h2>",
                unsafe_allow_html=True)

    st.markdown("### 📊 最終計分")
    sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
    for rank, p in enumerate(sorted_players):
        medal = ["🥇","🥈","🥉","4️⃣"][rank]
        bal_str = "✅ 均衡餐盤 +5" if p.is_balanced() else ""
        cats = {}
        for c in p.plate:
            cats[c.category] = cats.get(c.category, 0) + 1
        imbal = [f"❌ {cat}超量 -10" for cat, cnt in cats.items() if cnt > 3]

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{medal} {p.name}**")
            plate_preview = " ".join([c.get_emoji() for c in p.plate]) or "空餐盤"
            st.write(f"餐盤：{plate_preview}")
            if bal_str: st.success(bal_str)
            for ib in imbal: st.error(ib)
        with col2:
            st.markdown(f'<div class="score-badge" style="font-size:1.5rem;">{p.score} 分</div>',
                        unsafe_allow_html=True)
        st.markdown("---")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 再玩一局", use_container_width=True, type="primary"):
            st.session_state.setup = True
            del st.session_state.gs
            st.rerun()

# ─── 行動函式 ──────────────────────────────────────────────────
def action_draw(gs, player):
    if gs["deck"]:
        card = gs["deck"].pop()
        player.hand.append(card)
        gs["message"] = f"🃏 抽到了 {card.get_emoji()} {card.display_name()}"
        gs["message_type"] = "info"
    else:
        gs["message"] = "牌堆已空！"
        gs["message_type"] = "warning"
    gs["phase"] = "action"

def action_place(gs, player, idx):
    card = player.hand.pop(idx)
    player.plate.append(card)
    gs["message"] = f"🍽️ {card.get_emoji()} {card.display_name()} 放入餐盤！(+{card.get_points()}分)"
    gs["message_type"] = "success"
    st.session_state.selected_hand_idx = None
    end_turn(gs, gs["players"])

def action_discard(gs, player, idx):
    card = player.hand.pop(idx)
    gs["discard"].append(card)
    gs["message"] = f"🗑️ {card.get_emoji()} {card.display_name()} 棄置"
    gs["message_type"] = "info"
    st.session_state.selected_hand_idx = None
    end_turn(gs, gs["players"])

def action_function(gs, player, idx, players):
    card = player.hand.pop(idx)
    func = card.category
    gs["discard"].append(card)
    st.session_state.selected_hand_idx = None

    if func == "抽牌+2":
        drawn = []
        for _ in range(2):
            if gs["deck"] and len(player.hand) < MAX_HAND:
                c = gs["deck"].pop()
                player.hand.append(c)
                drawn.append(c.get_emoji())
        gs["message"] = f"🃏 抽了2張！{''.join(drawn)}"
        gs["message_type"] = "success"
        end_turn(gs, players)

    elif func == "順時針交換手牌":
        hands = [p.hand[:] for p in players]
        n = len(players)
        for i, p in enumerate(players):
            p.hand = hands[(i - 1) % n]
        gs["message"] = "🔄 所有玩家手牌順時針交換！"
        gs["message_type"] = "warning"
        end_turn(gs, players)

    elif func in ["偷1張", "暫停", "丟1張"]:
        gs["pending_function"] = func
        gs["message"] = f"✨ 使用 {func}，請選擇目標..."
        gs["message_type"] = "info"
        # 不結束回合，等待目標選擇

def end_turn(gs, players):
    # 檢查結束
    over, msg = check_game_end(gs)
    if over:
        gs["game_over"] = True
        gs["message"] = msg or "遊戲結束！"
        return

    if msg:
        gs["message"] = msg
        gs["message_type"] = "warning"

    # 下一位玩家
    n = len(players)
    gs["current_turn"] = (gs["current_turn"] + 1) % n
    # 跳過暫停玩家
    next_p = players[gs["current_turn"]]
    if next_p.skip_next:
        next_p.skip_next = False
        gs["current_turn"] = (gs["current_turn"] + 1) % n

    # 手牌上限
    cur = players[gs["current_turn"]]
    while len(cur.hand) > MAX_HAND:
        discarded = cur.hand.pop()
        gs["discard"].append(discarded)

    gs["phase"] = "draw"
    gs["pending_function"] = None

# ─── 入口點 ────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="最強糾察員",
        page_icon="🥗",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    if "setup" not in st.session_state:
        st.session_state.setup = True
    if "selected_hand_idx" not in st.session_state:
        st.session_state.selected_hand_idx = None

    if st.session_state.setup:
        show_setup()
    elif "gs" in st.session_state and st.session_state.gs.get("game_over"):
        show_gameover()
    elif "gs" in st.session_state:
        show_game()

if __name__ == "__main__":
    main()
