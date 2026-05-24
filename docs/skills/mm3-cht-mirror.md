---
name: mm3-cht-mirror
description: 接續 1991 SSI/NWC 魔法門 III 幻島歷險記 (Might and Magic III) 繁體中文版的「傳送鏡 / 代號 / 祕密區」reverse engineering 與 patch 工作。當使用者提到 MM3 mirror、傳送鏡、codeword、代號、祕密區、家園/海狗/自由人/命運/火熱/火/水/土/風/最後倒數昇空/大膽混進龍穴/偷拿究力神珠、LOC 0x69、SAVE0X.MM3 改存檔、傳送到特定地圖座標、競技場 200 局、改 mirror 接受新字串、想新增/重定向傳送鏡密碼、想在 mirror 加 cheat 入口時觸發。**與 mm3-cht-font skill 互補（那個只管字型）**，本 skill 管 mirror codeword 表、save file party position、mm3.cc 內 mirror 相關文字資源。也涵蓋同類 1991 年 DOS PE 16-bit MZ 內隱性 data table RE 技巧（pointer table redirect、parallel byte arrays、無 IDA 用 byte-pattern + 黑箱探針確認 table 位置）。
---

# MM3 繁體中文 Mirror / 傳送鏡 Patch Skill

接續魔法門 III (MM3) 繁體中文版「傳送鏡 (Mirror of Worlds)」reverse engineering 與 patch 工作。
**先讀本檔再動手** — 我們有把不容易找到的 data table 都標出來了，亂改會踩到 slot 6 ending trigger 等地雷。

## 專案路徑

```
D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\
├── mm3c\                              ← 主要工作目錄
│   ├── mm3b.exe (278KB, MZ DOS)        ← 遊戲主執行檔（mirror code 表都在這）
│   ├── mm3b.exe.bak                    ← 第一次 patch 自動建的備份
│   ├── mm3.cc (3.4MB)                  ← LZHUF + header-XOR 加密的 overlay archive
│   ├── SAVE00.MM3 ... SAVE09.MM3       ← 存檔 (207551 bytes，前 ~108KB 是 plain)
│   ├── out_cc_dump\                    ← mm3.cc 解壓出的 560 個 resource
│   │   ├── _UNKNOWN_FILE_ABDB.BIN      ← interactive object 字串表（mirror prompt 在這）
│   │   └── text01.maz ... text64.maz   ← 各地圖文字資料
│   ├── mm3_mirror_patch.py             ← 改 LOC/X/Y 主工具（任 codeword 任目的地）
│   ├── mm3_goto.py                     ← 改存檔 party 位置（mirror 之外的後備方案）
│   ├── mm3_add_mimi.py                 ← 改 string 為「祕密區」一鍵 patch（範本）
│   ├── patch_codeword_string.py        ← pointer redirect（重指 string 到別處）
│   ├── verify_codewords.py             ← dump 13 codeword 真實 ptr→string + LOC/X/Y
│   └── (各種 hunt_*.py / inspect_*.py RE 腳本)
└── 魔法門3中文版.bat                    ← 用 dosbox_debug.exe 跑
```

## 關鍵 data table 位置（全部驗證過）

`mm3b.exe` 內：

| 名稱 | file offset | 大小 | 內容 |
|---|---|---|---|
| Codeword pointer table | `0x1E608` | 13 × 2 byte | 13 個 mirror 代號的 string pointer |
| LOC table | `0x1B874` | 13 byte | 各代號傳送的目的地 LOC code |
| X table | `0x1B881` | 13 byte | 各代號傳送的 X 座標（town LOCs 為 0 時用地圖預設入口）|
| Y table | `0x1B88E` | 13 byte | 各代號傳送的 Y 座標 |
| Display name table | `0x1F64C` | 67 個 null-separated BIG5 | HUD 顯示「目前位置」用，跟 mirror 表不同 |
| `祕密區` 字串（既有） | `0x1F811` | 7 byte | `AF A6 B1 4B B0 CF 00` (祕用礻 radical) |
| Mirror input prompt | `out_cc_dump/_UNKNOWN_FILE_ABDB.BIN @ 0xE0` | — | `鍵入你的目的地。` |

