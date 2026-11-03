# 护甲被动 / stat 行的文件侧能力模型（build 26088801）

> **一页速查。** 详细证据与逐轮实机记录在 [ARMOR-KIT-WEIGHTS](ARMOR-KIT-WEIGHTS-26088801.md)（§1–§20）。
> 想改**三数字**（rating / speed / stamina）→ 那个文档；想改**被动与效果**（弹容 / 装填 / 抗性…）→ 本页。
> 这些「乘数层」与玩家 `AvatarComponentData` 基准字段的连接图（F 缩放体力、S 写 locomotion、Oxygenator=jog/sprint…）
> 见 [AVATAR-ARMOR-BRIDGE-26251122](../cases/AVATAR-ARMOR-BRIDGE-26251122.md)。

---

## 0 一句话

`generated_customization_passive_bonuses.dl_bin` 里每条被动有**两个变长数组**：
**`pm` 行管文案与 `armor_rating`，`sm` 行管武器类数值**。
改/加这两类行 = **整族甲生效**；再配合改 `armor_sets` 里那件甲的 **`passive` 字段** = **单件甲生效**。

---

## 1 数据结构（一张表说清）

```
容器 = u32 组数(33) + 每组 { 24 B 头 ['LDLD'][ver][type=0x63CE0FEB][payload_size][wide=1][4B] + payload }

payload = 56 B 记录头 + pm 行数组 + sm 行数组
    记录头： +0 id(u32)          ← perk 号（0..42，本 build 有 33 个块）
             +16 pm_off(u64)  +24 pm_cnt(u64)
             +32 sm_off(u64，空 = 0xFFFF_FFFF_FFFF_FFFF)  +40 sm_cnt(u64)
             +48 8 B 保留
    pm 行 16 B = { stat 键 u32, 类型 u32, 数值 f32, 描述 loc id u32 }
    sm 行 12 B = { stat 槽位 u32, 标志 u32(通常 0), 数值 f32 }
```

改完要**保住内容哈希**（Murmur64A，seed `0xDEADBEEFABAD1DEA`）：用 `plain_edit.py` / `passive_bonus_edit.py`，
它们都会「尾部追加 8 B 宿主 + 解一个校正字」，门禁里含 **哈希必须等于原版** 这一条。

---

## 2 两层作用范围（核心区别）

| 层级 | 改什么 | 谁吃到 | 判定 |
|---|---|---|---|
| **被动级** | `passive_bonuses` 里某 perk 的 pm / sm 行 | **同被动下的所有甲** | ✓✓ |
| **单件级** | `armor_sets` 里那件甲 kit 记录的 `+0x1C passive` → 指向另一条被动 | **只有那件甲** | ✓✓ |
| **单件级 + 自定义** | 上一行 + 往「目标被动」里加 pm/sm 行 | 目标甲（+ 该被动原主） | ✓✓ |

⚠ **没有真正的"空被动"可用**：`perk 0`（STANDARD ISSUE，头盔用）看着像空槽，但**引擎特判它** ——
往 perk 0 加 sm 行**完全不生效**（p9b 否证）。被动表里 33 个块**全部**被至少 1 件甲使用，也没有 4 / 22–30 的块。

**可用的"近单件"被动**（各只被 1 件甲使用）：

| perk | 甲 | 备注 |
|---|---|---|
| 35 | CPR-80 Bulwark | heavy |
| 36 | CPG-48 Sapper | medium |
| **37** | **CPH-26 Commandant** | light（p10 用它做成过） |

---

## 3 `pm` 行：只对 `armor_rating` 有效

```
RATING = 50 + 50 × ( mean(部件档位[槽位 2,4,5,6,7,8,9]) + Σ pm 行里的 armor_rating Add 值 )
```

| 事实 | 判定 |
|---|---|
| `armor_rating`（键 `0xAFAE3B47`，type 1 = Add）**可为任意 float，正负都行，多行求和** | ✓✓（150→250→125 两次实机） |
| **卡片显示层：整数、四舍五入**（151.5 → 152） | ✓✓ |
| 其余六类 pm 键（主/支援/副装填、弹容、副拔枪、副后坐）是 **`description-only`** —— **改了也不生效** | ✓✓（e15 的反面实例） |

> 六个 `description-only` 键：`CC530B21` · `35F17BEC` · `B4F88129` · `33C9C713` · `AD5289FE` · `22035F3C`。

---

## 4 `sm` 行：武器类数值全部走这里

