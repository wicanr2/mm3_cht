---
name: mm3-cc-archive
description: 接續 1991 SSI/NWC 魔法門 III 幻島歷險記 (Might and Magic III) 繁體中文版 `mm3.cc` overlay archive 的 reverse engineering 與 patch 工作。當使用者提到 mm3.cc、cc archive、LZHUF 壓縮、rewolf format、加密 header、ABDB.BIN/FFB7.BIN/8F99.BIN 等 mm3.cc 內部資源、想抽出/修改/重灌任何資源檔（含 cfonts 字型 overlay、ABDB credit 字串、textXX.maz 地圖文字、award.bin 成就字串、ABEB.BIN 競技場對話、各種 .pic .mon .vga .icn 資源）、想新增資源到 archive、想看 mm3.cc 內 560 個 hash 對應到什麼檔、或處理「同類 1990s NWC CC archive 格式（rewolf 那套 rot8+0x67 累加 key 加密 header + LZHUF 壓縮）」時觸發。**與 mm3-cht-font、mm3-cht-mirror 互補（那兩個各管一個 specific overlay）**，本 skill 管 mm3.cc archive 本身的 format、tooling、注入 workflow。也涵蓋同類「無 IDA 用 byte pattern 反推 archive 格式」、「Python port LZHUF」、「就地擴張 archive 不重排 offset」的技巧。
---

# MM3 `mm3.cc` Archive 修改 Skill

接續魔法門 III (MM3) 繁體中文版 `mm3.cc` overlay archive 工作。**先讀本檔再動手** — archive 是 LZHUF + rot8 累加 key 加密的，盲改 header 整個遊戲開不起來。

## 專案路徑

```
D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c\
├── mm3.cc (3.4MB+)              ← target archive
├── mm3.cc.bak                    ← 原版（任何 patch 失敗都從這還原）
├── mm3.cc.preABDB.bak            ← ABDB 注入前 snapshot
├── mm3.cc.injected               ← font patch 注入後（中間檔）
├── mm3.cc.injected_v2            ← font patch v2 壓縮版
├── mm3.cc.injected_abdb          ← font + ABDB 雙 patch 版
├── out_cc_dump\                  ← rewolf dumper 解出來 560 個 resource
│   ├── _UNKNOWN_FILE_8F99.BIN    ← 字型 code overlay (mm3-cht-font 用)
│   ├── _UNKNOWN_FILE_ABDB.BIN    ← interactive object 字串 (mirror prompt + 祕密區 credits)
│   ├── _UNKNOWN_FILE_ABEB.BIN    ← 競技場對話
│   ├── _UNKNOWN_FILE_FFB7.BIN    ← 大型敘事文字 + 譯者註
│   ├── _NOT_COMPRESSED_0000_*    ← header 標記為「未壓縮」的 entry
│   ├── text01.maz ... text64.maz ← 各地圖事件文字 (LOC % 100 後 mapping)
│   ├── award.bin                  ← 成就字串
│   ├── tavern.bin                 ← 酒館對話 (含 mirror codeword 提示)
│   ├── jester.bin / spldesc.bin   ← 小丑提示 / 法術描述
│   └── (大量 .pic .mon .vga .icn .sky .til .fac .m .out .raw .spl 等)
├── inject_overlay.py              ← rewolf format + crypt_header + entry parser (基底)
├── inject_overlay_v2.py           ← 注入 font overlay (8F99) 壓縮版
├── inject_abdb.py                 ← 注入 ABDB_zh 字串資源
├── patch_abdb_credits.py          ← 生成 ABDB_zh.BIN (英+中)
├── lzhuf_compress.py / lzhuf_decompress.py ← rewolf LZHUF Python port
├── mm3_cc_dumper.exe              ← rewolf 原 dumper (需 MSVCR110D.dll 才能跑)
└── (其他 RE 工具)
```

## mm3.cc Archive 格式（rewolf 2016 RE）

### Header 結構

```
[0..1]      uint16 LE  num_entries × 8
[2..H+2]    encrypted FileEntry[num_entries] (each 8 bytes)
[H+2..]     payload blobs (LZHUF compressed)
```

### Header 加密演算法

