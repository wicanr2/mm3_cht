"""Dump real codeword pointer→string + LOC/X/Y for all 13 mirror slots."""
import sys, struct
sys.stdout.reconfigure(encoding="utf-8")

d = open("mm3b.exe", "rb").read()
PTR_TABLE   = 0x1E608
LOC_TABLE   = 0x1B874
X_TABLE     = 0x1B881
Y_TABLE     = 0x1B88E
HEADER      = 0xE00
STRING_DS   = 0x1831 * 16   # 0x18310

print(f"{'idx':3s}  {'ptr':6s}  {'string':<18s}  {'LOC':4s}  {'X':4s}  {'Y':4s}")
print("-" * 60)
for i in range(13):
    ptr = struct.unpack_from("<H", d, PTR_TABLE + i*2)[0]
    file_off = HEADER + STRING_DS + ptr
    s = d[file_off:file_off+30]
    try:
        decoded = s.split(b'\x00')[0].decode('big5')
    except Exception:
        decoded = "(decode err)"
    loc = d[LOC_TABLE + i]
    x   = d[X_TABLE + i]
    y   = d[Y_TABLE + i]
    marker = "  ← 祕密區" if loc == 0x69 and (x, y) == (3, 14) else ""
    print(f"{i:3d}  0x{ptr:04X}  '{decoded}'{' '*(15-len(decoded)*2)}  0x{loc:02X}  0x{x:02X}  0x{y:02X}{marker}")
