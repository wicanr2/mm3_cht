"""Python port of rewolf's lzhuf_compress.cpp (which is Haruyasu Yoshizaki's LZHUF
modified by ReWolf for MM3.CC format)."""
import struct

# LZHUF constants (must match decoder rwf_lzhuf.cpp)
N = 4096           # buffer size
F = 60             # lookahead buffer size (0x3C)
THRESHOLD = 2
N_CHAR = 256 - THRESHOLD + F  # 314 = 0x13A
T = N_CHAR * 2 - 1            # 627 = 0x273
R = T - 1                     # 626 = 0x272 (root)
MAX_FREQ = 0x8000
NIL = N                       # leaf marker

# Position encoding tables (upper 6 bits of position -> Huffman-like code)
p_len = [
    0x03, 0x04, 0x04, 0x04, 0x05, 0x05, 0x05, 0x05,
    0x05, 0x05, 0x05, 0x05, 0x06, 0x06, 0x06, 0x06,
    0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06,
    0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07,
    0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07,
    0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07,
    0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
    0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
]
p_code = [
    0x00, 0x20, 0x30, 0x40, 0x50, 0x58, 0x60, 0x68,
    0x70, 0x78, 0x80, 0x88, 0x90, 0x94, 0x98, 0x9C,
    0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC,
    0xC0, 0xC2, 0xC4, 0xC6, 0xC8, 0xCA, 0xCC, 0xCE,
    0xD0, 0xD2, 0xD4, 0xD6, 0xD8, 0xDA, 0xDC, 0xDE,
    0xE0, 0xE2, 0xE4, 0xE6, 0xE8, 0xEA, 0xEC, 0xEE,
    0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7,
    0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF,
]


