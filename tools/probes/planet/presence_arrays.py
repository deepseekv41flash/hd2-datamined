import struct, re, sys
sys.path.insert(0, r'D:/mod/work/repo-datamined/tools')
import typelib

PLAIN = r'D:/mod/refs/dlbin/plaintext-26088801/'
lib = typelib.TypeLib(open(PLAIN + 'dl_library.dl_typelib', 'rb').read())
d = open(PLAIN + 'generated_galactic_presence_settings.dl_bin', 'rb').read()

p, gs = 4, []
while p + 24 <= len(d) and d[p:p+4] == b'LDLD':
    ver, tid, size, wide, flags = struct.unpack_from('<IIIII', d, p+4)
    gs.append((len(gs), p + 24, size, d[p+24:p+24+size]))
    p += 24 + size


def nam(g):
    strs = [m.group().decode('latin1') for m in re.finditer(rb'[ -~]{3,}', g[3][1000:])]
    return next((x for x in strs if x != 'None' and not x.startswith('content/')), '(unnamed)')


tid = gs[0][3] and struct.unpack_from('<I', d, gs[0][1] - 16)[0]
members = lib.members(tid)
print('row type 0x%08X members %d stride %d' % (tid, len(members), lib.desc(tid)[3]))

for gi in (80, 82, 94, 101, 25, 0):
    _, start, size, payload = gs[gi]
    print(f'\n=== group {gi} {nam(gs[gi])}  payload={size}')
    for m in members:
        off, msize = m["offset64"], m["size64"]
        if msize != 16:
            continue
        a_off, a_cnt = struct.unpack_from('<QQ', payload, off)
        if 0 < a_off < len(payload) and a_cnt:
            vals = [struct.unpack_from('<Q', payload, a_off + 8*i)[0] for i in range(min(a_cnt, 8))]
            print(f'  array +0x{off:X} -> offset={a_off} count={a_cnt} '
                  f'first=[{", ".join("0x%016X" % v for v in vals)}]')
