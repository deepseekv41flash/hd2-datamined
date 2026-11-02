# RECON — FAF-14 Spear Unguided（lua 时代 mod）→ dl_bin 等价性

- 侦察日期：2026-11-02（build 26251122 对照）
- 对象：`D:\Downloads\FAF-14-Spear-Unguided.zip`（1,554,090 B，sha256 `af90b79dfa50065b4bdc45b5102cd7a863c5dd226850a01561043f178fe7b219`）
- 结论一句话：**它就是一个「内存里改三张数据表 + 同包替换 Spear 单位资源」的数据 mod**；三张数据表全部落在
  `generated_entities.dl_bin` 与 `generated_projectile_settings.dl_bin` 里 ⇒ **dl_bin 路线 A 档等价**，
  功能部分已在 build 26251122 实机复现（第二档免锁开火 / 第一档仍要锁 / 准星随档切换 ✓✓✓）。

---

## §0 一句话机制

`ProgrammableAmmo`（武器功能 8）作为第二个功能档；档 0 打原制导弹，档 1 打一条**克隆出来的无制导射弹行**；
`GuidanceTarget` 新增「按功能状态的制导配置」并绑定到功能 8，档 1 的分支被改成免锁；
`WeaponData` 的 `FirstPersonSightNodes` 给出两个档位的准星；同包资源只修发射点几何（观感）。

## §1 清单与指纹

| 条目 | 类型 | 大小 | 说明 |
|---|---|---|---|
| `manifest.json` | — | 346 B | Name=`FAF-14 Spear Non-Guided Mode`，Guid=`8f2c4a6e-7d3b-4e91-a2c5-1f6b8e0d3a77` |
| `9ba626afa44a3aa3.patch_0` | 补丁 | 68,497 B | 10 条：mesh / bones / state_machine（同为 `0x25AA2FD4643CF4EE`）+ 6 条 animation + 1 条 lua `0x4DD5702766C90B5D` |
| `.patch_0.gpu_resources` | GPU | 5,234,384 B | mesh 的显存伴随（mesh toc 只有 16,180 B） |
| `.patch_0.stream` | stream | 0 B | 空 |

⚠ **撞车风险**：补丁基名 `9ba626afa44a3aa3` 与 `data/` 里现装的 Bingus 加载器 `9ba626afa44a3aa3.patch_0`
（946,416 B）**同名** ⇒ 按原名放进 `data/` 会覆盖加载器；正确做法是顺延成下一个 patch 索引（本机现在是
`patch_1` 占用 ⇒ 应作 `patch_2`）。**本报告不安装任何东西。**

## §2 作者自称做了什么（源码头两行）

```lua
-- FAF-14 Spear unguided mode (standard build: no diagnostics, no log file).
-- 按住装填键切换 制导/非制导; 非制导免锁直瞄, 同包资源修正发射点几何。
-- HD2-Addon: mods/dsh/faf_spear_unguided/spear
```

即：按住装填键切换两个功能档；非制导档免锁直瞄；资源只是修发射点几何。

## §3 载荷实测（636 行 LuaJIT 源码，非字节码）

运行形态：`CowboyBingusModLoader` API ≥ 1 → `_G.update` 钩子 → 每 60 s 幂等复查（失败 10 s 重试）。
**全部写入都是对游戏内存里两张表数据的原地改写**，没有任何 `.text`/hook：

