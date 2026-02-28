# 🥗 最強糾察員 — 健康飲食卡牌遊戲

## 快速啟動

```bash
pip install streamlit
streamlit run app.py
```

## 專案結構

```
food_inspector_game/
├── app.py              # 主程式（所有遊戲邏輯 + UI）
├── requirements.txt
├── README.md
└── images/             # 未來放卡牌圖檔（可選）
    ├── veg_1.jpg       # 蔬菜水果卡
    ├── protein_1.jpg   # 蛋白質卡
    └── ...
```

## 加入卡牌圖檔（未來擴充）

在 `app.py` 的 `build_deck()` 中，為每張 Card 指定 `image_path`：

```python
Card("food", "蔬菜水果", cid, image_path="images/veg_1.jpg")
```

Card 類別會自動優先顯示圖片，若圖片不存在則退回 emoji 顯示。

## 部署到 Streamlit Cloud

1. 推送到 GitHub
2. 前往 https://share.streamlit.io
3. 選擇 repo → `app.py` → Deploy

## 遊戲規則

| 類別 | 分數 |
|------|------|
| 蔬菜水果 | +5 |
| 蛋白質 | +4 |
| 澱粉 | +3 |
| 乳品 | +2 |
| 油炸與點心 | +1 |
| 均衡餐盤(蔬果+蛋白+澱粉) | 額外+10 |
| 超過3張同類 | -10 |

### 功能牌
- 抽牌+2：立即再抽2張
- 偷1張：從任意玩家手牌偷1張
- 丟1張：將自己餐盤中1張移至棄牌區
- 順時針交換手牌：所有玩家手牌輪轉
- 暫停：指定玩家跳過下回合

### 結束條件
- 抽牌堆抽完
- 玩家湊齊均衡餐盤後，全桌最後一輪
