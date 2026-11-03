# RECON：Slidedivers – Tribes 1.0（build 26251122，Chef 兼容）—— 滑步/移动参数案例

> 2026-11-03 只读侦察（zip 未装盘）。目标：弄清它到底改了什么、怎么部署、能不能用我们的
> 「generated_*.dl_bin 明文替换」路线完全复现。
> 结论：**能，而且明文逐字节复现成功**（sha 与作者文件相同）。
> 相关工具：`tools/hd2fm1.py`（Chef 系文件载荷容器）、`tools/entity_fields_batch.py`（一行多字段写 + 单校正字保哈希）、
> `tools/dlbin_seal.py`、`tools/dlbin_deploy.py`。

## 0. 一句话结论（三态）

| 维度 | 判定 |
|---|---|
| 它是什么 | 把 `data/game/generated_entities.dl_bin` **整文件替换**成一份「原版 + 15 个 f32 字段改写」的保哈希版本 |
| 改了什么 | **只改** `avatar_helldiver` 类型记录的 `AvatarComponentData` 第 0 行（`0x4D1C334D294DFA97`）的 15 个 f32：`StaminaCostSlide` + `SteepSlopeMovementInfo` 7 个（进入角/进入时长/滑速/重力倍率/最短保持/退出角/超角度退出延迟）+ `ActionSlideMovementInfo` 6 个（平地/上坡/下坡 × 时长/速度）+ `WeatheringSettings.DirtSpeedSliding`（字段名见 [AVATAR-HELLDIVER-FIELDS](AVATAR-HELLDIVER-FIELDS-26251122.md)） |
| 有没有动「物理属性」 | **没有**：不改 unit/bones/物理资源，也不改内存/代码；所有效果都来自这张实体表里的移动参数 |
| 能否用数据表路线复现 | ✓ **完全可复现**：我们从原版起重建出**逐字节相同**的明文（sha `cf09c51af2d688f4`），并已封包成可直接装盘的产物 |
| 部署方式 | 作者用 Chef 系「file-mod installer」Lua：游戏**退出时**把内嵌的已封装 dl_bin 写到游戏目录；我们用 `dlbin_deploy.py` 直接装，不需要 Chef |

## 1. 清单与校验

| 文件 | 大小 | sha256(前16) | 说明 |
|---|---|---|---|
| `Slidedivers-Tribes-v1.0-build26251122-Chef-Compatible.zip` | 51,946,986 | `0b4976c4ab6bdaec` | 主包（49.5 MB） |
| `Install/9ba626afa44a3aa3.patch_0` | 12,448 | `a2d3f616d2f28913` | 安装器 Lua（替换游戏 boot 脚本） |
| `Install/b5b0c0ffee5b5b1f.patch_0` | 47,260,208 | `7b5827697490c4de` | 载荷 Lua 资源（内含整份被封装的 entities 表） |
| `manifest.json` / `README.txt` | 942 / 1,747 | `5008c178…` / `9b042e6a…` | HD2 Arsenal 清单 + 作者说明 |
| `UninstallHelper/9ba626afa44a3aa3.patch_0` | 12,448 | 同安装器 | 同一份安装器的「卸载用」副本 |

- 两个 patch 都只含 **1 个 `lua` 资源**：
  - 安装器：id `0xF476DF93691895FA`，payload 12,241 B（`u32 len + u32 kind + 源码`）；
  - 载荷：id `0xB5B0C0FFEE5B5B1F`，payload 47,260,001 B（`kind=2`，body 47,259,993 B，`HD2FM1` 容器）。
- 载荷容器头：`HD2FM1` + u32 头长(527) + 头文本（name/version/target/size/stock/mod）+ **已封装的 .dl_bin**；
  `sealed` 47,259,456 B，sha `fbc6f7e29333aa6d`，其 `mod=` 指纹与实测一致；`stock=` 指纹（47,259,444 B，
  `5562BAE9…/…/…`）**与本 build 的原版封装文件完全一致**（我们现有原版备份 sha `4121f332a6d16307`）。