| # | 写入（作者命名） | 值 |
|---|---|---|
| 1 | Projectile225.shortName | `0xF1143DF5`（"guided" 档标签） |
| 2 | Projectile225.icon | `0x9D8034C9 / 0x7DB70E66`（guidance_on 图标） |
| 3-7 | Projectile220 @60/@72/@76/@96/@100 | 从 225 行**逐字段克隆**（伤害行 245 + 4 个引用原子） |
| 8-9 | Projectile220.NameUpper/NameCased | `0xD10F9B0E / 0x9D946B50`（空名原子） |
| 10 | Projectile220.shortName | `0xED1FC986`（"unguided" 档标签） |
| 11 | Projectile220.icon | `0x5284CF57 / 0xBC7975E0`（guidance_off 图标） |
| 12 | WeaponData.functionSlot(Left) +184 | `8`（ProgrammableAmmo） |
| 13 | WeaponData.perModeSightNodes +404（24 B） | `{8,0,16} {8,1,4}` 两个准星节点 |
| 14 | ProjectileWeapon.alternateProjectileType +576 | `220` |
| 15 | GuidanceTarget.functionBinding +72 | `8`（把制导行为绑到功能 8） |
| 16-20 | GuidanceTarget 第二档结构（+76 数组的 element[1]） | `@0=1 @4=1 @7=0 @8=0 @9=0` |

守卫（这是它「敢写内存」的部分）：先比对 `game.dll` / exe 的 **SHA256**（钉死 build），再按 28 B 头 +
组件 index 规模定位两张分配区；每条写入前验锚点（行数、原子、伤害/爆炸引用），写完**回读**，失败**回滚**。

## §4 本 build 的对应字段（全部现算，非照抄）

### §4.1 补丁 → 本 build 偏移映射

| 组件 | 作者 build | 本 build | 依据 |
|---|---|---|---|
| WeaponData 行大小 | 1232 | **1240** | typelib 行类型 `0xD25FC7F7` |
| ↑ 影响 | 0xB8 之前**同偏移**；0x190 之后**+4** | | 作者断言 `u32(+400)==16` 准星锚点，本 build 准星在 `+0x194` |
| ProjectileWeapon | 616 | 616 | 偏移完全相同 |
| GuidanceTarget | 124 | 124 | 偏移完全相同；作者锚点 `+12=100.0f / +16=1.0f / +28==1` 本 build 全中 |

### §4.2 射弹表（`generated_projectile_settings.dl_bin`，355×272）

作者常量与本 build 的**逐字对应**（强力交叉验证）：

| 作者常量 | 本 build 实测 | 命中 |
|---|---|---|
| `L.dumb_short = 0xF1CD5269` | Spear 射弹行 **229**(`Homing Ground Missile`) `+12` | ✓ |
| `blank_icon = 0x7D4BC8F5/0x6A659858` | 行 229 `+16` | ✓ |
| 行 225 名原子 `0x0C5324C4/0xE4F875DB`、爆炸 `304` | 行 229 `+4/+8/+144` | ✓ 同一行（build 间行号 +4） |
| `L.guided_short=0xF1143DF5` + icon on | **P-92 行 331 / P-33 行 154** = 原生"制导"档 | ✓ 原生存在 |
| `L.unguided_short=0xED1FC986` + icon off | **P-92 行 324 / P-33 行 129** = 原生"非制导"档 | ✓ 原生存在 |
| `dummy_name = 0xD10F9B0E/0x9D946B50` | P-33 行 154/129 `+4/+8` | ✓ |

⇒ 本 build **不需要自己发明任何原子**：两套档位标签/图标就是 P-92/P-33 原生那套；
Spear 自己那行 `229` 的 stock 值恰好是作者断言的 `dumb_short + blank_icon`。

### §4.3 实体表（`generated_entities.dl_bin`，Spear `0x25AA2FD4643CF4EE`）

| 组件 | 字段 | 本 build 原值 → 目标 |
|---|---|---|
| WeaponData `0x88E4DBB1` | `+0xB8` 左功能槽 | 0 → 8 |
| WeaponData | `+0x198..0x1AF` sight nodes | 全 0 → `{8,0,16} {8,1,4}` |
| ProjectileWeapon `0x45171B68` | `+0x240` 备选射弹 / `+0x248` 备选生成实体 | 0 / 0 → 备选行 id / **保持 0** |
| GuidanceTarget `0x84957034` | `+0x1C` requires_target_lock | **1（不动！）** |
| GuidanceTarget | `+0x48` 功能绑定 | 0 → 8 |
| GuidanceTarget | `+0x58` 制导表[1] u32 | 0 → 1 |
| GuidanceTarget | `+0x5C` 制导表[1] 字节 | `0x01000000` → `1`（即 [4]=1,[7]=0） |
| GuidanceTarget | `+0x60` 制导表[1] 字节 | `0x01000101` → `0` |

