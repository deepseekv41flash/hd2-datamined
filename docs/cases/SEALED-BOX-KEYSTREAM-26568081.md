# 密封盒 keystream[0:32] 的获取途径（build 26568081 实测）

> 问题：`keystream[0:32]` 无法从「明文/密文对」反推，那还有什么获取途径？
>
> 结论：**从来不需要从明文对反推——收件人私钥 `recipient.sk` 早就在我们手上（2026-10-22 从崩溃转储还原），
> 它才是 keystream 的完全决定因素。** 本文补上实现与实测：55 张官方表 **55/55 tag 校验通过**，
> 且用推导出的 keystream 重封官方明文 **55/55 与官方文件逐字节相同**。
> 顺手证明：`esk` 不可得**不是**障碍，因为解密/验证方向根本不用 `esk`。

- 日期：2026-11-11
- build：26568081（旧基线 26251122 用于对照）
- 工具：`tools/dlbin_tagkey.py`（新增）
- 证据目录：`D:\mod\refs\dlbin\baseline-26251122\tagkeys.json`

---

## 1. 先把格式摆清楚：为什么明文对只给一半 keystream

`.dl_bin` = libsodium `crypto_box_seal`，结构是

```
blob = epk(32) || tag(16) || ciphertext
```

内部实际执行的是 `crypto_secretbox`（XSalsa20-Poly1305），密钥材料是

```
key       = crypto_box_beforenm(epk, sk)
            = HSalsa20( X25519(sk, epk), 非零16字节 = 0 )
nonce     = blake2b-24( epk || recipient_pk )
keystream = XSalsa20(key, nonce)

poly_key  = keystream[0:32]          <-- MAC 密钥，全程不参与异或
cipher    = plain XOR keystream[32:]
tag       = Poly1305(cipher, poly_key)
```

- 明文对只能算出 `plain XOR cipher = keystream[32:]`；
- `keystream[0:32]` 只进 Poly1305、不进异或，**任何数量的明文对都推不出它**（Poly1305 的 256 位一次性密钥，
  已知 (message, tag) 对无信息论进攻面，更不存在「反推」）；
- 所以「用明文对重封」必须自己另给 tag（`dlbin_seal.py seal --tag copy|zero`），只能赌引擎不验证 MAC。

**但 `keystream` 完全由 `(sk, epk)` 决定，`epk` 就明写在文件头 32 字节里。**
`esk` 只是密封方生成 `epk` 时的一次性私钥，解密方从不需要它——所以「每次随机 esk ⇒ 每次重封字节都变」
并不构成障碍，只要我们有 `sk`。

`sk` 的来源（`D:\mod\refs\dlbin\keys\keys.json` 有完整 recipe）：

| 项 | 值 |
|---|---|
| 转储 | `crash-125128-pid18524-full.dmp`（旧 build 25480438，2026-10-18） |
| 模块 / 基址 | `helldivers2.exe` / `0x7ff767470000` |
| 私钥 RVA | `0x1653160`（公钥 `0x16532B0`） |
| 还原法 | 4 个 little-endian qword 各 XOR `0xEB63463F0C116E2C`，按序拼接 |
| sk (hex) | `a0296b81310b58f013d8a9b343a1c292008003dfd9ab15fcf351543048b49b64` |
| pk (hex) | `2dc9aa7c30e6eed5f7fd0e0e95c7287299b126f79520cc41de750982ee7ff50c` |

`pk == X25519_base(sk)` 已校验；当前 build 26568081 的 55 张表仍能解开 ⇒ **密钥未更换**。

---

## 2. 获取途径全表（按可行性排序）

| # | 途径 | 能否拿到 keystream[0:32] | 成本 | 状态 |
|---|---|---|---|---|
| A | **收件人私钥 `recipient.sk`** + 文件头 `epk` | ✅ 全量，任意文件 | 0（已有） | **已实现并验证 55/55** |
| B | **一次性固定材质**（`boot.lua` 里内嵌的 `epk` + 65536 B keystream + poly） | ✅ 仅对「用该 epk 封的」文件 | 0（已有） | 已复现（见 §3.4） |
| C | 明文/密文对 | ⚠️ 只给 `keystream[32:]`，tag 需外部提供 | 0 | 旧路线，只能赌引擎不验 MAC |
| D | 扫描 `epk` 复用 | ❌ 拿不到 poly key；只揭示「两文件共用同一 keystream」 | 低 | 已扫（§3.3） |
| E | 进程内存（解密时 block0 必在内存里） | ✅ 理论可行 | 高，且落在 EAC 保护面内 | **不做**（A 已覆盖，无收益） |
| F | 逆 Poly1305 / 爆破 `esk` / 爆破 `sk` | ❌ | — | 不可行（2^252 级；MAC 无已知弱点） |
| G | 从 `game.dll` 静态定位密钥常量 | ✅（A 的来源） | 中 | 无需再做 |

