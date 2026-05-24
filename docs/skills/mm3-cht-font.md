---
name: mm3-cht-font
description: 接續 1991 SSI/NWC 魔法門 III 幻島歷險記 (Might and Magic III) 繁體中文版的字型修改 / RE 工作。當使用者提到 MM3、魔法門 III、mm3b.exe、cfonts.grp、mm3.cc、CFONTS.GRP、BIG5 字型、16x15 glyph、rewolf LZHUF、字型 BLIT/lookup、瘦金體/MingLiU/標楷體中文化、或想調整字型粗細/筆畫/大小時觸發。也涵蓋類似 1991 年代 DOS PE 16-bit overlay 字型 hex patch（特別是 LZHUF 壓縮 + 加密 header 格式 / dispatch table 字型函式 / BIG5 dense lookup）。當使用者要還原原版、切換 thick/thin 字型、加大字身、修 dialog line spacing、或匯出新版 mm3.cc 也要主動套用此 skill。
---

# MM3 繁體中文字型修改 Skill

接續魔法門 III (MM3) 繁體中文版字型 reverse engineering 與修改工作。**先讀 `references/` 內檔案**理解全貌再動手 — 直接動手會踩到我們踩過的雷。

## 專案路徑

```
D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\
├── mm3c\                              ← 主要工作目錄
│   ├── mm3b.exe (278KB, 16-bit DOS MZ) ← 遊戲主執行檔
│   ├── mm3.cc (3.4MB)                  ← LZHUF + header-XOR 加密的 overlay archive
│   ├── mm3.cc.bak                       ← 原版備份
│   ├── cfonts.grp (174394 bytes)        ← 字模檔，5813 個 30-byte glyph
│   ├── cfonts.grp.bak                   ← 原版備份
│   ├── out_cc_dump\                     ← rewolf dumper 解出來的 560 個檔
│   │   └── _UNKNOWN_FILE_8F99.BIN (22202 bytes)  ← 字型 code overlay
│   ├── bulk_thick_15.py                 ← render cfonts.grp 厚體版
│   ├── bulk_thin_15.py                  ← render cfonts.grp 細體版（user 偏好）
│   ├── inject_overlay_v2.py             ← patch + 重壓 + inject 進 mm3.cc
│   ├── lzhuf_compress.py / decompress.py ← rewolf LZHUF 演算法 Python port
│   ├── launch_and_shot.py               ← DOSBox 自動截圖
│   └── (其他 RE 工具)
└── 魔法門3中文版.bat
```

## 三層架構

**Level 1 — cfonts.grp 字模**：5813 個 16×15 BE16 bitmap glyph，每 glyph 30 bytes
- idx 0-407 = 符號 / 數字 / 拉丁 / 希臘 / 注音 / Roman
- idx 408+ = hanzi，從 BIG5 A4 40 (一) 起 dense 排列

**Level 2 — mm3.cc overlay archive**：LZHUF 壓縮 + 加密 header 的 archive，包 560 個資源檔。其中 `_UNKNOWN_FILE_8F99.BIN` 是字型 code overlay。

**Level 3 — overlay 0x8F99**：22202 bytes 的 16-bit DOS code，含字型 BLIT / LOOKUP / OPEN 函式。我們的 1-byte patch 在這個 overlay 內。

## 三條常用工作流

### A. 換字型樣式（最常用）

```powershell
cd "D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"

# 細款（使用者偏好）— MingLiU size 11 直接 render top-aligned
py bulk_thin_15.py mingliu 11 t128 top

# 中等細
py bulk_thin_15.py mingliu 13 t128 top

# 厚體（粗）— MingLiU size 28 OR-downsample
py bulk_thick_15.py 28 160

# 細楷書（試過太破碎，不建議）
py bulk_thin_15.py kaiti 14 t128 center
```

只動 cfonts.grp，mm3.cc 維持已 patch 的版本（render 15 rows 的 BLIT）。

### B. 還原原版

```powershell
copy /Y mm3.cc.bak mm3.cc
copy /Y cfonts.grp.bak cfonts.grp
```

### C. 重做 mm3.cc patch（極少需要）

當 BLIT row count 或其他 overlay 內容要再改時：

```powershell
# 1. 修改 out_cc_dump\_UNKNOWN_FILE_8F99.BIN
# 2. 重 inject 進 mm3.cc
py inject_overlay_v2.py
# 3. 重 render cfonts.grp 配合新 BLIT
py bulk_thin_15.py mingliu 11 t128 top
```