结构依据 typelib：GuidanceTarget 行 124 B，`+76` 是 **4×12 B 数组**（`0x15CF74D6` =
{u32, u8×6}），element[1] 就是作者改的"第二档配置"；`+48` 是枚举型功能绑定（`0xDD248A52`）。

## §5 等价性判定

| 层 | 作者的做法 | 我们的载体 | 判定 |
|---|---|---|---|
| L1 设置表 | 改 ProjectileSettings 行 225/220 | 同名表可编辑（`proj_copy_row.py`，哈希 `946A4FE5FAAAE076` 已解） | **A · dl_bin 等价** |
| L2 实体组件 | WeaponData / ProjectileWeapon / GuidanceTarget 三行 | 同表同行同字段（`entity_batch_set.py`） | **A · dl_bin 等价**（核心已实机 ✓✓✓） |
| L3 资源 | mesh / bones / state_machine / 6×animation（同一 unit id） | `srkit` 解包 → 改 → `patch_N` | **B · 跨载体等价**（只影响发射点几何/观感；功能不需要） |
| L4 代码/内存 | 无（它只写数据表，不碰 `.text`） | — | **不适用** |

## §6 本 build 实测进度（单变量链）

| 轮 | 写入 | 实机 |
|---|---|---|
| 1 | `+0xB8=8` + `+0x240=324`（喂弹） | ✓ 弹丸被换（伤害/模型按 +0x28 原导弹） |
| 2 | `GuidanceTarget +0x1C` 1→0 | ✓✓ 完全不锁也能开火（门禁确认） |
| 3 | 三件套 + sight nodes（`+0x1C` 保持 1） | ✓ 准星随档切换；档 2 仍要锁 |
| 4 | + `+0x5C=0x01000001` | ✗ 同轮 3 |
| **5** | **+ `+0x48=8`、`+0x58=1`** | **✓✓✓ 档2 免锁开火 / 档1 仍要锁 / 准星随档切换** |
| 6（离线已备） | 把 element[1] 改成 **P-33 原生全字节**（[7][8][9] 也清零） | 未装 |

⇒ 经验上决定性的是 **`GuidanceTarget +0x48=8`（功能绑定）+ `+0x58=1`（element[1] 首 u32）**；
作者的 [7][8][9] 清零在本 build 不是必需（未拆分 `+0x48` 与 `+0x58` 谁起决定作用）。

## §7 与作者的差距（parity）

| 项 | 作者 | 我们现在 | 影响 |
|---|---|---|---|
| 档 1 射弹 | 克隆自己行列（伤害同制导 245） | 打 P-92 的 324 行（伤害行 102 = **80/AP3**，制导行 255 = **4000/AP7**） | 非制导档伤害偏低 |
| 档 0 菜单文字 | 改成 `guided` + guidance_on 图标 | 仍是原版 `dumb_short` + 空图标 | 菜单显示怪异 |
| 档 1 菜单文字 | `unguided` + guidance_off | **天然正确**（324 行原生就是这个） | — |
| 发射点几何 | mesh/bones/state_machine/animation | 未做（L3） | 观感 |

## §8 下一步（一句话）

用 `proj_copy_row.py` 把 Spear 自己那行 **229** 整行拷到一条**无主射弹行**，`--set` 三格
（`0x0C:0xED1FC986`、`0x10:0x5284CF57`、`0x14:0xBC7975E0`），再把 Spear `ProjectileWeapon +0x240`
指向它 ⇒ 非制导档拿到 Spear 自己的 4000 伤害 + 原生 "Unguided" 标签；同时把行 229 的 `+12/+16/+20`
改成 `0xF1143DF5 / 0x9D8034C9 / 0x7DB70E66` 修档 0 标签。

