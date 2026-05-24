# 魔法門 III 幻島歷險記 中文化擴充專案

> *Might and Magic III: Isles of Terra*（1991 New World Computing）
> — 元碁科技 1992 繁體中文版的後續 RE / patch 紀錄
> 字型 8 → 15 row 修復 ✦ 傳送鏡新增「祕密區」代號 ✦ 開發者祕密區 18 段 credits 中文翻譯 ✦ 存檔位置編輯器

---

## 目錄

1. [專案狀態](#status)
2. [快速開始](#quick-start)
3. [為何要做這個 patch？](#why)
4. [1992 元碁科技中文版的時代](#elite-1992)
5. [魔法門 III 在系列中的位置](#mm-series)
6. [傳送鏡（Mirror of Worlds）密碼系統](#mirror-codewords)
7. [祕密區 — NWC 開發者的彩蛋與譯者的留白](#secret-area)
8. [字型修復 — 從 8 row 到 15 row 的代價](#font-fix)
9. [技術深入](#technical-deep-dive)
10. [工具清單](#tools)
11. [License 與致謝](#credits)

---

<a name="status"></a>
## ✨ 專案狀態

這是 *Might and Magic III: Isles of Terra*（1991 NWC）**繁體中文版**（元碁科技 1992）的擴充與 RE 紀錄。

原版中文化由元碁科技在 1992 年完成，已是相當完整的翻譯。本專案專注於三件原版**未處理**或**故意未翻**的東西：

| 模組 | 狀態 | 說明 |
| --- | --- | --- |
| **字型 row count fix** | ✅ 完成 | overlay 0x8F99 內 BLIT 8 row → 15 row，配合 cfonts.grp 重 render |
| **傳送鏡新代號「祕密區」** | ✅ 完成 | 把 codeword「火」slot 7 重指向 LOC 0x69（祕密區），玩家輸入「祕密區」即傳送 |
| **存檔位置編輯器** | ✅ 完成 | `mm3_goto.py`，不動 mm3b.exe 直接改 SAVE0X.MM3 跳到任意 LOC/X/Y |
| **祕密區 18 段開發者 credits 中譯** | ✅ 完成 | ABDB.BIN 內 NWC 員工 18 句個人話，原本譯者**故意保留英文**，本專案補上中譯（英文保留） |
| **競技場 200 局獎勵 RE** | ⚠ 未發現 | mm3b.exe 找不到 hardcoded 200/75 trigger，可能是都市傳說 |

| 項目 | 值 |
| --- | --- |
| 原作 | New World Computing, Inc. (1991) |
| 中文化 | 元碁科技代理發行 (1992) |
| 平台 | MS-DOS（DOSBox 可玩） |
| 字型 | 5813 glyph × 30 byte，BIG5 自訂 idx 排序 |
| GitHub | [wicanr2/mm3_cht](https://github.com/wicanr2/mm3_cht) |
| 互補 repo | [wicanr2/u6-cht](https://github.com/wicanr2/u6-cht)（Ultima VI 完整中文化） |

---

<a name="quick-start"></a>
## ⚡ 快速開始

### 你需要準備

- **DOSBox**（推薦 DOSBox SVN-Daum 或 DOSBox-X，舊 0.74 也可）
- **MM3 繁體中文版原版資料**（請自行取得合法 copy，本 repo **不**附遊戲檔）
- **Python 3.9+**（執行 patch 工具）

### 三步啟動

```powershell
# 1. 取得本 repo
git clone https://github.com/wicanr2/mm3_cht.git
cd mm3_cht

# 2. 把 tools/ 內所有 .py 複製到你的 MM3 安裝目錄（含 mm3b.exe 和 mm3.cc 的那個資料夾）
copy tools\*.py C:\Games\MM3\

# 3. 跑你想要的 patch
cd C:\Games\MM3
py mm3_mirror_patch.py --target 火 --x 3 --y 14   # 火 codeword 改成傳到祕密區寶藏堆
py patch_codeword_string.py                        # 把 codeword 字串改為「祕密區」
py verify_codewords.py                              # 驗證
```

完成後**完全關閉 DOSBox**（process 級別，不只是主選單）再開遊戲，走到傳送鏡輸入「祕密區」，應該會掉在 X=3 Y=14 的寶藏堆。

---

<a name="why"></a>
## ✨ 為何要做這個 patch？

1991 年，**New World Computing**（後來被 3DO 收購）推出 *Might and Magic III: Isles of Terra*。這是 MM 系列第一款 256 色 VGA、第一款**有滑鼠介面**、第一款引入「按鍵 = 即時行動」的 MM 作品。在 1991 年的 RPG 標準下，它是**畫面、介面、戰鬥節奏**三方面都全面升級的工藝品。

1992 年，**元碁科技**完成繁體中文化，把對話、選單、地名、技能、法術全部翻譯，並用自製 cfonts.grp 字模（5813 個 BIG5 glyph）支援滿屏中文。這個翻譯版本在 90 年代是台灣 RPG 玩家的入門經典之一。

但有三個小遺憾：

1. **字型只渲染 row 0-7**（8 px 高），下半 7 row 是空 padding。多行字會擠在一起，閱讀體驗不佳。
2. **傳送鏡的「祕密區」入口被隱藏**——原本只能透過 GameMaster 改記憶體（修改 `X Y LOC = 01 0E 69`）才能進入。
3. **祕密區內的 18 段 NWC 員工 credits 故意未翻**——譯者在 mm3.cc 內留了一段文字解釋：「為了保留其原意，因此我們沒有翻譯，請各位玩家自行品嚐個中趣味。」這在 1992 年是合理的決定，但 30 年後英文閱讀仍有門檻。

**這個專案就是要把這三件事補完**：讓字型滿屏渲染、讓玩家可以正常用代號進祕密區、讓 18 段 dev credits 有中文對照。

> 「**改不出來想要看存檔的請留 MAIL 給我**」
> —— 使用者 2007 年寫給未來自己的便條。如今補完。

---

<a name="elite-1992"></a>
## 🏛 1992 元碁科技中文版的時代

90 年代台灣的 PC 遊戲中文化是**民間自組**到**正版代理**的過渡期。元碁科技（Elite Software）是當時極少數有能力做整套 DOS RPG 中文化的廠商，作品線包括：

- 魔法門 III 幻島歷險記 (1992)
- 魔法門 IV 神秘島雲圖 (1993)
- 魔眼殺機 (Eye of the Beholder) 系列
- 創世紀 VI 偽聖者 (Ultima VI) — 部分翻譯
- 銀河飛將 (Wing Commander) 系列

這些中文版的共同特徵：

1. **自製 BIG5 字模檔**（cfonts.grp / chinfont.fnt）內嵌進遊戲資源
2. **修改原版 EXE 內字串為 BIG5**（即 「strcmp 路徑 = 顯示路徑」，不像現代 Unicode 可拆）
3. **dispatch table 改寫**（覆寫原英文渲染 function，導向自訂 BIG5 lookup）

技術手法相當古典：沒有 Unicode、沒有 ICU、沒有 freetype。每個字都是手繪 16×15 點陣，每個翻譯都要逐 byte 對齊。今天看回去，每個字模都帶著那個時代的職人氣息。

> 本專案的 patch 不修改原譯者的翻譯內容，只**還原字型 row count**、**新增傳送鏡入口**、**補上 dev credits 中譯**。原版翻譯尊重保留。

---

<a name="mm-series"></a>
## 📜 魔法門 III 在系列中的位置

Might and Magic 是 Jon Van Caneghem（JVC）於 1986 年創立的 RPG 系列。一路發展到 2014 年 *Might and Magic X*。

| 作品 | 年份 | 引擎特色 |
| --- | --- | --- |
| MM I: Secret of the Inner Sanctum | 1986 | 文字介面，Apple II 起家 |
| MM II: Gates to Another World | 1988 | EGA 16 色 |
| **MM III: Isles of Terra** | **1991** | **VGA 256 色 + 滑鼠** ← 本作 |
| MM IV: Clouds of Xeen | 1992 | 同 III 引擎進化 |
| MM V: Darkside of Xeen | 1993 | 同 III/IV 引擎，可與 IV 合併成「World of Xeen」 |
| MM VI: Mandate of Heaven | 1998 | 3D 引擎，3DO 接手後重啟 |

**MM III 的承前啟後**：

- **承前**：保留 MM I-II 的「party of 6 + grid-based dungeon crawl」架構
- **啟後**：引入即時戰鬥動畫、VGA 大頭像、可隨時存檔讀檔
- **Easter egg 文化**：JVC 把整個 dev team 的 personality 放進「祕密區」——這是 MM III 最有趣的彩蛋，後面會詳述

---

<a name="mirror-codewords"></a>
## 🪞 傳送鏡（Mirror of Worlds）密碼系統

MM III 在數個城鎮裡放了**傳送鏡**這個 NPC 物件。靠近後互動會出現：

```
銀樣的玻璃上映出湖般的搖曳影像。說出你的目的地，可以到達。
鍵入你的目的地。
```

玩家輸入正確「代號」即可瞬移到該地。原版收錄 **13 個固定代號**：

| 代號 | 目的地 | LOC |
| --- | --- | --- |
| 家園 | 泉頂鎮 (Fountain Head) | 0x01 |
| 海狗 | 望海鎮 (Baywatch) | 0x02 |
| 自由人 | 荒原鎮 (Wildabar) | 0x03 |
| 命運 | 沼澤鎮 (Swamp Town) | 0x04 |
| 火熱 | 火峰鎮 (Blistering Heights) | 0x05 |
| 競技場 | 競技場 | 0x6A |
| 最後倒數昇空 | 結局過關畫面 ⚠ | 0x69 |
| 火 | 火焰島 | 0x32 |
| 水 | 死亡沼澤 | 0x3B |
| 土 | 孤獨沙漠 | 0x3C |
| 風 | 寒冰島 | 0x3D |
| 大膽混進龍穴 | 龍穴 | 0x0E |
| 偷拿究力神珠 | 金字塔密室 | 0x25 |

### 三張平行表

代號 → 目的地的查表，存在 `mm3b.exe` 內**三張 13-byte 平行陣列**：

```
file 0x1B874   LOC[13]    01 02 03 04 05 6A 69 32 3B 3C 3D 0E 25
file 0x1B881   X[13]      00 00 00 00 00 00 00 0C 07 03 00 07 0E
file 0x1B88E   Y[13]      00 00 00 00 00 00 00 00 0A 03 0C 0A 07
```

加上 codeword 字串的 pointer table（`file 0x1E608`，13 × 2 byte）。

### 一個值得記下的雷區

**slot 6（最後倒數昇空）綁了 hardcoded ending trigger**。我們實驗確認：

- slot 6 即使把字串改成「祕密區」+ X/Y 改成寶藏堆座標 → 依然觸發過關 cutscene
- slot 10（風）改 LOC=0x69 X=3 Y=14 → 正常進祕密區，無 cutscene

也就是說 trigger **綁在 slot index = 6，不綁在 LOC=0x69 或字串內容**。要加新代號**一定要選 slot ≠ 6**。

---

<a name="secret-area"></a>
## 🏛 祕密區 — NWC 開發者的彩蛋與譯者的留白

### 1991 年的開發團隊簽名

LOC 0x69 是 MM III 內藏最深的房間。畫面上是一片金色花紋地板，散落著紅寶石、王座、黑曜石裝備。最特別的是滿滿一圈**寶座**，每個寶座上坐著一位 NWC 員工的虛擬像，互動會跳出他們各自的 personality：

| 員工 | 原英文（保留） |
| --- | --- |
| Benjamin Bent | *Laugh now monkey boy!* |
| Ron Bolinger | *The writing in this game was awesome.* |
| Andy Caldwell | *Juuuuuulia..* |
| Mark Caldwell | *Women!* |
| Mike Clement | *Trojans are the superior brand.* |
| Richard Espy | *Poker, anyone?* |
| Douglas Grounds | *Sit, Toto! Sit!* |
| Dave Hathaway | *You too shall be honored... Boot to the head!* |
| Bonnie Long-Hemsath | *Remember - reality is user-defined. Go therefore and take responsibility for your reality. If it is not as you would have it, create a new one. It can be done.* |
| Todd Hendrix | *Lick the Chalice!* |
| Eric Hyman | *Jay + C = Hap + E.* |
| Louis Johnson | *Where's the nearest jam?* |
| Eric Newhouse '1292 | *Go Crimson! Ja^2, Rubes, Fitz, Visc, & House: Leverett Hoops'92!* |
| Paul Rattner | *To all my creditors: Don't call me; I'll call you. PS. Your check is in the mail.* |
| Scott T. Smith | *Debbo-meister.* |
| Allen Treschler | *FOOL'S MATE 1.) P-KB4 P-K3 2.) P-KN4 Q-R5 mate! is the fastest kill there is.* |
| Jon Van Canegham | *Life is a game. Let's play!* |

最後一位 **Jon Van Canegham** 就是 MM 系列創始人，也是日後 *Heroes of Might and Magic* 的締造者。"Life is a game. Let's play!" — 在 1991 年的 dot-com 前夜，這句話有那個時代的天真與熱忱。

### 中文版譯者的留白

元碁科技 1992 年的譯者，遇到這 18 段時做了一個有趣的決定 —— **他們不翻譯，但是在 mm3.cc 裡留下一段中文便條**（檔 `_UNKNOWN_FILE_FFB7.BIN` @ offset 0x29AF）：

> 「（中文版翻譯者註）**祕密區的許多寶座坐滿了魔法門 III 原作公司的職員，每個人都說了一些話。為了保留其原意，因此我們沒有翻譯**，請各位玩家自行品嚐個中趣味。」

這是非常**詩意**的決定。30 年後重看這段譯者註，能感覺到一種跨越時代的職業敬意 —— 不是「我不會翻」，而是「我覺得不該翻」。

### 本專案的補完

我們選擇**英中對照**——保留原英文不動，下方附上中文翻譯。這樣：

- 原譯者「保留原意」的精神不違背（英文依然在第一行）
- 不懂英文的玩家可以讀懂笑點與致敬
- 譯者留下的那段「為什麼不翻」的便條，本身成為**雙語版本下被新解讀的一段文字**

範例：

```
Bonnie Long-Hemsath

Remember - reality is user-defined.
Go therefore and take responsibility for your reality.
If it is not as you would have it, create a new one. It can be done.

記住—現實由你自己定義。所以去吧，為你的現實負起責任。
如果它不符合你的期望，就創造一個新的。這是辦得到的。
```

### 為什麼祕密區叫 LOC 0x69

LOC 0x69 = 105 decimal。MM III 引擎只認 64 張地圖 (text01.maz ~ text64.maz)，**LOC 0x69 完全超出範圍**。這正是為什麼譯者沒給它對話檔案 —— 它根本不在正常 LOC 索引內。它是**藏在 F1 地下城同一張 .maz 檔內的特殊座標區**，要靠 codeword 跳到 (X=3, Y=14) 才會落在寶藏堆。

使用者在 2007 年留下的便條：

> 「**這個方法 中英文版都適用**...由 X 開始修改，改成 `01 0E 69` 然後存檔再讀檔...科科 恭喜老爺 你已經在秘密區了。」

那個年代靠 GameMaster 改記憶體才能進去；20 年後我們用 patch 把這個秘密入口開放給傳送鏡。

---

<a name="font-fix"></a>
## 🔤 字型修復 — 從 8 row 到 15 row 的代價

`cfonts.grp` 是 174,394 byte 的字模檔，存 5813 個 BIG5 字符。每字 30 byte = 16 cols × 15 rows × 1 bpp。

**原版有個怪現象**：所有 5813 個 glyph **只在 row 0-7 寫入像素**，下半 7 row 永遠為 0。

```
row activity (out of 5813 glyphs)
  row  0:  2917  ##############
  row  1:  5674  ################################################
  row  2:  5699  #################################################
  row  3:  5747  #################################################
  row  4:  5732  #################################################
  row  5:  5749  #################################################
  row  6:  5742  #################################################
  row  7:  5724  #################################################
  row  8:   104
  row  9:     0
  ...
  row 14:     0
```

原因是 `_UNKNOWN_FILE_8F99.BIN` 內 BLIT function（位置 `0x1DFA`）寫死 `mov bx, 8` —— 引擎只繪上半 8 row。

修復是 **1 byte patch**：`08` → `0F`（bx = 15），讓 BLIT 畫滿 15 row。配合用 MingLiU 11 重新 render 滿屏中文字模，整體閱讀體驗大幅改善。

詳細請見 [`mm3-cht-font` skill](https://github.com/wicanr2/mm3_cht)（暫存於 `~/.claude/skills/mm3-cht-font/`）。

---

<a name="technical-deep-dive"></a>
## 🔬 技術深入

### mm3.cc archive 格式（rewolf 2016 RE）

```
[0..1]      uint16 LE  num_entries × 8
[2..H+2]    encrypted FileEntry array (8 byte each)
[H+2..]     LZHUF compressed payload blobs
```

**Header 加密**：rot8 + key 累加，start 0xAC，每 byte 後 key += 0x67：

```python
def crypt_header(buf, encrypt=False):
    key = 0xAC
    out = bytearray(buf)
    for i in range(len(out)):
        if encrypt:
            out[i] = rotr8((out[i] - key) & 0xFF, 2)
        else:
            out[i] = (rotl8(out[i], 2) + key) & 0xFF
        key = (key + 0x67) & 0xFF
    return bytes(out)
```

**FileEntry 結構**（8 byte）：

```
offset 0..1   uint16 LE  hash (filename → 16-bit hash)
offset 2..3   uint16 LE  offset_lo
offset 4      uint8      offset_hi   (total = (hi << 16) | lo)
offset 5..6   uint16 LE  compressed_size
offset 7      uint8      padding
```

**Payload 結構**（每個 entry，從 offset 起）：

```
[+0]   uint8  iv          (LZHUF seed)
[+1]   uint8  iv          (重複，rewolf 寫兩份)
[+2]   uint8  size_hi
[+3]   uint8  size_lo     (decompressed size)
[+4..] LZHUF compressed bytes
```

### 已知 hash → 用途對照表（部分）

| Hash | 用途 |
| --- | --- |
| `0x8F99` | 字型 code overlay（BLIT 函式 patch 點）|
| `0xABDB` | Interactive object 字串表（mirror prompt + 祕密區 18 段 credits）|
| `0xABEB` | 競技場對話 |
| `0xFFB7` | 大型敘事 + 譯者註 |

全 560 個 entry 列表見 `out_cc_dump\`（用 rewolf 工具解出）。

### 傳送鏡 codeword 表（mm3b.exe）

```
file 0x1E608   Pointer table (13 × 2 byte) — 指向 codeword 字串
file 0x1B874   LOC[13]   — 目的地 LOC code
file 0x1B881   X[13]     — 目的地 X 座標
file 0x1B88E   Y[13]     — 目的地 Y 座標
file 0x1FA43   Codeword 字串集中區（變長 BIG5）
file 0x1F811   「祕密區」既存字串（HUD 顯示用，可被 pointer redirect 重用）
```

### 存檔 (`SAVE0X.MM3`) party position

```
file offset    欄位
0x2B2E         X
0x2B2F         Y
0x2B30         LOC
```

前 ~108KB 是 plain region，後段壓縮加密。位置這 3 個 byte 在 plain 區直接改不需處理壓縮。

---

<a name="tools"></a>
## 🛠 工具清單

全部 Python 工具放在 `tools/` 目錄。執行前複製到含 `mm3b.exe` 和 `mm3.cc` 的遊戲目錄。

### 傳送鏡相關

| 工具 | 用途 | 範例 |
| --- | --- | --- |
| `mm3_mirror_patch.py` | 改任一 codeword 的 LOC/X/Y | `py mm3_mirror_patch.py --target 火 --x 3 --y 14` |
| `patch_codeword_string.py` | 重指 slot 7 字串到「祕密區」 | `py patch_codeword_string.py` |
| `verify_codewords.py` | 列出 13 codeword 的真實 ptr→string + LOC/X/Y | `py verify_codewords.py` |

### 存檔編輯

| 工具 | 用途 | 範例 |
| --- | --- | --- |
| `mm3_goto.py` | 把存檔 party 傳送到任意 LOC/X/Y | `py mm3_goto.py SAVE05.MM3` 預設進祕密區 |
| | | `py mm3_goto.py --list` 列出所有命名地點 |
| | | `py mm3_goto.py SAVE05.MM3 --name 龍穴 --x 7 --y 7` |

### mm3.cc archive 操作

| 工具 | 用途 |
| --- | --- |
| `lzhuf_compress.py` / `lzhuf_decompress.py` | rewolf LZHUF 演算法 Python port |
| `inject_overlay.py` | 基礎 archive header 解析 + crypto helper |
| `inject_overlay_v2.py` | 注入字型 overlay (0x8F99) 壓縮版 |
| `patch_abdb_credits.py` | 生成 ABDB_zh.BIN（英文+中文）|
| `inject_abdb.py` | 把 ABDB_zh.BIN 壓縮注入 mm3.cc |

### 完整工作流範例 — 套用所有 patch

```powershell
# 假設你的 MM3 安裝在 C:\Games\MM3
cd C:\Games\MM3
copy <path-to-repo>\tools\*.py .

# 1. 確認 .bak 存在
copy mm3b.exe mm3b.exe.bak
copy mm3.cc mm3.cc.bak

# 2. 傳送鏡新代號「祕密區」
py mm3_mirror_patch.py --target 火 --x 3 --y 14
py patch_codeword_string.py
py verify_codewords.py

# 3. 祕密區 18 段 dev credits 中譯
py patch_abdb_credits.py     # 生成 ABDB_zh.BIN
py inject_abdb.py            # 注入到 mm3.cc

# 4. 完全關閉 DOSBox 再開遊戲測試
```

要還原：
```powershell
copy /Y mm3b.exe.bak mm3b.exe
copy /Y mm3.cc.bak mm3.cc
```

---

<a name="credits"></a>
## 📜 License 與致謝

本專案的所有 patch / 工具 / 文件以 **MIT** 條款公開。

**原作版權**：
- *Might and Magic III: Isles of Terra* © 1991 New World Computing, Inc.
- 繁體中文版 © 1992 元碁科技

本 repo **不**附原版遊戲檔（`mm3b.exe` / `mm3.cc` / SAVE.MM3 等）。請玩家自行取得合法 copy 後套用本 repo 提供的 patch。

### 技術致謝

- **rewolf** ([@rwfpl](https://github.com/rwfpl)) — 2016 年 mm3.cc archive format RE + dumper + LZHUF reference implementation。本專案的 mm3.cc 壓縮 / 加密 / inject workflow 完全建立在他的研究上。([repo](https://github.com/rwfpl/rewolf-mm3-dumper) / [blog](https://blog.rewolf.pl/blog/?p=1202))
- **元碁科技 1992 翻譯團隊** — 30 年前完成 MM III 主翻譯，並留下了那段「為什麼不翻譯祕密區 credits」的譯者註。本專案站在他們的肩膀上。
- **New World Computing 1991 開發團隊** — 把整個團隊的 personality 放進祕密區寶座，造就了 RPG 史上最有溫度的開發者彩蛋之一。

### 關聯專案

- [wicanr2/u6-cht](https://github.com/wicanr2/u6-cht) — Ultima VI 完整繁中化（ScummVM Nuvie 引擎）
- [rwfpl/rewolf-mm3-dumper](https://github.com/rwfpl/rewolf-mm3-dumper) — rewolf 原 dumper

### Claude Code Skills（本專案用到的 RE 知識封裝）

- `mm3-cht-font` — 字型 / cfonts.grp / 0x8F99 overlay patch
- `mm3-cht-mirror` — 傳送鏡 codeword 表 + save patch
- `mm3-cc-archive` — mm3.cc archive 格式 + LZHUF + 通用 inject workflow

這些 skill 安裝在 `~/.claude/skills/`，供未來繼續擴充 MM III 中文化時自動載入。

---

> *"Life is a game. Let's play!"*
> — Jon Van Canegham, 1991（從 MM III 祕密區寶座傳來的話）