**Codeword pointer 計算**：DS para `0x1831` → file offset = `0xE00 + 0x18310 + ptr_value`

## 13 個 codeword 完整清單（原版）

| idx | string | LOC | X | Y | 目的地 | 備註 |
|---|---|---|---|---|---|---|
| 0 | 家園 | `0x01` | 0 | 0 | 泉頂鎮 | town（X/Y 用地圖預設）|
| 1 | 海狗 | `0x02` | 0 | 0 | 望海鎮 | town |
| 2 | 自由人 | `0x03` | 0 | 0 | 荒原鎮 | town |
| 3 | 命運 | `0x04` | 0 | 0 | 沼澤鎮 | town |
| 4 | 火熱 | `0x05` | 0 | 0 | 火峰鎮 | town |
| 5 | 競技場 | `0x6A` | 0 | 0 | 競技場 | 可能有 hardcoded check（200 局謠言？）|
| **6** | **最後倒數昇空** | **`0x69`** | 0 | 0 | **過關 cutscene** | **⚠ Hardcoded ending trigger 綁 slot 6，不能改用** |
| 7 | 火 | `0x32` | 0x0C | 0 | 火焰島 (F1) | safe to repurpose |
| 8 | 水 | `0x3B` | 7 | 0x0A | 死亡沼澤 | safe |
| 9 | 土 | `0x3C` | 3 | 3 | 孤獨沙漠 | safe |
| 10 | 風 | `0x3D` | 0 | 0x0C | 寒冰島 | safe（已驗證 patch 走全 LOC/X/Y）|
| 11 | 大膽混進龍穴 | `0x0E` | 7 | 0x0A | 龍穴 | safe |
| 12 | 偷拿究力神珠 | `0x25` | 0x0E | 7 | 金字塔密室 | safe |

## 祕密區秘密

- **「祕密區」= LOC `0x69`** （不在原 codeword 目的地中）
- LOC 0x69 的 default entry 顯示為 **F1**（不是「祕密區」）
- 「祕密區」HUD label 只在特定 cell 顯示（已驗證 X=3 Y=14, X=4 Y=5 都顯示「祕密區」）
- 寶藏堆（黃金、王座、黑曜石裝備）在 LOC 0x69 X=3 Y=14
- SAVE00.MM3 就在 LOC 0x69 X=4 Y=5（user 2007 年自己存的）
- 原本只能用 GameMaster 改記憶體進入；現在可用 mirror codeword（patch 後）

## SAVE 檔 party position（plain region）

| file offset | 欄位 | 範圍 |
|---|---|---|
| `0x2B2E` | X | 0-15 |
| `0x2B2F` | Y | 0-15 |
| `0x2B30` | LOC | 0x01..0x42 + 0x69, 0x6A |

存檔前 ~108KB 是 plain data，後面才壓縮/加密。這 3 個 byte 直接改不需處理壓縮。

## 三條常用工作流

### A. 加新 mirror 代號（重定向既有 codeword）

最常用情境：把不重要的 codeword (例如「火」) 變成你想要的入口（「祕密區」）。

```powershell
cd "D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"

# Step 1: 改 LOC/X/Y（讓「火」傳送到 LOC 0x69 X=3 Y=14）
py mm3_mirror_patch.py --target 火 --x 3 --y 14

# Step 2: 把 slot 7 的 pointer 重指向既存的「祕密區」字串
py patch_codeword_string.py

# Step 3: 確認結果
py verify_codewords.py

# 應該看到 slot 7: ptr=0x6701 '祕密區' LOC=0x69 X=3 Y=14
```

完全關 DOSBox 重啟，輸入「祕密區」即傳送。**Side-effect**: 「火」codeword 失效。

### B. 把任意存檔傳送到任意位置

不動 mm3b.exe，純改 SAVE 檔（最安全）：

```powershell
# 預設進祕密區
py mm3_goto.py SAVE05.MM3

# 列出所有命名地點
py mm3_goto.py --list

# 指定座標
py mm3_goto.py SAVE05.MM3 --x 4 --y 5 --loc 0x69
py mm3_goto.py SAVE05.MM3 --name "龍穴" --x 7 --y 7
```

