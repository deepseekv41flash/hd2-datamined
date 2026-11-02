# 武器「可切换模式」配方（build 26251122，实机 ✓✓✓）

> 来源：复盘 Lua 时代第三方 mod `FAF-14 Spear Unguided`（侦察见 `D:\mod\c12-recon\FAF14-Spear-Unguided-recon.md`），
> 并用 **纯数据表（dl_bin）+ 资源补丁** 在本 build 复刻。2026-11-02 实机验收全过。

## 0. 一句话

给任意制导武器加一个 **`ProgrammableAmmo`（功能 8）第二档**，档 2 打一条"自家无制导弹行"、免锁直射，
准星随档切换、菜单显示各自的档位图标/文字，并可选用资源层修炮口几何。
**`requires_target_lock +0x1C` 全程保持 1** —— 免锁是"按功能状态的覆盖"，不是把武器改成永久免锁。

## 1. 实机验收（2026-11-02，FAF-14 Spear）

| 判据 | 结果 |
|---|---|
| 档 2 不锁定能开火 | ✓ |
| 档 2 打的是"自己的弹"（不是借来的别的武器弹丸） | ✓ |
| 发射方向跟准星（不再向上飘） | ✓ |
| 模式菜单图标/文字正常 | ✓ |
| 档 1 仍然必须锁定 | ✓ |
| 准星随档切换 | ✓ |

## 2. 配方（三层，共 12 处数据 + 1 处资源）

### 2.1 `generated_entities.dl_bin`（L2 实体层，6 处）

武器实体（Spear `0x25AA2FD4643CF4EE`）：

| 组件（容器 type） | 行内偏移 | 原值 → 目标 | 作用 |
|---|---|---|---|
| `WeaponDataComponentData` `0x88E4DBB1` | `+0xB8` | 0 → **8** | 左功能槽绑定 `ProgrammableAmmo`（出现选择器） |
| 同上 | `+0x198` (24 B) | 0 → `{8,0,16}{8,1,4}` | `FirstPersonSightNodes[2]`：按功能状态的准星覆盖 |
| `ProjectileWeaponComponentData` `0x45171B68` | `+0x240` | 0 → **无制导弹行 id** | 档 2 实际发射的射弹 |
| 同上 | `+0x248` | 保持 0 | 不带生成实体 ⇒ 不制导 |
| `GuidanceTargetComponentData` `0x84957034` | `+0x48` | 0 → **8** | 把制导行为绑到功能 8（按状态生效的前提） |
| 同上 | `+0x58`（= 12 B 数组 element[1] 首 u32） | 0 → **1** | **档 2 免锁的决定性一格** |
| 同上 | `+0x5C` | `0x01000000` → `0x01000001` | element[1] 第 4 字节 = 1（与 `+0x58` 一起构成"档 2 分支"） |
| 同上 | `+0x1C` `requires_target_lock` | **保持 1** | 门禁不动；免锁只对档 2 生效 |

> `GuidanceTarget` 行 = 124 B：`+0x4C` 起是 **4 × 12 B 的按状态配置数组**（元素 = u32 + 6×u8），`element[1]` = 功能状态 1。

### 2.2 `generated_projectile_settings.dl_bin`（L1 射弹表，6 处）

`srow` 布局 = `44 + i×272`；行 id 由行内 `+0` 决定。

| 行 | 字段 | 目标值 | 说明 |
|---|---|---|---|
| **无制导行**（Spear = 223「Homing Ground Missile Mk2」） | `+60` | 制导行的伤害行（255） | 伤害对齐制导档 |
| 同上 | `+72/+76/+96/+100` | 制导行同值 | 效果/引用对齐（旧 mod 的 `clone_rels`） |
| 同上 | `+4/+8` | `0xD10F9B0E / 0x9D946B50` | 名字原子清空（dummy） |
| 同上 | `+12` | `0xED1FC986` | 档位标签 "unguided" |
| 同上 | `+16/+20` | `0x5284CF57 / 0xBC7975E0` | 图标 `guidance_off` |
| **制导行**（Spear = 229「Homing Ground Missile」） | `+12` | `0xF1143DF5` | 档位标签 "guided" |
| 同上 | `+16/+20` | `0x9D8034C9 / 0x7DB70E66` | 图标 `guidance_on` |

> 四个档位标签/图标原子是**原生**的（P-92 行 331/324、P-33 行 154/129 就用这套），不用自己造。
> 备选行优选「武器自家的遗留 dumb 行」：同一爆炸 id、dumb 标签、空图标、与制导行只差 8 个 dword。

### 2.3 资源层（L3，可选但决定"发射点几何"）