| stat | 含义 | 实测来源 |
|---|---|---|
| **12** | **弹容（ammo capacity）** | ✓✓ p6：32 → 64 |
| **13** | **主武器装填** | ✓✓ p7 |
| **14** | **支援武器装填** | ✓✓ p7（另：2026-10-16 秒表 4.04 → 3.14 / 2.16 s） |
| **15** | 副武器装填 | 名字确定（SDK 目录），⚠ 未实机 |
| **16** | 副武器拔枪/收枪速度 | 同上 |
| **17** | 副武器后坐 | 同上 |
| **11** | 受击后坐/硬直（×0.05 ≈ −95%） | 同上（SDK 未命名，靠 wiki「reduces damage recoil by 95%」+ 数值吻合） |

**数值口径**：都是**乘数**，作用于「速度」而非「时间」。

| 规律 | 内容 |
|---|---|
| 弹容 | **`ceil(基准 × 乘数)`** —— 32 × 1.2 = 38.4 → **39**（实测） |
| 装填 | **仿射**：`t = 3.90 / mul + 0.14`（GR-8 实测）⇒ 乘数越大收益越小，下限 ≈0.14 s |
| 同 key 多行 | **求和**（1.0 + 2.0 = 3.0 → rating 250） |
| 不存在 | 往 `perk 0` 加 sm 行**不生效**（引擎特判 id 0） |

---

## 5 三条做 mod 必须记住的硬约束

| # | 约束 | 违反的后果 |
|---|---|---|
| 1 | **改表后必须重启 + spawn** | 表在启动时读入；stat 行在**出生时**由穿着的那件甲施加（`0x11DA190` → `SetStat 0xA076C0`） |
| 2 | **`pm` 只改 `armor_rating`** | 改那六个 description-only 键 ⇒ 只有文案变、效果零 |
| 3 | **写 kit 的 passive 会整条换身份** | 那件甲**失去**自己原被动、**拿到**目标被动全部效果（卡片名、rating、效果全变） |

---

## 6 已验证可用的配方

| 配方 | 命令要点 | 效果 |
|---|---|---|
| 整族加弹容/装填 | 往 perk 加 `sm{12/13/14}` | 同被动全部甲（p7：B-01 → 弹容 ×2 + 主/支援装填 ×2） |
| 整族改护甲值（可正可负） | 往 perk 的 pm 加 `armor_rating ±x` | 全部甲 rating 变化（p3 250 / p4 125） |
| **单件甲换被动** | 改 kit 记录 `+0x1C` = 目标 perk | 那一件甲整条换成目标被动（p8b：CW-9 → SIEGE-READY） |
| **单件甲 + 自定义** | 上一条 + 往目标 perk 加行 | 目标甲拿到任意效果（p10：CW-9 → perk 37 + 弹容/装填 ×2） |

---

## 7 工具

| 工具 | 用途 | 门禁 |
|---|---|---|
| `tools/passive_bonus_edit.py` | 被动表：`--show` / `--add-pm` / `--add-sm` | G1/G2/G4/G5（含哈希保持） |
| `tools/armor_kit_weight.py` | 部件档位（三数字）+ 列 kit / perk / rating | 8 道门 + `--verify-model` **135/135** |
| `tools/plain_edit.py` | 通用字节写（改 kit 的 `+0x1C` 用它） | G1–G6 |
| `tools/dlbin_seal.py` | `open-key` 解封 / `seal-material`·`seal-key` 重新封装 | 往返自检 |
| `D:\mod\tools\dlbin_deploy.py` | `status` / `install` / `restore`（装前自动备份） | 逐个 sha256 复核 |

**典型流程**：解封 → 改 → 封包 → 回封校验 → 装机 → **重启游戏进任务** → 看「卡片数字 / 弹容 / 装填」。

---

## 8 未解

| 项 | 状态 |
|---|---|
| `stat 15/16/17/11` 的实机效果 | 名字已知，未逐个实测 |
| `perk 0` 特判的确切位置 | 只知道现象（sm 不施加），未定位代码 |
| 加行后卡片文案失准 | 追加行后卡片仍写原描述；`text` 是 loc id，**可以改**但未试 |
| 指向"非单件被动"时 stat 行是否同样跟随 | p10 证明指向**非零**被动即生效，理论上同样；未逐一验 |
| 部件档位的 7 个槽均值语义之外（cape/hips 是否参与实战） | 见 [ARMOR-KIT-WEIGHTS](ARMOR-KIT-WEIGHTS-26088801.md) §2.1 双口径 |
