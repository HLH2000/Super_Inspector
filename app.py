"""
最強糾察員 ── ESPORTS EDITION
賽博龐克電競風 | 熱座模式 | 即時排名看板
"""
import streamlit as st
import random
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  常數
# ══════════════════════════════════════════════════════════════
FOOD_CATS = {
    "蔬菜水果": {"pts": 5, "emoji": "🥦", "neon": "#00ff88", "glow": "#00ff8844"},
    "蛋白質":   {"pts": 4, "emoji": "🍗", "neon": "#ff3860", "glow": "#ff386044"},
    "澱粉":     {"pts": 3, "emoji": "🌾", "neon": "#ffb347", "glow": "#ffb34744"},
    "乳品":     {"pts": 2, "emoji": "🥛", "neon": "#00cfff", "glow": "#00cfff44"},
    "油炸與點心":{"pts": 1, "emoji": "🍟", "neon": "#bf94ff", "glow": "#bf94ff44"},
}
FUNC_CARDS = {
    "抽牌+2":      {"emoji": "⚡", "neon": "#ffe000", "glow": "#ffe00044", "desc": "立即再抽 2 張牌",        "target": "self"},
    "偷1張":       {"emoji": "🎯", "neon": "#ff3860", "glow": "#ff386044", "desc": "從指定玩家偷 1 張牌",   "target": "enemy"},
    "丟1張":       {"emoji": "💣", "neon": "#ff6b00", "glow": "#ff6b0044", "desc": "移除自己餐盤中 1 張",   "target": "self_plate"},
    "順時針交換手牌":{"emoji": "🔀", "neon": "#00ff88", "glow": "#00ff8844", "desc": "所有人手牌順時針傳",  "target": "all"},
    "暫停":         {"emoji": "⛔", "neon": "#bf94ff", "glow": "#bf94ff44", "desc": "讓指定玩家跳過回合",   "target": "enemy"},
}
MAX_HAND = 5; MAX_PLATE = 4
BALANCED_SET = {"蔬菜水果","蛋白質","澱粉"}
BALANCED_BONUS = 5; IMBALANCE_PENALTY = -10
FOOD_PER_CAT = 5; FUNC_PER_TYPE = 3

# 玩家霓虹顏色組
P_NEON = ["#00cfff", "#ff3860", "#00ff88", "#ffe000"]
P_GLOW = ["#00cfff33","#ff386033","#00ff8833","#ffe00033"]

# ══════════════════════════════════════════════════════════════
#  資料模型
# ══════════════════════════════════════════════════════════════
@dataclass
class Card:
    kind: str; cat: str; cid: int; img: Optional[str] = None
    @property
    def emoji(self): return FOOD_CATS[self.cat]["emoji"] if self.kind=="food" else FUNC_CARDS[self.cat]["emoji"]
    @property
    def neon(self):  return FOOD_CATS[self.cat]["neon"]  if self.kind=="food" else FUNC_CARDS[self.cat]["neon"]
    @property
    def glow(self):  return FOOD_CATS[self.cat]["glow"]  if self.kind=="food" else FUNC_CARDS[self.cat]["glow"]
    @property
    def pts(self):   return FOOD_CATS[self.cat]["pts"]   if self.kind=="food" else 0
    @property
    def desc(self):  return f"+{self.pts} 分"            if self.kind=="food" else FUNC_CARDS[self.cat]["desc"]

@dataclass
class Player:
    name: str; neon: str; glow: str
    hand: List[Card] = field(default_factory=list)
    plate: List[Card] = field(default_factory=list)
    skip_next: bool = False; score: int = 0
    def plate_score(self):
        if not self.plate: return 0
        t = sum(c.pts for c in self.plate); cats = [c.cat for c in self.plate]
        if BALANCED_SET.issubset(set(cats)): t += BALANCED_BONUS
        for cat in FOOD_CATS:
            if cats.count(cat) > 3: t += IMBALANCE_PENALTY
        return t
    def is_balanced(self): return BALANCED_SET.issubset({c.cat for c in self.plate})
    def imbalanced_cat(self):
        cats = [c.cat for c in self.plate]
        for cat in FOOD_CATS:
            if cats.count(cat) > 3: return cat
        return None

# ══════════════════════════════════════════════════════════════
#  遊戲邏輯
# ══════════════════════════════════════════════════════════════
def build_deck():
    cards, cid = [], 0
    for cat in FOOD_CATS:
        for _ in range(FOOD_PER_CAT): cards.append(Card("food",cat,cid)); cid+=1
    for cat in FUNC_CARDS:
        for _ in range(FUNC_PER_TYPE): cards.append(Card("func",cat,cid)); cid+=1
    random.shuffle(cards); return cards