## §10 资源层实测（2026-11-02，vanilla bundle `530bb611a14b6ce3` 对照）

同一 unit id `0x25AA2FD4643CF4EE` 在补丁里带 4 族资源 + 6 个动画。逐字节对照结果：

| 资源 | vanilla | mod | 结论 |
|---|---|---|---|
| bones | 381 B | 381 B | **逐字节相同**（0 处差异）→ 骨骼没动 |
| state_machine | 1868 B | 1860 B | 只有 2 处头偏移（`0x740→0x73C`、`0x748→0x740`）+ 尾部 8 B 零填充被裁 ⇒ **无功能改动**，重打包重序列化产物 |
| physics | 15,100 B | 未带 | 未改 |
| animation ×6 | — | — | 已比对 6/6：全部**逐字节相同**（见下） |
| mesh | toc 10,016 B / gpu 919,466 B | toc 16,180 B / gpu 5,234,384 B | **只有这里真改了**（见 §10.1） |

### §10.1 mesh 里的真实几何改动 = `muzzle` 节点

mesh 自带 32 条节点变换表（名字与骨骼同名：root/skeleton/boss/**muzzle**/sight/attach_optic/attach_mag/attach_ammo/foregrip/eye/pivot…）。
逐条比对后**只有 `muzzle` 一条是真实改动**，其余 9 条数值完全相同（只是重导出产生的 ±0.0 / 末位浮点噪声）：

| muzzle 节点 | vanilla | mod | 变化 |
|---|---|---|---|
| 局部位置 (x,y,z) | (−0.00000008, **0.3626496**, **0.3118765**) | (−0.00000008, **0.3617977**, **0.3183470**) | z **+6.47 mm**、y −0.85 mm |
| 绕 X 旋转 | **−15.00°** | **+0.50°** | 把枪口静置姿态从下俯 15° **拉平到 ~0.5°** |

⇒ 作者说的"修正发射点几何"就是这一条：**mesh 节点表里 `muzzle` 骨骼的静置变换被调平 + 前移 6.5 mm**。
其余 mesh 差异都是建模工具**重导出的副作用**（不是功能改动）：
vertex stride 20 → 44 B、material 槽 4 → 19（同一批材质重复登记）、10 个 LOD 槽全部指向同一份满细节网格
（gpu 919 KB → 5.23 MB）、`opaque_bone_info` 2,032 → 7,888 B。

**工程含义**：这一层是 L3（资源载体），要用 srkit 走 `patch_N` 才能复刻；功能（切换/免锁/准星/伤害）全都
不需要它，它只影响第三人称的炮口位置与朝向观感，以及"满细节 LOD"带来的显存/性能开销。

## §11 非制导模式用的是哪条射弹（本 build）

- 作者 build 用 **projectile 220**；本 build 同一行 = **projectile 223**。
  交叉锚点：名原子 `0xE9CEEEAC/0xAE182F69`、档标签 `0xF1CD5269`(dumb)、空图标 `0x7D4BC8F5/6A659858`、
  `+72=0xB0ADACB2 +76=0xD517240A +96=0x4DCA80A3 +100=0x555CA615`、`+144` 爆炸 `304` —— 全部与本 build 行 223 相同。
- 行 223 的名字表条目 = **"Homing Ground Missile Mk2"**（行 229 = "Homing Ground Missile"）。
  它与行 229 **只差 8 个 dword**：`+0`(type)、`+4/+8`(名字原子)、**`+60`(伤害行 256 vs 255)**、
  `+72/+76`、`+96/+100` —— 正好是 mod 的 `clone_rels = {60,72,76,96,100}` ⇒ **它就是 Spear 自己的遗留"无制导"弹行**，
  本 build 伤害行 256 = 1500/AP8-7-6-0（制导行 255 = 4000/AP7）。
- **是孤儿行**：全实体表里带 `ProjectileType` 枚举字段的 7 个组件块、0 处引用它；爆炸表 `+84` 破片射弹 0 处引用它；
  全表只有 229/223 两条共享爆炸 304（都是 Spear 家族）。
