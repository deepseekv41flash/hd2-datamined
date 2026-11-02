# 一次性武器：丢弃开关与"能不能有备弹"（build 26251122）

> 2026-11-02 收尾支线（EAT-17 / EAT-700 / EAT-411 / MLS-4X Commando）。
> 一句话：**"打空被扔掉"由一个字段控制（`auto_drop_ability`），但"备弹"在数据表层加不出来** ——
> 换弹组件、弹匣备弹、正常开火能力三者补齐后，游戏里按 R 仍然没反应（引擎在武器 unit/动画层拒绝）。

## 0. 结论

| 问题 | 答案 | 证据 |
|---|---|---|
| 什么控制"打空被扔"？ | `WeaponDataComponentData.auto_drop_ability`（本 build 行内 `+0x1D0`） | 一次性武器 = 96 = `AbilityId_avatar_drop_latoneshot`；普通武器 = 0 = Invalid；改 0 → 打空留手（实机 ✓） |
| 一次性武器能有备弹吗？ | **数据表层：不能** | 补 `WeaponReloadComponentData`（复制 GR-8 行）+ 弹匣 `magazines=3/max=3` + 换成普通开火能力后，**按 R 无反应**（实机 ✗） |
| 能拿到什么？ | 可以做成"**打空不丢、空枪留手**" | `auto_drop_ability` 置 0 即可（其余不动） |
| 和"背包弹链武器不能有备弹"一样吗？ | 类似但更硬：背包供弹武器是"弹药在背包实体里"（弹匣行 `magazines=0`）；一次性武器是连换弹链路都没有，补上链路也被引擎拒绝 | 见 §1/§3 |

## 1. 数据对照（本 build 实体表）

| 武器 | 实体键 | `auto_drop_ability` | `WeaponReloadComponentData` | 弹匣 cap/mags/max | fire ability 值（`+0x3B4`） |
|---|---|---|---|---|---|
| EAT-17  Expendable Anti-Tank | `0x80932FA0ED6901D3` | **96** | **无** | 1 / **0** / **0** | 0xA83（lat_oneshot） |
| EAT-700 Expendable Napalm | `0xB2B5E0D185605F9E` | **96** | **无** | 1 / 0 / 0 | 0xA84 |
| EAT-411 Leveller | `0x7617642765AC38C7` | **96** | **无** | 1 / 0 / 0 | 0xA83 |
| MLS-4X Commando | `0x5990123D142B16CB` | **96** | **无** | 4 / 0 / 0 | 0xA9F |
| GR-8 Recoilless Rifle | `0x9F80D67A12A7E40F` | 0 | 有（`complex_reload_recoilless`，6 s） | 1 / 0 / 0（背包供弹） | 0xA7E |
| MG-43 | `0x11C27D3BABB38956` | 0 | 有（machinegun，4.5 s） | 175 / 2 / 3 | 0xA7C |
| APW-1 | `0x89C5493E08CA4207` | 0 | 有（sniper_rifle，3 s） | 7 / 5 / 8 | 0xA9F |
| Spear / WASP | — | 0 | 有 | 1 / 0 / 0 · 7 / 0 / 0（背包） | — |
| Quasar | `0x35A61296619CC47E` | 0 | **无**（充能武器） | 无弹匣组件 | — |
| MGX-42 Bullet Storm | （见 entity_index） | **97**（另一个丢弃类 ability） | 无 | 300 / 0 / 0 | — |

字段名依据：公开 datamine（shalzuth/HelldiversData）`WeaponDataComponent` 的 `auto_drop_ability` 字段
（EAT-17 / Commando = `AbilityId_avatar_drop_latoneshot`，其它 = `AbilityId_Invalid`）+ 本 build 四把一次性武器全 96、其它全 0 的完全对应。
其余字段（`magazines` 等）值也与公开 dump 逐项一致，说明行定位与偏移无误。

## 2. 实机链（每轮单变量）