def init_game(names):
    deck = build_deck()
    players = [Player(n, P_NEON[i], P_GLOW[i]) for i,n in enumerate(names)]
    for p in players:
        for _ in range(3):
            if deck: p.hand.append(deck.pop())
    return dict(players=players, deck=deck, discard=[], turn=0,
                phase="draw", over=False, last_round=False, last_starter=None,
                msg="▶  GAME START", msg_type="info", pending=None,
                events=[], round_count=1)

def check_end(gs):
    if not gs["deck"]: return True,"牌堆耗盡"
    for p in gs["players"]:
        if p.is_balanced() and not gs["last_round"]:
            gs["last_round"]=True; gs["last_starter"]=gs["turn"]
            return False,f"★ {p.name} 完成均衡餐盤！最後一輪開始！"
    if gs["last_round"]:
        nxt=(gs["turn"]+1)%len(gs["players"])
        if nxt==gs["last_starter"]: return True,"最後一輪結束"
    return False,""

def advance(gs):
    over,msg = check_end(gs)
    if over: gs["over"]=True; gs["msg"]=f"◈ GAME OVER — {msg}"; gs["msg_type"]="success"; return
    if msg: gs["events"].append(msg); gs["msg"]=msg; gs["msg_type"]="warning"
    n=len(gs["players"]); gs["turn"]=(gs["turn"]+1)%n; gs["round_count"]+=1
    p=gs["players"][gs["turn"]]
    if p.skip_next:
        p.skip_next=False; gs["events"].append(f"⛔ {p.name} 被暫停，跳過回合")
        gs["turn"]=(gs["turn"]+1)%n
    cur=gs["players"][gs["turn"]]
    while len(cur.hand)>MAX_HAND: c=cur.hand.pop(); gs["discard"].append(c)
    gs["phase"]="draw"; gs["pending"]=None
    gs["msg"]=f"▶  {cur.name} — 請抽牌"; gs["msg_type"]="info"

def do_draw(gs):
    p=gs["players"][gs["turn"]]
    if gs["deck"] and len(p.hand)<MAX_HAND:
        c=gs["deck"].pop(); p.hand.append(c)
        gs["msg"]=f"DRAW ›› {c.emoji} {c.cat}"; gs["msg_type"]="info"
    else: gs["msg"]="手牌滿或牌堆空"; gs["msg_type"]="warning"
    gs["phase"]="action"

def do_place(gs,hi):
    p=gs["players"][gs["turn"]]
    if hi>=len(p.hand): return
    c=p.hand.pop(hi); p.plate.append(c)
    gs["msg"]=f"PLACE ›› {c.emoji} {c.cat} ＋{c.pts}分"; gs["msg_type"]="success"
    if p.is_balanced(): gs["events"].append(f"🌟 {p.name} 均衡！+{BALANCED_BONUS}")
    if p.imbalanced_cat(): gs["events"].append(f"⚠ {p.name} 失衡 {p.imbalanced_cat()} −10")
    st.session_state.sel=None; advance(gs)

def do_discard(gs,hi):
    p=gs["players"][gs["turn"]]
    if hi>=len(p.hand): return
    c=p.hand.pop(hi); gs["discard"].append(c)
    gs["msg"]=f"DISCARD ›› {c.emoji} {c.cat}"; gs["msg_type"]="info"
    st.session_state.sel=None; advance(gs)

def do_func(gs,hi):
    p=gs["players"][gs["turn"]]; players=gs["players"]
    if hi>=len(p.hand): return
    card=p.hand[hi]; func=card.cat; p.hand.pop(hi); gs["discard"].append(card)
    st.session_state.sel=None
    if func=="抽牌+2":
        drawn=[]
        for _ in range(2):
            if gs["deck"] and len(p.hand)<MAX_HAND: c=gs["deck"].pop(); p.hand.append(c); drawn.append(c.emoji)
        gs["msg"]=f"⚡ 抽牌+2 ›› {''.join(drawn)}"; gs["msg_type"]="success"; advance(gs)
    elif func=="順時針交換手牌":
        saved=[pl.hand[:] for pl in players]; n=len(players)
        for i,pl in enumerate(players): pl.hand=saved[(i-1)%n]
        gs["msg"]="🔀 手牌順時針大交換！"; gs["msg_type"]="warning"
        gs["events"].append("🔀 全員手牌順時針傳遞！"); advance(gs)
    elif func in ("偷1張","暫停","丟1張"):
        gs["pending"]=func; gs["phase"]="action"
        gs["msg"]=f"{card.emoji} {func} — 選擇目標"; gs["msg_type"]="warning"

def resolve_steal(gs,ti):
    p=gs["players"][gs["turn"]]; tp=gs["players"][ti]
    if not tp.hand: gs["msg"]=f"{tp.name} 手牌為空"; gs["msg_type"]="warning"; gs["pending"]=None; advance(gs); return
    s=random.choice(tp.hand); tp.hand.remove(s); p.hand.append(s)
    gs["events"].append(f"🎯 {p.name} 從 {tp.name} 偷到 {s.emoji}{s.cat}！")
    gs["msg"]=f"STEAL ›› {s.emoji}{s.cat} from {tp.name}"; gs["msg_type"]="warning"
    gs["pending"]=None; advance(gs)

