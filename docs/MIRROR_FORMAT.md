# MM3 (CHT) 傳送鏡 / 祕密區 修改筆記

> 元碁科技 1992 繁體中文版《魔法門 III 幻島歷險記》 — 傳送鏡 (Mirror of
> Worlds) 代號表與「祕密區」(LOC 0x69) 完整 RE 紀錄。

對應的 GitHub issue / 動機：見 `../mm3-secret.md`。原本只能用 GameMaster 改記
憶體 (`X Y LOC = 01 0E 69`) 才能進入的祕密區，本文件提供兩條工具化路徑：

1. **`mm3_goto.py`** — 直接改存檔（不動 mm3b.exe，最安全）
2. **`mm3_mirror_patch.py`** — patch mm3b.exe，把任一現有代號改寫成 LOC 0x69

---

## 一、結構發現摘要

### 1.1 傳送鏡代號字串指標表 — `mm3b.exe @ 0x1E608`

13 個代號的 BIG5 字串以指標形式存放，data segment paragraph = `0x1831`，
讀取時：`file_offset = 0xE00 + 0x18310 + ptr`。

| idx | ptr 位址 (file) | ptr 值 | 字串 file 位址 | 代號 (BIG5) |
| --: | --: | --: | --: | --- |
| 0 | `0x1E608` | `0x6933` | `0x1FA43` | 家園 |
| 1 | `0x1E60A` | `0x6938` | `0x1FA48` | 海狗 |
| 2 | `0x1E60C` | `0x693D` | `0x1FA4D` | 自由人 |
| 3 | `0x1E60E` | `0x6944` | `0x1FA54` | 命運 |
| 4 | `0x1E610` | `0x57C5` | `0x1E8D5` | 火熱 |
| 5 | `0x1E612` | `0x6708` | `0x1F818` | 競技場 |
| 6 | `0x1E614` | `0x6949` | `0x1FA59` | 最後倒數昇空 |
| 7 | `0x1E616` | `0x57DB` | `0x1E8EB` | 火 |
| 8 | `0x1E618` | `0x5BD4` | `0x1ECE4` | 水 |
| 9 | `0x1E61A` | `0x6956` | `0x1FA66` | 土 |
| 10 | `0x1E61C` | `0x5B76` | `0x1EC86` | 風 |
| 11 | `0x1E61E` | `0x6959` | `0x1FA69` | 大膽混進龍穴 |
| 12 | `0x1E620` | `0x6966` | `0x1FA76` | 偷拿究力神珠 |

> ⚠️ 同一指標表後面 (0x1E622+) 還有 `和誰交換位置` / `遣散誰` / 版權字串 /
> .pic 名稱清單，那些**不是**傳送鏡代號。

### 1.2 代號 → LOC 對應表 — `mm3b.exe @ 0x1B874`

13 連續 byte，順序與 1.1 完全一致：

```
file 0x1B870  00 00 10 10                       <-- preamble
file 0x1B874  01 02 03 04 05 6A 69 32 3B 3C 3D 0E 25
              ^家園       ^火熱  ^最後  ^火    ^風    ^pyramid
                     ^競技場  ^倒數
                            ^昇空
```

| idx | LOC | 代號 | 目的地 (使用者實測) |
| --: | --: | --- | --- |
| 0 | `0x01` | 家園 | 泉頂鎮 |
| 1 | `0x02` | 海狗 | 望海鎮 |
| 2 | `0x03` | 自由人 | 荒原鎮 |
| 3 | `0x04` | 命運 | 沼澤鎮 |
| 4 | `0x05` | 火熱 | 火峰鎮 |
| 5 | `0x6A` | 競技場 | 競技場 |
| 6 | **`0x69`** | 最後倒數昇空 | 觀賞過關畫面（**會觸發過關 cut-scene**，無法自由探索） |
| 7 | `0x32` | 火 | 火焰島 |
| 8 | `0x3B` | 水 | 死亡沼澤 |
| 9 | `0x3C` | 土 | 孤獨沙漠 |
| 10 | `0x3D` | 風 | 寒冰島 |
| 11 | `0x0E` | 大膽混進龍穴 | 龍穴 |
| 12 | `0x25` | 偷拿究力神珠 | 金字塔後段貨艙密室 |

**關鍵發現**：`LOC 0x69` = 祕密區。代號「最後倒數昇空」就是設計來去那裡的，
但 handler 額外做了 ending cut-scene 觸發，所以無法當作普通傳送點用。

### 1.3 X / Y 補位陣列 — 接在 LOC 表後（推測）

```
file 0x1B881  00 00 00 00 00 00 00 0C 07 03 00 07 0E   <-- 推測 X[13]
file 0x1B88E  00 00 00 00 00 00 0A 03 0C 0A 07 …       <-- Y 推測但邊界不確定
```

前 7 個 X 都是 0 — 城鎮 / 競技場 / 過關 cut-scene 大概用該地圖的預設 entry
point。後 6 個 (火/水/土/風/龍穴/pyramid) 才有明確 X/Y 落點。Y 陣列尾端與
"Error..." 字串重疊，需要再確認。**不影響本文件下方的修改路徑**——我們只動
LOC byte。

### 1.4 顯示名稱表（與代號表無關）— `mm3b.exe @ 0x1F64C`

另一張 67 個 BIG5 字串的 LOC 顯示名稱表（HUD 上方那條「目前位置」）。索引
0x00..0x42，**不是** LOC 0x69 — 它涵蓋 5 城鎮 + 5 城鎮洞穴 + 城堡 + 太空船
+ A1..F4 + 祕密區/競技場 等 顯示用名稱。完整清單見 `mm3_goto.py --list`。