class LzHuffCompress:
    def __init__(self):
        self.out_buf = bytearray()
        self.codesize = 0
        self.text_buf = [0] * (N + F - 1)
        self.match_position = 0
        self.match_length = 0
        self.lson = [0] * (N + 1)
        self.rson = [0] * (N + 257)
        self.dad = [0] * (N + 1)
        self.freq = [0] * (T + 1)
        self.prnt = [0] * (T + N_CHAR)
        self.son = [0] * T
        self.putbuf = 0
        self.putlen = 0

    def init_tree(self):
        for i in range(N + 1, N + 257):
            self.rson[i] = NIL
        for i in range(N):
            self.dad[i] = NIL

    def insert_node(self, r):
        cmp = 1
        key = self.text_buf
        p = N + 1 + key[r]
        self.rson[r] = self.lson[r] = NIL
        self.match_length = 0
        while True:
            if cmp >= 0:
                if self.rson[p] != NIL:
                    p = self.rson[p]
                else:
                    self.rson[p] = r
                    self.dad[r] = p
                    return
            else:
                if self.lson[p] != NIL:
                    p = self.lson[p]
                else:
                    self.lson[p] = r
                    self.dad[r] = p
                    return
            for i in range(1, F):
                cmp = key[r + i] - key[p + i]
                if cmp != 0:
                    break
            else:
                i = F
            if i > THRESHOLD:
                if i > self.match_length:
                    self.match_position = ((r - p) & (N - 1)) - 1
                    self.match_length = i
                    if self.match_length >= F:
                        break
                if i == self.match_length:
                    c = ((r - p) & (N - 1)) - 1
                    if c < self.match_position:
                        self.match_position = c
        self.dad[r] = self.dad[p]
        self.lson[r] = self.lson[p]
        self.rson[r] = self.rson[p]
        self.dad[self.lson[p]] = r
        self.dad[self.rson[p]] = r
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = r
        else:
            self.lson[self.dad[p]] = r
        self.dad[p] = NIL

    def delete_node(self, p):
        if self.dad[p] == NIL:
            return
        if self.rson[p] == NIL:
            q = self.lson[p]
        elif self.lson[p] == NIL:
            q = self.rson[p]
        else:
            q = self.lson[p]
            if self.rson[q] != NIL:
                while self.rson[q] != NIL:
                    q = self.rson[q]
                self.rson[self.dad[q]] = self.lson[q]
                self.dad[self.lson[q]] = self.dad[q]
                self.lson[q] = self.lson[p]
                self.dad[self.lson[p]] = q
            self.rson[q] = self.rson[p]
            self.dad[self.rson[p]] = q
        self.dad[q] = self.dad[p]
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = q
        else:
            self.lson[self.dad[p]] = q
        self.dad[p] = NIL

    def putcode(self, l, c):
        # putbuf is a 16-bit register
        self.putbuf |= (c >> self.putlen) & 0xFFFF
        self.putbuf &= 0xFFFF
        self.putlen += l
        if self.putlen >= 8:
            self.out_buf.append((self.putbuf >> 8) & 0xFF)
            self.putlen -= 8
            if self.putlen >= 8:
                self.out_buf.append(self.putbuf & 0xFF)
                self.codesize += 2
                self.putlen -= 8
                self.putbuf = (c << (l - self.putlen)) & 0xFFFF
            else:
                self.putbuf = (self.putbuf << 8) & 0xFFFF
                self.codesize += 1

    def start_huff(self):
        for i in range(N_CHAR):
            self.freq[i] = 1
            self.son[i] = i + T
            self.prnt[i + T] = i
        i = 0
        j = N_CHAR
        while j <= R:
            self.freq[j] = self.freq[i] + self.freq[i + 1]
            self.son[j] = i
            self.prnt[i] = self.prnt[i + 1] = j
            i += 2
            j += 1
        self.freq[T] = 0xFFFF
        self.prnt[R] = 0

    def reconst(self):
        j = 0
        for i in range(T):
            if self.son[i] >= T:
                self.freq[j] = (self.freq[i] + 1) // 2
                self.son[j] = self.son[i]
                j += 1
        i = 0
        j = N_CHAR
        while j < T:
            k = i + 1
            f = self.freq[i] + self.freq[k]
            self.freq[j] = f
            k = j - 1
            while f < self.freq[k]:
                k -= 1
            k += 1
            l = (j - k) * 1   # number of WORDS to move (we move per-element)
            # memmove freq[k+1..k+1+l] = freq[k..k+l]
            for m in range(l, 0, -1):
                self.freq[k + m] = self.freq[k + m - 1]
            self.freq[k] = f
            for m in range(l, 0, -1):
                self.son[k + m] = self.son[k + m - 1]
            self.son[k] = i
            i += 2
            j += 1
        for i in range(T):
            k = self.son[i]
            if k >= T:
                self.prnt[k] = i
            else:
                self.prnt[k] = self.prnt[k + 1] = i

    def update(self, c):
        if self.freq[R] == MAX_FREQ:
            self.reconst()
        c = self.prnt[c + T]
        while True:
            self.freq[c] += 1
            k = self.freq[c]
            l = c + 1
            if k > self.freq[l]:
                while True:
                    l += 1
                    if k <= self.freq[l]:
                        break
                l -= 1
                self.freq[c] = self.freq[l]
                self.freq[l] = k
                i = self.son[c]
                self.prnt[i] = l
                if i < T:
                    self.prnt[i + 1] = l
                j = self.son[l]
                self.son[l] = i
                self.prnt[j] = c
                if j < T:
                    self.prnt[j + 1] = c
                self.son[c] = j
                c = l
            c = self.prnt[c]
            if c == 0:
                break

    def encode_char(self, c):
        j = 0
        i = 0
        k = self.prnt[c + T]
        # travel from leaf to root
        while True:
            i >>= 1
            if k & 1:
                i += 0x8000
            j += 1
            k = self.prnt[k]
            if k == R:
                break
        self.putcode(j, i & 0xFFFF)
        self.update(c)

    def encode_position(self, c):
        i = c >> 6
        self.putcode(p_len[i], (p_code[i] << 8) & 0xFFFF)
        self.putcode(6, ((c & 0x3F) << 10) & 0xFFFF)

    def encode_end(self):
        if self.putlen:
            self.out_buf.append((self.putbuf >> 8) & 0xFF)
            self.codesize += 1

    def compress(self, in_buf, init_value):
        in_size = len(in_buf)
        textsize = 0
        self.start_huff()
        self.init_tree()
        s = 0
        r = N - F
        for i in range(s, r):
            self.text_buf[i] = init_value
        in_pos = 0
        for length in range(F):
            if in_pos < in_size:
                self.text_buf[r + length] = in_buf[in_pos]
                in_pos += 1
            else:
                break
        else:
            length = F  # the loop completed
        if 'length' not in dir():
            length = 0
        # Actually if loop terminated by `break`, length keeps last value (correct).
        # If `else` ran, length is F-1 after loop body but `else` doesn't set. Need explicit:
        # Use a different approach.
        length = min(F, in_size)
        # fill text_buf[r..r+length] from in_buf[0..length]
        # (Already done above — recompute to be safe)
        in_pos = length
        textsize = length
        for i in range(1, F + 1):
            self.insert_node((r - i) & (N + F - 2))  # safe?
        self.insert_node(r)
        while length > 0:
            if self.match_length > length:
                self.match_length = length
            if self.match_length <= THRESHOLD:
                self.match_length = 1
                self.encode_char(self.text_buf[r])
            else:
                self.encode_char(255 - THRESHOLD + self.match_length)
                self.encode_position(self.match_position)
            last_match_length = self.match_length
            i = 0
            while i < last_match_length and in_pos < in_size:
                c = in_buf[in_pos]
                in_pos += 1
                self.delete_node(s)
                self.text_buf[s] = c
                if s < F - 1:
                    self.text_buf[s + N] = c
                s = (s + 1) & (N - 1)
                r = (r + 1) & (N - 1)
                self.insert_node(r)
                i += 1
            while i < last_match_length:
                self.delete_node(s)
                s = (s + 1) & (N - 1)
                r = (r + 1) & (N - 1)
                length -= 1
                if length > 0:
                    self.insert_node(r)
                i += 1
        self.encode_end()
        return bytes(self.out_buf), self.codesize


def lzhuf_compress(data: bytes, init_value: int) -> bytes:
    enc = LzHuffCompress()
    out, _ = enc.compress(data, init_value)
    return out


def stat_file(buf):
    """Return the most-frequent non-zero byte (matches rewolf's statFile)."""
    counts = [0] * 256
    max_c = 0
    max_count = 0
    for b in buf:
        if b != 0:
            counts[b] += 1
            if counts[b] > max_count:
                max_count = counts[b]
                max_c = b
    return max_c


if __name__ == "__main__":
    # Round-trip test against decompressor (also ported below)
    import sys
    test_data = b"Hello, World! Hello, World! abcdefg" * 50
    iv = stat_file(test_data)
    print(f"iv = {iv:#x}")
    compressed = lzhuf_compress(test_data, iv)
    print(f"orig: {len(test_data)} bytes -> compressed: {len(compressed)} bytes")