- mod 不依赖 223 的原始数值：它把制导行的 5 个差异字段**克隆进 223**，于是非制导档的伤害/效果与制导档完全一致。

## §12 Parity 版实现（2026-11-02，已装盘，**实机 ✓✓✓**）

> 实机验收（2026-11-02）：档 2 不锁定能开火、打的是 Spear 自己的弹、发射方向跟准星、图标文字正常；
> 档 1 仍需锁定、准星随档切换。配方已沉淀为 `docs/cases/WEAPON-SWITCHABLE-MODE-26251122.md`。

按 §11 的结论 + §10 的 muzzle 改动做成三层等价品：

| 层 | 产物 | 改动 |
|---|---|---|
| L2 实体 | `out/parity-entities.dl_bin`（47,259,536 B，sha `611fbfe5…`，回读 `e53f3191…`） | 第 5 轮实机通过的那套（`+0xB8=8`、sight nodes、`GuidanceTarget +0x48=8/+0x58=1/+0x5C=0x01000001`、`+0x1C` 保持 1）+ **`ProjectileWeapon +0x240 = 223`** |
| L1 射弹表 | `out/parity-proj.dl_bin`（96,652 B，sha `574b2630…`，回读 `2276d5d6…`） | 行 **223**：名字→dummy 原子、标签→`0xED1FC986`(unguided)、图标→guidance_off、`+60→255`、`+72/+76/+96/+100` ← 行 229；行 **229**：标签→`0xF1143DF5`(guided)、图标→guidance_on |
| L3 资源 | `out/meshpatch2/9ba626afa44a3aa3.patch_2*`（10,208 B + 919,466 B gpu） | 只含 1 条 mesh 资源；`opaque_transform_info.bin` 里 `muzzle` 的局部变换（+0x3D0）与世界矩阵（+0xBD0）改成案例值（−15° → +0.5°，位置 +6.47 mm） |

离线门禁：实体 G1–G9 全 PASS；射弹表 G1–G6 全 PASS（长度不变、差异 ⊆ 声明字段 ∪ 校正字、哈希回到**本 build 原值**）；
mesh patch `srkit list` = 1 条 mesh，toc 与 vanilla 仅差 38 字节（两处 muzzle 变换），gpu 逐字节相同。
装盘回读：两个 `.dl_bin` 解密后 sha256 与目标明文逐字节一致；`data/9ba626afa44a3aa3.patch_2` 已就位。

### ⚠ 重要发现：内容哈希锚点是**按 build** 的

`tools/proj_copy_row.py` 里硬编码的 `EXPECTED_HASH = 0x946A4FE5FAAAE076` 是 **build 26088801/25988413** 的值；
build 26251122 的 `generated_projectile_settings` vanilla 明文哈希是 **`0x113A5833529A71B5`**（实测两代缓存）。

| build | 明文哈希 |
|---|---|
| 26088801 / 25988413 | `0x946A4FE5FAAAE076` |
| **26251122（本 build）** | **`0x113A5833529A71B5`** |

⇒ 改任何 dl_bin 时**不要照抄固定锚点**，一律「保留输入明文自己的哈希」（工具里 `h0 = murmur64(data)` 就是这个语义，
常量只作 sanity 提示）。实体表两种 build 恰好同值（`0x8E49771B181FFAA1`），所以之前没暴露。

### 回滚（三条）

```bash
cd /d/mod
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_projectile_settings.dl_bin
rm "D:/SteamLibrary/steamapps/common/Helldivers 2/data/9ba626afa44a3aa3.patch_2" "…patch_2.gpu_resources" "…patch_2.stream"
```

## §9 明确不做

- 不安装这个 zip（撞加载器名）；不启动游戏；不改仓库既有结论；
- 不照抄作者的 RVA / 行号 / 伤害行 id（build 间行号已 +4，伤害行 245→255 也不同）。