### 1.5 存檔黨員位置 byte — `SAVE0X.MM3`

10 個存檔之 byte-diff 比較確認：

| file offset | 欄位 |
| --: | --- |
| `0x2B2E` | 隊伍 X |
| `0x2B2F` | 隊伍 Y |
| `0x2B30` | 隊伍 LOC |

驗證資料（mm3c/SAVE0X.MM3）：

| 存檔 | X | Y | LOC | 推測位置 |
| --- | --: | --: | --: | --- |
| SAVE00 | 0x04 | 0x05 | 0x69 | 祕密區某格 |
| SAVE01 | 0x0E | 0x06 | 0x05 | 火峰鎮某格 |
| SAVE02-09 | 0x02 | 0x05 | 0x01 | 泉頂鎮起點 |

存檔其餘 ~210KB 多為加密 / 壓縮資料（後段 `H ≥ 4.5`），但這 3 個 byte 在
plain region 裡，**可直接 patch 不需處理壓縮**。

---

## 二、工具用法

### 2.1 改存檔（推薦，零風險）— `mm3_goto.py`

```powershell
# 進入祕密區
py mm3_goto.py SAVE05.MM3

# 任意地點
py mm3_goto.py SAVE05.MM3 --x 8 --y 8 --loc 0x3C    # 孤獨沙漠 (土)
py mm3_goto.py SAVE05.MM3 --name "龍穴" --x 7 --y 7

# 列出所有命名地點
py mm3_goto.py --list
```

預設 `--x 1 --y 14 --loc 0x69` = 祕密區 (X=1,Y=0E,LOC=0x69)。第一次執行會
自動產 `SAVE0X.MM3.bak`。

### 2.2 改 mm3b.exe（讓傳送鏡長出新代號）— `mm3_mirror_patch.py`

```powershell
# 看當前 LOC 表
py mm3_mirror_patch.py --dump

# 把「風」(原 LOC 0x3D 寒冰島) 改成 LOC 0x69 (祕密區)
py mm3_mirror_patch.py --target 風

# 還原
py mm3_mirror_patch.py --revert
```

patch 後在遊戲裡找到傳送鏡，輸入「風」即可傳送到 LOC 0x69。

**選哪個代號比較好？**
- ✅ `風 / 水 / 土 / 火` — 單字、好記，原始目的地是元素島可有可無
- ⚠️ `最後倒數昇空` — 已經是 LOC 0x69 但**會觸發過關 cut-scene**，不要選
- ❌ `家園 / 海狗 / 自由人 / 命運 / 火熱` — 5 個主要城鎮傳送，捨不得換

**⚠️ 未在 DOSBox 實測**：因為沒辦法在這個環境跑遊戲。第一次測試請：
1. 先 `--dump` 確認 byte 跟筆記一致
2. 跑 patch
3. 進遊戲嘗試代號
4. 若觸發 ending 或行為怪異，立刻 `--revert`

X/Y 補位陣列裡這個 idx 的值若不是 0，傳送可能會落在很奇怪的格子（也許牆裡）。
若發生，落地後立刻用 `mm3_goto.py SAVE0X.MM3` 修一下 X/Y 即可。

---

## 三、未解 / 後續工作

- [ ] **codeword input handler 位置未定**。`mm3b.exe` 沒有 `cmp al, '5'`／
  `mov [???], 0x69` 的 immediate；handler 可能在 mm3.cc 的 overlay
  (`_UNKNOWN_FILE_8631..8637.BIN` / `_NOT_COMPRESSED_0001_D4BB.BIN`) 內。
  D4BB 內容看起來是加密／壓縮，需先解開。`mm3b.i64` (使用者 IDA 工程檔)
  應該已有更多 label，繼續做的話從那邊接手最快。
- [ ] **X/Y 陣列實際邊界**未驗證。0x1B881 起的 13 byte 第一推測，但 Y 陣列
  與 0x1B89C 的 "Error..." 字串相鄰，需要找到陣列基址在 code 中的真實參考
  才能定案。
- [ ] **新增**（而非取代）一個「祕密區」代號需要：擴充 0x1E608 指標表、
  擴充 0x1B874 LOC 表、把 codeword count（推測 = 13 = `0x0D`）在 handler
  裡更新、再放新字串。沒有 IDA 不建議硬幹。
- [ ] 競技場 / 過關 ending 是否由 handler 內部 hard-code 觸發（cmp 代號
  string 或 cmp LOC == 0x69）尚不清楚。若是後者，方法 2.2 也會觸發 ending；
  若是前者就只有「最後倒數昇空」字串本身會觸發。

---

## 四、相關檔案

> **驗證腳本（保留作為 RE 紀錄，未來可重跑驗證）**：
> `hunt_mirror.py`, `hunt_mirror_v2.py` ... `hunt_mirror_v8.py`,
> `hunt_mirror_codes.py`, `hunt_codeword_table.py`,
> `decode_codeword_table.py`, `hunt_dest_table.py`, `hunt_dest_v2.py`,
> `decode_dest_table.py`, `find_loc_table_ref.py`,
> `compare_saves.py`, `find_pos_bytes.py`, `dump_save_pos.py`,
> `verify_pos.py`, `parse_mz.py`

**核心工具**：

- `mm3_goto.py` — 改存檔，跨檔案、跨 LOC 通用
- `mm3_mirror_patch.py` — 改 mm3b.exe，把某代號重指向 LOC 0x69

兩者皆會自動產 `.bak`，可隨時還原。
