# 26251122 落地后的密钥与表级 diff（2026-10-29）

> 前置：升级前已把盘面还原成纯原版并做了 642 MB 备份与明文/指纹快照，
> 见 [BUILD-26251122-PRE-UPDATE](BUILD-26251122-PRE-UPDATE.md)。用户已确认新 build 能正常进游戏。

## 1 密钥：**没变**（`✓ 离线`）

用我们手上的 `refs/dlbin/keys/recipient.sk` 直接解新 build 的全部表：

* `data/game/*.dl_bin` **55 张 + `dl_library.dl_typelib`** → **56/56 全部解封成功，0 失败**
  （解出明文以 `LDLD` 开头、组数与旧版一致）
* 新封包头格式相同：48 B（`epk 32 B | tag 16 B`）+ 密文

⇒ **封/解封链路、`dlbin_deploy`、`entity_transplant` 等所有依赖密钥的工具继续可用**，
不需要重新取密钥。

## 2 typelib：**字节完全相同**（`✓ 离线`）

| 项 | 旧 26088801 | 新 26251122 |
|---|---|---|
| `dl_library.dl_typelib` | 1,080,024 B / `a2392b58c80a2a70…` | 1,080,024 B / `a2392b58c80a2a70…` |

⇒ **所有字段偏移、`TransitionId` 枚举（46 个值）、SeatCollection/Mount/Health/Vehicle 的行结构结论继续有效**。

## 3 表级 diff：55 张表，**51 张逐字节不变**，4 张变了

工具：`tools/build_diff.py`（结构层）→ 55 张全部比较、0 解封失败；再用新增的
`tools/table_row_diff.py`（组/字节/值级）逐张展开。

| 表 | 变化 | 值级结论 | 对应官方说明 |
|---|---|---|---|
| `generated_projectile_settings.dl_bin` | **1 处 u32** | `+0x10F18`: **60.0 → 20.0** | AMW-20 APEX **口径 60 → 20** |
| `generated_damage_settings.dl_bin` | **1 处 u32** | `+0x3FB4`: **15 → 30** | APEX **拆除强度 → 30** |
| `generated_stratagem_settings.dl_bin` | 名字表 **1 条**（整体 −8 B 重排） | `$TEAM WEAPONS. LASER RIFLE ION` → `TEAM WEAPONS. LASER RIFLE ION`（去掉前导 `$`） | 显示名修正（notes 未写） |
| `generated_video_flow_settings.dl_bin` | **−120 B**（两个条目） | 两条音乐流程被删 | "Removed two music tracks" |

**其余 51 张（含 `generated_entities.dl_bin`）逐字节相同** ⇒ TD-220 / Maelstrom / GATER 的
每一行、`SeatCollection +0x00`、`MountComponentData` 槽位、`Health`/`Vehicle` 参数**全部照旧**。

### 3.1 与官方 notes 的三条交叉验证

| notes 条目 | 数据侧观察 | 结论 |
|---|---|---|
| APEX 口径 60→20、拆除强度→30 | projectile 表 60→20 一处；damage 表 15→30 一处 | **一致** |
| LAS-44 NOVA 只修显示 | 无对应数值变化 | **一致** |
| SG-22 BUSHWACKER 405→486 / 108→135 | damage 表**没有**第二处改动 | notes 明说这是"上一版算错的更正" ⇒ 属文档更正，非本版数据变化，**自洽** |

### 3.2 一处 `⚠ 未证`

`generated_generation_settings.dl_bin`：旧明文集（`plaintext-26088801/`）**缺这一张**
（历史 dump 漏收），无法做内容级对比。新旧封包大小同为 **10,444 B**，且本次 notes 未涉及该表
⇒ 暂记"未观察到变化"，升级前的指纹里保留了它的旧 sha 供以后复核。

## 4 产物

| 文件 | 内容 |
|---|---|
| `refs/dlbin/plaintext-26251122/` | **56 个**新 build 明文（55 张表 + typelib） |
| `refs/build-diff-26251122.json` | 结构层 diff（build_diff.py 输出） |
| `refs/row-diff-generated_{projectile,damage,stratagem,video_flow}_settings.json` | 值级 diff 明细 |
| `tools/table_row_diff.py` | 新工具：组/字节/值级 diff（`--style groups|chain`、`--stride` 行号换算、`--match` 数字过滤） |

## 5 影响与下一步

1. **我们的所有 mod 资产要按新明文重封包**：旧 `.patch_N` 绑定的是旧包内容，**不可直接复用**。
2. **GATER 换壳线可以原样继续**：新 build 的 entities 与旧版逐字节相同 ⇒ 之前的宿主选择、
   14 行移植 spec、`TransitionId 33`、`boss` 挂点分析全部仍然成立；只需把基线从
   `plaintext-26088801` 换成 `plaintext-26251122` 重跑 `entity_transplant.py` 再封包。
3. 未证嫌疑仍是两个：**壳状态机**（曾装上"换成坦克 SM"但没拿到实机判读）与**挂载物/托架**（`nomount` 版已备）。
4. 第三方 APC 模组同理需要按新 build 的包重打；它的 `recipe.json` 内容哈希锚点也要重新核对。