def resolve_pause(gs,ti):
    tp=gs["players"][ti]; tp.skip_next=True
    gs["events"].append(f"⛔ {tp.name} 下回合被暫停！")
    gs["msg"]=f"SUSPEND ›› {tp.name}"; gs["msg_type"]="warning"
    gs["pending"]=None; advance(gs)

def resolve_remove(gs,pi):
    p=gs["players"][gs["turn"]]
    if pi>=len(p.plate): return
    c=p.plate.pop(pi); gs["discard"].append(c)
    gs["msg"]=f"REMOVE ›› {c.emoji}{c.cat} 從餐盤移除"; gs["msg_type"]="info"
    gs["pending"]=None; advance(gs)

# ══════════════════════════════════════════════════════════════
#  CSS — 賽博龐克電競
# ══════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@400;600;700&display=swap');

:root{
  --bg0:#030712; --bg1:#0a0f1e; --bg2:#0d1529;
  --border:#1a2744; --dim:#1e2d50;
  --text:#c8d8f0; --muted:#4a6080;
}
*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Exo 2',sans-serif;color:var(--text)}
.stApp{background:var(--bg0)!important}
.stApp > .main > .block-container{padding-top:16px!important;max-width:1400px}

/* Scanline overlay */
.stApp::before{content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.12) 2px,rgba(0,0,0,.12) 4px);
  pointer-events:none;z-index:9999}

