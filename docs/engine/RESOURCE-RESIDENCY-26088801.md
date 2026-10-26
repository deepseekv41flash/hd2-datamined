# 资源层驻留（`.patch_N`）— build 26088801

> **一句话**：**声明口管「包在不在」，补丁管「资源在不在」。**
> 声明口（`+0xA8` / `+0xF8`）只有一百多个、还带「行不在普通任务栏就读不到」的死结；
> 而 `data/<宿主包>.patch_N` 把**资源**塞进**已经常驻**的包、按 `file_id` 全局可查 —— **不受口数限制**。
>
> 本文是这条路线的主档。声明口那条线（`+0xA8` / `+0xF8` / `+0xC8`、教学关行 138 陷阱、包解析链）
> 在 [LIMITED-CROSS-PACKAGE-LOADING](LIMITED-CROSS-PACKAGE-LOADING-26088801.md)，两者的分工见 §1。

**三态约定**：`✓` 离线可复核 · `✓✓` 实机验过 · `✗` 否证 · `⚠` 未证/未测

---

## 1 两条路线怎么分工（别混）

| | **声明路线**（[限跨包](LIMITED-CROSS-PACKAGE-LOADING-26088801.md)） | **补丁路线**（本文） |
|---|---|---|
| 改什么 | 战备行的 `+0xA8` / `+0xF8` / `+0xC8` | `data/<宿主包>.patch_N` 里的资源条目 |
| 解决什么 | **包会不会被加载** | **资源在不在**（能不能被解析） |
| 上限 | 155 个空口，且行必须真的会被读 | 条目数 51 / toc 3.5 MB 已通，上限未撞到 |
| 代价 | 抢占战备行的口 | 补丁体积 + **真加载**进内存 |
| 典型用法 | 让一台载具/一个哨戒的包进来 | 卸载声明口：把包整包搬进常驻包 |

**两者可以叠加并已实测**：投送舱三件 rig（`✓✓`）里 Nova 走舱行 `+0xA8`、Warp 与 GL-28 各走一个整包补丁，
同一舱三件全出、战备表里对后两件一个字都没写。

---

## 2 机制（`✓` + `✓✓`）

| 事实 | 状态 | 证据 |
|---|---|---|
| 文件名 `data/<宿主包>.patch_N`，引擎启动时**按连续序号**合并进**那一个包** | `✓✓` | 缺号时后面的补丁整体不生效（早期踩过）|
| 条目按 `file_id` 进**全局**资源索引（62,915 个 id ↔ 322,711 条条目）；任一**已加载**包里有的 id 都能解析 | `✓✓` | P1–P4 |
| **类型不挑**：`lua` / `texture` / `bones` / `physics` / `particles` / `material` / `state_machine` / `unit`… | `✓✓` | 见 §3 表 |
| 带 GPU / stream 负载的类型（`texture`、`unit`、`geometry_group`…）必须配套同名 `.gpu_resources` / `.stream` | `✓✓` | 缺了就是白模/紫问号 |
| 同 id 冲突**高号胜** | `✓✓` | [SAMEID-PATCH-PRIORITY](../cases/SAMEID-PATCH-PRIORITY-26088801.md) |
| 宿主**不限于**注册表包 `9ba626afa44a3aa3`：`data/<任意包>.patch_N` 都会被读 | `✓✓` | P2/P4（共享基础包 `f6fb08cc02d24255`）|
| 一个宿主包可以有多条补丁（各自序号连续） | `✓✓` | `f6fb08cc02d24255.patch_0`（Warp）+ `patch_1`（火箭哨戒）|
| 同一宿主包内**同 id 两处**：**高号胜**（可用来"只覆盖一个资源"）| `✓✓` 实机 | `f6fb08cc02d24255.patch_1` 整包含 unit 原件、`patch_2` 单条 unit 带 +2 m 位移 |

---

## 3 实测案例（每轮单变量）

| 轮 | 补丁 | 宿主包 | 条目 | 读数 |
|---|---|---|---:|---|
| **P1 资源级** | `9ba626afa44a3aa3.patch_5`（82,864 B）| 注册表包 | 19（3 `particles` + 16 `material`，79.3 KB）| 把 `SOS` 59 的 `+0xA8` **清零**后，火箭炮塔的**拖尾 / 命中爆炸 / 枪口全在** ⇒ 68 MB 的包被 79 KB 资源顶掉 `✓✓` |
| **P2 整包·基础包** | `f6fb08cc02d24255.patch_0`（3.52 MB toc + 1.84 MB gpu + 2.65 MB stream）| 共享基础包 `f6fb08cc02d24255`（782 资源，必然常驻）| 50（LIFT-182 Warp Pack 整包）| 舱里 **Warp Pack 正常渲染**，零 `+0xA8` `✓✓` |
| **P3 整包·注册表包** | `9ba626afa44a3aa3.patch_6`（2.74 MB + 6.06 MB + 4.19 MB）| 注册表包 | 51（GL-28 Belt-Fed 整包）| 舱里 **GL-28 正常渲染**，零声明 `✓✓` |
| **P4 整包·基础包·挂载件** | `f6fb08cc02d24255.patch_1`（1.26 MB toc + 4.37 MB gpu + 2.29 MB stream）| 共享基础包（第 2 条）| 41（火箭哨戒包 `11bbdf8ce39e5fc5` 整包：11 animation / 9 texture / 9 particles / 6 material / 1 bones / 1 **unit** / 1 physics / 1 state_machine / 2 wwise）| **✓✓ 实机**：M-102 炮手位挂载**火箭哨戒**，战备表 `+0xA8` **全清零**（增援 57 与 `SOS` 59 都回 0）⇒ 模型 / 材质 / 贴图 / 动画**全部正常**（不是紫问号、不是白模），**零声明**完全成立 |

