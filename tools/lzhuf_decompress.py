"""Python port of rewolf's rwf_lzhuf.cpp decompressor (matches MM3.CC format)."""

MAX_FREQ = 0x8000
N = 0x1000
F = 0x3C
THRESHOLD = 2
N_CHAR = 0x100 - THRESHOLD + F   # 0x13A
T = N_CHAR * 2 - 1               # 0x273
R = T - 1                        # 0x272

d_len = [
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
]

d_code = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5,
    6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7,
    8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9,
    10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11,
    12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15,
    16, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 19,
    20, 20, 20, 20, 21, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 23,
    24, 24, 25, 25, 26, 26, 27, 27, 28, 28, 29, 29, 30, 30, 31, 31,
    32, 32, 33, 33, 34, 34, 35, 35, 36, 36, 37, 37, 38, 38, 39, 39,
    40, 40, 41, 41, 42, 42, 43, 43, 44, 44, 45, 45, 46, 46, 47, 47,
    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63,
]


def lzhuf_decompress(in_buf: bytes, out_size: int, init_value: int) -> bytes:
    freq = [0] * (T + 1)
    prnt = [0] * (T + N_CHAR)
    son = [0] * T
    cache = 0x8000

    for i in range(N_CHAR):
        freq[i] = 1
        prnt[i + T] = i
        son[i] = i + T
    i = 0
    j = N_CHAR
    while j < T:
        freq[j] = freq[i] + freq[i + 1]
        son[j] = i
        prnt[i] = j
        prnt[i + 1] = j
        i += 2
        j += 1
    prnt[R] = 0
    freq[T] = 0xFFFF

    text_buf_index = N - F
    text_buf = [init_value] * N
    out_buf = bytearray(out_size)
    out_buf_index = 0
    in_pos = 0

    while out_buf_index < out_size:
        c = son[R]
        while c < T:
            bit = (cache >> 15) & 1
            cache = (cache << 1) & 0xFFFF
            if cache == 0:
                tmp = ((in_buf[in_pos] << 8) | in_buf[in_pos + 1]) & 0xFFFF
                in_pos += 2
                bit = (tmp >> 15) & 1
                cache = ((tmp << 1) | 1) & 0xFFFF
            c += bit
            c = son[c]
        c -= T

        if freq[R] == MAX_FREQ:
            # tree reconstruction (rare for MM3)
            j_ = 0
            for i_ in range(T):
                if son[i_] >= T:
                    freq[j_] = (freq[i_] + 1) // 2
                    son[j_] = son[i_]
                    j_ += 1
            i_ = 0
            j_ = N_CHAR
            while j_ < T:
                k = i_ + 1
                f = freq[j_] = freq[i_] + freq[k]
                k = j_ - 1
                while f < freq[k]:
                    k -= 1
                k += 1
                l = j_ - k
                for m in range(l, 0, -1):
                    freq[k + m] = freq[k + m - 1]
                freq[k] = f
                for m in range(l, 0, -1):
                    son[k + m] = son[k + m - 1]
                son[k] = i_
                i_ += 2
                j_ += 1
            for i_ in range(T):
                k = son[i_]
                if k >= T:
                    prnt[k] = i_
                else:
                    prnt[k] = prnt[k + 1] = i_

        # update tree
        b = prnt[c + T]
        while True:
            freq[b] += 1
            k = freq[b]
            if k > freq[b + 1]:
                l = b + 1
                l += 1
                while k > freq[l]:
                    l += 1
                l -= 1
                freq[b] = freq[l]
                freq[l] = k
                i_ = son[b]
                prnt[i_] = l
                if i_ < T:
                    prnt[i_ + 1] = l
                j_ = son[l]
                son[l] = i_
                prnt[j_] = b
                if j_ < T:
                    prnt[j_ + 1] = b
                son[b] = j_
                b = l
            b = prnt[b]
            if b == 0:
                break

        if c < 0x100:
            out_buf[out_buf_index] = c
            text_buf[text_buf_index] = c
            text_buf_index = (text_buf_index + 1) & (N - 1)
            out_buf_index += 1
            continue

        # decode position (LZ77 back-reference)
        bt = 0
        for i_ in range(8):
            bit = (cache >> 15) & 1
            cache = (cache << 1) & 0xFFFF
            if cache == 0:
                cache = ((in_buf[in_pos] << 8) | in_buf[in_pos + 1]) & 0xFFFF
                in_pos += 2
                bit = 1
                for j_ in range(8 - i_):
                    tmp_bit = (cache >> 15) & 1
                    cache = (cache << 1) & 0xFFFF
                    cache |= bit
                    bit = tmp_bit
                    tmp_bit = (bt >> 15) & 1
                    bt = (bt << 1) & 0xFFFF
                    bt |= bit
                    bit = tmp_bit
                break
            bt = (bt << 1) & 0xFFFF
            bt |= bit

        dc = d_code[bt] << 6
        i_ = d_len[bt] - 1
        while True:
            i_ -= 1
            if i_ == 0:
                break
            bit = (cache >> 15) & 1
            cache = (cache << 1) & 0xFFFF
            if cache == 0:
                cache = ((in_buf[in_pos] << 8) | in_buf[in_pos + 1]) & 0xFFFF
                in_pos += 2
                bit = (cache >> 15) & 1
                cache = (cache << 1) & 0xFFFF
                cache |= 1
            bt = (bt << 1) & 0xFFFF
            bt |= bit

        dc |= (bt & 0x3F)
        text_buf_index2 = text_buf_index - dc - 1
        cnt = c - 0xFD
        for _ in range(cnt):
            text_buf_index2 &= 0xFFF
            tmp = text_buf[text_buf_index2]
            out_buf[out_buf_index] = tmp
            text_buf[text_buf_index] = tmp
            text_buf_index = (text_buf_index + 1) & (N - 1)
            out_buf_index += 1
            text_buf_index2 += 1

    return bytes(out_buf)
