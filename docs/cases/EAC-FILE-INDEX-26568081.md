# EAC 文件完整性索引：载体定位（build 26568081，2026-11-11）

> **一句话**：EAC 确实按"Hah 清单/模板"比对游戏文件，但**不是**游戏目录里的明文文件——清单与校验逻辑一起
> 打包在**按 deployment 下载的 EAC 模块**里（本机 32,075,192 B，熵 8.0）。本机只能找到载体与版本指纹，
> 明文清单需逆向 EAC 混淆，本仓库不做。

## 1. 载体（本机实证）

| 文件 | 大小 | mtime | 性质 |
|---|---:|---|---|
| `%APPDATA%\EasyAntiCheat\<productid>\<deploymentid>\easyanticheat_x64.eac` | 32,075,192 | 2026-11-11 19:32 | 熵 **8.000**、非 PE、首字节是递进 keystream 模式 → 加密/混淆 blob |
| 同目录 `easyanticheat_x64.eac.metadata` | 88 | 2026-11-11 19:32 | **明文**：`sha1=62526a9b200397ba2015f2ff2985bcd1b18c8871`、`etag="96bb93bce4dd642da9744bd450d80488"` |
| `C:\Program Files (x86)\EasyAntiCheat_EOS\EasyAntiCheat_EOS.sys` | 40,189,592 | 2026-11-11 19:32 | 内核驱动 PE；无 `.dl_bin`/`catalogue`/`hash_list` 明文串 |
| `<游戏>\EasyAntiCheat\Certificates\base.bin` | 59,826 | 2026-11-11 18:31 | `EAC\0` + version 5 容器，正文高熵（证书/密钥，不是文件清单） |
| `<游戏>\EasyAntiCheat\Certificates\runtime.conf` | 1,108 | — | 高熵，疑似配置加密 |

下载源（`anticheatlauncher.log` 明文）：

```
https://modules-cdn.eac-prod.on.epicgames.com/modules/f163733398a54335966be5046900198b/8511004301af474cad0c5a65679fe02e/win64
```

启动器日志同时记录：`Easy Anti-Cheat launcher finished with: 301`、模块版本
`bootstrapper 1.9.4, architecture: x86-64`。

## 2. 为什么不在游戏目录里拿明文清单

- `EasyAntiCheat/` 下只有 `Settings.json`（产品/部署 id、启动项）、`Localization/`、`Licenses/`、
  `Certificates/`、`SplashScreen.png`——没有任何"文件清单"文件；
- 本机实测目录里**没有** EAC 索引的明文副本；引擎侧倒是有一份可读的 55 表白名单，但那是**另一套机制**
  （见 §3）。

## 3. 两套清单互不相干

| 机制 | 位置 | 比对对象 | 失败行为 |
|---|---|---|---|
| 引擎内容校验 | `game.dll` 白名单 `0x2CAED08`，55 条 × 16 B（文件名 murmur64 + 明文内容 murmur64） | **解密后的明文** | 只打印 `Game resource mismatch…`，**不退出** |
| EAC 文件索引 | `easyanticheat_x64.eac`（本次 32 MB） | **磁盘上封印后的文件字节** | 弹 `Easy Anti-Cheat Error! 未知的文件版本 (<path>)`，拦启动 |

本机交叉验证：新 build 唯一变化的表 `generated_zone_data`，其明文 `murmur64a = 0x4072B2DE6B1DCB16`
与报告引用的新白名单目标逐位一致；其余 54 张表明文与 26251122 逐字节相同。
⇒ 重封文件"明文不变"能过引擎、过不了 EAC，两条路完全独立。

## 4. 不建议做清单提取

`.eac` 熵 8.0，清单在混淆/加密层内；提取属于**绕过反作弊**，本仓库不提供此类工具，且 EAC 模块随
deployment 更新（本次 19:32 重新下载 32 MB），提取物只在当前 deployment 有效。

**替代方案（黑盒测覆盖范围）**：EAC 报错会点名文件，按类别各做一次启动即可：

| # | 改动 | 判读 |
|---|---|---|
| ① | 重封同名 `.dl_bin` | **已证**：`error_file_version` 拦截 |
| ② | 改官方 `.stream` bundle 1 字节 | 被拦 → bundle 也在索引内 |
| ③ | **新增** `data/*.patch_N` | 静默 → 新增文件不在索引（数据层路线仍可行）；报 `error_file_forbidden` → 也被管 |
| ④ | 新增无关文件（如 `data/aaa.txt`） | 区分"只查清单内文件"与"目录白名单" |

③ 是决定性的，直接决定 `data/*.patch_N` 覆盖层路线是否成立。

## 5. 版本指纹（用于追踪 EAC 是否换清单）

每次游戏更新后记录：

```
easyanticheat_x64.eac  sha1(size,mtime)   + .metadata 里的 sha1/etag
EasyAntiCheat_EOS.sys size/mtime
Certificates/base.bin mtime
```

本次（26568081）：

```
eac  32,075,192 B  mtime 2026-11-11 19:32
meta sha1=62526a9b200397ba2015f2ff2985bcd1b18c8871  etag=96bb93bce4dd642da9744bd450d80488
sys  40,189,592 B  mtime 2026-11-11 19:32
base.bin mtime 2026-11-11 18:31
```

## 6. 为什么"明文一字不改、只重新封包"也会被拦

`.dl_bin` 是 libsodium 的 sealed box：

```
文件 = epk(32) || tag(16) || ciphertext
keystream = XSalsa20( X25519(esk, recipient_pk), nonce = blake2b(epk || recipient_pk) )
ciphertext = plaintext XOR keystream[32:]
tag        = Poly1305(ciphertext, key = keystream[0:32])
```

1. **每次封包 `esk` 都是随机的** ⇒ `epk` 不同 ⇒ nonce 不同 ⇒ keystream 不同 ⇒ **密文和 tag 全变**。
   所以"明文相同"根本推不出"文件相同"：同一份明文重封两次，磁盘字节必不相同。
2. **EAC 索引的是磁盘上的 blob**（路径 → 大小 + 哈希），不是解密后的明文。
   明文 sha256 与官版完全一致也没用——EAC 看到的是一份它没见过的 blob ⇒ `error_file_version`。
3. **想改内容就必须改密文**，而密文的 Poly1305 tag 需要 `keystream[0:32]` 这个 tag 密钥；
   它无法从"明文/密文对"里反推（这正是我们给 dl_bin 出流的同一套推导），所以**无法伪造合法 tag**。
   能产出合法 tag 的只有接收方公钥 + 自己随机 ephemeral（我们手上的 `seal-key`），
   而那条路产出的是**新 blob**，又被 EAC 索引拦下。
4. 每次游戏更新官方会把全部表**重新封一遍**（本次 57 张表全部重封），所以也不存在
   "沿用上个 build 的官方 blob"这种跨版本巧合。

结论：两条闸门的要求互相矛盾——**引擎要"明文内容哈希不变"，EAC 要"磁盘 blob 逐字节等于官方"**。
同时满足的唯一方式是"这一字节都别碰"。要改内容，只能走**不在 EAC 索引里**的通道：
新增补丁文件（本仓库正在测）、运行时、或网络代理。