## 2. 作者自带文档（先读作者的）

1. **zip 内 `README.txt`**：必须用 Chef 1.1.0；先卸载其它替换 `generated_entities.dl_bin` 的 mod；
   Chef 放最后/最高优先级；先启动到主菜单再正常退出（安装发生在退出时）；看 `HD2FileMods.log`；
   与 JAR-5 / MG-206 / Fire & Fall 等「整文件替换」互斥。
2. **GitHub `RojoMojo666/mods` → `slidedivers-tribes/README.md`**：给出三个变体的倍率表（见 §4.3）与安装/卸载/切换纪律。
3. **AyakaMods 更新页（1.0 EAC 版）**：以玩家语言描述效果：
   > Flat ground: 4× slide duration and 1.7× slide speed. / Uphill: 1.75× slide duration and 1.15× slide speed. /
   > Downhill: 5.2× slide duration and 2.2× slide speed. / Slide stamina cost: 35% of normal. /
   > Steep slopes: faster automatic sliding, stronger downhill pull and quicker entry. /
   > Dirt buildup while sliding: 75% of normal.

   并强调「这是改游戏设置，地形/碰撞/正常移动打断仍会结束滑步」。

## 3. 包结构与部署机制

### 3.1 两个 Lua 资源，各司其职

- **安装器**（archive `9ba626afa44a3aa3`）：替换游戏的 **boot 脚本**（原脚本只有空的 init/update/render/shutdown）。
  它在 `shutdown`（游戏正常退出）时：
  1. 扫描 `data/b5b0c0ffee5b5b10 … 1f` 这些 archive 的 `patch_N` 文件，逐个找载荷资源；
  2. 解析 `HD2FM1`：核对 `stock=`/`mod=` **指纹**（长度 + 头/中/尾各 32 B 的十六进制）与 `target`；
  3. 只有当前文件是「已知原版」或「本家旧版 mod」时才动手：先备份 `HD2FileMods.<文件名>.original`，
     再把载荷里的封装 dl_bin 写进 `data/game/<target>`；状态写 `HD2FileMods.state`，日志写 `HD2FileMods.log`；
  4. 载荷缺失（mod 被禁用）时，把文件从备份还原；
  5. 同 target 多载荷 → 记 `CONFLICT`，只应用第一个；文件不认识 → `REFUSE`，绝不强写。
- **载荷**（archive `b5b0c0ffee5b5b1f`）：**不是** Lua 代码，而是「以 `lua` 资源类型携带的二进制文件容器」。

> 机制要点：**写盘发生在退出时，效果从下一次启动开始**（这与 README 的「启动到主菜单→正常退出→再启动」一致）。
> 指纹用「长度+三处 32 B」而不是整文件哈希，于是能跨随机封包识别同一内容；这也是它敢在游戏更新后
> 「刷新过期备份」的底气。

### 3.2 `HD2FM1` 容器（我们已做成工具 `tools/hd2fm1.py`）

```
resource body = u32 body_len | u32 kind(=2) | "HD2FM1" | u32 header_len |
                header lines (name= / version= / target= / size= / stock= / mod=) |
                sealed .dl_bin (size 字节)
```
`stock=`/`mod=` 的指纹格式：`<文件长度>:<头32B><中32B><尾32B>`（hex 大写）。

### 3.3 为什么**我们不需要 Chef**

安装器做的事，等价于我们已有的两条命令：

```bash
python tools/hd2fm1.py extract <载荷.bin> --out payload.sealed.dl_bin --unseal refs/dlbin/keys/recipient.sk --plain payload.plain
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed payload.sealed.dl_bin
```
（`dlbin_deploy.py` 自带原版备份与 `restore`，比用 Lua 在游戏退出时写盘更可控。）

## 4. 载荷内容：只改一个实体的 15 个 f32

### 4.1 定位