```python
def crypt_header(buf, encrypt=False):
    """rot8 + 0x67 累加 key. start key = 0xAC."""
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

### FileEntry (8 bytes per entry)

```
offset 0..1   uint16 LE  hash (BIG5 filename → 16-bit hash by rewolf algo)
offset 2..3   uint16 LE  offset_lo
offset 4      uint8      offset_hi          ← total offset = (hi << 16) | lo
offset 5..6   uint16 LE  compressed_size
offset 7      uint8      padding / flag
```

### Payload format (per entry, at `offset`)

```
[+0]   uint8  iv          (LZHUF initial vector / seed)
[+1]   uint8  iv          (重複，rewolf 寫兩份)
[+2]   uint8  size_hi     ← decompressed size 高 byte
[+3]   uint8  size_lo     ← decompressed size 低 byte
[+4..] LZHUF compressed bytes
```

> 雖然 dumper 解過部分 entry 是「uncompressed」（檔名 prefix `_NOT_COMPRESSED_*`），但 mm3b.exe runtime loader **要求所有 entry 是真實 LZHUF 壓縮的**。注入 uncompressed payload 雖然 dumper 能解，loader 會 crash。

## 三條常用工作流

### A. 抽出 mm3.cc 內某個 resource

已有 `out_cc_dump\` 內所有 560 個檔。資源檔名規則：
- 有對應命名的：`bank.m`, `cfonts.grp`, `text01.maz`, `award.bin`, etc.
- 未命名 hash：`_UNKNOWN_FILE_{HASH:04X}.BIN` (例 `_UNKNOWN_FILE_8F99.BIN`)
- 標記未壓縮的：`_NOT_COMPRESSED_{idx:04d}_{HASH:04X}.BIN`

要 re-dump：

```powershell
# 原 rewolf dumper (需要 MSVCR110D.dll)
mm3_cc_dumper.exe mm3.cc out_cc_dump\

# 或用 Python port (還沒寫獨立 dumper script，目前靠 inject_overlay.py 內 helpers)
```

### B. 修改既有 resource 並 inject 回 archive

通用 pattern（已實作兩個範例 `inject_overlay_v2.py` 跟 `inject_abdb.py`）：

```python
# 1. 修改 _UNKNOWN_FILE_HHHH.BIN（或對應命名檔）
# 2. LZHUF compress
iv = stat_file(overlay_bytes)               # iv = decompressed[0] 通常
compressed = lzhuf_compress(overlay_bytes, iv)
entry_data = bytes([iv, iv,
                    (len(overlay_bytes) >> 8) & 0xFF,
                    len(overlay_bytes) & 0xFF]) + compressed

# 3. 驗證 round-trip
assert lzhuf_decompress(entry_data[4:], len(overlay_bytes), iv) == overlay_bytes