> 补充：libsodium 的公开 API **不暴露** `keystream[0:32]`——`crypto_secretbox_easy` 只返回 `MAC||cipher`，
> 前 32 字节被库自己吃掉。所以工具里这 32 字节由纯 Python XSalsa20 现算，并用 libsodium 从偏移 32 起的
> 全部字节做逐字节对照（§3.1）。

---

## 3. 实测证据

### 3.1 自检：纯 Python XSalsa20 == libsodium

```
python tools/dlbin_tagkey.py selftest
  XSalsa20 pure-Python vs libsodium,  64 B: PASS
  XSalsa20 pure-Python vs libsodium, 200 B: PASS
  Poly1305 RFC 7539 vector: PASS (a8061dc1305136c6c22b8baf0c0127a9)
```

（64/200 B 两个长度覆盖整块与跨块计数器；Poly1305 用 RFC 7539 §2.5.2 向量。）

### 3.2 官方 55 张表：tag 全部由推导 keystream 复算命中

```
python tools/dlbin_tagkey.py verify "D:\mod\refs\dlbin\baseline-26251122" \
    --sk "...\keys\recipient.sk" --pk "...\keys\recipient.pk"
...
55 file(s): 55 tag MATCH, 0 MISMATCH
distinct epk: 55  (all distinct => random esk per file)
```

- `keystream[0:32]` 若有一个字节不对，`Poly1305` 命中的概率是 2^-128 ⇒ 这 55 条是**充分证明**；
- `distinct epk = 55` ⇒ 官方确实是每文件一次性随机 `esk`（所以「重封必然不同字节」的旧结论没错，
  但原因只是 `esk` 随机，而不是「拿不到 keystream」）；
- 报告落盘：`baseline-26251122\tagkeys.json`（含每文件 `epk / nonce / poly_key / tag_ok`）。

### 3.3 二进制回归：重封官方明文 == 官方文件（逐字节）

```
python tools/dlbin_tagkey.py roundtrip \
    --sealed "...\baseline-26251122" --plain "...\plaintext-26251122" \
    --sk "...\keys\recipient.sk" --pk "...\keys\recipient.pk"

55 table(s): 55 byte-identical after reseal, 0 differ, 0 skipped
=> reseal(official_plaintext, official_epk, derived keystream) reproduces the official file exactly
```

这条比 §3.2 更强：它说明我们可以**复用原 `epk`**（= 复用原 keystream）产出**合法 MAC** 的封装。
于是「改一个字节」的磁盘差分不再是整文件乱码，而是：

| 文件 | 大小 | 改 1 字节后的差异字节数 | 占比 |
|---|---|---|---|
| `generated_stratagem_upgrade_settings.dl_bin` | 181 B | **17**（16 B tag + 1 B 正文） | 9.4%（小文件里 tag 占比高） |
| `generated_zone_data.dl_bin` | 518,526 B | **17** | **0.003%** |

对比旧做法（新随机 `esk`，`seal-key`）：100% 字节变化。这条差分能力是新的。

### 3.4 `boot.lua` 固定材质可由 `sk` 完整复现

