# GWE 抓包 + 对表：探明「让引擎相信服务器」的能力边界

> 两个工具：`tools/gwe_capture.py`（给第三方代理加只读落盘开关）+ `tools/gwe_join.py`（拿 dump 对本地对象空间）。
> 状态：两个工具都过了离线自检（`selftest`，含**能失败的对照**）；**实机抓包尚未做**，因为要装一次代理并进一次游戏。

---

## 0. 为什么要抓这一份

「服务器给值、引擎自己解释」这条通道能做什么，只取决于一张表：
`GET /api/WarSeason/GalacticWarEffects`（约 300 条 effect）。每条 effect 的两个属性决定一切：

| 属性 | 决定 | 已知取值 |
|---|---|---|
| `effectType` | 引擎用哪个**解释器** | 32 = 临时配发战备 · 40 = 星图词条 · 71 = presence（局内玩法）· **其余未知** |
| `values[]` | 指向哪个**本地对象** | 71 的 `values[0]` = presence 身份键；32 的值为战备 hash |

**端点表在游戏文件里拿不到**：本会话扫过整装目录，`/api/` 只命中两段 EAC 相关碎片
（`/api/v1/publicAntiCheat…`），HD2 自己的 API 路径一条都没有 ⇒ 只能从流量里取。

---

## 1. 两步

### 1.1 打补丁（改的是第三方文件，就地 + 可还原）

```bash
# 先把开关设好（PowerShell）
$env:HD2_GWE_DUMP  = "D:\mod\out\gwe"
$env:HD2_GWE_PATHS = "/api/WarSeason/GalacticWarEffects"   # 可逗号分隔多个
$env:HD2_GWE_MAX   = "8388608"                              # 可选，缺省 8 MiB

python tools/gwe_capture.py status  --proxy D:/Downloads/variant_mod/tools/war_proxy.py
python tools/gwe_capture.py patch   --proxy D:/Downloads/variant_mod/tools/war_proxy.py
# …按原方式启动代理（run.ps1 或面板）→ 进一次游戏 → 回飞船看 out/gwe/index.txt
python tools/gwe_capture.py unpatch --proxy D:/Downloads/variant_mod/tools/war_proxy.py
```

补丁只加两段：一个模块级函数 + **chunked 解码之后、改写之前**的一行调用。

**硬规则（写死在代码里，不可配置）**：

* 只写**响应体**：header / cookie / query / 请求体一律不写 —— token 在请求头里，所以碰不到；
* 只落 `HD2_GWE_PATHS` 命中的路径，其它请求一个字节不动；
* 大小上限 + `index.txt` 只记 `时间 / 路径 / 字节数 / sha256 / 是否合法 JSON`；
* 任何异常都被吞掉并记一行日志：抓包失败**不允许**影响代理主流程。

补丁前会建 `war_proxy.py.bak`；`unpatch` 优先从备份还原。第三方代码不进本仓库。

### 1.2 对表

```bash
python tools/gwe_join.py report --gwe out/gwe --out out/planet/gwe-report.json
# → out/planet/gwe-report.json + gwe-report.md
```

输出：**实际字段名**（第一次跑就知道真实 schema）、`effectType` 分布、每种类型的 arity、
`tag/mechanic` 邻接配对、**presence 覆盖率 `n/137`**、以及"没对上的 values"清单。

---

## 2. 报告怎么读：四个判据

拿到报告后，对每个新字段问四个问题，就能把它归进四类（这是本线的**边界判定法**）：

| 判据 | 观测 | 结论 |
|---|---|---|
| 落地 | 星图 / 局内 / UI 是否出现 | 不落地 ⇒ 客户端根本不读这个字段 |
| **刷新** | 下一次拉 `Status` 后是否被还原 | 还原 ⇒ **纯显示层**；不还原 ⇒ 被引擎吸收成权威状态 |
| 传播 | 客机是否也看到 | 是 ⇒ 进了 board 同步（主机权威，**全队受影响**）|
| 资源 | 紫问号 / 崩溃 / 无模型 | 是 ⇒ **id 越界**，超出本地对象空间 |