# 4. 更新 archive header entry
n = struct.unpack("<H", cc[0:2])[0]
hdr_dec = crypt_header(cc[2:2+n*8], encrypt=False)
entries = parse_entries(hdr_dec)
idx = next(i for i, e in enumerate(entries) if e[0] == TARGET_HASH)
entries[idx][1] = len(cc)                    # new offset = end of file
entries[idx][2] = len(entry_data)            # new compSize
cc_out = bytearray(cc)
cc_out[2:2+n*8] = crypt_header(build_entries(entries), encrypt=True)
cc_out += entry_data
open("mm3.cc", "wb").write(bytes(cc_out))
```

**重點**：寫 entry 到 archive 尾端（不重排其他 entry 的 offset，最安全），同 hash 的舊 entry 變 orphan 但不被引用所以無害。

### C. 還原原版或某個 snapshot

```powershell
copy /Y mm3.cc.bak mm3.cc            # 完全還原
copy /Y mm3.cc.preABDB.bak mm3.cc    # 還原到 font patch 之後、ABDB 之前
```

## 已知 hash → 用途對照

| Hash | 檔名 / 用途 |
|---|---|
| `0x8F99` | 字型 code overlay（OPEN/LOOKUP/BLIT 函式，mm3-cht-font patch 位置 0x1DFA）|
| `0xABDB` | Interactive object 字串表（mirror prompt 「鍵入你的目的地。」+ 祕密區 18 段 dev credits）|
| `0xABEB` | 競技場對話（「歡迎來到競技場」、「恭喜你贏得第 %u 場」）|
| `0xFFB7` | 大型敘事 + 譯者註（含「祕密區...為了保留其原意，因此我們沒有翻譯」）|
| `0x7A39` | unknown overlay (15210 bytes) |
| `0x8631-0x8637` | 7 個 overlay 檔（可能是 game-mode overlays，未細查）|
| `0xABEB-0xAC1B` | 4 個小 overlay (370, 63, 63, 63 bytes) — 可能是相關 lookup |
| `0x1E0F` / `0xD4BB` | NOT_COMPRESSED entry，內容看起來像加密 / 壓縮過的 data |

完整 560 個 entry 列表見 `out_cc_dump\` 目錄。

## 注入後 mm3.cc 結構

```
+----------------------+
| header (561 × 8 byte) |   ← entries[idx] 更新指向 new offset
+----------------------+
| original payload blobs |   ← orphan 舊 entry data 還在這裡（不被引用）
+----------------------+
| (...font patch v2...)  |   ← inject_overlay_v2.py 添加的字型 overlay
+----------------------+
| (...ABDB_zh...)        |   ← inject_abdb.py 添加的 credit 翻譯
+----------------------+
```

每次 inject 都會把新 entry 加到尾端。多次 inject 同一個 hash 會留下 orphan，但不影響功能。要清理需 rebuild 整個 archive（目前沒實作 tool）。

## 關鍵 RE 知識

### LZHUF iv 來源

`iv` (initial vector) 是壓縮演算法的 seed。實測 `iv = stat_file(data)` 用某個函式算出，rewolf source.cpp 內有公式。最簡單就直接用 `lzhuf_compress.stat_file()` helper。

### 為什麼 NOT_COMPRESSED entry 不能直接用

rewolf dumper 看到 `compressed_size == decompressed_size` 就標 `NOT_COMPRESSED`。但 mm3b.exe loader **永遠走 LZHUF decompress path**，所以「未壓縮」payload 反而會 crash。**所有注入都要 LZHUF compress**，哪怕資料變大。

### filename hash 是怎麼算的

rewolf 有 Python port 但目前沒整合進工具。多數情況我們**靠 hash → 既知檔名 lookup**（用 `out_cc_dump\` 內檔名）就夠。要新增資源（用未知 hash）才需算 hash。

## 雷區（避免重蹈覆轍）

1. **不能注入 uncompressed payload** — loader 會 crash，所有 entry 必須真 LZHUF 壓縮
2. **header 加密 key starts 0xAC, increment 0x67** — 試其他常數一定錯
3. **rewolf 2016 mm3_cc_dumper.exe 需 MSVCR110D.dll** — 一般 Windows 跑不起來，已 port Python 版（`lzhuf_compress.py` + `inject_overlay.py` helpers）
4. **同 hash 的舊 entry 變 orphan** — 多次 inject 同檔會讓 mm3.cc 持續長大，要 reset 從 .bak 開始
5. **string resource 長度改變不會破壞 archive**（loader 用 null terminator 跑），但**個別 string 內存的 control codes（`<0C>nn`、`<0B>nnn`）跟前後 byte offset 有關係要小心**
6. **不要直接覆寫原 entry 位置** — 舊 entry 的壓縮 payload 跟後面 entry 緊鄰，覆寫會踩到下一個 entry 的 LZHUF 資料。永遠 append 到 file 尾端、更新 header offset
7. **iv 一定要一致** — entry_data 前 2 byte (iv, iv) 跟 LZHUF state 必須對齊，不然 decompress 出垃圾
8. **某些 entry 是 BIG5 文字 mixed 控制碼**（`<03>c` 顏色、`<0B>nnn` Y 座標、`<0C>nn` 字色）— 翻譯時這些 escape sequence 不能拆開
9. **DOSBox 會 cache mm3.cc 內容** — 改 mm3.cc 必須**完全關 DOSBox 整個 process** 再開
10. **多個 hash 共用 string region 的可能性** — 不同 entry 可能指向 archive 內同一片段資料（共用字串），改一個會影響多個 use case。注入前 grep 一下

## 引用資源

- rewolf 原始 dumper repo: https://github.com/rwfpl/rewolf-mm3-dumper
- rewolf blog: https://blog.rewolf.pl/blog/?p=1202
- Source.cpp 跟 LZHUF 演算法 clone 在: `C:\Users\原來是個胖仔\AppData\Local\Temp\mm3-dumper\`
- memory 紀錄: `project_mm3_mirror.md`（指向本 skill 工具集）
- 互補 skills:
  - **mm3-cht-font** — 只管 cfonts.grp + 字型 overlay 8F99 patch + BLIT row count
  - **mm3-cht-mirror** — 只管 mm3b.exe 內 mirror codeword 表 + save file 改位置
  - **本 skill (mm3-cc-archive)** — archive 格式本身 + 通用注入 workflow
