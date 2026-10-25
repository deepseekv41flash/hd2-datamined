# examples/ —— 可直接运行的示例

> **这里只放「能直接跑」的最小示例**（纯标准库，不需要游戏、不需要密钥），用的是仓库自带的
> [`tables/`](../tables) 明文表。
>
> **完整案例不在这里** —— 案例在 [`docs/cases/`](../docs/cases)（25 篇，文件名带 build 号）和
> [`docs/tables/`](../docs/tables)、[`docs/explosions/`](../docs/explosions)；
> 总入口永远是 [`INDEX.md`](../INDEX.md)。本目录 2026-10-25 重新整理过一次
> （原来只有 3 个 25988413 时代的老示例，没有指路）。

## 跑一下

```bash
# ① 当前 build（26088801）：战备表「额外战备 +0xC8」—— 未发布战备进任务的入口
python examples/stratagem_extra_demo.py            # 打印 153 行里带「额外 / 未发布」的那些
python examples/stratagem_extra_demo.py --verify   # 自检（行数 / M-104 / Eagle 的 +0xC8 / 7 条已验证 id）

# ② 基础解析（25988413 时代写的最小示例，表结构跨 build 不变）
python examples/parse_examples.py --projectile tables/generated_projectile_settings.dl_bin
python examples/parse_examples.py --blocks     <entities 明文>      # 实体表仓库未附带
python examples/parse_examples.py --slots      <entities 明文> 0x193CCE8

# ③ 真改字节 + 保哈希（不用写代码，用工具）
python tools/plain_edit.py --plain tables/generated_projectile_settings.dl_bin \
    --set 0x<偏移>=u32:123 --out /tmp/out.plain
```

## 文件

| 文件 | 说明 | 时代 |
|---|---|---|
| **`stratagem_extra_demo.py`** | **战备表 `+0xC8` 额外战备**：块/行解析、内部名解码、未发布候选列表、自检 | **`26088801`** |
| `parse_examples.py` | 弹丸行 / 块布局 / 组件槽的最小解析（示意图，注释带 `[实测]`/`[推断]`） | `25988413` |
| `entity_fields.py` | 实体组件字段的最小读法 | `25988413`（现用 [`tools/entity_field_set.py`](../tools/entity_field_set.py)） |
| `WEAPONDATA-FIELDS.md` | 武器数据组件字段图（示意） | `25988413`（当前字段表见 [`docs/tables/`](../docs/tables)） |

## 想看案例？按这个顺序

| 你想… | 去哪 |
|---|---|
| 把**未发布战备**带进任务 | [UNRELEASED-STRATAGEMS](../docs/tables/UNRELEASED-STRATAGEMS-26088801.md)（名单 + 4+4 配方 + 五条约束） |
| 看这条路线怎么被逆向出来的 | [RECON-SHODAN-EXTRA-STRATAGEM](../docs/cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md) |
| 给 P-11 加自愈（状态爆） | [STATUS-EFFECTS §7](../docs/tables/STATUS-EFFECTS-26088801.md) |
| 改自己机器上的游戏文件 | [FILE-ROUTE-WORKFLOW](../docs/cases/FILE-ROUTE-WORKFLOW-26088801.md)（8 步链 + 93 条坑） |
| 看全部 64 篇文档 | [INDEX](../INDEX.md) |