三条已知硬边界（各有证据）：

1. **本地对象空间**：id 必须是客户端已定义的（137 presence / 58 战备…）——案例 10-14 崩溃对照 + Mount 线 R2 整包驻留同源；
2. **权威归属**：账号 / 货币 / 解锁 / 战功属服务端权威，改响应只改本地视图（⚠ 机制推断，未实测，也不该拿主账号测）；
3. **请求方向**：本通道只改响应；伪造提交是另一个风险层级，案例明确没做。

---

## 3. Wireshark 在这条线里能干什么

结论先说：**能做旁证和找漏，不能替代补丁**（除非 TLS 密钥能拿到）。

| 用途 | 可行性 | 具体做法 |
|---|---|---|
| **直接解密 HTTP（首选尝试）** | 取决于 TLS 后端 | 游戏目录有 `bin/libcurl.dll`。若它用 OpenSSL 且尊重 `SSLKEYLOGFILE`：设 `SSLKEYLOGFILE=D:\mod\out\tls.keys` → 启动游戏 → Wireshark `Preferences→Protocols→TLS→(Pre)-Master-Secret log filename` 指向该文件。能解就是**明文 HTTP，连补丁都不用打** |
| **主机→客机会话流量画像** | ✓ 不需要解密 | 只看协议/端口/包长/时序。若改写后主机上行出现 ~2.5 KB 粒度增量（board 记录 `0x9C0`=2496 B），就是"引擎自己同步 board"的旁证 —— 正好回答"它是不是给客机发假包" |
| **端点面外延** | ✓ 不需要解密 | 抓 DNS / TLS SNI，列出客户端还连了哪些域（遥测、EAC、CDN）。这决定**还有没有第二条"服务器→客户端"通道可写** |
| 看具体 path / body / 304 条件请求 | ✗ 无密钥 | TLS 1.2/1.3 记录是密文；Steam/EOS 数据报同理 |

抓包注意：hosts 指向**局域网 IP** 时抓对应网卡（不是 loopback）；Npcap 要装 loopback 支持才看得到 127.0.0.1 的 CRL 服务。

**推荐顺序**：先花 5 分钟试 `SSLKEYLOGFILE`（成功则最省事）→ 不行就走 §1 的补丁 → Wireshark 只用来做"会话流量画像"和"端点外延"这两件旁证。

---

## 4. 离线自检（已跑过，可复跑）

```bash
python tools/gwe_capture.py selftest    # 10 项：钩子插入 / 调用点位置 / py_compile / --help 仍可用
                                        # / gzip 落盘一致 / index 只有 5 字段(无 header) / 非白名单不落
                                        # / 自动建目录 / 超上限不落 / 未设开关完全静默
python tools/gwe_join.py selftest       # 8 项：type71→presence 精确命中 / effect id→变种名
                                        # / type32→战备 / 未知类型入候选 / 未对上值记账
                                        # / tag↔mechanic 邻接配对 / **对照：键改坏后不再命中**
```

两条对照的意义：抓包侧证明"开关关掉时对原代理零影响"，对表侧证明"匹配器是能失败的"
（把 presence 键异或掉全部位后必须不再命中）—— 否则匹配逻辑只是"总能命中"的假象。

---

## 5. 已知空白

* 真实 `GalacticWarEffects` 的 schema 未见过，工具按 id/effectType/values 三组键名自适应，并把实际键名打进报告；
* `effectType` 全集只知 3 个；其余由报告给出（这也是本线最想要的结果）；
* 邻接配对（40 与 71 按 id ±1/±2）是**启发式**，权威配对要用 `Status` 里 tag/玩法 1:1 共现次数推（案例的做法）；
* 那份 effect 菜单的另一个可能来源是社区项目 `Planet-Campaign` 的 `effect_options.lua`（案例的战备目录就是用它生成的，`kind=32` + `native_hash`）；本机没有该文件，若日后拿到，可作交叉验证面。
