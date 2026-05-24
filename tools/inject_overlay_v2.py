"""Inject patched overlay as a CORRECTLY-COMPRESSED entry, appended at end of mm3.cc."""
import os, sys, struct, hashlib, shutil
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"
sys.path.insert(0, ROOT)
from inject_overlay import crypt_header, parse_entries, build_entries
from lzhuf_compress import lzhuf_compress, stat_file

MM3CC = os.path.join(ROOT, "mm3.cc")
BAK = os.path.join(ROOT, "mm3.cc.bak")
NEW = os.path.join(ROOT, "mm3.cc.injected_v2")
OVERLAY = os.path.join(ROOT, "out_cc_dump", "_UNKNOWN_FILE_8F99.BIN")
OVERLAY_HASH = 0x8F99


def main():
    cc = open(BAK, "rb").read()
    overlay = open(OVERLAY, "rb").read()
    assert overlay[0x1DFA] == 0x0F, f"Overlay not patched"
    print(f"Source mm3.cc.bak: {len(cc)} bytes")
    print(f"Patched overlay: {len(overlay)} bytes (byte 0x1DFA = {overlay[0x1DFA]:#x})")

    # Compress
    iv = stat_file(overlay)
    print(f"  iv = {iv:#x}")
    compressed = lzhuf_compress(overlay, iv)
    print(f"  compressed: {len(compressed)} bytes")

    # Build entry data: 4-byte header + compressed bytes
    # Per Source.cpp pack code:
    #   filesBuffer[curOff] = iv
    #   filesBuffer[curOff + 1] = iv
    #   filesBuffer[curOff + 2] = (fSize >> 8) & 0xFF   <-- decompSize hi
    #   filesBuffer[curOff + 3] = fSize & 0xFF          <-- decompSize lo
    decompSize = len(overlay)
    entry_data = bytes([iv, iv, (decompSize >> 8) & 0xFF, decompSize & 0xFF]) + compressed
    print(f"  total entry data: {len(entry_data)} bytes")

    # Verify by decompressing
    from lzhuf_decompress import lzhuf_decompress
    re_decomp = lzhuf_decompress(entry_data[4:], decompSize, entry_data[0])
    assert re_decomp == overlay, "Compression round-trip failed!"
    print("  ✓ round-trip verified")

    # Find overlay entry in header
    n_entries = struct.unpack("<H", cc[0:2])[0]
    hdr_size = n_entries * 8
    dec = crypt_header(cc[2:2+hdr_size], encrypt=False)
    entries = parse_entries(dec)
    idx = next(i for i, e in enumerate(entries) if e[0] == OVERLAY_HASH)
    print(f"\nOverlay entry [{idx}]: hash={entries[idx][0]:04X}")
    print(f"  orig: offset={entries[idx][1]:#x}, compSize={entries[idx][2]}")

    # Update: point to end-of-file, set new compressedSize
    new_offset = len(cc)
    new_compSize = len(entry_data)
    print(f"  new : offset={new_offset:#x}, compSize={new_compSize}")
    entries[idx][1] = new_offset
    entries[idx][2] = new_compSize

    # Rebuild header
    new_decrypted = build_entries(entries)
    new_encrypted = crypt_header(new_decrypted, encrypt=True)

    # Write new mm3.cc
    out = bytearray(cc)
    out[2:2+hdr_size] = new_encrypted
    out += entry_data
    open(NEW, "wb").write(bytes(out))
    print(f"\nWrote {NEW} ({len(out)} bytes)")
    print(f"  md5: {hashlib.md5(bytes(out)).hexdigest()}")
    shutil.copy2(NEW, MM3CC)
    print(f"  installed to {MM3CC}")


if __name__ == "__main__":
    main()