| 轮 | 改动 | 实机结果 | 判读 |
|---|---|---|---|
| R24 | EAT-17 `auto_drop_ability` 96→0 | **打一发后发射器留在手上**（空枪） | 丢弃开关找到 → `auto_drop_ability` 控制"打空即扔" |
| 反证 | GR-8 `auto_drop_ability` 0→96，打光全部弹药 | **仍留在手上**（未丢） | 单加 ability 不生效 ⇒ 触发端与一次性武器自身绑定（推测是开火能力 `lat_oneshot`），不是通用"弹匣空"事件 |
| R26 | 给 EAT-17 补 GR-8 的 `WeaponReloadComponentData` 行 + 弹匣备弹 3（`auto_drop` 仍 96） | **打一发照旧被扔** | `auto_drop` 优先级最高，有备弹也照丢 |
| R27 | R26 + `auto_drop_ability`=0 | **留手，但按 R 没反应** | 换弹链路不完整 |
| R29 | R27 + 开火能力换成 GR-8 的（0xA83→0xA7E） | **开火正常，R 仍没反应** | 数据层三要素齐了仍被引擎拒绝 ⇒ 卡在武器 unit/动画/能力绑定层 |

## 3. 行结构与改法（供复现）

- `WeaponMagazineComponent` 行（160 B）：
  `+0x00` MagazineType、`+0x04` MagazinePattern(132 B)、**`+0x88` capacity、`+0x8C` magazines、`+0x90` magazines_refill、`+0x94` magazines_max、`+0x98` reload_threshold、`+0x9C` chambered**。
- `WeaponReloadComponent` 行（80 B）：
  `+0x00` manual_clearing、`+0x01` reload_allow_move、**`+0x04` ability(AbilityId)**、`+0x08` WeaponMagazineAnimEvent(48 B)、**`+0x38` duration**、`+0x3C` has_shared_deposit。
- **给实体新增组件**（本支线用的方法，已验证可行）：
  `python tools/entity_hashmap_insert.py --block 0x991D454E --key 0x80932FA0ED6901D3 --copy-row-from 0x9F80D67A12A7E40F --plain X.plain --out Y.plain`
  —— 往哈希图插入 `EAT-17 → 新行` 映射、整行复制 GR-8 的换弹组件（新行 254），G1–G6 全 PASS、内容哈希保持 `0x8E49771B181FFAA1`。
- `WeaponDataComponent` 行（1240 B）关键格：`+0x1D0` = auto_drop_ability、`+0x3B4` = fire ability、
  `+0xB8/+0xBC` = WeaponFunctionInfo(left/right)。

## 4. 产物（全部装盘后 unseal 回读一致）

| 产物 | sealed sha256（前 16） | 内容 |
|---|---|---|
| `out/eat17-nodrop.dl_bin` | `0d9efc402fa7e818` | EAT-17 关丢弃（打空留手） |
| `out/gr8-autodrop.dl_bin` | `e9566a4b1f79b6bc` | 反证：GR-8 加丢弃 ability |
| `out/eat17-reloadmags.dl_bin` | `8dc93468496cc857` | EAT-17 + 换弹组件 + 备弹 3（仍丢） |
| `out/eat17-nodrop-reload.dl_bin` | `4764c25cd3b44d38` | 关丢弃 + 换弹组件 + 备弹（R 无反应） |
| `out/eat17-firegr8.dl_bin` | `1193aa4369125526` | 再加正常开火能力（R 仍无反应） |

## 5. 回滚

```bash
cd /d/mod
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed D:/mod/out/wasp-r20-e4zero.dl_bin  # 回纯 Spear 高抛版（一次性武器全原版）
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin                                          # 回原版
```

## 6. 未解 / 可选下一步

1. **资源层换弹动画**：怀疑 EAT-17 的武器 unit 没有换弹动画节点（复制来的 `WeaponMagazineAnimEvent` 节点在它身上不存在）
   → 需要给 weapon unit 补 reload 动画/状态机（资源层，重）；
2. 换用 **MG-43 / APW-1 的换弹行**（先验证是不是 GR-8 行特有）——1 轮；
3. **MGX-42 `auto_drop`=97** 的语义：另一个"丢弃类"ability，可能是"打空才丢"（对比 96 的"打一发就丢"）；
4. "打空不丢"成品配方（`auto_drop_ability`=0）可单独做成 mod。
