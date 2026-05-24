"""Redirect slot 7 codeword string pointer: 火 → 祕密區 (already in binary).

The mirror codeword pointer table is at file 0x1E608.
Slot 7's pointer is at file 0x1E616 (= 0x1E608 + 7*2).
Currently it points to '火' string at file 0x1E8EB (in-seg 0x57DB for DS 0x1831).

「祕密區」(BIG5 祕=AF A6 礻 radical) already exists at file 0x1F811 — that's the
HUD display-name table entry, NOT a codeword. We can reuse it by redirecting
slot 7's pointer there.

For DS para 0x1831:
  file 0x1F811 → image 0x1F011 → in-seg offset = 0x1F011 - 0x18310 = 0x6D01

Patch: 2 bytes at file 0x1E616: DB 57  →  01 6D

Net effect after this + the prior LOC/X/Y patch:
  Typing「祕密區」  → matches slot 7 → warp to LOC 0x69, X=3, Y=14 ✓
  Typing「火」      → no match (slot 7 string is now 祕密區)
  Other 12 codewords UNCHANGED.
"""
import sys, os, shutil, struct, argparse

EXE = "mm3b.exe"
PTR_OFFSET = 0x1E616          # slot 7 pointer location in file
PTR_OLD = bytes([0xDB, 0x57])  # 0x57DB → '火'
PTR_NEW = bytes([0x01, 0x6D])  # 0x6D01 → '祕密區'


def find_exe():
    if os.path.exists(EXE): return EXE
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, EXE)
    if os.path.exists(p): return p
    sys.exit(f"error: {EXE} not found")


def show(path):
    d = open(path, "rb").read()
    ptr = struct.unpack_from("<H", d, PTR_OFFSET)[0]
    target_file = 0xE00 + 0x18310 + ptr
    if target_file + 8 <= len(d):
        tail = d[target_file:target_file+8]
        try:
            decoded = tail.split(b'\x00')[0].decode('big5')
        except Exception:
            decoded = "(decode err)"
    else:
        decoded = "(oob)"
    print(f"slot 7 ptr @ 0x{PTR_OFFSET:X}: 0x{ptr:04X} → file 0x{target_file:X} → {decoded!r}")


def apply_patch(path, no_backup=False):
    d = bytearray(open(path, "rb").read())
    cur = bytes(d[PTR_OFFSET:PTR_OFFSET+2])
    if cur == PTR_NEW:
        print("Already patched. No change."); return
    if cur != PTR_OLD:
        print(f"warning: pointer bytes don't match expected {PTR_OLD.hex(' ')}, found {cur.hex(' ')}")
        ans = input("Proceed? [y/N]: ").strip().lower()
        if ans != "y": sys.exit("aborted")
    if not no_backup:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak); print(f"backup written: {bak}")
    d[PTR_OFFSET:PTR_OFFSET+2] = PTR_NEW
    open(path, "wb").write(d)
    print(f"patched: ptr {PTR_OLD.hex(' ')} → {PTR_NEW.hex(' ')} at file 0x{PTR_OFFSET:X}")


def revert(path):
    bak = path + ".bak"
    if not os.path.exists(bak): sys.exit(f"no backup: {bak}")
    shutil.copy2(bak, path); print(f"restored from {bak}")


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--verify", action="store_true")
    g.add_argument("--revert", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    a = p.parse_args()
    path = find_exe()
    if a.verify:    show(path)
    elif a.revert:  revert(path); show(path)
    else:           apply_patch(path, a.no_backup); show(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
