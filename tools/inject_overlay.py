"""Inject patched overlay into mm3.cc as an UNCOMPRESSED entry.

Strategy:
  1. Read mm3.cc.bak (original)
  2. Parse encrypted header to find overlay entry (hash 0x8F99)
  3. Compute the size+offset to append our patched overlay
  4. Append patched overlay raw at end of mm3.cc
  5. Update entry: new offset, new compressedSize=22202
  6. Re-encrypt header
  7. Write new mm3.cc

Rewolf format (from Source.cpp):
  [0:2]    LE uint16   header_count_x8 (i.e. number of entries * 8)
  [2:H+2]  encrypted FileEntry array (each 8 bytes)
  [H+2:..] file data blobs

  decrypt: for i in range(size): buf[i] = rotl8(buf[i], 2) + key; key += 0x67  (start key=0xAC)
  encrypt: for i in range(size): buf[i] = rotr8(buf[i] - key, 2); key += 0x67  (start key=0xAC)
  rotl8(b, n) = ((b << n) | (b >> (8-n))) & 0xFF

  FileEntry (8 bytes):
    uint16 hash
    uint16 offsetLo
    uint8  offsetHi
    uint16 compressedSize
    uint8  padding
"""
import os, sys, struct, hashlib, shutil
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\03_game_tmp\1991_魔法門3_幻島歷險記_Might And Magic III\mm3c"
MM3CC = os.path.join(ROOT, "mm3.cc")
BAK = os.path.join(ROOT, "mm3.cc.bak")
NEW = os.path.join(ROOT, "mm3.cc.injected")
OVERLAY = os.path.join(ROOT, "out_cc_dump", "_UNKNOWN_FILE_8F99.BIN")
OVERLAY_HASH = 0x8F99


def rotl8(b, n):
    return ((b << n) | (b >> (8 - n))) & 0xFF


def rotr8(b, n):
    return ((b >> n) | (b << (8 - n))) & 0xFF


def crypt_header(buf, encrypt=False):
    """In-place encrypt/decrypt of header bytes (after the 2-byte count)."""
    key = 0xAC
    out = bytearray(buf)
    for i in range(len(out)):
        if encrypt:
            out[i] = rotr8((out[i] - key) & 0xFF, 2)
        else:
            out[i] = (rotl8(out[i], 2) + key) & 0xFF
        key = (key + 0x67) & 0xFF
    return bytes(out)


def parse_entries(decrypted_hdr):
    entries = []
    for i in range(0, len(decrypted_hdr), 8):
        e = decrypted_hdr[i:i+8]
        hash_ = struct.unpack("<H", e[0:2])[0]
        off_lo = struct.unpack("<H", e[2:4])[0]
        off_hi = e[4]
        comp_size = struct.unpack("<H", e[5:7])[0]
        padding = e[7]
        offset = (off_hi << 16) | off_lo
        entries.append([hash_, offset, comp_size, padding])
    return entries


def build_entries(entries):
    out = bytearray()
    for hash_, offset, comp_size, padding in entries:
        out += struct.pack("<H", hash_)
        out += struct.pack("<H", offset & 0xFFFF)
        out += bytes([(offset >> 16) & 0xFF])
        out += struct.pack("<H", comp_size & 0xFFFF)
        out += bytes([padding & 0xFF])
    return bytes(out)


def main():
    src = BAK if os.path.exists(BAK) else MM3CC
    cc = open(src, "rb").read()
    print(f"Source: {src} ({len(cc)} bytes)")

    overlay = open(OVERLAY, "rb").read()
    print(f"Overlay (patched): {len(overlay)} bytes")
    # Verify patch
    assert overlay[0x1DFA] == 0x0F, f"Overlay NOT patched: byte at 0x1DFA = {overlay[0x1DFA]:#x}"
    assert overlay[0:2] != bytes([overlay[0], overlay[0]]), "overlay first 2 bytes are same — won't be treated as uncompressed!"
    print(f"  byte[0x1DFA] = {overlay[0x1DFA]:#x} (mov bx, 15) ✓")
    print(f"  first 2 bytes: {overlay[0]:02X} {overlay[1]:02X} (low != high ✓)")

    # Parse header
    n_entries = struct.unpack("<H", cc[0:2])[0]
    header_size = n_entries * 8
    print(f"\nHeader: {n_entries} entries ({header_size} bytes)")

    encrypted_hdr = cc[2:2 + header_size]
    decrypted_hdr = crypt_header(encrypted_hdr, encrypt=False)
    entries = parse_entries(decrypted_hdr)

    # Find overlay entry
    overlay_idx = None
    for i, e in enumerate(entries):
        if e[0] == OVERLAY_HASH:
            overlay_idx = i
            print(f"  Overlay entry [{i}]: hash={e[0]:04X}, offset={e[1]:#x}, compSize={e[2]}, pad={e[3]}")
            break
    if overlay_idx is None:
        raise SystemExit("Overlay hash not found!")

    # Plan: append overlay raw at end of file. Update entry.
    new_offset = len(cc)
    new_size = len(overlay)
    print(f"\nNew overlay placement: offset={new_offset:#x}, size={new_size}")

    # Sanity: 24-bit offset limit
    if new_offset > 0xFFFFFF:
        raise SystemExit(f"Offset {new_offset:#x} exceeds 24-bit field!")

    entries[overlay_idx][1] = new_offset
    entries[overlay_idx][2] = new_size
    # padding stays 0

    # Rebuild header
    new_decrypted = build_entries(entries)
    new_encrypted = crypt_header(new_decrypted, encrypt=True)

    # Sanity check: re-decrypt and compare
    rt = crypt_header(new_encrypted, encrypt=False)
    assert rt == new_decrypted, "encrypt/decrypt roundtrip failed"

    # Build new mm3.cc
    out = bytearray(cc)
    # replace header bytes
    out[2:2 + header_size] = new_encrypted
    # append overlay
    out += overlay
    open(NEW, "wb").write(bytes(out))
    print(f"\nNew mm3.cc: {NEW} ({len(out)} bytes)")
    print(f"  md5: {hashlib.md5(bytes(out)).hexdigest()}")
    print(f"  original md5: {hashlib.md5(cc).hexdigest()}")

    # Install
    shutil.copy2(NEW, MM3CC)
    print(f"\nInstalled to {MM3CC}")


if __name__ == "__main__":
    main()