**验收 rig（P2/P3，`✓✓` 三件全出）**：StA-X3 投送舱（rack 29）三件、`spawn=3` ——
Nova 走舱行 `+0xA8`（基准）、Warp 走共享基础包补丁、GL-28 走注册表包补丁。

> P4 的实机也顺手暴露了一个**与驻留无关**的问题：火箭哨戒在炮手位"是展开的、但整体缩在车体里"——
> 那是壳的 `elevator_01/02` 升降骨骼没被抬起来（部署 clip 才抬），不是资源没加载。
> 判据与后续改法见 [SENTRY-TURRET-FIELDS §3.8.4.4](../tables/SENTRY-TURRET-FIELDS-26088801.md)。

**P4 新补的三件事**（此前三轮都没覆盖）：

1. **第一次用于「载具挂载件」**，不是投送舱 rack 物品 —— 挂载路径（`MountInfo.item`）
   同样只按 `file_id` 取资源，不需要包被"请求"；
2. **同一条补丁里可以既放整包拷贝、又放自己改过的资源**：`srkit unpack --raw` 出工作区 →
   改 `resources/<type>_<id>/toc.bin`、**同步改同目录 `resource.json` 的 `size`/`sha256`** → `srkit pack`。
   P4 就是这样把 `state_machine 37079568DC86E9C6` 的 `layer0.DefaultState` 改成 3 带进去的
   （`resource_patch.py dump <patch> 14` 出来 4,364 B，与 `sm_rocket.bin` 逐字节相同）；
3. **`+0xA8` 清零后依然出模型** —— P1 的「零声明」结论在「整包 + 挂载」上复现。

**一条旧判断的修正**：`content/fac_helldivers/hellpod/aa_turret`（AC-8 壳）的
`bones / physics / state_machine / unit` **在 `54dc633a67baa93d` 与 `418322d5ff8b13bc` 里各有一整套**
（`srkit list --id 0xCBFE1FC7158347F3` 共 8 条，两个包各 4 条、尺寸逐项相同），
所以当初"AC-8 必须声明两个包"是**保守做法，一个就够**。
（曾误判为"两套壳都没有 `unit` 资源"，那是 `srkit` 类型名显示 bug，见 §8。）

---

## 4 三条配方

```bash
# A) 资源级：几个 (type,id,payload) 进注册表包
#    以现有补丁为模板解析 → 清条目 → add_entry → to_bytes（别新建容器，会丢头里 56 B 元数据）
python tools/resource_patch.py build spec.json -o out --index 5
#    spec.json: [{"type":"A486D4045106165C","id":"0x3707...","file":"sm.bin","gpu":null,"stream":null}]

# B) 整包：解→打
python -m srkit unpack "<game>/data" -o ws --package <源包> --raw
python -m srkit pack   ws -o out --name <宿主包>.patch_<N>

# C) 整包 + 顺手改资源（本文的推荐路径，一条命令、带门禁）
python tools/whole_package_patch.py build \
    --package 11bbdf8ce39e5fc5 --host f6fb08cc02d24255 \
    --edit state_machine:0x37079568DC86E9C6=sm_rocket.bin \
    --out D:/mod/out/rocket-res-patch
```

资源级写入器**回归**：`resource_patch.py repack` 要打 `IDENTICAL`（它证明"解析→重写"不丢字节）。

---

## 5 工具：`whole_package_patch.py`

`tools/whole_package_patch.py`（依赖 `srkit` + 同目录 `resource_patch.py`）：

| 子命令 | 作用 |
|---|---|
| `list --package <id>` | 只列包内资源（类型直方图 + toc/gpu/stream 总量），不解包 |
| `build --package <id> --host <包> [--index N] [--edit TYPE:ID=FILE]...` | 解包 → 改资源（含 `resource.json` 同步）→ 打包 → 复核；序号默认自动取下一个连续值 |
| `check <patch> [--edit ...]` | 复核成品：条目/类型/伴生文件，可选核对改过的载荷是否逐字节相同 |