第一次執行自動產 `SAVE0X.MM3.bak`，可隨時還原。

### C. 還原 mm3b.exe

```powershell
py mm3_mirror_patch.py --revert
# 或
copy /Y mm3b.exe.bak mm3b.exe
```

## 關鍵 RE 知識（為什麼這樣做）

### 為什麼 slot 6 不能改

「最後倒數昇空」(idx 6, LOC 0x69) 觸發 ending cutscene。Trigger **綁在 slot index 6，不是綁在 string 內容也不是綁在 LOC 0x69**。實驗確認：
- slot 6 換字串為「祕密區」+ X=3 Y=14 → 還是放 ending
- slot 10 (風) 改 LOC=0x69 X=3 Y=14 → 正常進祕密區自由探索

所以要加新代號**一定要選 slot ≠ 6**。

### 為什麼 town codeword (slot 0-4) X/Y=0

家園/海狗/自由人/命運/火熱 的 X/Y 都是 0。實驗確認 typing 家園 → 泉頂鎮會落在 (X=2, Y=5) 預設入口，**不是** (0,0)。代表 town LOC 的 entry 點由 map data 決定，handler 看到 X=0 Y=0 就用 map default。

非 town LOC（火/水/土/風/龍穴/pyramid）的 X/Y 才會被尊重。**祕密區 LOC 0x69 也屬於非 town，X/Y 直接用 table 值**。

### Codeword handler code 找不到（已知限制）

我們花大量時間搜過 mm3b.exe 與 overlays：
- LOC 表的 read 只找到 1 處 (`0x7A02: mov al, [bx+0x3124]`)，那個 function 不像 mirror handler
- **X/Y 表的 read 完全找不到** — 用 `mov al, [bx+disp16]` 各種 ModR/M 變體都搜過
- count 13 在 mm3b.exe 沒有 `mov [imm], 13` 或 `cmp ?, 13` 對應到 mirror loop
- handler 大概在 mm3.cc 內某個 overlay，**用 LES + far ptr indirect** 讀表

結論：**沒 IDA / DOSBox-X heavy debugger 找不到 handler**。但**改 table byte 確定有效**（user 三次驗證），所以可以放心做 table-level patch；只是**沒辦法擴大 13 → 14 個 codeword**（要改 count，但 count 變數位置未明）。

### 已驗證有效的 patch 機制

1. **LOC byte patch** (1 byte at `0x1B874+idx`) → 改變代號目的地
2. **X/Y byte patch** (1 byte at `0x1B881+idx` / `0x1B88E+idx`) → 改變座標
3. **String overwrite** (寫到字串原位置) → 改 codeword 接受的字串（要長度 ≤ 原長度 + null padding）
4. **Pointer redirect** (2 byte at `0x1E608+idx*2`) → 把 codeword 字串指向別處（不用動原字串）

機制 4 最乾淨，因為不破壞既有字串資料。

### BIG5 字元注意：祕 vs 秘

| 字 | 部首 | BIG5 | 用途 |
|---|---|---|---|
| 祕 | 礻 (示) | `AF A6` | 遊戲內顯示用的字 |
| 秘 | 禾 | `AF B5` | 一般 IME 預設輸出的字 |

**遊戲只接受 `AF A6` (礻)**，IME 出 `AF B5` (禾) 就比對不到。Patch 寫字串時務必用 `AF A6`。IME 打字「ㄇㄧˋ」時可能要切到備選字。

## mm3.cc 內 mirror 相關資源

### Mirror prompt 字串

- **`鍵入你的目的地。`** 在 `_UNKNOWN_FILE_ABDB.BIN @ 0xE0`
- ABDB.BIN 是 interactive object 字串表，含寶藏 / 拉桿 / 巫師 / 開發者 credits 等

### 各地圖的 mirror intro

- `銀樣的玻璃上映出湖般的搖曳影像。說出你的目的地，可以到達。`
- 在 `text01.maz`, `text02.maz`, `text03.maz`, `text04.maz`, `text05.maz`, `text08.maz`, `text12.maz`, `text44.maz` 等
- 同一段文字在多個 map 重複（每個有 mirror 的地圖各放一份）

