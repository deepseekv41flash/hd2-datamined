# Helldivers 2 · 离线数据表逆向笔记与工具

> 当前验证 build **`26088801`** ｜ 历史基线 `25480438` → `25988413`
> 本仓库不绑定某个 build：**结构层**结论（密封盒、内容哈希、`LDLD`、实体块布局、本地化 ID）跨 build 有效；
> **偏移 / 地址类**结论必须逐 build 复验，所以事实类文档都带 build 号。

## 这是什么

一套**离线**的 Helldivers 2 数据表研究笔记与工具 —— **改磁盘上的数据文件**，不碰进程内存、不需要 Lua / FFI / 注入 / DLL。

核心里程碑：解密 `data/game/*.dl_bin` → 保住引擎的 MurmurHash64A 内容哈希改写字节 → 重封 → 盘上回读 → 分级实机验证 → 可回滚。
已实机覆盖：战备（冷却 / 呼叫 / 次数 / 弹幕轮数与弹数 / **Eagle 回收**）· 爆炸（伤害 / 半径 / 破片 / **外观整行克隆 + `+0xA8` 跨包加载**）· 弹头换装 · 武器数值与可选弹种 / 独立弹药池 · 实体组件块。

**→ 全部文档、能力明细与已验证结论，见 [INDEX.md](INDEX.md)（唯一索引入口）。**

## 不是什么

- **不包含任何游戏资产、密钥或密钥材料**。`tables/` 只有三张很小的参数表（合计 ~180 KB），用于验证解析器。
- 不提供"解除封锁 / 解锁付费内容 / 破坏他人游戏"的方法。已证否的路线也如实写「否证」。
- **不提供在游戏进程内加载未签名 DLL 的方法** —— 不是没写，是实测走不通：加载器只映射它自己带的映像，
  未签名 `577`、签名但不在名单 `193`、自签并装进 `LocalMachine\Root` 仍然 `577`
  （[MEMORY-ACCESS §12](docs/boundaries/MEMORY-ACCESS-25988413.md)）。要绕开只能动反作弊本身，不做。
- 不是通用 mod 管理器；mod 打包 / 安装请用社区工具。

## 三十秒上手

核心工具**纯 Python 3.11+，无第三方依赖**（少数可选工具需要 PyNaCl / Pillow / lupa / `srkit`，见 [INDEX §3 工具清单](INDEX.md#3-工具清单tools)）。

```bash
# 0) 当前 build 的示例：战备表「额外战备 +0xC8」——未发布战备进任务的入口
python examples/stratagem_extra_demo.py --verify

# 1) 解析一张表（用仓库自带明文，不需要游戏、不需要密钥）
python examples/parse_examples.py --projectile tables/generated_projectile_settings.dl_bin

# 2) 算一个文件的 Murmur64A —— 就是引擎用来校验内容哈希的那个
python tools/murmur64.py <file>

# 3) 改一张表并过全部门禁（同样不需要密钥，练的是绝对偏移 / 值语法 / tail 宿主）
python tools/plain_edit.py --plain tables/generated_projectile_settings.dl_bin \
    --set 0x<偏移>=u32:123 --out /tmp/out.plain.dl_bin
```

**要动自己机器上的游戏文件** → 从 [改盘上数据的完整工作流](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) 入手（8 步链 + 锚点哈希 + 93 条坑）。
**要让代理自动做** → 用技能 [skills/hd2-file-route-mod](skills/hd2-file-route-mod/SKILL.md)（只给方法论，知识一律指回本仓库）。
**案例在哪** → [`docs/cases/`](docs/cases)（25 篇）· 战备/未发布内容在 [`docs/tables/`](docs/tables) · 总入口 [INDEX](INDEX.md)。

> **两条前置，动手之前必须确认**：
> ① **密钥** —— `recipient.pk` / `recipient.sk` 不随仓库提供，但**可以自己解出来**：一份旧 build 的全量内存转储 + [DLBIN-SEALED-BOX §10](docs/engine/DLBIN-SEALED-BOX.md) 的 RVA / XOR 常数 / seek 工具 / 三重验证。
> ② **原版判定** —— 「明文哈希 == 锚点」**识别不出**保哈希的 mod，判原版要靠封包字节数或装前备份（[WORKFLOW §2.5](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md)）。

## 仓库结构

```
INDEX.md   ★ 唯一索引入口：按问题找 / 按类型浏览 / 能力明细 / 已验证结论
BUILDS.md  换 build 的操作手册：三步 / 判读规则 / 锚点复验 / 基线存放（记录在 INDEX §2 builds/）
docs/      65 篇文档（INDEX 按类收录 64 篇 + 目录说明；案例全在 cases/）
tools/     离线工具链（解析 / 改字节 / 保哈希 / 行级编辑 + 门禁）
tables/    三张很小的明文参数表，供离线验证解析器
refs/      字段图与索引：表几何 / 行名 / 本地化名 / 弹头引用链 / 组件块类型名
examples/  可直接运行的示例（纯标准库）+ 案例指路
skills/    代理技能 hd2-file-route-mod —— 只写方法论，知识全在 docs/
```

## 相关仓库

- **[hd2-srkit](https://github.com/deepseekv41flash/hd2-srkit)** —— Stingray/HD2 资源解包打包工具（资源层：toc/bundle/DSAR、unit/texture/material/lua）。本仓库的 `tools/` 是**数据表**层面的实验脚本，两者互补。
  > 它**不**包含运行期内存改写与 Lua addon 构建管线 —— 那些在 build 25988413 已不可用（Lua 无 `ffi` + EAC 拒绝外部读内存），不发布以免误导。

## 免责声明

- 仅供**单人 / 私人环境**的研究与学习。改动数据文件可能违反游戏服务条款，也可能导致崩溃、存档异常或联机异常。
- **不要**在多人游戏中使用会改变他人体验的改动；不要分发改过的游戏数据。
- 所有结论标注三态：`✓ 实机` / `✓ 离线` / `✗ 否证` / `⚠ 未证`。游戏更新后偏移与哈希会整体失效，本仓库不保证跨版本。
- 改动前请自行备份 `data/game/`。链接自检：`python tools/check_links.py`（0 断链才算过）。

## 许可证

[MIT License](LICENSE) —— 代码、文档、索引一并用 MIT。