## 關鍵 RE 知識（為什麼這樣做）

### BIG5 → idx 公式（已 marker test 100% 驗證）
```python
idx = 408 + (hi - 0xA4) * 157 + offset(lo)
offset(lo) = (lo - 0x40)       if 0x40 <= lo <= 0x7E
           = 63 + (lo - 0xA1)  if 0xA1 <= lo <= 0xFE
```

例：戲 (BIG5 C0B8) → idx 4890；舊 (C2C2) → 5214；魔 (C55D) → 5618。

**之前 memory 紀錄的 `idx_base=110` 是錯的**，正確 `408`。一/二/大/日 在低 idx 110-245 區看到的「形狀像」只是巧合（那邊其實是 Roman Ⅰ-Ⅹ / 數字 / 拉丁字母區）。

### 我們做過的關鍵 patch
**overlay file offset 0x1DFA**: `08` → `0F` (`mov bx, 8` → `mov bx, 15`)

這 1 byte 把 BLIT 從畫 8 rows 改成畫 15 rows。再把 cfonts.grp 從 8-row top-aligned 重 render 成滿 15-row 內容。

### 為什麼某些東西改不動
- **主選單按鈕（開始新遊戲 / 載入舊進度 / 備忘錄 / 立體造形 / 必須返回）是 baked image**（在 mm3.cc 內的 .icn 圖檔），改 cfonts.grp 永遠不會影響它們
- **dialog line spacing（行距）** 目前沒找到單一常數可改 — `cmp al, 0Ah` 7 處全是檔案 I/O / 日期 check。Game 可能用 `\x0B`xxx escape code 在每串硬編碼 Y 位置
- **行距導致多行字會 overlap** — 使用 size 11 細款後 overlap 比 size 28 厚體小很多但仍可見

## 詳細 reference

- `references/overlay_internals.md` — overlay 0x8F99 完整反組譯結果（OPEN/LOOKUP/BLIT 位置與構造）
- `references/cc_format.md` — mm3.cc 檔頭加密 + LZHUF 壓縮細節 + filename hash
- `references/workflow.md` — 從零開始的完整步驟（含環境裝設）

## 雷區（避免重蹈覆轍）

1. **memory 舊紀錄說 idx_base=110 是錯的**，正確 408 — 不要相信舊資料
2. **interactive_swap.py GUI 用 hamming match** — 不可靠，user 的 manual_swaps.tsv 147 個 idx 大多錯位（雖然湊巧戲/舊等對到），bulk render 才是正解
3. **mm3.cc 不能用 uncompressed entry 注入** — 雖然 dumper 認，mm3b loader 不認，必須真實 LZHUF compress
4. **rewolf 2016 build mm3_cc_dumper.exe 需 MSVCR110D.dll**（debug runtime）— 一般 Windows 跑不起來；用我們 port 的 Python 版（`lzhuf_compress.py` + `inject_overlay_v2.py`）
5. **cfonts.grp 寫滿 15 rows + 原 BLIT (8 rows) = 多行字疊到下一行**（user 看到過破碎），G2 patch 解之
6. **DOSBox 截圖用 surface 後端**（mm3c_capture.conf）— ddraw 後端 PrintWindow 抓不到（純黑）
7. **render 用標楷體 size 12-14 在 16×15 cell 會缺筆破碎**（過細不可讀），MingLiU 至 size 11 是 sweet spot

## 補充 RE 待辦（若 user 要求繼續深挖）

- **找 dialog line spacing 真正位置** — 可能在 mm3.cc 內其他 overlay 或用 DOSBox-X heavy debugger 動態 trace
- **加大 cell 到 16×16**（G3 目標）— 改 glyph size 30→32 bytes、line stride、blit row count 多處同步
- **DOSBox-X 路徑**: `C:\Users\原來是個胖仔\AppData\Local\dosbox-x\mingw-build\mingw\dosbox-x.exe`（heavy debugger 內建，已下載）

## 引用資源

- rewolf 原始 dumper repo: https://github.com/rwfpl/rewolf-mm3-dumper
- rewolf blog: https://blog.rewolf.pl/blog/?p=1202（SSL 失敗，但 source code 已 clone 在 `C:\Users\原來是個胖仔\AppData\Local\Temp\mm3-dumper\`）
- 之前 memory 紀錄: `project_mm3_mm4_font.md`, `project_mm3_wip.md`, `project_mm3_re_font.md`