`mesh_25AA2FD4643CF4EE` 的 `opaque_transform_info.bin`（mesh toc 里的未解码区）：

| 位置 | 内容 | 原值 → 目标 |
|---|---|---|
| `+0x3D0`（32×64 B 局部变换，第 15 条 = `muzzle`） | 9 个旋转 float + 3 个位置 float | 绕 X **−15° → +0.5°**；pos `(−7.99e-8, 0.3626496, 0.3118765)` → `(…, 0.3617977, 0.3183470)`（前移 6.47 mm） |
| `+0xBD0`（32×64 B 世界矩阵，第 15 条） | 4×4 matrix | 同上旋转 + 平移 |

打包：`srkit pack <ws> --name 9ba626afa44a3aa3.patch_2`（只含这一条 mesh，toc 与 vanilla 差 38 B，gpu 逐字节不变）。

## 3. 机制小结（为什么是这几格）

```
WeaponData +0xB8 = 8 ──> 武器出现 ProgrammableAmmo 选择器（档 0/1）
WeaponData +0x198    ──> 每档的准星（按 {功能类型, 状态} 覆盖）
GuidanceTarget +0x48 = 8 ──> 制导配置也按功能状态选 element[state]
GuidanceTarget element[1] = {u32 1, [+4]=1, …} ──> 档 1 免锁分支
ProjectileWeapon +0x240 = 备选弹行；+0x248 = 0 ──> 档 1 发纯弹道（无制导实体）
备选弹行的 +12/+16 ──> 菜单里显示的档位文字/图标（取"发射的射弹行自己的"标签）
```

## 4. ⚠ 锚点按 build（踩过的坑）

| build | `generated_projectile_settings` vanilla 明文 Murmur64A |
|---|---|
| 26088801 / 25988413 | `0x946A4FE5FAAAE076` |
| **26251122（本 build）** | **`0x113A5833529A71B5`** |

改任何 dl_bin 都**保留输入明文自己的哈希**，不要照抄固定常量（实体表两代恰好同值 `0x8E49771B181FFAA1`，所以一直没暴露）。

## 5. 换武器的复用清单

1. 武器实体 id：`D:\mod\refs\entity-locid-names.json` 按名字反查；
2. 读四行原值：`WeaponData +0xB8/+0x198`、`ProjectileWeapon +0x240/+0x248`、`GuidanceTarget +0x48/+0x58/+0x5C`；
   - `+0xB8` 必须为空（0），否则换另一个功能槽；
   - 有 `GuidanceTarget` 行才谈得上"免锁档"（纯实弹武器不需要这一层）；
3. 在射弹表里找该武器**自家遗留的无制导行**（同爆炸 id、dumb 标签、与制导行只差 `{60,72,76,96,100}`）；
   找不到就把制导行整行拷到一条**无主行**（`tools/proj_copy_row.py`，判据：实体表无引用 + 不被爆炸当破片）；
4. 按 §2.2 改标签/图标/伤害引用；
5. 资源：把该武器 unit 的 `muzzle` 节点变换调平（可选；纯观感/发射方向）；
6. 门禁（G1–G9）+ 封包 + 装盘 + 回读 + 实机。

## 6. 产物与回滚

| 层 | 产物 |
|---|---|
| 实体 | `D:\mod\out\parity-entities.dl_bin`（47,259,536 B，sha `611fbfe5…`） |
| 射弹表 | `D:\mod\out\parity-proj.dl_bin`（96,652 B，sha `574b2630…`） |
| 资源 | `D:\mod\out\meshpatch2\9ba626afa44a3aa3.patch_2*`（10,208 B + 919,466 B gpu） |

```bash
cd /d/mod
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_projectile_settings.dl_bin
rm "D:/SteamLibrary/steamapps/common/Helldivers 2/data/9ba626afa44a3aa3.patch_2"{,.gpu_resources,.stream}
```

## 7. 与第三方案例的差异（我们做得更"原版形状"的地方）

| 项 | 旧 Lua mod | 本次 dl_bin 版 |
|---|---|---|
| 实现载体 | 运行期内存写入（ffi + WriteProcessMemory） | 盘上数据（dl_bin 保哈希改 + 资源补丁） |
| mesh | 整份重导出（vertex stride 20→44、材质 4→19、10 档 LOD 全满细节、gpu 919 KB→5.23 MB） | 只改 `muzzle` 两个 64 B 记录（toc 差 38 B，gpu 不变） |
| bones / state_machine / 6 动画 | 随包重发（实测与 vanilla 逐字节相同 / 仅少 8 B 零填充） | 不碰 |
| 弹道/伤害 | 克隆制导行 5 个字段 | 同（并额外把两档标签都对齐原生原子） |
