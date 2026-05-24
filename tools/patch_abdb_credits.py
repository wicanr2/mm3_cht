"""Patch ABDB.BIN: keep English, append Chinese translation to 18 developer
credit quotes. Names stay as-is (they're real people's names).

Format per quote:  原英文\n中文翻譯\0
Each string is null-terminated and the engine iterates by index, so as long as
the SEQUENCE of 18 names + 18 quotes is preserved, code that picks string #N
still works. The file grows in total size — we'll handle re-injection separately.

Run:
  py patch_abdb_credits.py           # writes ABDB_zh.BIN + diff report
  py patch_abdb_credits.py --revert  # not applicable (we don't modify mm3.cc here)
"""
import os, sys, struct
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"
DUMP = os.path.join(ROOT, "out_cc_dump")
SRC  = os.path.join(DUMP, "_UNKNOWN_FILE_ABDB.BIN")
OUT  = os.path.join(ROOT, "ABDB_zh.BIN")


def is_big5_lead(b): return 0xA1 <= b <= 0xFE
def is_big5_trail(b): return (0x40 <= b <= 0x7E) or (0xA1 <= b <= 0xFE)


def render(data):
    out = []; i = 0
    while i < len(data):
        b = data[i]
        if i + 1 < len(data) and is_big5_lead(b) and is_big5_trail(data[i+1]):
            try:
                out.append(data[i:i+2].decode("big5")); i += 2; continue
            except Exception: pass
        if 0x20 <= b < 0x7F: out.append(chr(b))
        elif b == 0x0A: out.append("\\n")
        elif b == 0: out.append("\\0")
        else: out.append(f"<{b:02X}>")
        i += 1
    return "".join(out)


# Translation table for the 18 developer quotes (KEEP English + append Chinese).
# Keys are the original quote strings (bytes), values are Chinese to append.
# NAMES are NOT translated (they're real people).
# The 18 entries in order match ABDB.BIN @ offsets 0x111+ (alternating Name, Quote).
TRANSLATIONS = [
    # (name, quote_old_bytes, chinese_to_append)
    ("Benjamin Bent",
     b"Laugh now monkey boy\xa1\x49.",      # "Laugh now monkey boy！."
     "笑吧，猴小子！"),
    ("Ron Bolinger",
     b"The writing in this game was awesome.",
     "這款遊戲的劇本超棒。"),
    ("Andy Caldwell",
     b"Juuuuuulia..",
     "茱~~~~~莉亞．．"),
    ("Mark Caldwell",
     b"Women\xa1\x49",                       # "Women！"
     "女人啊！"),
    ("Mike Clement",
     b"Trojans are the superior brand.",
     "特洛伊才是最棒的牌子。"),
    ("Richard Espy",
     b"Poker, anyone\xa1\x48",               # "Poker, anyone？"
     "來局撲克如何？"),
    ("Douglas Grounds",
     b"Sit, Toto\xa1\x49 Sit\xa1\x49",       # "Sit, Toto！ Sit！"
     "坐下，托托！坐下！"),
    ("Dave Hathaway",
     b"You too shall be honored. . .\x0a\x0aBoot to the head\xa1\x49",
     "你也將獲得殊榮．．．\n\n一靴踢上腦門！"),
    ("Bonnie Long-Hemsath",
     b"Remember - reality is user-defined.  Go therefore and take responsibility for your reality.  If it is not as you would have it, create a new one.  It can be done.",
     "記住—現實由你自己定義。所以去吧，為你的現實負起責任。如果它不符合你的期望，就創造一個新的。這是辦得到的。"),
    ("Todd Hendrix",
     b"\x0c\x31\x38Lick the Chalice\xa1\x49\x0c\x30\x30",  # color codes wrap
     "舔聖杯吧！"),
    ("Eric Hyman",
     b"Jay + C = Hap + E.",
     "Jay + C = 快 + 樂。"),
    ("Louis Johnson",
     b"Where's the nearest jam\xa1\x48",     # "Where's the nearest jam？"
     "最近的爵士 jam 在哪？"),
    # Eric Newhouse's name includes a class-of-1292 tag; his quote is the
    # Crimson/Leverett Hoops shoutout
    ("Eric Newhouse'\x0c\x31\x32\x39\x32\x0c\x30\x30",
     b"Go\x0c\x30\x37Crimson\x0c\x30\x30\xa1\x49\x0a\x0aJa^2,  Rubes,  Fitz,  Visc,  &  House:\x0a\x0a\x0c\x31\x38Leverett Hoops'92\xa1\x49\x0c\x30\x30",
     "哈佛深紅加油！Ja^2、Rubes、Fitz、Visc、& House：Leverett 籃球隊 '92！"),
    ("Paul Rattner",
     b"To all my creditors:\x0a\x0a\x0aDon't call me; I'll call you.\x0a\x0aPS.  Your check is in the mail.",
     "致所有債主：\n\n別打給我，我會打給你。\n\n附註：支票已經寄出了。"),
    ("Scott T. Smith",
     b"Debbo-meister.",
     "Debbo 大師。"),
    ("Allen Treschler",
     b"FOOL'S MATE\x0a\x0a1.) P-KB4   P-K3\x0a2.) P-KN4   Q-R5 mate\xa1\x49\x0a\x0ais the fastest kill there is.",
     "傻瓜將死局\n\n1.) P-KB4   P-K3\n2.) P-KN4   Q-R5 將軍！\n\n是史上最快的殺局。"),
    ("Jon Van Canegham",
     b"Life is a game.  Let's play\xa1\x49",
     "人生如戲，玩起來吧！"),
]


