#!/usr/bin/env python3
r"""Derive the Poly1305 key ( = XSalsa20 keystream[0:32] ) of a sealed ``.dl_bin``.

Why this exists
    ``crypto_box_seal`` blob = epk(32) || tag(16) || ciphertext.
    Inside, ``crypto_secretbox`` uses

        keystream = XSalsa20(beforenm(sk, epk), nonce = blake2b(epk||pk, 24))
        poly_key  = keystream[0:32]                 <- MAC key, never XORed with data
        cipher    = plain XOR keystream[32:]

    A plaintext/ciphertext pair therefore only reveals ``keystream[32:]``; the first
    32 bytes (the MAC key) cannot be recovered from pairs alone - BUT they are fully
    determined by ``(recipient.sk, epk)``, which we hold.  No plaintext is needed.

    So this tool answers "where does keystream[0:32] come from?" with: recompute it
    from the recipient secret key, then *prove* it by re-deriving the stored tag.

Commands
    tagkey <sealed-file> --sk FILE [--json]
    verify <dir|file> --sk FILE [--pk FILE] [--out report.json] [--dump-keystream DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

EPK_LEN, TAG_LEN = 32, 16
HEADER = EPK_LEN + TAG_LEN

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlbin_seal import poly1305  # noqa: E402


# ---------------------------------------------------------------- Salsa20 core
def rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _rounds(x):
    z = list(x)
    for _ in range(10):                       # 10 double-rounds = 20 rounds
        # column round
        z[4] ^= rotl((z[0] + z[12]) & 0xFFFFFFFF, 7)
        z[8] ^= rotl((z[4] + z[0]) & 0xFFFFFFFF, 9)
        z[12] ^= rotl((z[8] + z[4]) & 0xFFFFFFFF, 13)
        z[0] ^= rotl((z[12] + z[8]) & 0xFFFFFFFF, 18)
        z[9] ^= rotl((z[5] + z[1]) & 0xFFFFFFFF, 7)
        z[13] ^= rotl((z[9] + z[5]) & 0xFFFFFFFF, 9)
        z[1] ^= rotl((z[13] + z[9]) & 0xFFFFFFFF, 13)
        z[5] ^= rotl((z[1] + z[13]) & 0xFFFFFFFF, 18)
        z[14] ^= rotl((z[10] + z[6]) & 0xFFFFFFFF, 7)
        z[2] ^= rotl((z[14] + z[10]) & 0xFFFFFFFF, 9)
        z[6] ^= rotl((z[2] + z[14]) & 0xFFFFFFFF, 13)
        z[10] ^= rotl((z[6] + z[2]) & 0xFFFFFFFF, 18)
        z[3] ^= rotl((z[15] + z[11]) & 0xFFFFFFFF, 7)
        z[7] ^= rotl((z[3] + z[15]) & 0xFFFFFFFF, 9)
        z[11] ^= rotl((z[7] + z[3]) & 0xFFFFFFFF, 13)
        z[15] ^= rotl((z[11] + z[7]) & 0xFFFFFFFF, 18)
        # row round
        z[1] ^= rotl((z[0] + z[3]) & 0xFFFFFFFF, 7)
        z[2] ^= rotl((z[1] + z[0]) & 0xFFFFFFFF, 9)
        z[3] ^= rotl((z[2] + z[1]) & 0xFFFFFFFF, 13)
        z[0] ^= rotl((z[3] + z[2]) & 0xFFFFFFFF, 18)
        z[6] ^= rotl((z[5] + z[4]) & 0xFFFFFFFF, 7)
        z[7] ^= rotl((z[6] + z[5]) & 0xFFFFFFFF, 9)
        z[4] ^= rotl((z[7] + z[6]) & 0xFFFFFFFF, 13)
        z[5] ^= rotl((z[4] + z[7]) & 0xFFFFFFFF, 18)
        z[11] ^= rotl((z[10] + z[9]) & 0xFFFFFFFF, 7)
        z[8] ^= rotl((z[11] + z[10]) & 0xFFFFFFFF, 9)
        z[9] ^= rotl((z[8] + z[11]) & 0xFFFFFFFF, 13)
        z[10] ^= rotl((z[9] + z[8]) & 0xFFFFFFFF, 18)
        z[12] ^= rotl((z[15] + z[14]) & 0xFFFFFFFF, 7)
        z[13] ^= rotl((z[12] + z[15]) & 0xFFFFFFFF, 9)
        z[14] ^= rotl((z[13] + z[12]) & 0xFFFFFFFF, 13)
        z[15] ^= rotl((z[14] + z[13]) & 0xFFFFFFFF, 18)
    return z


SIGMA = struct.unpack("<4I", b"expand 32-byte k")


def _state(key: bytes, inp: bytes) -> list[int]:
    k = struct.unpack("<8I", key)
    n = struct.unpack("<4I", inp)
    return [SIGMA[0], k[0], k[1], k[2], k[3], SIGMA[1], n[0], n[1],
            n[2], n[3], SIGMA[2], k[4], k[5], k[6], k[7], SIGMA[3]]


def hsalsa20(key: bytes, inp16: bytes) -> bytes:
    """crypto_core_hsalsa20: output words (0,5,10,15,6,7,8,9), no feed-forward."""
    z = _rounds(_state(key, inp16))
    return struct.pack("<8I", z[0], z[5], z[10], z[15], z[6], z[7], z[8], z[9])


def salsa20_block(key: bytes, nonce8: bytes, counter: int) -> bytes:
    inp = nonce8 + struct.pack("<Q", counter)
    x = _state(key, inp)
    z = _rounds(x)
    return struct.pack("<16I", *[(a + b) & 0xFFFFFFFF for a, b in zip(z, x)])


def xsalsa20_stream(key: bytes, nonce24: bytes, length: int) -> bytes:
    subkey = hsalsa20(key, nonce24[:16])
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += salsa20_block(subkey, nonce24[16:24], counter)
        counter += 1
    return bytes(out[:length])


# ------------------------------------------------------------------- sealing
def seal_nonce(epk: bytes, recipient_pk: bytes) -> bytes:
    """blake2b-24 of epk||pk - the sealed-box nonce (raw bytes, not hex)."""
    from nacl.encoding import RawEncoder
    from nacl.hash import blake2b
    return blake2b(epk + recipient_pk, digest_size=24, encoder=RawEncoder)


def shared_key(epk: bytes, sk: bytes) -> bytes:
    """crypto_box_beforenm(epk, sk) - HSalsa20(X25519(sk, epk), 0)."""
    from nacl import bindings
    return bindings.crypto_box_beforenm(epk, sk)


def keystream_tail(key: bytes, nonce24: bytes, length: int) -> bytes:
    """XSalsa20 keystream bytes ``[32, 32+length)`` at libsodium speed.

    ``crypto_secretbox_easy`` on an all-zero message returns ``MAC(16) || cipher``
    where ``cipher = keystream[32:]`` - libsodium never exposes the first 32 bytes
    because they are the Poly1305 key.  Those 32 bytes come from the pure-Python
    ``xsalsa20_stream`` above (verified against libsodium on every byte from 32 on).
    """
    if length <= 0:
        return b""
    from nacl import bindings
    return bindings.crypto_secretbox_easy(b"\x00" * length, nonce24, key)[16:]


def poly_key_for(key: bytes, nonce24: bytes) -> bytes:
    """keystream[0:32] - the absent-from-libsodium-API half of block 0."""
    return xsalsa20_stream(key, nonce24, 32)


def derive(blob: bytes, sk: bytes, pk: bytes, stream_len: int = 0):
    epk, tag, cipher = blob[:EPK_LEN], blob[EPK_LEN:HEADER], blob[HEADER:]
    key = shared_key(epk, sk)
    nonce = seal_nonce(epk, pk)
    out = {"epk": epk, "tag": tag, "cipher": cipher, "nonce": nonce, "key": key,
           "poly_key": poly_key_for(key, nonce), "stream": b""}
    if stream_len:
        out["stream"] = keystream_tail(key, nonce, stream_len)
    return out


def selftest() -> bool:
    """Two independent checks of the pure-Python core.

    1. Poly1305 against the RFC 7539 §2.5.2 vector.
    2. XSalsa20 keystream against libsodium, for a fixed key/nonce and 4 blocks, so
       a whole-block and block-counter error cannot hide.
    """
    ok = True
    for length in (64, 200):
        key = hashlib.sha256(b"selftest-key").digest()
        nonce = hashlib.blake2b(b"selftest-nonce", digest_size=24).digest()
        mine = xsalsa20_stream(key, nonce, 32 + length)[32:]
        lib = keystream_tail(key, nonce, length)
        good = mine == lib
        ok &= good
        print(f"  XSalsa20 pure-Python vs libsodium, {length:3d} B: "
              f"{'PASS' if good else 'FAIL'}")
        if not good:
            first = next(i for i in range(length) if mine[i] != lib[i])
            print(f"    first differing byte @{first}: {mine[first]:02x} != {lib[first]:02x}")
    from dlbin_seal import poly_selftest
    ok &= poly_selftest()
    return ok


# ------------------------------------------------------------------ commands
def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def cmd_tagkey(args) -> int:
    blob = read(args.file)
    sk = read(args.sk)
    pk = read(args.pk) if args.pk else None
    if pk is None:
        from nacl import bindings
        pk = bindings.crypto_scalarmult_base(sk)
    info = derive(blob, sk, pk, stream_len=16)
    tag = poly1305(info["cipher"], info["poly_key"])
    ok = tag == info["tag"]
    print(f"{os.path.basename(args.file)}  {len(blob):,} B  ciphertext {len(info['cipher']):,} B")
    print(f"  epk        {info['epk'].hex()}")
    print(f"  nonce      {info['nonce'].hex()}   (blake2b-24 of epk||pk)")
    print(f"  poly_key   {info['poly_key'].hex()}   <- keystream[0:32]")
    print(f"  tag stored {info['tag'].hex()}")
    print(f"  tag recomp {tag.hex()}   {'MATCH' if ok else 'MISMATCH'}")
    print(f"  keystream[32:48] {info['stream'][:16].hex()}")
    if args.json:
        print(json.dumps({
            "file": args.file, "epk": info["epk"].hex(), "poly_key": info["poly_key"].hex(),
            "nonce": info["nonce"].hex(), "tag": info["tag"].hex(), "tag_ok": ok,
        }))
    return 0 if ok else 1


def cmd_verify(args) -> int:
    sk = read(args.sk)
    if args.pk:
        pk = read(args.pk)
    else:
        from nacl import bindings
        pk = bindings.crypto_scalarmult_base(sk)
    paths = []
    if os.path.isdir(args.target):
        for root, _dirs, files in os.walk(args.target):
            for name in sorted(files):
                if name.endswith(".dl_bin"):
                    paths.append(os.path.join(root, name))
        paths.sort()
    else:
        paths = [args.target]
    ok_n = bad_n = 0
    rows, epks = [], {}
    for path in paths:
        blob = read(path)
        if len(blob) < HEADER:
            print(f"  {os.path.basename(path):46s} SKIP (too short)")
            continue
        info = derive(blob, sk, pk)
        tag = poly1305(info["cipher"], info["poly_key"])
        ok = tag == info["tag"]
        ok_n += ok
        bad_n += not ok
        epks.setdefault(info["epk"].hex(), []).append(os.path.basename(path))
        rows.append({
            "name": os.path.basename(path), "size": len(blob),
            "epk": info["epk"].hex(), "poly_key": info["poly_key"].hex(),
            "nonce": info["nonce"].hex(), "tag_ok": ok,
            "tag_stored": info["tag"].hex(), "tag_recomputed": tag.hex(),
        })
        print(f"  {os.path.basename(path):46s} {len(blob):>10,} B  "
              f"{'MATCH' if ok else 'MISMATCH'}  epk {info['epk'].hex()[:16]}…")
        if args.dump_keystream and ok:
            out = os.path.join(args.dump_keystream, os.path.basename(path) + ".keystream")
            os.makedirs(args.dump_keystream, exist_ok=True)
            with open(out, "wb") as handle:
                handle.write(info["poly_key"] + info["stream"])
    print(f"\n{len(rows)} file(s): {ok_n} tag MATCH, {bad_n} MISMATCH")
    print(f"distinct epk: {len(epks)}"
          + ("  (all distinct => random esk per file)" if len(epks) == len(rows) else ""))
    for hex_epk, names in epks.items():
        if len(names) > 1:
            print(f"  !! epk {hex_epk} reused by {len(names)} files: {', '.join(names)}")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"recipient_pk": pk.hex(), "files": rows,
                       "tag_match": ok_n, "tag_mismatch": bad_n,
                       "distinct_epk": len(epks)}, handle, indent=2)
        print(f"report -> {args.out}")
    return 0 if bad_n == 0 else 1


def cmd_roundtrip(args) -> int:
    """Prove reseal(official plaintext, official epk) == official blob, byte for byte.

    That identity is what turns "we hold the key" into "we can edit a table and keep
    the on-disk diff confined to the edited bytes + the 16-byte tag".
    """
    sk = read(args.sk)
    if args.pk:
        pk = read(args.pk)
    else:
        from nacl import bindings
        pk = bindings.crypto_scalarmult_base(sk)
    sealed_dir, plain_dir = args.sealed, args.plain
    names = sorted(f for f in os.listdir(sealed_dir) if f.endswith(".dl_bin"))
    same = diff = missing = 0
    for name in names:
        blob = read(os.path.join(sealed_dir, name))
        plain_path = os.path.join(plain_dir, name)
        if not os.path.isfile(plain_path):
            print(f"  {name:46s} SKIP (no plaintext)")
            missing += 1
            continue
        plain = read(plain_path)
        info = derive(blob, sk, pk, stream_len=len(plain))
        cipher = xor(plain, info["stream"])
        tag = poly1305(cipher, info["poly_key"])
        rebuilt = info["epk"] + tag + cipher
        ok = rebuilt == blob
        if ok:
            same += 1
        else:
            diff += 1
            first = next((i for i in range(min(len(rebuilt), len(blob)))
                          if rebuilt[i] != blob[i]), None)
            print(f"  {name:46s} DIFF @{first}  (rebuilt {len(rebuilt):,} B, "
                  f"official {len(blob):,} B)")
        if args.verbose:
            print(f"  {name:46s} {'IDENTICAL' if ok else 'DIFFERS'}")
    print(f"\n{len(names)} table(s): {same} byte-identical after reseal, {diff} differ, "
          f"{missing} skipped")
    print("=> reseal(official_plaintext, official_epk, derived keystream) reproduces the "
          "official file exactly" if diff == 0 else
          "=> NOT reproduced - derivation or plaintext set is wrong")
    return 0 if diff == 0 else 1


def cmd_reseal(args) -> int:
    """Seal ANY plaintext against a given epk with a valid tag (keeps that epk's identity)."""
    sk = read(args.sk)
    if args.pk:
        pk = read(args.pk)
    else:
        from nacl import bindings
        pk = bindings.crypto_scalarmult_base(sk)
    epk = bytes.fromhex(args.epk)
    if len(epk) != EPK_LEN:
        print(f"--epk must be {EPK_LEN} bytes hex, got {len(epk)}")
        return 1
    plain = read(args.file)
    key = shared_key(epk, sk)
    nonce = seal_nonce(epk, pk)
    cipher = xor(plain, keystream_tail(key, nonce, len(plain)))
    tag = poly1305(cipher, poly_key_for(key, nonce))
    blob = epk + tag + cipher
    out = args.out or (os.path.splitext(args.file)[0] + ".sealed.dl_bin")
    print(f"  epk  {epk.hex()}  (reused: minimal on-disk diff vs that file)")
    print(f"  tag  {tag.hex()}  (valid MAC)")
    print(f"  plain {len(plain):,} B -> sealed {len(blob):,} B")
    with open(out, "wb") as handle:
        handle.write(blob)
    print(f"wrote {out} (sha256 {hashlib.sha256(blob).hexdigest()[:16]})")
    return 0


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("tagkey", help="derive + verify keystream[0:32] for one sealed file")
    p.add_argument("file")
    p.add_argument("--sk", required=True)
    p.add_argument("--pk")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_tagkey)

    p = sub.add_parser("verify", help="derive + verify a whole directory")
    p.add_argument("target")
    p.add_argument("--sk", required=True)
    p.add_argument("--pk")
    p.add_argument("--out")
    p.add_argument("--dump-keystream")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("selftest", help="Salsa20 core against RFC 7539 vector")
    p.set_defaults(func=lambda a: 0 if selftest() else 1)

    p = sub.add_parser("reseal", help="seal any plaintext against a chosen epk, valid tag")
    p.add_argument("file", help="plaintext to seal")
    p.add_argument("--epk", required=True, help="32-byte ephemeral public key, hex")
    p.add_argument("--sk", required=True)
    p.add_argument("--pk")
    p.add_argument("--out")
    p.set_defaults(func=cmd_reseal)

    p = sub.add_parser("roundtrip", help="reseal(official plain, official epk) == official blob?")
    p.add_argument("--sealed", required=True)
    p.add_argument("--plain", required=True)
    p.add_argument("--sk", required=True)
    p.add_argument("--pk")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_roundtrip)

    args = ap.parse_args()
    if args.command != "selftest":
        sys.stdout.reconfigure(encoding="utf-8")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