/* Title */
.cyber-title{font-family:'Orbitron',monospace;font-size:1.9rem;font-weight:900;
  text-align:center;letter-spacing:4px;text-transform:uppercase;
  background:linear-gradient(90deg,#00cfff,#00ff88,#ffe000,#ff3860,#bf94ff,#00cfff);
  background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  animation:neonShift 6s linear infinite;margin-bottom:0;line-height:1.1}
@keyframes neonShift{to{background-position:300% center}}
.cyber-sub{font-family:'Orbitron',monospace;font-size:.6rem;letter-spacing:6px;
  text-align:center;color:var(--muted);text-transform:uppercase;margin-top:4px}

/* HUD panels */
.hud-panel{background:var(--bg1);border:1px solid var(--border);
  border-radius:8px;padding:10px 14px;position:relative;overflow:hidden}
.hud-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--neon,#00cfff),transparent)}
.hud-label{font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:3px;
  color:var(--muted);text-transform:uppercase;margin-bottom:4px}
.hud-val{font-family:'Orbitron',monospace;font-size:1.6rem;font-weight:900;
  color:var(--neon,#00cfff);text-shadow:0 0 12px var(--neon,#00cfff)}

/* Message */
.msg-bar{font-family:'Orbitron',monospace;font-size:.75rem;letter-spacing:2px;
  padding:10px 16px;border-radius:6px;text-align:center;
  border-left:3px solid var(--neon,#00cfff);background:var(--bg2);
  animation:msgSlide .3s ease;text-transform:uppercase}
@keyframes msgSlide{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}

/* Ranking board */
.rank-board{background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:12px;overflow:hidden;position:relative}
.rank-board::after{content:'LIVE RANKING';position:absolute;top:8px;right:12px;
  font-family:'Orbitron',monospace;font-size:.5rem;letter-spacing:3px;color:var(--muted)}
.rank-row{display:flex;align-items:center;gap:10px;padding:7px 10px;
  border-radius:6px;margin-bottom:5px;border:1px solid transparent;
  transition:all .3s ease;font-size:.82rem;font-weight:700}
.rank-1st{border-color:#ffe000!important;background:linear-gradient(90deg,#ffe00010,transparent)!important;
  animation:rankPulse 2s ease infinite}
@keyframes rankPulse{0%,100%{box-shadow:0 0 0 #ffe000}50%{box-shadow:0 0 10px #ffe00066}}
.rank-num{font-family:'Orbitron',monospace;font-size:.7rem;width:22px;text-align:center}
.rank-name{flex:1;font-size:.85rem}
.rank-score{font-family:'Orbitron',monospace;font-size:1rem;font-weight:900}
.rank-bar-wrap{width:80px;height:6px;background:var(--dim);border-radius:3px;overflow:hidden}
.rank-bar{height:100%;border-radius:3px;transition:width .6s ease}

/* Cards */
.c-card{border-radius:10px;padding:10px 6px 8px;text-align:center;
  background:var(--bg2);border:1.5px solid var(--neon,#00cfff);
  box-shadow:0 0 8px var(--glow,#00cfff22);
  transition:transform .2s cubic-bezier(.34,1.56,.64,1),box-shadow .2s ease;
  cursor:pointer;position:relative;overflow:hidden}
.c-card::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
  background:linear-gradient(45deg,transparent 40%,rgba(255,255,255,.04) 50%,transparent 60%);
  animation:cardSheen 4s linear infinite}
@keyframes cardSheen{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.c-card:hover{transform:translateY(-10px) scale(1.06);
  box-shadow:0 0 20px var(--glow,#00cfff55),0 16px 32px rgba(0,0,0,.5)!important;z-index:20}
.c-card-sel{transform:translateY(-12px) scale(1.08)!important;
  box-shadow:0 0 28px var(--glow,#00cfff88),0 0 0 2px var(--neon,#00cfff)!important;
  border-color:var(--neon,#00cfff)!important}
.c-card-sel::after{content:'SEL';position:absolute;top:4px;right:5px;
  font-family:'Orbitron',monospace;font-size:.5rem;color:var(--neon,#00cfff);letter-spacing:1px}
.c-emoji{font-size:1.9rem;line-height:1;margin-bottom:3px}
.c-name{font-family:'Orbitron',monospace;font-size:.6rem;letter-spacing:1px;
  color:var(--neon,#00cfff);font-weight:700;margin-bottom:2px}
.c-desc{font-size:.6rem;color:var(--muted);font-weight:600}
.c-back{border-radius:10px;padding:14px 6px;text-align:center;
  background:linear-gradient(135deg,#0a0f1e,#1a2744);
  border:1.5px solid #1a2744;box-shadow:0 2px 8px rgba(0,0,0,.4);
  font-size:1.4rem;color:#1e3060}

/* Player header */
.p-header{font-family:'Orbitron',monospace;font-size:.72rem;letter-spacing:2px;
  padding:8px 12px;border-radius:6px 6px 0 0;font-weight:900;
  display:flex;align-items:center;gap:8px;text-transform:uppercase}
.p-active{animation:activeFlash 1.5s ease infinite}
@keyframes activeFlash{0%,100%{opacity:1}50%{opacity:.8}}

/* Plate zone */
.plate{background:var(--bg2);border:1px solid var(--border);
  border-radius:0 0 8px 8px;padding:8px;min-height:85px;
  transition:box-shadow .4s ease}
.plate-balanced{border-color:#00ff88!important;
  box-shadow:0 0 16px #00ff8833,inset 0 0 20px #00ff8808!important;
  animation:balanceGlow 2.5s ease infinite}
@keyframes balanceGlow{0%,100%{box-shadow:0 0 12px #00ff8833}50%{box-shadow:0 0 28px #00ff8866}}

/* Action buttons */
.stButton>button{font-family:'Orbitron',monospace!important;font-size:.65rem!important;
  letter-spacing:2px!important;text-transform:uppercase!important;
  border-radius:4px!important;transition:all .2s ease!important}
.stButton>button:hover{transform:translateY(-2px)!important;
  box-shadow:0 6px 20px rgba(0,200,255,.25)!important}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#0a1a3a,#0d2244)!important;
  border:1px solid #00cfff!important;color:#00cfff!important;
  box-shadow:0 0 10px #00cfff33!important}
.stButton>button[kind="primary"]:hover{
  box-shadow:0 0 20px #00cfff66,0 6px 20px rgba(0,0,0,.4)!important}

/* Event ticker */
.event-ticker{font-family:'Orbitron',monospace;font-size:.62rem;letter-spacing:2px;
  padding:5px 14px;border-radius:4px;margin-bottom:4px;
  background:var(--bg2);border-left:2px solid #ffe000;color:#ffe000;
  animation:tickIn .3s ease}
@keyframes tickIn{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:translateX(0)}}

/* Phase badge */
.phase-badge{font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:3px;
  padding:4px 10px;border-radius:3px;text-transform:uppercase;display:inline-block}

/* Section header */
.sec-head{font-family:'Orbitron',monospace;font-size:.65rem;letter-spacing:4px;
  color:var(--muted);text-transform:uppercase;padding:6px 0 4px;
  border-bottom:1px solid var(--border);margin-bottom:8px}

/* Balanced glow text */
.bal-tag{font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:2px;
  color:#00ff88;text-shadow:0 0 8px #00ff8888;animation:balanceGlow 2s ease infinite}

/* Target card for function selection */
.target-btn{background:var(--bg2);border:1px solid var(--border);border-radius:8px;
  padding:12px;text-align:center;font-weight:700;font-size:.82rem;transition:all .2s ease}

/* Streamlit overrides */
.stExpander{background:var(--bg1)!important;border:1px solid var(--border)!important;border-radius:8px!important}
div[data-testid="stHorizontalBlock"]{gap:10px}
.element-container{margin-bottom:0!important}
</style>
"""

MSG_CFG = {
    "info":    ("var(--neon,#00cfff)", "#00cfff"),
    "success": ("#00ff88","#00ff88"),
    "warning": ("#ffe000","#ffe000"),
    "error":   ("#ff3860","#ff3860"),
}

# ══════════════════════════════════════════════════════════════
#  HTML 元件
# ══════════════════════════════════════════════════════════════
def card_html(card: Card, selected=False, small=False):
    sel = "c-card-sel" if selected else ""
    sz = "1.4rem" if small else "1.9rem"
    img = (f'<img src="{card.img}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;margin-bottom:3px;">'
           if card.img and Path(card.img).exists()
           else f'<div class="c-emoji" style="font-size:{sz};">{card.emoji}</div>')
    nm_sz = ".55rem" if small else ".6rem"
    return f"""<div class="c-card {sel}" style="--neon:{card.neon};--glow:{card.glow};border-color:{card.neon}44;">
      {img}
      <div class="c-name" style="font-size:{nm_sz};color:{card.neon};">{card.cat}</div>
      <div class="c-desc">{card.desc}</div>
    </div>"""

def back_html():
    return '<div class="c-back">▪▪▪</div>'

def msg_bar_html(text, mtype="info"):
    neon = MSG_CFG[mtype][1]
    return f'<div class="msg-bar" style="border-color:{neon};color:{neon};">{text}</div>'

def hud_html(label, val, neon="#00cfff"):
    return f"""<div class="hud-panel" style="--neon:{neon}">
      <div class="hud-label">{label}</div>
      <div class="hud-val" style="color:{neon};text-shadow:0 0 12px {neon};">{val}</div>
    </div>"""

def rank_board_html(players, cur_idx):
    ranked = sorted(enumerate(players), key=lambda x: x[1].plate_score(), reverse=True)
    max_sc = max((p.plate_score() for p in players), default=1) or 1
    medals = ["◈","◇","△","○"]
    rows = ""
    for ri,(pi,p) in enumerate(ranked):
        sc = p.plate_score()
        pct = max(4, int(sc/max_sc*100)) if max_sc>0 else 4
        is1st = ri==0 and sc>0
        is_cur = pi==cur_idx
        active = "p-active" if is_cur else ""
        row_cls = "rank-1st" if is1st else ""
        skip_ico = "⛔" if p.skip_next else ""
        bal_ico  = '<span style="color:#00ff88;font-size:.7rem;">✦</span>' if p.is_balanced() else ""
        cur_ico  = "▶ " if is_cur else ""
        rows += f"""<div class="rank-row {row_cls} {active}" style="border-color:{p.neon}22;background:linear-gradient(90deg,{p.glow},transparent);">
          <span class="rank-num" style="color:{p.neon};">{medals[ri]}</span>
          <span class="rank-name" style="color:{p.neon};">{cur_ico}{p.name}{skip_ico}</span>
          {bal_ico}
          <div class="rank-bar-wrap"><div class="rank-bar" style="width:{pct}%;background:{p.neon};box-shadow:0 0 6px {p.glow};"></div></div>
          <span class="rank-score" style="color:{p.neon};text-shadow:0 0 8px {p.glow};">{sc}</span>
        </div>"""
    return f'<div class="rank-board">{rows}</div>'

# ══════════════════════════════════════════════════════════════
#  設定頁
# ══════════════════════════════════════════════════════════════
def page_setup():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="cyber-title">⬡ 最強糾察員</div>', unsafe_allow_html=True)
    st.markdown('<div class="cyber-sub">NUTRITION BATTLE CARD GAME ·· ESPORTS EDITION</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1.1, 1])
    with col_l:
        st.markdown('<div class="sec-head">PLAYER CONFIG</div>', unsafe_allow_html=True)
        num = st.slider("人數", 2, 4, 2, key="sn")
        names = []
        for i in range(num):
            default = ["PLAYER_01","PLAYER_02","PLAYER_03","PLAYER_04"][i]
            n = st.text_input(f"P{i+1}", value=default, key=f"pn{i}",
                              label_visibility="collapsed",
                              placeholder=f"玩家{i+1}名稱")
            names.append(n.strip() or f"P{i+1}")
        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            if st.button("▶  BATTLE START", use_container_width=True, type="primary"):
                if len(set(names))<len(names): st.error("名稱重複！"); return
                st.session_state.gs = init_game(names)
                st.session_state.sel = None; st.session_state.page = "game"; st.rerun()

    with col_r:
        st.markdown('<div class="sec-head">SCORING SYSTEM</div>', unsafe_allow_html=True)
        for cat, info in FOOD_CATS.items():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1a2744;font-size:.82rem;"><span>{info["emoji"]} {cat}</span><span style="color:{info["neon"]};font-family:Orbitron,monospace;font-weight:700;">+{info["pts"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="padding:6px 0;font-size:.8rem;color:#00ff88;">★ 均衡餐盤(蔬果+蛋白+澱粉) <b>+{BALANCED_BONUS}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="padding:2px 0;font-size:.8rem;color:#ff3860;">✕ 同類超過3張 <b>{IMBALANCE_PENALTY}</b></div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-head" style="margin-top:12px;">ABILITY CARDS</div>', unsafe_allow_html=True)
        for func, info in FUNC_CARDS.items():
            st.markdown(f'<div style="font-size:.75rem;padding:3px 0;color:{info["neon"]};">{info["emoji"]} <b>{func}</b> — {info["desc"]}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  遊戲主頁
# ══════════════════════════════════════════════════════════════
def page_game():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    players: List[Player] = gs["players"]
    ci = gs["turn"]; cur = players[ci]
    sel = st.session_state.get("sel", None)

    # ── 頂部 HUD ────────────────────────────────────────────
    h_cols = st.columns([2,1,1,1,1])
    with h_cols[0]:
        st.markdown(f'<div class="cyber-title" style="font-size:1.2rem;text-align:left;">⬡ 最強糾察員</div>', unsafe_allow_html=True)
        phase_color = "#00cfff" if gs["phase"]=="draw" else "#ffe000"
        phase_label = "DRAW PHASE" if gs["phase"]=="draw" else "ACTION PHASE"
        st.markdown(f'<div class="phase-badge" style="background:{phase_color}15;border:1px solid {phase_color};color:{phase_color};">{phase_label}</div>', unsafe_allow_html=True)
    with h_cols[1]: st.markdown(hud_html("DECK", len(gs["deck"]), "#00cfff"), unsafe_allow_html=True)
    with h_cols[2]: st.markdown(hud_html("ROUND", gs["round_count"], "#ffe000"), unsafe_allow_html=True)
    with h_cols[3]:
        top = gs["discard"][-1] if gs["discard"] else None
        val = f"{top.emoji}" if top else "—"
        st.markdown(hud_html("DISCARD", val, "#bf94ff"), unsafe_allow_html=True)
    with h_cols[4]:
        last_ico = "🔴" if gs["last_round"] else "🟢"
        st.markdown(hud_html("STATUS", last_ico, "#00ff88"), unsafe_allow_html=True)

    st.markdown(msg_bar_html(gs["msg"], gs["msg_type"]), unsafe_allow_html=True)

    # 事件ticker
    for ev in gs["events"]:
        st.markdown(f'<div class="event-ticker">{ev}</div>', unsafe_allow_html=True)
    gs["events"].clear()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 排名 + 餐盤 ─────────────────────────────────────────
    left_col, right_col = st.columns([1, 2.8])

    with left_col:
        st.markdown('<div class="sec-head">LIVE RANKING</div>', unsafe_allow_html=True)
        st.markdown(rank_board_html(players, ci), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">OPPONENT STATUS</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            if i == ci: continue
            bal_tag = '<span class="bal-tag">✦ BALANCED</span>' if p.is_balanced() else ""
            skip_tag = '<span style="color:#bf94ff;font-size:.65rem;font-family:Orbitron,monospace;">SUSPENDED</span>' if p.skip_next else ""
            st.markdown(f"""<div style="background:var(--bg2);border:1px solid {p.neon}33;border-radius:6px;padding:8px 10px;margin-bottom:6px;">
              <div style="color:{p.neon};font-family:Orbitron,monospace;font-size:.65rem;font-weight:700;display:flex;align-items:center;gap:6px;">{p.name} {bal_tag} {skip_tag}</div>
              <div style="font-size:.72rem;color:var(--muted);margin-top:3px;">手牌 {len(p.hand)} 張 ｜ 餐盤 {len(p.plate)}/{MAX_PLATE} ｜ {p.plate_score()} 分</div>
            </div>""", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="sec-head">BATTLE PLATES</div>', unsafe_allow_html=True)
        p_cols = st.columns(len(players))
        for pi, p in enumerate(players):
            with p_cols[pi]:
                is_cur = pi == ci
                hdr_bg = f"background:{p.neon}22;border-bottom:2px solid {p.neon};" if is_cur else f"background:{p.neon}0a;border-bottom:1px solid {p.neon}33;"
                active_cls = "p-active" if is_cur else ""
                bal_cls = "plate-balanced" if p.is_balanced() else ""
                st.markdown(f'<div class="p-header {active_cls}" style="{hdr_bg}color:{p.neon};border:1px solid {p.neon}33;border-radius:6px 6px 0 0;">{"▶ " if is_cur else ""}{p.name}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plate {bal_cls}">', unsafe_allow_html=True)
                if p.plate:
                    cc = st.columns(min(len(p.plate), 4))
                    for j, c in enumerate(p.plate):
                        with cc[j]: st.markdown(card_html(c, small=True), unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:center;color:#1e3060;padding:20px 0;font-family:Orbitron,monospace;font-size:.6rem;letter-spacing:2px;'>EMPTY</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if p.is_balanced():
                    st.markdown('<div class="bal-tag" style="text-align:center;display:block;font-size:.6rem;margin-top:3px;">✦ BALANCED +5</div>', unsafe_allow_html=True)

        # ── 當前玩家手牌 ──────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="sec-head" style="color:{cur.neon};">▶ {cur.name} — HAND</div>', unsafe_allow_html=True)

        # 對手牌背
        for i, p in enumerate(players):
            if i == ci: continue
            if p.hand:
                st.markdown(f'<div style="font-size:.6rem;font-family:Orbitron,monospace;color:{p.neon};letter-spacing:2px;margin-bottom:4px;">{p.name} 手牌背面</div>', unsafe_allow_html=True)
                bc = st.columns(min(len(p.hand), 5))
                for bc_col in bc: bc_col.markdown(back_html(), unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if cur.hand:
            hc = st.columns(min(len(cur.hand), 5))
            for i, card in enumerate(cur.hand):
                with hc[i]:
                    is_sel = (sel == i)
                    st.markdown(card_html(card, selected=is_sel), unsafe_allow_html=True)
                    btn_lbl = "[ SEL ]" if not is_sel else "[ ✓ OK ]"
                    if st.button(btn_lbl, key=f"hs{i}", use_container_width=True):
                        st.session_state.sel = i if not is_sel else None; st.rerun()
        else:
            st.markdown('<div style="color:var(--muted);font-family:Orbitron,monospace;font-size:.65rem;letter-spacing:2px;">NO CARDS</div>', unsafe_allow_html=True)

        sel_card = cur.hand[sel] if (sel is not None and sel < len(cur.hand)) else None
        if sel_card:
            st.markdown(f'<div style="background:{sel_card.glow};border:1px solid {sel_card.neon};border-radius:6px;padding:7px 12px;font-family:Orbitron,monospace;font-size:.62rem;letter-spacing:1px;color:{sel_card.neon};text-align:center;margin-top:4px;">{sel_card.emoji} {sel_card.cat} ›› {sel_card.desc}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 行動區 ───────────────────────────────────────────────
    pending = gs.get("pending")

    if pending == "偷1張":
        st.markdown('<div class="sec-head" style="color:#ff3860;">⦿ SELECT STEAL TARGET</div>', unsafe_allow_html=True)
        targets = [(i,p) for i,p in enumerate(players) if i!=ci and p.hand]
        if targets:
            tc = st.columns(len(targets))
            for idx,(ti,tp) in enumerate(targets):
                with tc[idx]:
                    st.markdown(f'<div style="background:{tp.glow};border:1px solid {tp.neon};border-radius:8px;padding:10px;text-align:center;"><div style="color:{tp.neon};font-family:Orbitron,monospace;font-size:.65rem;font-weight:700;">{tp.name}</div><div style="color:var(--muted);font-size:.72rem;">手牌 {len(tp.hand)} 張</div></div>', unsafe_allow_html=True)
                    if st.button(f"STEAL {tp.name}", key=f"st{ti}", use_container_width=True, type="primary"):
                        resolve_steal(gs, ti); st.rerun()
        else:
            st.warning("所有對手手牌為空")
            if st.button("SKIP"): gs["pending"]=None; advance(gs); st.rerun()

    elif pending == "暫停":
        st.markdown('<div class="sec-head" style="color:#bf94ff;">⦿ SELECT SUSPEND TARGET</div>', unsafe_allow_html=True)
        targets = [(i,p) for i,p in enumerate(players) if i!=ci]
        tc = st.columns(len(targets))
        for idx,(ti,tp) in enumerate(targets):
            with tc[idx]:
                st.markdown(f'<div style="background:{tp.glow};border:1px solid {tp.neon};border-radius:8px;padding:10px;text-align:center;"><div style="color:{tp.neon};font-family:Orbitron,monospace;font-size:.65rem;font-weight:700;">{tp.name}{"  ⛔" if tp.skip_next else ""}</div><div style="color:var(--muted);font-size:.72rem;">{tp.plate_score()} 分</div></div>', unsafe_allow_html=True)
                if st.button(f"SUSPEND {tp.name}", key=f"pa{ti}", use_container_width=True, type="primary"):
                    resolve_pause(gs, ti); st.rerun()

    elif pending == "丟1張":
        st.markdown('<div class="sec-head" style="color:#ff6b00;">⦿ SELECT CARD TO REMOVE FROM PLATE</div>', unsafe_allow_html=True)
        if cur.plate:
            rc = st.columns(len(cur.plate))
            for j,c in enumerate(cur.plate):
                with rc[j]:
                    st.markdown(card_html(c, small=True), unsafe_allow_html=True)
                    if st.button("REMOVE", key=f"rp{j}", use_container_width=True):
                        resolve_remove(gs, j); st.rerun()
        else:
            st.info("餐盤為空"); 
            if st.button("CANCEL"): gs["pending"]=None; st.rerun()

    else:
        phase = gs["phase"]
        if phase == "draw":
            c1,c2,c3 = st.columns([1,2,1])
            with c2:
                if st.button("◈  DRAW CARD", use_container_width=True, type="primary"):
                    do_draw(gs); st.rerun()
        elif phase == "action":
            can_place   = sel_card and sel_card.kind=="food" and len(cur.plate)<MAX_PLATE
            can_func    = sel_card and sel_card.kind=="func"
            can_discard = sel_card is not None
            ac = st.columns(3)
            with ac[0]:
                if st.button("▶  PLACE ON PLATE", disabled=not can_place, use_container_width=True, type="primary"):
                    do_place(gs, sel); st.rerun()
            with ac[1]:
                if st.button("✦  USE ABILITY", disabled=not can_func, use_container_width=True, type="primary"):
                    do_func(gs, sel); st.rerun()
            with ac[2]:
                if st.button("✕  DISCARD", disabled=not can_discard, use_container_width=True, type="primary"):
                    do_discard(gs, sel); st.rerun()
            if not sel_card:
                st.markdown(msg_bar_html("SELECT A CARD FROM YOUR HAND FIRST", "info"), unsafe_allow_html=True)

    if gs["last_round"]:
        st.markdown(f'<div class="event-ticker" style="border-color:#ff3860;color:#ff3860;text-align:center;font-size:.7rem;">⚡ FINAL ROUND — LAST CHANCE TO FIGHT BACK ⚡</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩ QUIT", key="quit_btn"):
        st.session_state.page="setup"
        if "gs" in st.session_state: del st.session_state.gs
        st.rerun()

# ══════════════════════════════════════════════════════════════
#  結果頁
# ══════════════════════════════════════════════════════════════
def page_result():
    st.markdown(CSS, unsafe_allow_html=True)
    gs = st.session_state.gs
    players: List[Player] = gs["players"]
    for p in players: p.score = p.plate_score()
    ranked = sorted(players, key=lambda p: p.score, reverse=True)
    winner = ranked[0]

    st.markdown('<div class="cyber-title">◈ GAME OVER</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-family:Orbitron,monospace;font-size:1.2rem;font-weight:900;color:{winner.neon};text-shadow:0 0 20px {winner.glow};letter-spacing:4px;margin:10px 0;">★ {winner.name} WINS ★</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-family:Orbitron,monospace;font-size:2.5rem;font-weight:900;color:{winner.neon};text-shadow:0 0 30px {winner.neon};">{winner.score} <span style="font-size:1rem;">PTS</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    medals = ["◈ 1ST","◇ 2ND","△ 3RD","○ 4TH"]
    for ri, p in enumerate(ranked):
        cats = {}
        for c in p.plate: cats[c.cat] = cats.get(c.cat,0)+1
        raw = sum(c.pts for c in p.plate)
        bal_b = BALANCED_BONUS if p.is_balanced() else 0
        imbal = sum(IMBALANCE_PENALTY for cat,cnt in cats.items() if cnt>3)
        plate_disp = " ".join(f"{c.emoji}" for c in p.plate) or "─"
        with st.expander(f"{medals[ri]}  {p.name}  ─  {p.score} PTS", expanded=(ri==0)):
            dc1,dc2 = st.columns([2,1])
            with dc1:
                st.markdown(f'<div style="font-family:Orbitron,monospace;font-size:.65rem;color:var(--muted);letter-spacing:2px;">PLATE CONTENTS</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:1.4rem;margin:4px 0;">{plate_disp}</div>', unsafe_allow_html=True)
                if bal_b: st.markdown(f'<div style="color:#00ff88;font-size:.8rem;">✦ BALANCED BONUS +{bal_b}</div>', unsafe_allow_html=True)
                if imbal: st.markdown(f'<div style="color:#ff3860;font-size:.8rem;">✕ IMBALANCE PENALTY {imbal}</div>', unsafe_allow_html=True)
            with dc2:
                st.markdown(f"""<div style="background:{p.glow};border:1px solid {p.neon};border-radius:8px;padding:14px;text-align:center;">
                  <div style="font-family:Orbitron,monospace;font-size:.55rem;color:var(--muted);letter-spacing:2px;">BASE</div>
                  <div style="font-size:1.2rem;font-weight:900;color:{p.neon};">{raw}</div>
                  <div style="font-size:.65rem;color:var(--muted);">{"＋"+str(bal_b) if bal_b else "─"} / {imbal if imbal else "─"}</div>
                  <div style="font-family:Orbitron,monospace;font-size:1.4rem;font-weight:900;color:{p.neon};text-shadow:0 0 10px {p.neon};margin-top:4px;">{p.score}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        if st.button("▶  REMATCH", use_container_width=True, type="primary"):
            st.session_state.page="setup"
            if "gs" in st.session_state: del st.session_state.gs
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════════
def main():
    st.set_page_config(page_title="最強糾察員 | ESPORTS", page_icon="⬡",
                       layout="wide", initial_sidebar_state="collapsed")
    if "page" not in st.session_state: st.session_state.page = "setup"
    if "sel"  not in st.session_state: st.session_state.sel  = None
    gs = st.session_state.get("gs")
    if   st.session_state.page == "setup": page_setup()
    elif gs and gs.get("over"):            page_result()
    else:                                  page_game()

if __name__ == "__main__":
    main()
