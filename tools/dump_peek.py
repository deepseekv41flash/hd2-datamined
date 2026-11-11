#!/usr/bin/env python3
"""Minimal minidump reader: exception record + module map + faulting module offset.

No external deps; parses the MINIDUMP directory streams directly.
Usage: python dump_peek.py <file.dmp> [--modules]
"""
import struct
import sys

MDMP = b"MDMP"
STREAM_THREAD_LIST, STREAM_MODULE_LIST, STREAM_EXCEPTION = 3, 4, 6
STREAM_MEMORY_LIST, STREAM_SYSTEM_INFO = 5, 7
EXC_NAMES = {
    0xC0000005: "ACCESS_VIOLATION",
    0xC000001D: "ILLEGAL_INSTRUCTION",
    0xC000000D: "INVALID_PARAMETER",
    0xC0000409: "STACK_BUFFER_OVERRUN / FAST_FAIL",
    0x80000003: "BREAKPOINT",
    0xE06D7363: "C++ EXCEPTION",
    0xC0000374: "HEAP_CORRUPTION",
    0xC00000FD: "STACK_OVERFLOW",
}


def read_utf16(buf, rva):
    if not rva:
        return ""
    (length,) = struct.unpack_from("<I", buf, rva)
    return buf[rva + 4:rva + 4 + length].decode("utf-16-le", "replace")


def main() -> int:
    path = sys.argv[1]
    show_modules = "--modules" in sys.argv
    buf = open(path, "rb").read()
    if buf[:4] != MDMP:
        print(f"{path}: not a minidump ({buf[:4]!r})")
        return 1
    (version, nstreams, dir_rva, _check, timestamp, flags) = struct.unpack_from("<IIIIII", buf, 4)
    print(f"minidump: {len(buf):,} B  version {version:#x}  streams {nstreams}  "
          f"timestamp {timestamp} (0x{timestamp:08X})  flags {flags:#x}")

    streams = {}
    for i in range(nstreams):
        stype, size, rva = struct.unpack_from("<III", buf, dir_rva + i * 12)
        streams.setdefault(stype, []).append((size, rva))
    print(f"stream types: {sorted(streams)}")

    modules = []
    if STREAM_MODULE_LIST in streams:
        _size, rva = streams[STREAM_MODULE_LIST][0]
        (nmod,) = struct.unpack_from("<I", buf, rva)
        pos = rva + 4
        for _ in range(nmod):
            base, size, _csum, _ts, name_rva = struct.unpack_from("<QIIII", buf, pos)
            modules.append({"base": base, "size": size, "name": read_utf16(buf, name_rva)})
            pos += 108
        print(f"modules: {len(modules)}")

    def resolve(addr):
        for m in modules:
            if m["base"] <= addr < m["base"] + m["size"]:
                return f"{m['name']}+0x{addr - m['base']:X}"
        return f"0x{addr:X} (unmapped)"

    if STREAM_EXCEPTION in streams:
        size, rva = streams[STREAM_EXCEPTION][0]
        tid, _align = struct.unpack_from("<II", buf, rva)
        code, eflags, nested, addr, nparam = struct.unpack_from("<IIQQI", buf, rva + 8)
        params = struct.unpack_from("<15Q", buf, rva + 8 + 32)
        print(f"\nexception: thread {tid}  code {code:#x} "
              f"({EXC_NAMES.get(code, 'unknown')})  flags {eflags:#x}")
        print(f"  address : {addr:#x} -> {resolve(addr)}")
        print(f"  params  : {[hex(p) for p in params[:nparam]]}")
        if code == 0xC0000005 and nparam >= 2:
            kind = {0: "read", 1: "write", 8: "execute"}.get(params[0], f"?{params[0]}")
            print(f"  AV kind : {kind}  target {params[1]:#x}")
    else:
        print("no exception stream")

    if STREAM_MEMORY_LIST in streams:
        _size, rva = streams[STREAM_MEMORY_LIST][0]
        (n,) = struct.unpack_from("<I", buf, rva)
        print(f"memory descriptors: {n}")

    if show_modules:
        print("\nmodules (base .. end  name):")
        for m in sorted(modules, key=lambda m: m["base"]):
            print(f"  {m['base']:#018x} .. {m['base'] + m['size']:#018x}  "
                  f"{m['size']:>10,}  {m['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