### 修改流程（如要重寫 mirror intro 或 prompt）

ABDB 跟 text*.maz 都是 mm3.cc 內 resource。要改：
1. 從 mm3.cc 抽出（已 dumped 到 `out_cc_dump/`）
2. 編輯該 .BIN 或 .maz
3. 重 inject 進 mm3.cc（參考 mm3-cht-font 的 `inject_overlay_v2.py`，邏輯一樣，只是換 resource ID）

⚠ 字串長度若改變要小心：可能影響後續 offset。**最安全是替換等長字串**或**改 pointer 重指向新位置**（同 codeword pointer redirect 技巧）。

## 雷區（避免重蹈覆轍）

1. **slot 6 (最後倒數昇空) 不能 repurpose** — hardcoded ending trigger，任何改都會放 cutscene
2. **祕 (AF A6) ≠ 秘 (AF B5)** — patch 字串時搞錯 byte 玩家輸入就比對不到
3. **DOSBox cache exe** — 改完 mm3b.exe 必須**完全關閉 DOSBox 整個 process** 再開，否則跑舊版
4. **table 位置不是任何 code 直接 ref 找得到** — 是 LES + far ptr indirect，hex search 找不到 disp16 = 0x3124（除了那 1 處非 mirror 的 caller）
5. **count 13 在 mm3b.exe 沒 immediate** — `mov [imm], 13` 三處全是別 function，**真正 mirror loop 的 count 來源未知**，**所以不能擴大到 14 個 codeword**
6. **town codeword X/Y 設了沒用** — handler 看 X=0 Y=0 就讓 map decide entry point；要設定座標必須改 LOC 為非 town（如 0x69）
7. **dump 工具的 codeword 名稱是寫死的** — `mm3_mirror_patch.py --dump` 顯示「火」永遠是「火」，要看實際 patch 後的 string 用 `verify_codewords.py`
8. **DOSBox-X debugger 比 SVN-Daum 強很多** — 但 user setup 卡住沒做出來；若要動態 trace 改用 DOSBox-X heavy debugger

## 競技場 200 局謠言（待調查）

User 提到「競技場不是打滿 200 局會有驚喜」。`競技場` codeword (slot 5, LOC `0x6A`) 進入。
- 可能 hardcoded 在 `0x6A` 路徑（類似 slot 6 ending trigger）
- 也可能在 arena 戰鬥內部累計 counter，達 200 (0xC8) 觸發
- mm3b.exe 與 overlays 內搜 `0xC8` immediate、`cmp ?, 0xC8` / `cmp ?, 200` 找 trigger
- 另一可能：counter 在 SAVE 檔某 offset，比較不同戰況的 save 找

優先用 dynamic debugger 或記憶體 diff 比賽前/賽後找 counter 位置，再反查 trigger code。

## 可重用工具速查

| 工具 | 一句話 |
|---|---|
| `mm3_mirror_patch.py` | 改任一 codeword 的 LOC/X/Y（不動 string）|
| `mm3_goto.py` | 改存檔 X/Y/LOC，不動 exe |
| `patch_codeword_string.py` | 重指 slot 7 pointer 到 0x6701 (祕密區)|
| `verify_codewords.py` | 列出 13 codeword 的真實 ptr→string + LOC/X/Y |
| `mm3_add_mimi.py` | 改 slot 12 為「祕密區」(範本，可改) |
| `hunt_mirror_v*.py` / `hunt_handler_*.py` | RE 探索腳本（保留作歷史紀錄）|

## 引用資源

- `D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c\MM3_MIRROR_FORMAT.md` — 早期 RE 紀錄
- `D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3-secret.md` — user 2007 年的 GameMaster 修改心得
- memory: `project_mm3_mirror.md` — 之前對話的 memory 摘要
- 互補 skill: **mm3-cht-font** — 只處理 cfonts.grp / BLIT / overlay 0x8F99 字型部分，不涵蓋 mirror code 表
