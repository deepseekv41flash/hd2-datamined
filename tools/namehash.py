#!/usr/bin/env python3
"""Stingray / Helldivers 2 name-hash utilities (offline, stdlib only).

Why this exists
    Every Stingray resource identifies its *types* and *fields* by **hash of the name**,
    not by a string.  Once the hash function is known, a binary resource becomes readable
    by dictionary attack: compute the hash of a candidate name and search the bytes.
    That is how the `.particles` channel names in this project were found
    (`position` / `color` / `size` / `rotation` / `tangent`).

The function (verified against 5 resource-type ids and the on-disk particle file)
    type/field id  =  MurmurHash64A(name, seed = 0)          -- 64-bit form
    32-bit form    =  the **high 32 bits** of the 64-bit hash

    Verified pairs (64-bit):
        particles  a8193123526fad64      unit        e0a48d0be9a7453f
        material   eac0b497876adedf      lua         a14e8dfa2cd117e2
        texture    cd4238c6a0c69e32
    Verified pairs (32-bit, high half, found inside a real `.particles` file):
        position 8bbeb160   color 06776dda   size 66870586
        rotation 20605662   tangent 604debb8

Usage
    python tools/namehash.py particles unit lua                # hashes for names
    python tools/namehash.py --h32 particles                   # only the 32-bit form
    python tools/namehash.py --unknown 0x8bbeb160 --words w.txt  # crack a hash
    python tools/namehash.py --scan file.bin words.txt         # which names appear in a file
    python tools/namehash.py --scan file.bin words.txt --h32   # ... using the 32-bit form

`--scan` prints file offsets (hex) so a hit can be dumped with a hex viewer or parsed in place.
"""
from __future__ import annotations

import argparse
import struct
import sys

MASK64 = (1 << 64) - 1
_M = 0xC6A4A7935BD1E995
_R = 47


def murmur64a(data: bytes, seed: int = 0) -> int:
    """MurmurHash64A — the hash Stingray uses for ids (seed 0)."""
    h = (seed ^ (len(data) * _M)) & MASK64
    n = len(data) // 8
    for i in range(n):
        k = struct.unpack_from("<Q", data, i * 8)[0]
        k = (k * _M) & MASK64
        k ^= k >> _R
        k = (k * _M) & MASK64
        h ^= k
        h = (h * _M) & MASK64
    tail = data[n * 8:]
    for i, byte in enumerate(tail):
        h ^= byte << (8 * i)
    if tail:
        h = (h * _M) & MASK64
    h ^= h >> _R
    h = (h * _M) & MASK64
    h ^= h >> _R
    return h


def name_hash64(name: str) -> int:
    return murmur64a(name.encode("utf-8"))


def name_hash32(name: str) -> int:
    """The 32-bit form Stingray stores in resources: high half of the 64-bit hash."""
    return (name_hash64(name) >> 32) & 0xFFFFFFFF


def scan(path: str, words: list[str], h32: bool, limit: int = 0) -> int:
    """Report every byte offset at which a candidate name's hashes occur."""
    blob = open(path, "rb").read()
    print(f"{path}: {len(blob):,} B")
    hits = 0
    seen: dict[str, list[int]] = {}
    for word in words:
        for tag, value in (("hi32", name_hash32(word)), ("lo32", name_hash64(word) & 0xFFFFFFFF)):
            if h32 and tag != "hi32":
                continue
            offsets = []
            pattern = struct.pack("<I", value)
            i = blob.find(pattern)
            while i != -1:
                offsets.append(i)
                i = blob.find(pattern, i + 1)
            if offsets:
                seen.setdefault(f"{word}  {tag}=0x{value:08x}", offsets)
                hits += 1
    for label, offsets in seen.items():
        shown = ", ".join(f"0x{o:X}" for o in offsets[:limit or len(offsets)])
        more = "" if limit and len(offsets) > limit else ""
        print(f"  HIT {label:38s} x{len(offsets):<3} {shown}{more}")
    if not hits:
        print("  no candidate name hash found")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stingray name-hash calculator / dictionary scanner")
    ap.add_argument("names", nargs="*", help="names to hash")
    ap.add_argument("--h32", action="store_true", help="print only the 32-bit form")
    ap.add_argument("--scan", nargs=2, metavar=("FILE", "WORDLIST"), help="search FILE for the hashes of names listed one per line in WORDLIST")
    ap.add_argument("--unknown", metavar="HASH", help="given a hash, print the candidate names from --words that match")
    ap.add_argument("--words", metavar="WORDLIST", help="word list for --unknown")
    args = ap.parse_args(argv)

    if args.unknown:
        if not args.words:
            print("--unknown needs --words", file=sys.stderr)
            return 2
        want = int(args.unknown, 16)
        names = [ln.strip() for ln in open(args.words, encoding="utf-8", errors="replace") if ln.strip()]
        found = [n for n in names if name_hash32(n) == want or (name_hash64(n) & 0xFFFFFFFF) == want or name_hash64(n) == want]
        print(f"0x{want:08x}: " + (", ".join(found) if found else "no candidate in word list"))
        return 0 if found else 1

    if args.scan:
        path, words_path = args.scan
        names = [ln.strip() for ln in open(words_path, encoding="utf-8", errors="replace") if ln.strip()]
        return 0 if scan(path, names, args.h32) else 1

    if not args.names:
        ap.print_help()
        return 2
    for name in args.names:
        h64 = name_hash64(name)
        if args.h32:
            print(f"{name:34s} 0x{h64 >> 32:08x}")
        else:
            print(f"{name:34s} 0x{h64:016x}   hi32=0x{h64 >> 32:08x}   lo32=0x{h64 & 0xFFFFFFFF:08x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