def patch_abdb():
    data = open(SRC, "rb").read()
    print(f"Original ABDB.BIN: {len(data)} bytes")

    out = bytearray()
    pos = 0
    # Find pos of first developer quote ("Benjamin Bent" at 0x111)
    first_name = b"Benjamin Bent\x00"
    bb_pos = data.find(first_name)
    if bb_pos < 0:
        sys.exit("ERR: Cannot find 'Benjamin Bent' marker in ABDB.BIN")
    print(f"Developer credits start at 0x{bb_pos:X}")

    # Copy everything up to (and including) "Benjamin Bent\0"
    out.extend(data[:bb_pos])
    pos = bb_pos

    # Iterate through the translation table.
    # ABDB format: alternating Name\0 Quote\0, but our table groups them.
    # We need to handle the case where some entries have None for name
    # (a collective shoutout instead of name).
    for entry in TRANSLATIONS:
        name, quote_old, zh = entry

        # Read the next string from `data` at pos — should be the name (or shoutout)
        nul = data.index(b"\x00", pos)
        cur_string = data[pos:nul]

        if name is not None:
            # Should match the expected name
            if cur_string != name.encode("latin-1"):
                print(f"WARN at 0x{pos:X}: expected name '{name}', got {render(cur_string)!r}")
            # Copy name as-is + null (use original bytes from file, not re-encoded)
            out.extend(cur_string + b"\x00")
            pos = nul + 1
            # Now read the quote
            nul2 = data.index(b"\x00", pos)
            cur_quote = data[pos:nul2]
            if cur_quote != quote_old:
                print(f"WARN at 0x{pos:X}: quote mismatch for {name}:")
                print(f"  expected: {render(quote_old)!r}")
                print(f"  found:    {render(cur_quote)!r}")
            # Build new quote: English + \n\n + Chinese
            sep = b"\x0a\x0a"
            zh_bytes = zh.encode("big5")
            new_quote = cur_quote + sep + zh_bytes
            out.extend(new_quote + b"\x00")
            pos = nul2 + 1
            print(f"  '{name}' quote: {len(cur_quote)} → {len(new_quote)} bytes (+{len(new_quote)-len(cur_quote)})")
        else:
            # Treat as quote-only (no preceding name)
            if cur_string != quote_old:
                print(f"WARN at 0x{pos:X}: collective shoutout mismatch:")
                print(f"  expected: {render(quote_old)!r}")
                print(f"  found:    {render(cur_string)!r}")
            sep = b"\x0a\x0a"
            zh_bytes = zh.encode("big5")
            new_quote = cur_string + sep + zh_bytes
            out.extend(new_quote + b"\x00")
            pos = nul + 1
            print(f"  [collective] quote: {len(cur_string)} → {len(new_quote)} bytes (+{len(new_quote)-len(cur_string)})")

    # Append the remaining tail (anything after last developer quote)
    out.extend(data[pos:])

    print(f"\nPatched ABDB.BIN: {len(out)} bytes (+{len(out)-len(data)})")

    with open(OUT, "wb") as f:
        f.write(out)
    print(f"written: {OUT}")

    return out


if __name__ == "__main__":
    patch_abdb()
