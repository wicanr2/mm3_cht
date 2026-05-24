"""mm3_goto.py — patch the party position in an MM3 save file.

Usage:
  py mm3_goto.py SAVE0X.MM3                       # default: go to 祕密區 (1,14,0x69)
  py mm3_goto.py SAVE0X.MM3 --loc 0x69 --x 1 --y 14
  py mm3_goto.py SAVE0X.MM3 --name 火峰鎮          # by displayed name
  py mm3_goto.py --list                            # list all 67 known locations

The save file is patched in place after creating a .bak backup. Load the saved
slot in MM3 to appear at the new position.

Save-file format (verified against SAVE00..SAVE09 in mm3c/):
  offset 0x2B2E = X coordinate (0..15 typical)
  offset 0x2B2F = Y coordinate (0..15 typical)
  offset 0x2B30 = LOC code (1..0x42 for named maps; 0x69 for 祕密區)
"""
import sys, os, argparse, shutil

# ---- LOC code table -----------------------------------------------------
# Names appear in mm3b.exe at file offset 0x1F64C as a contiguous list of
# null-terminated BIG5 strings. Index → LOC code is direct (LOC = index).
# 祕密區 has internal LOC 0x69 (not in the 0..0x42 named-list range).
LOCATIONS = [
    (0x00, "無 (none)"),
    (0x01, "泉頂鎮 (Fountain Head)"),
    (0x02, "望海鎮 (Baywatch)"),
    (0x03, "荒原鎮 (Wildabar)"),
    (0x04, "沼澤鎮 (Swamp Town)"),
    (0x05, "火峰鎮 (Blistering Heights)"),
    (0x06, "泉頂鎮洞穴"),
    (0x07, "望海鎮洞穴"),
    (0x08, "荒原鎮洞穴"),
    (0x09, "沼澤鎮洞穴"),
    (0x0A, "火峰鎮洞穴"),
    (0x0B, "獨眼巨人洞穴"),
    (0x0C, "蜘蛛洞穴"),
    (0x0D, "寒咒洞穴"),
    (0x0E, "龍穴"),
    (0x0F, "魔法洞穴"),
    (0x10, "古代莫教神殿"),
    (0x11, "邪教禁地"),
    (0x12, "恐怖要塞"),
    (0x13, "痴瘋大殿"),
    (0x14, "黑武士要塞"),
    (0x15, "殘殺教堂"),
    (0x16, "驚魂古墓"),
    (0x17, "地獄迷宮"),
    (0x18, "白盾堡"),
    (0x19, "血權堡"),
    (0x1A, "龍牙堡"),
    (0x1B, "陰風堡"),
    (0x1C, "黑風堡"),
    (0x1D, "白盾堡地下城"),
    (0x1E, "血權堡地下城"),
    (0x1F, "龍牙堡地下城"),
    (0x20, "陰風堡地下城"),
    (0x21, "黑風堡地下城"),
    (0x22, "α引擎室"),
    (0x23, "主引擎室"),
    (0x24, "β引擎室"),
    (0x25, "後段貨艙"),
    (0x26, "中央控制室"),
    (0x27, "前段貨艙"),
    (0x28, "主控制室"),
    (0x29, "A1"), (0x2A, "A2"), (0x2B, "A3"), (0x2C, "A4"),
    (0x2D, "B1"), (0x2E, "B2"), (0x2F, "B3"), (0x30, "B4"),
    (0x31, "C1"), (0x32, "C2"), (0x33, "C3"), (0x34, "C4"),
    (0x35, "D1"), (0x36, "D2"), (0x37, "D3"), (0x38, "D4"),
    (0x39, "E1"), (0x3A, "E2"), (0x3B, "E3"), (0x3C, "E4"),
    (0x3D, "F1"), (0x3E, "F2"), (0x3F, "F3"), (0x40, "F4"),
    (0x41, "祕密區 (mm3b 名稱表索引)"),     # name-table index, not the LOC code
    (0x42, "競技場 (Arena)"),
    # Verified separately: actual LOC code for 祕密區 in the engine
    (0x69, "祕密區 (Secret Area — only via memory edit / this tool)"),
]

OFFSET_X   = 0x2B2E
OFFSET_Y   = 0x2B2F
OFFSET_LOC = 0x2B30


def list_locations():
    print("LOC   Name")
    print("----  ----------------------------------------")
    for loc, name in LOCATIONS:
        print(f"0x{loc:02X}  {name}")


def parse_int(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


def patch_save(path, x, y, loc, no_backup=False):
    if not os.path.exists(path):
        sys.exit(f"error: file not found: {path}")
    size = os.path.getsize(path)
    if size != 207551:
        print(f"warning: expected 207551 bytes, got {size} — proceeding anyway")

    data = bytearray(open(path, "rb").read())
    old = (data[OFFSET_X], data[OFFSET_Y], data[OFFSET_LOC])
    print(f"current  X=0x{old[0]:02X}  Y=0x{old[1]:02X}  LOC=0x{old[2]:02X}")
    print(f"new      X=0x{x:02X}  Y=0x{y:02X}  LOC=0x{loc:02X}")

    if (x, y, loc) == old:
        print("no change needed.")
        return

    if not no_backup:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
            print(f"backup written: {bak}")

    data[OFFSET_X]   = x & 0xFF
    data[OFFSET_Y]   = y & 0xFF
    data[OFFSET_LOC] = loc & 0xFF
    with open(path, "wb") as f:
        f.write(data)
    print(f"patched: {path}")


def main():
    p = argparse.ArgumentParser(description="Teleport an MM3 (CHT) save file's party.")
    p.add_argument("save", nargs="?", help="path to SAVE0X.MM3")
    p.add_argument("--x",   type=parse_int, default=1,    help="X (default 1)")
    p.add_argument("--y",   type=parse_int, default=14,   help="Y (default 14 = 0x0E)")
    p.add_argument("--loc", type=parse_int, default=0x69, help="LOC code (default 0x69 = 祕密區)")
    p.add_argument("--name", help="lookup by displayed name (overrides --loc)")
    p.add_argument("--list", action="store_true", help="list all known LOC codes")
    p.add_argument("--no-backup", action="store_true", help="skip .bak creation")
    args = p.parse_args()

    if args.list:
        list_locations(); return

    if not args.save:
        p.print_help(); sys.exit(1)

    loc = args.loc
    if args.name:
        # Prefer exact start-of-name match (drops the parenthetical translation)
        bare = lambda s: s.split(" ", 1)[0]
        exact = [code for code, n in LOCATIONS if bare(n) == args.name]
        if exact:
            loc = exact[0]
        else:
            match = [code for code, n in LOCATIONS if args.name in n]
            if not match:
                sys.exit(f"error: no location matches name {args.name!r}")
            if len(match) > 1:
                opts = ", ".join(f"0x{c:02X}={n}" for c, n in LOCATIONS if c in match)
                sys.exit(f"error: ambiguous name {args.name!r} — matches: {opts}")
            loc = match[0]

    patch_save(args.save, args.x, args.y, loc, args.no_backup)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
