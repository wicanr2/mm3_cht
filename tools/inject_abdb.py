"""Inject patched ABDB_zh.BIN into mm3.cc (preserving any existing patches).

Uses current mm3.cc as base — re-running grows the file (orphan old entries).
For clean state, restore from mm3.cc.bak first.
"""
import os, sys, struct, hashlib, shutil
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"
sys.path.insert(0, ROOT)
from inject_overlay import crypt_header, parse_entries, build_entries
from lzhuf_compress import lzhuf_compress, stat_file
from lzhuf_decompress import lzhuf_decompress

MM3CC   = os.path.join(ROOT, "mm3.cc")
BACKUP  = os.path.join(ROOT, "mm3.cc.preABDB.bak")    # snapshot before our patch
NEW     = os.path.join(ROOT, "mm3.cc.injected_abdb")
PAYLOAD = os.path.join(ROOT, "ABDB_zh.BIN")
ABDB_HASH = 0xABDB


def main():
    if not os.path.exists(PAYLOAD):
        sys.exit(f"missing {PAYLOAD} — run patch_abdb_credits.py first")

    cc = open(MM3CC, "rb").read()
    overlay = open(PAYLOAD, "rb").read()
    print(f"Source mm3.cc: {len(cc)} bytes")
    print(f"ABDB_zh.BIN: {len(overlay)} bytes")

    # Snapshot current mm3.cc before our patch (only first time)
    if not os.path.exists(BACKUP):
        shutil.copy2(MM3CC, BACKUP)
        print(f"pre-ABDB snapshot: {BACKUP}")

    # Compress
    iv = stat_file(overlay)
    print(f"  iv = {iv:#x}")
    compressed = lzhuf_compress(overlay, iv)
    print(f"  compressed: {len(compressed)} bytes")

    decompSize = len(overlay)
    entry_data = bytes([iv, iv,
                        (decompSize >> 8) & 0xFF,
                        decompSize & 0xFF]) + compressed
    print(f"  total entry data: {len(entry_data)} bytes")

    # Round-trip verify
    re_decomp = lzhuf_decompress(entry_data[4:], decompSize, entry_data[0])
    assert re_decomp == overlay, "Compression round-trip FAILED"
    print("  round-trip verified")

    # Parse mm3.cc header
    n_entries = struct.unpack("<H", cc[0:2])[0]
    hdr_size = n_entries * 8
    dec = crypt_header(cc[2:2+hdr_size], encrypt=False)
    entries = parse_entries(dec)
    idx = next(i for i, e in enumerate(entries) if e[0] == ABDB_HASH)
    print(f"\nABDB entry [{idx}]: hash={entries[idx][0]:04X}")
    print(f"  orig: offset={entries[idx][1]:#x}, compSize={entries[idx][2]}")

    # New offset = end of current mm3.cc
    new_offset  = len(cc)
    new_compSize = len(entry_data)
    print(f"  new : offset={new_offset:#x}, compSize={new_compSize}")
    entries[idx][1] = new_offset
    entries[idx][2] = new_compSize

    # Rebuild header
    new_decrypted = build_entries(entries)
    new_encrypted = crypt_header(new_decrypted, encrypt=True)

    out = bytearray(cc)
    out[2:2+hdr_size] = new_encrypted
    out += entry_data
    open(NEW, "wb").write(bytes(out))
    print(f"\nwrote {NEW} ({len(out)} bytes)")
    print(f"  md5: {hashlib.md5(bytes(out)).hexdigest()}")
    shutil.copy2(NEW, MM3CC)
    print(f"  installed to {MM3CC}")


if __name__ == "__main__":
    main()