门禁：**G1** 源包可列且非空 · **G2** `--edit` 的资源在工作区找得到 · **G3** 补丁可解析且条目数 == 源包 ·
**G4** 改过的载荷 dump 回来逐字节相等 · **G5** 伴生文件该有就有 · **G6** 序号连续 ·
**G7** sha256 · **G8** `resource.json` 的 size/sha 与写入一致。

**复现证明**（`✓`）：用它重跑 P4 那条补丁，三件产物与盘上**逐字节相同**
（toc `a3f71af78d333f02` / gpu `9c63665fe8e4c6eb` / stream `56e9e6715ec76329`），耗时约 5 s。

---

## 6 上限与代价

| 项 | 现状 |
|---|---|
| 补丁体积 | toc 1.26 / 2.74 / 3.52 MB 已通（含 gpu 6 MB、stream 4 MB 级伴生）；**上限未测** |
| 条目数 | 50 / 51 / 41 条已通；资源级 19 条 |
| 序号 | **每个宿主包各自连续**（0…N），中间缺号后面全部不生效 |
| 同 id 冲突 | **高号胜**；同一 id 出现在两条补丁里时内容必须一致，否则"谁胜"没有保证（`⚠`）|
| 内存 | 驻留 = **真加载**；200 MB 级特效包会明显掉帧（旧档）|
| 启动耗时 | `⚠` 未测（整包越多、启动越慢，没有量化）|

---

## 7 能力边界

**补丁只解决"资源在不在"，不解决"包在不在"** —— 要让引擎**主动请求**某个包，仍然只有
`+0xA8` / `+0xF8` 两条声明口。区别在于：**被直接引用的资源（挂载件、rack 物品、粒子/材质引用）
不需要包被请求**，只要 id 能解析就行；而"某个系统按包名/包 id 去加载一包东西"的路径，
没有声明口就不会发生。

---

## 8 坑清单

1. **实体库不是普通 LDLD**：实体 `u32 type | 'LDLD' | ver | type | payload | …`（头 28 B、尺寸在 `head+16`），
   普通表 `'LDLD' | ver | type | payload | wide | extra`（头 24 B、尺寸在 `head+12`）。
   `plain_edit.py` 只能改后者；实体表用 `rack_edit.py` / `entity_field_set.py` / `mount_table.py`。
2. **`srkit` 类型名显示 bug**（`✓` 已核）：`0xE0A48D0BE9A7453F` 常量名是 `TYPE_UNIT`，
   但 `srkit/util/ids.py` 的 `TYPE_NAMES[TYPE_UNIT] = "mesh"` ⇒ `srkit list` 把 **`unit` 显示成 `mesh`**。
   `resource_patch.py` 的映射是对的（显示 `unit`）。
   ⇒ 按名字过滤会拿错类型；**按 type id 过滤最稳**（`--type 0xE0A48D0BE9A7453F`）。
   副作用：以前"整包里没有 unit"的判断是被这个显示名骗的（见 §3 末）。
3. **伴生文件**：`texture` / `unit` / `geometry_group` 这类带 GPU/stream 的资源，缺 `.gpu_resources`
   / `.stream` 就是白模或紫问号。
4. **补丁序号必须连续**，且是**按宿主包**计数的（`9ba626…patch_0..8` 与 `f6fb08…patch_0..1` 互不影响）。
5. **整包 = 真加载**：把 200 MB 级的敌人/特效包整包常驻会掉帧。
6. **改工作区里的资源一定要同步 `resource.json` 的 sha**，否则打包出去的东西自述与实际不符
   （`whole_package_patch.py` 的 G8 就是防这个）。

---

## 9 还没做（`⚠`）

1. 补丁**体积上限**与**条目上限**（现在最大 3.52 MB toc / 51 条）；
2. **启动耗时**与**内存峰值**的量化；
3. 能不能让引擎把补丁里的资源当成"包"来请求（目前 `✗`：只能让 id 可解析）；
4. P4 的实机读数（火箭哨戒在 FRV 炮手位是否出场即展开、材质是否正常、150 s 是否自消失）。

---

## 10 相关

- [LIMITED-CROSS-PACKAGE-LOADING](LIMITED-CROSS-PACKAGE-LOADING-26088801.md) —— 声明口那条线（`+0xA8` / `+0xF8` / `+0xC8`）
- [POD-RACK](../tables/POD-RACK-26088801.md) —— 投送舱 rack 与物品解析
- [SENTRY-TURRET-FIELDS](../tables/SENTRY-TURRET-FIELDS-26088801.md) §3.8.4 —— P4 用的挂载配方与状态机修正
- [FILE-ROUTE-WORKFLOW](../cases/FILE-ROUTE-WORKFLOW-26088801.md) —— 数据表路线（与资源内容互补）
- [SAMEID-PATCH-PRIORITY](../cases/SAMEID-PATCH-PRIORITY-26088801.md) —— 同 id 高号胜
