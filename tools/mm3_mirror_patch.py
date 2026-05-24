"""mm3_mirror_patch.py — patch mm3b.exe to repurpose a Mirror codeword.

The Chinese MM3 Mirror (傳送鏡) accepts 13 hard-coded text codewords. Each maps
to (LOC, X, Y) destination data via three parallel 13-byte arrays in mm3b.exe.

Verified offsets:
  0x1B874 = LOC[13]   (verified — change here makes 風 go to a different map)
Speculated offsets (probe to verify):
  0x1B881 = X[13]     (preamble of 7 zeros for towns/arena/ending, then explicit values)
  0x1B88E = Y[13]     (Y array boundary unsure — adjacent to 'Error...' fmt string)

Codeword index 0..12 in pointer table 0x1E608:
  0 家園        1 海狗      2 自由人    3 命運      4 火熱
  5 競技場      6 最後倒數昇空           7 火        8 水
  9 土          10 風       11 大膽混進龍穴        12 偷拿究力神珠

User's target: warp directly to 祕密區 = (X=1, Y=14, LOC=0x69), which is the
treasure room inside the F1 map (LOC 0x69).

Usage:
  py mm3_mirror_patch.py --dump
  py mm3_mirror_patch.py --target 風                # legacy: LOC only
  py mm3_mirror_patch.py --target 風 --x 1 --y 14   # set LOC=0x69 + X + Y
  py mm3_mirror_patch.py --target 風 --x 10 --y 10 --probe   # distinctive probe
  py mm3_mirror_patch.py --revert
"""
import sys, os, argparse, shutil, struct

EXE = "mm3b.exe"
LOC_TABLE_OFFSET = 0x1B874
X_TABLE_OFFSET   = 0x1B881   # speculated
Y_TABLE_OFFSET   = 0x1B88E   # speculated
TABLE_LEN = 13

ENTRIES = [
    (0,  "家園",          "泉頂鎮"),
    (1,  "海狗",          "望海鎮"),
    (2,  "自由人",        "荒原鎮"),
    (3,  "命運",          "沼澤鎮"),
    (4,  "火熱",          "火峰鎮"),
    (5,  "競技場",        "競技場"),
    (6,  "最後倒數昇空",  "觀賞過關畫面"),
    (7,  "火",            "火焰島"),
    (8,  "水",            "死亡沼澤"),
    (9,  "土",            "孤獨沙漠"),
    (10, "風",            "寒冰島"),
    (11, "大膽混進龍穴",  "龍穴"),
    (12, "偷拿究力神珠",  "金字塔後段貨艙密室"),
]
SECRET_LOC = 0x69


def find_exe():
    if os.path.exists(EXE): return EXE
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, EXE)
    if os.path.exists(p): return p
    sys.exit(f"error: {EXE} not found in cwd or script dir")


def read_table(path, off):
    data = open(path, "rb").read()
    return list(data[off : off + TABLE_LEN])


def dump(path):
    locs = read_table(path, LOC_TABLE_OFFSET)
    xs   = read_table(path, X_TABLE_OFFSET)
    ys   = read_table(path, Y_TABLE_OFFSET)
    print(f"Codeword tables in {path}:")
    print(f"  LOC @ 0x{LOC_TABLE_OFFSET:X}")
    print(f"  X   @ 0x{X_TABLE_OFFSET:X}  (speculated)")
    print(f"  Y   @ 0x{Y_TABLE_OFFSET:X}  (speculated)")
    print()
    print(f"  idx  LOC   X     Y     codeword               default")
    print(f"  ---  ----  ----  ----  ---------------------  --------------------")
    for (idx, cw, dest), loc, x, y in zip(ENTRIES, locs, xs, ys):
        marker = "  <-- 祕密區 LOC" if loc == SECRET_LOC else ""
        print(f"  {idx:3d}  0x{loc:02X}  0x{x:02X}  0x{y:02X}  {cw:<22} {dest}{marker}")


def patch(path, target_codeword, new_x=None, new_y=None, no_backup=False, probe=False):
    match = [i for i, (idx, cw, _) in enumerate(ENTRIES) if cw == target_codeword]
    if not match:
        opts = ", ".join(cw for _, cw, _ in ENTRIES)
        sys.exit(f"error: '{target_codeword}' not found. Options: {opts}")
    idx = match[0]
    loc_off = LOC_TABLE_OFFSET + idx
    x_off   = X_TABLE_OFFSET   + idx
    y_off   = Y_TABLE_OFFSET   + idx

    data = bytearray(open(path, "rb").read())
    old_loc, old_x, old_y = data[loc_off], data[x_off], data[y_off]

    print(f"target codeword: {target_codeword}  (idx {idx})")
    print(f"  LOC: 0x{loc_off:X}  0x{old_loc:02X} -> 0x{SECRET_LOC:02X}")
    if new_x is not None:
        print(f"  X  : 0x{x_off:X}  0x{old_x:02X} -> 0x{new_x:02X}")
    if new_y is not None:
        print(f"  Y  : 0x{y_off:X}  0x{old_y:02X} -> 0x{new_y:02X}")

    if not no_backup:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
            print(f"  backup written: {bak}")

    data[loc_off] = SECRET_LOC
    if new_x is not None: data[x_off] = new_x & 0xFF
    if new_y is not None: data[y_off] = new_y & 0xFF
    open(path, "wb").write(data)
    print(f"  patched: {path}")

    if probe:
        print(f"\n=== PROBE MODE ===")
        print(f"In DOSBox: open Mirror, type '{target_codeword}'.")
        print(f"Expected landing IF speculated X/Y offsets are correct:")
        print(f"  LOC = 0x{SECRET_LOC:02X} (F1 map)")
        print(f"  X   = {new_x if new_x is not None else old_x}")
        print(f"  Y   = {new_y if new_y is not None else old_y}")
        print(f"Use GameMaster to verify actual party X/Y/LOC after teleport.")
        print(f"If X/Y do NOT match, the speculated offsets are wrong — report observed values.")
    else:
        print(f"\nIn-game: open Mirror, type '{target_codeword}'. Party should warp to (X,Y,LOC).")


def revert(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        sys.exit(f"error: no backup at {bak}")
    shutil.copy2(bak, path)
    print(f"restored {path} from {bak}")


def parse_int(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


def main():
    p = argparse.ArgumentParser(description="Patch the Chinese MM3 Mirror codeword tables.")
    p.add_argument("--exe", default=None, help="path to mm3b.exe (default: ./mm3b.exe)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dump",   action="store_true", help="show current LOC/X/Y tables")
    g.add_argument("--target", help="codeword to repurpose (e.g. 風)")
    g.add_argument("--revert", action="store_true", help="restore mm3b.exe from .bak")
    p.add_argument("--x", type=parse_int, default=None, help="new X for codeword's slot")
    p.add_argument("--y", type=parse_int, default=None, help="new Y for codeword's slot")
    p.add_argument("--probe", action="store_true", help="print verification hints for probe testing")
    p.add_argument("--no-backup", action="store_true")
    args = p.parse_args()

    path = args.exe or find_exe()
    if args.dump:    dump(path)
    elif args.revert: revert(path)
    else:             patch(path, args.target, args.x, args.y, args.no_backup, args.probe)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