- 明文 = 47,259,408 B = 原版（47,259,396）+ **12 B**（4 B 补零 + 8 B 哈希校正字）；
  **Murmur 内容哈希仍是 `0x8E49771B181FFAA1`**（与原版一致）⇒ 作者用的就是「tail 宿主保哈希」同一套数学。
- 与纯净原版逐字节比较：**15 个 4 字节字**（全在一个组件行内）+ 末块 payload 字段（560→572）。
- 组件：`AvatarComponentData`（块 tid `0x40EF204C`，哈希图 32 B + 2 行 × 852 B，块头 `0x191B0A8`）；
  行 0 的实体键 = `0x4D1C334D294DFA97`，`dev_name = content/fac_helldivers/cha_avatar/avatar_helldiver`
  ⇒ **玩家 Helldiver 的类型记录**（`AvatarComponentData` record 0）。
- 行结构 `0xB501F712`（852 B）的成员与本项目已知的 hd2runtime 字段表**完全对得上**
  （+4…+48 移动速度、+52… 体力、+340 起 ExertionLevelInfo），这也是下面语义命名的依据。

### 4.2 字段表（行内偏移；原版 → Tribes OG）

| 行内偏移 | 字段（filediver 名，见 [AVATAR-HELLDIVER-FIELDS](AVATAR-HELLDIVER-FIELDS-26251122.md)） | 原版 | Tribes OG | 倍率 | 作者描述对应 |
|---:|---|---:|---:|---:|---|
| `+0x05C` | `MovementInfo.StaminaCostSlide` | 0.05 | 0.0175 | ×0.35 | 滑步体力 35% ✓ |
| `+0x098` | `SteepSlopeMovement.SlideEnterAngle` | 45 | 36 | ×0.8 | "quicker entry"（进入角更松） |
| `+0x09C` | `SteepSlopeMovement.SlideEnterMinimumDuration` | 0.3 | 0.15 | ×0.5 | "quicker entry"（需保持时间减半） |
| `+0x0A0` | `SteepSlopeMovement.SlideSpeed` | 3 | 5.4 | ×1.8 | "faster automatic sliding" |
| `+0x0A4` | `SteepSlopeMovement.SlideGravityMultiplier` | 1 | 1.5 | ×1.5 | "stronger downhill pull" |
| `+0x0A8` | `SteepSlopeMovement.SlideMinimumDuration` | 0.3 | 0.525 | ×1.75 | 最短滑行时间更长 |
| `+0x0AC` | `SteepSlopeMovement.SlideExitAngle` | 40 | 28 | ×0.7 | 更晚退出滑行 |
| `+0x0B0` | `SteepSlopeMovement.SlideBeyondMoverMaxAngleExitDuration` | 0.2 | 0.25 | ×1.25 | 超坡度后更晚退出 |
| `+0x0D0` | `SlideMovementInfo.SlideFlatDuration` | 0.5 | 2.0 | ×4.0 | 平地时长 4× ✓ |
| `+0x0D4` | `SlideMovementInfo.SlideFlatSpeed` | 3 | 5.1 | ×1.7 | 平地速度 1.7× ✓ |
| `+0x0D8` | `SlideMovementInfo.SlideUphillDuration` | 0.1 | 0.175 | ×1.75 | 上坡时长 1.75× ✓ |
| `+0x0DC` | `SlideMovementInfo.SlideUphillSpeed` | 2.9 | 3.335 | ×1.15 | 上坡速度 1.15× ✓ |
| `+0x0E0` | `SlideMovementInfo.SlideDownhillDuration` | 1 | 5.2 | ×5.2 | 下坡时长 5.2× ✓ |
| `+0x0E4` | `SlideMovementInfo.SlideDownhillSpeed` | 3.6 | 7.92 | ×2.2 | 下坡速度 2.2× ✓ |
| `+0x150` | `WeatheringSettings.DirtSpeedSliding` | 20 | 15 | ×0.75 | 滑步尘土 75% ✓ |

