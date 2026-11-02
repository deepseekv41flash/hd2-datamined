# WASP 弹道修复（打转 + 随机发射方向）— 纯数据表路线（build 26251122）

> 2026-11-02 一整天的单变量实机链收口。所有结论来自 `generated_entities.dl_bin` 明文编辑（保内容哈希 `0x8E49771B181FFAA1`），
> 未用 Lua、未换资源、未换生成实体。关联文档：`GUIDANCE-MODES-26251122.md`（制导三问 + deviation 拆分细节）。

## 0. 结论一句话

WASP Burst 的两个弹道毛病都在**弹头实体**（`0x14CC0DB942F6D7F2`）的
`SeekingMissileComponentData` → `SeekingMissileDeviationSettings`（`+0xB4` 起 68 B）里：

| 字段（行内偏移） | 语义（实机） |
|---|---|
| `+0xB8/+0xBC` | **发射方向随机范围（度）** —— 原版 −75/+75 |
| `+0xC0/+0xC4` | **弧线半径/偏离弧度** —— 原版 40/55 |
| `+0xE4` | **打转开关/转速档位** —— 原版 5（开），P-33 是 2（关） |
| `+0xE8` | 非开关（未定；R5 保持 0.2 仍不打转） |
| `+0xC8…+0xDC` 两个 Vec3 | 与打转无关（R1 全改无感）；含义未定 |

→ 想"直线"：A 对压到 ±15 以下 + B 对压到 10/15 + `+0xE4`=2（P-33 配置）。
→ 想"弧线但不打转"：只把 `+0xE4` 改 2（其余保持 WASP 原值）= **当前装盘 R5**。

## 1. 案源：Lua 时代 mod `WASP Trajectory Fix`

`D:\Downloads\WASP Trajectory Fix.zip`（sha256 `0ca90557…`，两个变体 Trajectory / WASP-33）。

- 作者做法：唯一运行期写入 = `ProjectileWeaponComponentData +0x28`（8 B）把 WASP Burst 的生成实体
  `0x14CC0DB942F6D7F2` 换成 P-33 的 `0xA1470A4DAB237264`；另重发 P-33 导弹单位 `0x350168E3FD02B325` 的
  mesh/贴图/材质（资产驻留）。**射弹行一个字节没改。**
- 作者注释原话：v2 把整行 P-33 射弹数据拷过去后"仍是 WASP 式跟踪路径"，因为**实体没换** ⇒ 飞行/模型由生成实体决定。
- 对我们的意义：定位到实体层；但**纯数据层不需要换实体**，只改实体里 68 B 参数即可（更小、不动模型与资源）。

## 2. 实验链（全部单变量实机，基线 A 对固定 ±15 防随机方向干扰）

| 轮 | 改动 | 实机结果 |
|---|---|---|
| W1 | 只改 A 对 −75/75→−8/8 | 发射方向随机**消失**；打转仍在 |
| W2 | deviation 整块 68 B = P-33（12 处） | 随机 + 打转**都消失** |
| R1 | A + V1/V2 两个 Vec3 = P-33 | 打转仍在 ⇒ V1/V2 与打转无关 |
| R2 | A + B 对 + 尾部两格 = P-33 | 打转消失 ⇒ 关键在 B 对或尾部 |
| R3 | A + 只 B 对 = P-33（10/15） | 打转仍在、**半径变小** ⇒ B 不是开关 |
| R4 | A + 尾部两格（5/0.2→2/0.1） | **不打转**、轨迹仍是弧线 ⇒ 尾部是开关 |
| **R5** | A + **只 `+0xE4`**（5→2） | **打转消失** ⇒ 开关 = `+0xE4` 单字段 |

## 3. 跨武器数值一致性（模型自洽验证）

| 武器 | A 对 | B 对 | `+0xE4` | 实机观感 |
|---|---|---|---|---|
| WASP Burst | −75/75 | 40/55 | 5 | 小半径弧 + 打转 |
| WASP Artillery | −8/8 | 60/75 | 2 | 高抛弧、不打转 |
| P-33 | −15/15 | 10/15 | 2 | 准直 |
| P-92 | 0/0 | 0/0 | 5 | 半径 0，无异常 |

## 4. 外部资料核查（字段名）

- 本地（`refs/hd2runtime-repo`、`c11-recon/sdk-0.30.3`、`refs/helldiversdata`、wiki）：**没有** deviation 字段文档。
- 社区 dump [shalzuth/HelldiversData](https://github.com/shalzuth/HelldiversData)（编辑器元数据，最后提交 2025-09-20，早于本 build）：
  - 有 `SeekingMissileComponent` 的 **29 个字段名 + 官方 tooltip**（可用部分：`targeting_mode`、`angle_lost_guidance`=180、
    `max_lifetime`=30、`acceleration`=200、`max_angle_to_target`=45、`javelin_firing_mode`"先上抛再下压" 等，
    与本 build 实测值逐一对上）；
  - 有 `SeekingMissileTargetingMode` 枚举顺序：**Behavior0 / Guidance1 / TargetLock2 / External3 / Count4**；
  - **没有** `SeekingMissileDeviationSettings`（本 build 才新增）⇒ 68 B 结构无公开字段名，语义只能靠实机。

## 5. 产物（均已装盘验证）

| 轮 | 产物 | sealed sha256 | 说明 |
|---|---|---|---|
| W1 | `out/wasp-dev1.dl_bin` | `7fdd447c3240aaf9` | 只 ±8° |
| W2 | `out/wasp-devfull.dl_bin` | `0d075ee2479c43bf` | 整块 = P-33 |
| R1 | `out/wasp-r1-vec.dl_bin` | `46a4f7736d48b26b` | Vec3 组 |
| R2 | `out/wasp-r2-bpitch.dl_bin` | `84e3624f1704a30b` | B 对 + 尾部 |
| R3 | `out/wasp-r3-bonly.dl_bin` | `a158914075328c08` | 只 B 对 |
| R4 | `out/wasp-r4-rates.dl_bin` | `fce5f467681d9f9b` | 尾部两格 |
| **R5（当前盘）** | `out/wasp-r5-e4.dl_bin` | `0071ea71489f46f9` | **只 `+0xE4`**（弧线保留、不打转） |

全部基于 Spear parity 盘（`+0x240=223`、`GT+0x48=8`、`+0x58=1` 保留），G1–G9 全 PASS，回读逐字节一致。

## 6. 回滚

```bash
cd /d/mod
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed D:/mod/out/parity-entities.dl_bin  # 回 parity（保留 Spear 改动）
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin                                            # 回原版
```

## 7. 未解（下一步可做，每项 1 轮单变量）

- B 对两格（`+0xC0` vs `+0xC4`）分工 —— 半径下限/上限？
- `+0xE8`（0.2 vs 0.1）作用 —— 幅度/衰减？
- `+0xE4`=0 的行为 —— 彻底关闭还是异常？
- 两个 Vec3 的含义（与打转无关）。

## 8. 方法学备注

- 每轮都是"基线控制变量（A 对 ±15）+ 单字段/单组变量"，靠实机现象判读；
- 全部编辑走 `entity_batch_set.py`（tail 宿主保哈希），装盘前后都做 unseal 回读比对；
- **锚点按 build**：`generated_entities` = `0x8E49771B181FFAA1`；`generated_projectile_settings` 在 26251122 是
  `0x113A5833529A71B5`（不是旧文档的 `0x946A4FE5FAAAE076`）。
