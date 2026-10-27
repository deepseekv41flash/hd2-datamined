import sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"D:/mod/work/repo-datamined/docs/tables/CHARGE-WEAPONS-26088801.md"
s = open(p, encoding="utf-8").read()

a = s.index("## 6.6 安全模式（Railgun 安全 / 不安全）")
b = s.index("---\n\n## 7 三态")
repl = """## 6.6 射击模式 / 安全模式 / 加模式 —— **已拆到独立一篇**

射击模式那部分（模式槽、选择键、`FireMode` 枚举反查表、Railgun 安全模式、给 APW-1 加全自动、
Volley / Total 实验、射速三档）已经长到可以独立成篇，移到
[**WEAPON-FIRE-MODES**](WEAPON-FIRE-MODES-26088801.md)。

一句话摘要：**模式 = `WeaponDataComponentData +0x90…0x9C` 里的 `FireMode` 值**
（`1` 自动 / `2` 半自动 / `3` 连发 / `4` 齐射 / `5` 安全 / `6` 不安全 / `7` 全射，**槽位上限 3**），
**能否切换**看 `function_info` 是否绑了 `Firemode(3)`（`+0xB8` 左 / `+0xBC` 右）。
本页只保留**蓄力相关**（`ChargeStateSetting` / 过蓄倍率 / 过蓄自毁爆炸）。

"""
s = s[:a] + repl + s[b:]

# 三态里那几条射击模式的条目移走，只留蓄力
old_tri_start = "| Railgun「恒定安全」= 删掉第二模式槽（`+0x94` 6→0） | **✓ 实机**（run 3：面板只剩「安全」） |"
if old_tri_start in s:
    s = s.replace(old_tri_start + "\n", "")
for frag in (
    "| 模式槽 + 选择键 = 可给任意武器加射击模式 | **✓ 实机**（run 4：APW-1 能在半自动/全自动之间切并连续开火） |\n",
    "| 射速切换 = `ProjectileWeapon +4/+8/+12` 三档 rpm + `function_info` 写 `ROF(2)` | **✓ 离线**（MG-43/M-105/MG-206 三者 rpm 三档与右侧选择键） |\n",
    "| `FireMode 4` = Volley | **✓ 离线**（SG-88 wiki「Semi • Volley」↔ 数据 `[2,4]`） |\n",
    "| `FireMode 7` = Total | **✓ 离线**（VG-70 wiki 三模式 ↔ `[1,4,7]` 排除法） |\n",
    "| `FireMode 6` = Unsafe | **⚠ 强推断**（Epoch `[6,6]` 能过蓄 + Railgun `[5,6]`） |\n",
    "| 给 AR-23 加**第四档**模式（`+0x9C` = 4） | **✗ 实机**：面板仍只有三档，第四档不显示 |\n",
    "| 引擎是否允许 4 个模式槽 | **✗ 否证**（run 5：第四槽不显示；SDK 的 `maxModes: 4` 不成立，实际上限 **3**） |\n",
    "| 值 `4` 能否被非多管武器接受 | **✓ 实机**（run 6：AR-23 能加能切） |\n",
    "| `FireMode 4` = **齐射 / Volley** | **✓ 实机**（run 6：游戏内就显示「齐射」；SDK 的 `Safety_Off` 命名 ✗ 错） |\n",
    "| 齐射\"打几发\"由枪管数决定，且枪管数不在数据表里 | **✓ 实机 + 离线**（单管 AR-23 = 1 发） |\n",
    "| `Total(7)` 能否给任意武器加、是否真倾泻弹匣 | **⚠ 待 run 7** |\n",
):
    s = s.replace(frag, "")
s = s.replace("| 射击模式那套见 §6.6",
              "| 射击模式那套见 [WEAPON-FIRE-MODES](WEAPON-FIRE-MODES-26088801.md)")

# 下一步：把射击模式的条目指向新篇
a2 = s.index("## 8 下一步")
b2 = s.index("## 10 锁定")
new_next = """## 8 下一步

1. ~~收 run 1（ARC-3 时间）~~ → **✓ 已收**。
2. ~~收 run 2（Railgun 过蓄不自伤）~~ → **✓ 已收**（爆闪照旧、不掉血）。
3. 把短蓄力推广：Accelerator `0.50`、Railgun `0.50`、Epoch `2.50` → 0.05。
4. 倍率区单独验：**Railgun `DamageOver` 2.5 → 5.0**，看蓄满伤害是否翻倍（同时验证"线性插值"）。
5. `Min.ProjType` 路线：给 ARC-3 的 Min 档填一个合法电弧弹丸类型，看能否提早开火。
6. **射击模式的所有后续**（加全自动 / 齐射 / 全射、射速切换、安全模式）见
   [WEAPON-FIRE-MODES](WEAPON-FIRE-MODES-26088801.md) §5–§6。

"""
s = s[:a2] + new_next + s[b2:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("charge doc trimmed")