> 说明：字段名来自 filediver 的 Go 反向工程（`AvatarComponent` 结构），并已用我们的 typelib 做**偏移级验证**
> （28/28 成员偏移对齐、总大小 852 B 精确一致）；完整字段图与语义见
> [AVATAR-HELLDIVER-FIELDS-26251122](AVATAR-HELLDIVER-FIELDS-26251122.md)。
> 由此**全部 15 个改动都有确定字段名**，作者 README 的每一条描述都能一一落到字段上。

### 4.3 三个变体交叉验证 → 6 个滑步档位字段坐实

作者发布了 3 个变体；把它们的载荷都解出来后，只有 4 个字段不同，且与 README 的倍率表**完全一致**：

| 字段 | Tribes OG | Tribes Faster | Tribes Oxygenator | README 对照 |
|---|---:|---:|---:|---|
| `+0xD0` 平地时长 | 2.0 (×4) | 2.0 (×4) | **0.75 (×1.5)** | OG/Faster 4×；Oxy 1.5× ✓ |
| `+0xD4` 平地速度 | 5.1 (×1.7) | **6.0 (×2.0)** | **6.0 (×2.0)** | OG 1.7×；Faster/Oxy 2.0× ✓ |
| `+0xD8` 上坡时长 | 0.175 (×1.75) | 0.175 (×1.75) | **0.1（原版，不改）** | OG/Faster 1.75×；Oxy 1.0× ✓ |
| `+0xDC` 上坡速度 | 3.335 (×1.15) | 3.335 | 3.335 | 全部 1.15× ✓ |
| `+0xE0` 下坡时长 | 5.2 (×5.2) | 5.2 | 5.2 | 全部 5.2× ✓ |
| `+0xE4` 下坡速度 | 7.92 (×2.2) | **15.12 (×4.2)** | **15.12 (×4.2)** | OG 2.2×；Faster/Oxy 4.2× ✓ |

⇒ `+0xD0…+0xE4` 六个字段的**槽位含义**（平地/上坡/下坡 × 时长/速度）现在是**实证结论**，不是猜测。
（`+0x98…+0xB0` 七个字段与 `+0x150` 在三个变体里完全相同，属于「Tribes 系列共享的陡坡/尘土调校」。）

### 4.4 对「移动/物理」的含义

- 这 15 个字段都是**角色移动参数**：`ActionSlideMovementInfo` 的滑步时长/速度（按坡度分档）、`StaminaCostSlide` 体力消耗、`SteepSlopeMovementInfo` 的陡坡自动滑行（进入/退出角、滑速、重力倍率等）、`DirtSpeedSliding` 滑步沾土速率。
- **不是**发动机物理（没有碰 unit/物理资源、没有碰碰撞体、没有碰重力表）；地形/碰撞/打断仍由引擎逻辑决定。
- 记录是 **type-wide**：改的是 `avatar_helldiver` 类型记录 ⇒ 本机模拟的每个 Helldiver 都读它（任务内会立刻生效）；
  船上 avatar 有私有副本（hd2runtime 记录的 delta `0x73012E9238B6E3B9`），所以在飞船上测不出来，要在任务里测。

## 5. 与我们的工具链等价：**逐字节复现成功**

- 用我们新写的 `tools/entity_fields_batch.py`（一次写同一行任意多字段，仍然只是一个 8 B 尾部校正字）：
  以 15 个字段的**原始位模式**重建 → 明文 sha `cf09c51af2d688f4`，**与作者载荷的解封明文逐字节相同** ✓。
- 若用 README 倍率在 Python 里做 f32 乘法再写，会有 4 个浮点数**最低位**不同（`+0xA8/+0xD8/+0xE0/+0xE4`，
  差 ~1e-7）：作者生成器有它自己的 f32 运算/取整路径；对实际效果无影响，但做「逐字节复现」时应直接用位模式。
- 产物（可直接装盘，**不需要 Chef**）：

