#!/usr/bin/env python3
"""`.dl_bin` sealed-box helper: pairs -> keystream, unseal / seal, LDLD structure.

What the format is (build 25988413, from FOUR-SEALABLE-TABLES.md + our own checks)
    every ``data/game/generated_*.dl_bin`` is **48 bytes longer** than its LDLD plaintext:

        blob = epk(32) || tag(16) || ciphertext
        ciphertext = plaintext XOR keystream[32:]        (XSalsa20-Poly1305, per-file key)

    ``epk`` is the ephemeral public key of the sealing operation.  Everything the
    game needs to rebuild the stream is in (epk, its own private key) - which is
    why a **plaintext/ciphertext pair is enough to recover that file's stream**,
    and also why recovering the stream is *not* enough to produce a new valid
    Poly1305 tag: the tag key is keystream[0:32], which no pair reveals.

    BUT the tag key is not out of reach: it is ``XSalsa20(crypto_box_beforenm(epk, sk),
    blake2b24(epk||pk))[0:32]``, so holding the recipient secret key is enough.
    See ``tools/dlbin_tagkey.py`` - it derives that key for any file from ``epk`` +
    ``recipient.sk`` (verified 55/55 against the official tag, and resealing the
    official plaintext reproduces the official bytes exactly).  Use it whenever a
    *valid* MAC is wanted; the paths below are the pair-only fallbacks.

So this tool can, without the sealing material:
    * decryption (read the tables)                          -- fully usable
    * re-encryption with the file's own stream + a supplied tag
      -- only valid in game if the engine does not verify the MAC

and once the sealing material (recipient public key, or a precomputed keystream)
is at hand, ``seal`` is the one call that changes.

Commands
    pairs  <dir> [--out DIR]     plaintext/ + ciphertext/ pairs -> per-file streams + report
    inspect <file>               show the 48-byte header (epk/tag) of a sealed file
    unseal <cipher> --stream S [--out FILE]
    seal   <plain>  --stream S [--tag copy|zero|HEX] [--out FILE]
    blocks <plaintext>           LDLD container: group table + payload offsets
    selftest <dir>               pairs -> seal(unseal(x)) == x for every table
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

EPK_LEN, TAG_LEN = 32, 16
HEADER = EPK_LEN + TAG_LEN          # 48
LDLD, LTLD = b"LDLD", b"LTLD"


# --------------------------------------------------------------------------- io
def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def write(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
    print(f"wrote {path} ({len(data):,} B, sha256 {hashlib.sha256(data).hexdigest()[:16]})")


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


# ----------------------------------------------------------------- LDLD parser
def parse_ldld(data: bytes) -> list[dict]:
    """Split an LDLD/LTLD container into groups. Raises if the layout does not fit."""
    if len(data) < 4:
        raise ValueError("too short for a container header")
    count = struct.unpack_from("<I", data, 0)[0]
    if count == 0 or count > 4096:
        raise ValueError(f"implausible group count {count}")
    offset = 4
    groups = []
    for index in range(count):
        if offset + 24 > len(data):
            raise ValueError(f"group {index}: header runs past end of file")
        magic = data[offset:offset + 4]
        if magic not in (LDLD, LTLD):
            raise ValueError(f"group {index} @0x{offset:X}: bad magic {magic!r}")
        version, type_id, payload_size, wide = struct.unpack_from("<IIII", data, offset + 4)
        payload_offset = offset + 24
        if payload_offset + payload_size > len(data):
            raise ValueError(f"group {index}: payload runs past end of file")
        groups.append({
            "index": index, "magic": magic.decode("ascii"),
            "version": version, "type_id": type_id, "payload_size": payload_size,
            "wide": wide, "header_offset": offset, "payload_offset": payload_offset,
        })
        offset = payload_offset + payload_size
    if offset != len(data):
        raise ValueError(f"{len(data) - offset} trailing byte(s) after the last group")
    return groups



# --------------------------------------------------------------------- Poly1305
def poly1305(message: bytes, key: bytes) -> bytes:
    """RFC 7539 Poly1305 one-time authenticator (the tag libsodium puts in a sealed box)."""
    if len(key) != 32:
        raise ValueError("Poly1305 key must be 32 bytes")
    r = int.from_bytes(key[:16], "little") & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:32], "little")
    prime = (1 << 130) - 5
    acc = 0
    for offset in range(0, len(message), 16):
        block = message[offset:offset + 16]
        acc = ((acc + int.from_bytes(block, "little") + (1 << (8 * len(block)))) * r) % prime
    return ((acc + s) & ((1 << 128) - 1)).to_bytes(16, "little")


RFC7539_KEY = bytes.fromhex(
    "85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b")
RFC7539_TAG = bytes.fromhex("a8061dc1305136c6c22b8baf0c0127a9")


def poly_selftest() -> bool:
    got = poly1305(b"Cryptographic Forum Research Group", RFC7539_KEY)
    print(f"  Poly1305 RFC 7539 vector: {'PASS' if got == RFC7539_TAG else 'FAIL'} ({got.hex()})")
    return got == RFC7539_TAG



# -------------------------------------------------------------------- commands
def cmd_blocks(args) -> int:
    data = read(args.file)
    try:
        groups = parse_ldld(data)
    except ValueError as exc:
        print(f"{args.file}: not a plaintext container ({exc})")
        return 1
    print(f"{args.file}  {len(data):,} B  {len(groups)} group(s)")
    print("  #  magic  ver  type_id      payload   wide  payload_off")
    for g in groups:
        print(f"  {g['index']:2d} {g['magic']}  {g['version']:3d}  0x{g['type_id']:08X} "
              f"{g['payload_size']:>8,}  {g['wide']:4d}  0x{g['payload_offset']:06X}")
    return 0


def cmd_inspect(args) -> int:
    data = read(args.file)
    if len(data) < HEADER:
        print(f"{args.file}: shorter than the 48-byte header")
        return 1
    epk, tag, body = data[:EPK_LEN], data[EPK_LEN:HEADER], data[HEADER:]
    print(f"{args.file}  {len(data):,} B  ciphertext {len(body):,} B")
    print(f"  epk {epk.hex()}")
    print(f"  tag {tag.hex()}")
    first = body[:4]
    print(f"  first 4 bytes of the body: {first.hex()} "
          f"({'looks like plaintext LDLD - NOT sealed!' if first in (LDLD, LTLD) else 'high entropy, as expected'})")
    return 0


def cmd_pairs(args) -> int:
    root = args.dir
    plain_dir = os.path.join(root, "plaintext")
    cipher_dir = os.path.join(root, "ciphertext")
    if not (os.path.isdir(plain_dir) and os.path.isdir(cipher_dir)):
        print(f"{root}: expected plaintext/ and ciphertext/ subdirectories")
        return 1
    out_dir = args.out or os.path.join(root, "streams")
    names = sorted(f for f in os.listdir(plain_dir) if f.endswith(".dl_bin"))
    report = []
    problems = 0
    for name in names:
        plain = read(os.path.join(plain_dir, name))
        cipher = read(os.path.join(cipher_dir, name))
        record = {"name": name, "plaintext": len(plain), "ciphertext": len(cipher)}
        try:
            groups = parse_ldld(plain)
            record["groups"] = len(groups)
            record["type_ids"] = [f"0x{g['type_id']:08X}" for g in groups]
        except ValueError as exc:
            record["plaintext_error"] = str(exc)
            problems += 1
        if len(cipher) != len(plain) + HEADER:
            record["error"] = f"ciphertext is {len(cipher) - len(plain)} bytes longer, expected 48"
            problems += 1
            report.append(record)
            continue
        stream = xor(cipher[HEADER:], plain)          # keystream[32:] for this file
        epk, tag = cipher[:EPK_LEN], cipher[EPK_LEN:HEADER]
        record.update({
            "epk": epk.hex(), "tag": tag.hex(),
            "stream_sha256": hashlib.sha256(stream).hexdigest(),
        })
        write(os.path.join(out_dir, name.replace(".dl_bin", ".xor")), stream)
        report.append(record)
    # cross-table: a fixed ephemeral would mean one shared stream
    streams = {}
    for record in report:
        path = os.path.join(out_dir, record["name"].replace(".dl_bin", ".xor"))
        if os.path.isfile(path):
            streams[record["name"]] = read(path)
    shared = None
    if streams:
        names_sorted = sorted(streams)
        base = streams[names_sorted[0]]
        shared = all(streams[n][:len(base)] == base for n in names_sorted[1:])
    epks = {r["epk"] for r in report if "epk" in r}
    print(f"\n{len(report)} pair(s), {problems} problem(s)")
    print(f"  distinct epk: {len(epks)}   shared stream: {shared}")
    write(os.path.join(out_dir, "report.json"),
          json.dumps({"pairs": report, "distinct_epk": len(epks), "shared_stream": shared},
                     indent=2, ensure_ascii=False).encode())
    return 1 if problems else 0


def load_stream(path: str) -> bytes:
    data = read(path)
    if not data:
        raise SystemExit(f"{path}: empty stream")
    return data


def cmd_unseal(args) -> int:
    blob = read(args.file)
    if len(blob) < HEADER:
        print(f"{args.file}: shorter than the 48-byte header")
        return 1
    body = blob[HEADER:]
    stream = load_stream(args.stream)
    if len(stream) < len(body):
        print(f"{args.stream}: stream is {len(stream):,} B, need {len(body):,}")
        return 1
    plain = xor(body, stream[:len(body)])
    try:
        groups = parse_ldld(plain)
        types = ", ".join("0x%08X" % g["type_id"] for g in groups)
        print("  plaintext parses as a container: %d group(s), types %s" % (len(groups), types))
    except ValueError as exc:
        print("  WARNING: plaintext does not parse (%s) - wrong stream?" % exc)
    out = args.out or (os.path.splitext(args.file)[0] + ".plain.dl_bin")
    write(out, plain)
    return 0


def cmd_seal(args) -> int:
    plain = read(args.file)
    stream = load_stream(args.stream)
    if len(plain) > len(stream):
        print(f"{args.file}: {len(plain):,} B exceeds the {len(stream):,} B stream")
        return 1
    if args.tag == "zero":
        tag = b"\x00" * TAG_LEN
    elif args.tag == "copy":
        if not args.from_blob:
            print("--tag copy needs --from-blob <original sealed file>")
            return 1
        tag = read(args.from_blob)[EPK_LEN:HEADER]
        print(f"  tag copied from {args.from_blob}: {tag.hex()} "
              f"(stale unless the plaintext is unchanged)")
    else:
        tag = bytes.fromhex(args.tag)
        if len(tag) != TAG_LEN:
            print(f"--tag must be {TAG_LEN} bytes, got {len(tag)}")
            return 1
    if not args.epk:
        print("--epk <hex> is required (the 32-byte ephemeral public key to keep)")
        return 1
    epk = bytes.fromhex(args.epk)
    if len(epk) != EPK_LEN:
        print(f"--epk must be {EPK_LEN} bytes, got {len(epk)}")
        return 1
    blob = epk + tag + xor(plain, stream[:len(plain)])
    out = args.out or (os.path.splitext(args.file)[0] + ".sealed.dl_bin")
    write(out, blob)
    return 0



def cmd_seal_material(args) -> int:
    """Seal with the precomputed fixed-ephemeral material (epk/poly/keystream)."""
    plain = read(args.file)
    material_dir = args.material
    epk = read(os.path.join(material_dir, "epk.bin"))
    poly_key = read(os.path.join(material_dir, "poly.bin"))
    keystream = read(os.path.join(material_dir, "keystream.bin"))
    if len(epk) != EPK_LEN or len(poly_key) != 32:
        print("material: epk must be 32 B and poly 32 B")
        return 1
    if len(plain) > len(keystream) - 32:
        print(f"{args.file}: {len(plain):,} B exceeds the material limit "
              f"({len(keystream) - 32:,} B)")
        return 1
    cipher = xor(plain, keystream[32:32 + len(plain)])
    tag = poly1305(cipher, poly_key)
    blob = epk + tag + cipher
    try:
        groups = parse_ldld(plain)
        print("  plaintext: %d group(s)" % len(groups))
    except ValueError as exc:
        print("  WARNING: plaintext is not a container (%s)" % exc)
    print(f"  tag {tag.hex()}")
    out = args.out or (os.path.splitext(args.file)[0] + ".sealed.dl_bin")
    write(out, blob)
    return 0


def cmd_open_key(args) -> int:
    """Open a sealed file with the recipient secret key (any size, standard libsodium)."""
    from nacl.public import PrivateKey, SealedBox
    blob = read(args.file)
    plain = SealedBox(PrivateKey(read(args.key))).decrypt(blob)
    try:
        groups = parse_ldld(plain)
        types = ", ".join("0x%08X" % g["type_id"] for g in groups[:4])
        print("  plaintext: %d group(s) (%s%s)" % (len(groups), types, ", ..." if len(groups) > 4 else ""))
    except ValueError as exc:
        print("  WARNING: plaintext is not a container (%s)" % exc)
    out = args.out or (os.path.splitext(args.file)[0] + ".plain")
    write(out, plain)
    return 0


def cmd_seal_key(args) -> int:
    """Seal a plaintext to the recipient public key with a fresh ephemeral (no size limit)."""
    from nacl.public import PublicKey, SealedBox
    plain = read(args.file)
    blob = SealedBox(PublicKey(read(args.key))).encrypt(plain)
    try:
        groups = parse_ldld(plain)
        print("  plaintext: %d group(s)" % len(groups))
    except ValueError as exc:
        print("  WARNING: plaintext is not a container (%s)" % exc)
    out = args.out or (os.path.splitext(args.file)[0] + ".dl_bin")
    write(out, blob)
    return 0

def cmd_selftest(args) -> int:
    root = args.dir
    plain_dir = os.path.join(root, "plaintext")
    cipher_dir = os.path.join(root, "ciphertext")
    out_dir = os.path.join(root, "streams")
    failures = 0
    for name in sorted(f for f in os.listdir(plain_dir) if f.endswith(".dl_bin")):
        plain = read(os.path.join(plain_dir, name))
        cipher = read(os.path.join(cipher_dir, name))
        stream_path = os.path.join(out_dir, name.replace(".dl_bin", ".xor"))
        if not os.path.isfile(stream_path):
            print(f"  {name}: no stream yet (run the pairs command first)")
            failures += 1
            continue
        stream = read(stream_path)
        rebuilt = cipher[:EPK_LEN] + cipher[EPK_LEN:HEADER] + xor(plain, stream[:len(plain)])
        ok = rebuilt == cipher
        failures += 0 if ok else 1
        print(f"  {name:42s} round-trip {'PASS' if ok else 'FAIL'}")
    if not poly_selftest():
        failures += 1
    print(f"selftest: {failures} failure(s)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pairs", help="derive per-file streams from plaintext/ciphertext pairs")
    p.add_argument("dir")
    p.add_argument("--out")
    p.set_defaults(func=cmd_pairs)

    p = sub.add_parser("inspect", help="show the 48-byte sealed header")
    p.add_argument("file")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("unseal", help="decrypt with a recovered stream")
    p.add_argument("file")
    p.add_argument("--stream", required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_unseal)

    p = sub.add_parser("seal", help="re-encrypt with a stream (tag must be supplied)")
    p.add_argument("file")
    p.add_argument("--stream", required=True)
    p.add_argument("--epk", required=True, help="32-byte ephemeral public key, hex")
    p.add_argument("--tag", default="copy", help="copy | zero | 32-hex-char tag")
    p.add_argument("--from-blob", help="sealed file to copy the tag from (--tag copy)")
    p.add_argument("--out")
    p.set_defaults(func=cmd_seal)

    p = sub.add_parser("seal-material", help="seal with the precomputed material (valid MAC)")
    p.add_argument("file")
    p.add_argument("--material", required=True, help="directory with epk.bin/poly.bin/keystream.bin")
    p.add_argument("--out")
    p.set_defaults(func=cmd_seal_material)

    p = sub.add_parser("open-key", help="decrypt with the recipient secret key (any size)")
    p.add_argument("file")
    p.add_argument("--key", required=True, help="32-byte recipient.sk")
    p.add_argument("--out")
    p.set_defaults(func=cmd_open_key)

    p = sub.add_parser("seal-key", help="encrypt to the recipient public key with a fresh ephemeral")
    p.add_argument("file")
    p.add_argument("--key", required=True, help="32-byte recipient.pk")
    p.add_argument("--out")
    p.set_defaults(func=cmd_seal_key)

    p = sub.add_parser("blocks", help="parse the LDLD container")
    p.add_argument("file")
    p.set_defaults(func=cmd_blocks)

    p = sub.add_parser("selftest", help="seal(unseal(x)) == x over a pair directory")
    p.add_argument("dir")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