`D:\mod\refs\dlbin\material\`（来源 `D:\mod\work\armor\Source\boot.lua`）：

| 文件 | 内容 |
|---|---|
| `epk.bin` | `5bbc2459cd5f34de62fa11fcf36aa4a37d4fc6a31f91fc761bfb44e559b8a07f` |
| `keystream.bin` | 65,536 B |
| `poly.bin` | 前 32 B，与 `keystream[0:32]` 一致 |

用 `(sk, epk.bin)` 现算 65,536 B keystream：**逐字节相同**。说明该材质本身就是同一套数学算出来的，
只是被静态内嵌进 Lua（生态里别人拿它给 patch 载荷做合法封装）。

代价：**固定 `epk` ⇒ 所有用它封的文件共用同一条 keystream**（一次性密码本复用）。
我们自己历史上的 `color_set_red_material` / `color_set_resealed_same_content` / `passives_medkit`
三个文件就撞在同一个 `epk` 上。已知其一会泄露其余，**不建议再用固定材质封多个文件**；
需要复用 `epk` 时应当明确只复用一个官方文件自己的 `epk`。

### 3.5 顺带修正一条旧记录

`D:\mod\refs\dlbin\demo\color_set_red.sealed.dl_bin`（2,012 B）——复用官方 `epk 6b71b219…`、
tag 沿用旧值 → `verify` 报 **MISMATCH**。这是「只有 keystream[32:] 时的产物」。现在它可以被修正为合法 tag。
`vanilla_*` 官方件全部 MATCH；`*.plain.dl_bin` 是明文误命名，报 MISMATCH 属预期。

---

## 4. 工具

```bash
# 单文件：打印 epk / nonce / poly_key / stored tag / 复算 tag
python tools/dlbin_tagkey.py tagkey generated_zone_data.dl_bin --sk recipient.sk [--pk recipient.pk]

# 整目录校验（并输出 json；--dump-keystream DIR 落 poly_key+tail）
python tools/dlbin_tagkey.py verify <dir> --sk recipient.sk --out tagkeys.json

# 逐字节回归：reseal(官方明文, 官方 epk) == 官方 blob
python tools/dlbin_tagkey.py roundtrip --sealed <dir> --plain <dir> --sk recipient.sk

# 机制自检
python tools/dlbin_tagkey.py selftest
```

编程接口：`derive(blob, sk, pk, stream_len=N)` 返回 `epk / tag / cipher / nonce / key /
poly_key / stream`；`poly_key` 即 `keystream[0:32]`，`stream` 为 `keystream[32:]`（libsodium 速度）。

实现要点（踩过的坑，写下来免得再踩）：

1. `nacl.hash.blake2b` 默认 `encoder=HexEncoder`，返回的是 **hex 字符串**（`digest_size=24` → 48 B）——
   做二进制 nonce 必须显式 `encoder=RawEncoder`，否则 nonce 全错；
2. libsodium 不导出 `keystream[0:32]`；`crypto_secretbox_easy(全零明文)` 的返回值是 `MAC(16)||keystream[32:]`，
   偏移再减 32 就错位（第一版就错在这里，55 条 tag 全对、大文件重封却差 32 字节）。

---

## 5. 这条能力解锁什么 / 不解锁什么

**解锁**

1. **任意官方表的合法重封**（tag 正确，引擎无需「不验 MAC」的假设）；
2. **最小差分编辑**：复用官方 `epk` 时，改动只落在被编辑字节 + 16 B tag（518 KB 表改 1 字节 → 17 B 差异）；
3. **patch 载荷与官方同构**：patch 覆盖层里如果放 `.dl_bin` 格式的资源，现在可以做成密码学合法的；
4. 三个以前做不了的判别性实验：
   - **E1**：官方表 + 最小差分重封 → 看 EAC 报什么。若仍 `未知的文件版本`，则索引是**整文件哈希**；
     若放过，则索引只看结构/内容 —— 这会直接决定 dl_bin 路线能否复活；
   - **E2**：同上文件放进 `data\9ba626afa44a3aa3.patch_N` → 看引擎 murmur64 白名单是否只记日志
     （`Game resource mismatch`）而不拒绝加载；
   - **E3**：故意写错 tag 的 `.dl_bin` → 判断加载链是否真的校验 MAC（决定 patch 载荷是否必须合法）。

**不解锁**

- **EAC 文件索引**：它比对的是**磁盘字节**（`未知的文件版本 (<path>)`）。最小差分也是差分，
  在 E1 出结果前不能假设能过；
- 引擎的 `generated_*.dl_bin` 明文 murmur64 白名单（`game.dll 0x2CAED08`，55 条 × 16 B）——
  明文改了哈希就变，这条与密封无关；
- 别人的构建（不同 `pk`/`sk`）：本结论只对当前这对密钥成立；密钥一换，A 途径就退化成 G（重新从模块里挖）。

---

## 6. 复发/回滚

- 全部为**只读推导**：`verify` / `roundtrip` / `selftest` 不写游戏目录、不改任何官方文件；
- `tagkeys.json` 与 `*.keystream` 属密钥材料派生，**不入 git**（`refs/` 本就在仓库外）；
- 若怀疑密钥失效：`tagkey` 单文件跑一次，`tag_ok=false` 即密钥/构造已变，回 §1 重新取 `sk`。
