import struct, re, collections, pathlib, time

PLAIN = pathlib.Path(r'D:/mod/refs/dlbin/plaintext-26088801')
P = PLAIN / 'generated_galactic_presence_settings.dl_bin'
d = P.read_bytes()
ROWSZ = 1000
pos = 4
rows = []
while pos + 24 <= len(d) and d[pos:pos+4] == b'LDLD':
    ver, tid, size, wide, flags = struct.unpack_from('<IIIII', d, pos+4)
    payload = d[pos+24: pos+24+size]
    rows.append({'size': size, 'row': payload[:ROWSZ],
                 'strs': [m.group().decode('latin1') for m in re.finditer(rb'[ -~]{3,}', payload[ROWSZ:])]})
    pos += 24 + size


def name_of(r):
    cand = [x for x in r['strs'] if x != 'None' and not x.startswith('content/')]
    return cand[0] if cand else '(unnamed)'


for r in rows:
    r['name'] = name_of(r)

h20 = {struct.unpack_from('<Q', r['row'], 0x20)[0]: r['name'] for r in rows if struct.unpack_from('<Q', r['row'], 0x20)[0]}
h28 = {struct.unpack_from('<Q', r['row'], 0x28)[0]: r['name'] for r in rows if struct.unpack_from('<Q', r['row'], 0x28)[0]}
print(f'identity hashes {len(h20)}, category hashes {len(h28)}')

files = sorted(p for p in PLAIN.glob('generated_*.dl_bin') if p.name != P.name)
print(f'scanning {len(files)} other tables for those hashes...')
t0 = time.time()
hits = collections.defaultdict(list)
for f in files:
    blob = f.read_bytes()
    for val, who in h20.items():
        i = blob.find(struct.pack('<Q', val))
        if i >= 0:
            hits[f.name].append((who, 'identity', hex(i)))
    for val, who in h28.items():
        i = blob.find(struct.pack('<Q', val))
        if i >= 0:
            hits[f.name].append((who, 'category', hex(i)))
print(f'done in {time.time()-t0:.1f}s; files with hits: {len(hits)}')
for f, v in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:15]:
    print(f'  {f}: {len(v)} hits, e.g. {v[:4]}')