| 产物 | 大小 | sha256(前16) | 说明 |
|---|---|---|---|
| `out/slidedivers/slidedivers-tribes-og.rebuilt.plain` | 47,259,408 | `cf09c51af2d688f4` | 与作者明文逐字节相同 |
| `out/slidedivers/slidedivers-tribes-og-rebuilt.dl_bin` | 47,259,456 | `301808a5a8106067` | 我们自己封装的 sealed 版（内容等价） |
| `out/slidedivers/mod-payload-as-shipped.sealed.dl_bin` | 47,259,456 | `fbc6f7e29333aa6d` | 作者原封装（证据/对照） |

安装 / 回滚：

```bash
# 装（先确认游戏已关闭；当前盘上是 LAS-17 三档测试盘，会被替换）
python tools/dlbin_deploy.py install --file generated_entities.dl_bin \
    --sealed out/slidedivers/slidedivers-tribes-og-rebuilt.dl_bin
# 回滚到本 build 原版
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
```

## 6. 风险与纪律

- **共享文件**：本 mod、JAR-5、MG-206、Fire & Fall 等「整文件替换」预设互斥，一次只能装一个（作者的安装器会记 `CONFLICT`）。
- **游戏更新**：更新后旧的 `<文件>.original` 备份不能直接还原（跨 build 备份会出问题）；本项目的账本也要按
  「备份必须与本 build 明文逐字节一致」的纪律核对（见 HEAT-LAS17 案 §36）。
- **EAC/联机**：文件替换路线属于第三方 mod，风险自担（作者也标注为 Single-Player/Trainers-Cheats 分类）。
- **不要边跑边写**：安装器只在游戏**退出**时写盘；我们的 `dlbin_deploy.py` 也应在游戏关闭时用。

## 7. 下一步建议（换线后的两条可选路）

1. **实测手感**：把 §5 的重建件装盘，进任务对比原版滑步（预期：平地滑得更久更快、下坡更远、上坡更短、滑步耗体力 35%）。
   这一步只验证「我们的替换 = 作者效果」，一次启动即可。
2. **单变量探针（把未命名字段钉死）**：用 `entity_fields_batch.py` 每次只改一个字段，实测：
   - `+0x98 / +0xAC`（45→36 / 40→28，像角度）→ 改大改小看「进入/退出滑步的坡度阈值」；
   - `+0x9C`（0.3→0.15）→ 进入延迟；
   - `+0xA0`（3→5.4）→ 陡坡自动滑行速度；
   - `+0xA4`（1→1.5）→ 下坡拉力；
   - `+0x150`（20→15）→ 尘土累积；
   - `+0xB0`（0.2→0.25）/ `+0xA8`（0.3→0.525）→ 待定。
   建议一次只改一个、数值取「极端值」以便肉眼判断（例如角度 45→15、拉力 1→5）。
3. **自建 preset**：工具已就绪，任意倍率组合都能一条命令生成 + 封包 + 装盘（模板见 §5）。
4. **同管线姊妹案例**：Fire & Fall（同为该仓库/同 `HD2FM1` 管线，改的是火/坠落伤害倍率）——可顺带侦察，
   把「Avatar/Health 类型记录」的另一组字段也钉死。

## 8. 复跑命令（侦察侧）

```bash
# 1) 解出 patch 里的 lua 资源（srkit）
cd D:/mod/work/repo-srkit
python -m srkit extract "<zip解压>/Install/b5b0c0ffee5b5b1f.patch_0" --id 0xB5B0C0FFEE5B5B1F -o <outdir>
python -m srkit extract "<zip解压>/Install/9ba626afa44a3aa3.patch_0" --id 0xF476DF93691895FA -o <outdir2>

# 2) 看载荷头 / 抽出 sealed / 解封
python tools/hd2fm1.py show    <outdir>/lua_B5B0C0FFEE5B5B1F.toc.bin
python tools/hd2fm1.py extract <outdir>/lua_B5B0C0FFEE5B5B1F.toc.bin \
    --out /tmp/payload.sealed --unseal refs/dlbin/keys/recipient.sk --plain /tmp/payload.plain

# 3) 与纯净原版 diff（定位到 AvatarComponentData 行 0）
#    再按 §5 用 entity_fields_batch.py 重建
```
