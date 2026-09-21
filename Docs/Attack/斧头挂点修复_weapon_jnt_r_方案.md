# 斧头（战斧）挂点修复方案 —— 为什么要换成 `weapon_jnt_r`

> 2026-09-21 · 回答「RTG_LOL_To_Darius 已经能用了，斧头怎么办」。

---

## ⚠️ 勘误（2026-09-21 23:45 —— 实测推翻了下文对锚点的选择）

**正确锚点是 `weapon_jnt_l`，不是 `weapon_jnt_r`。**

证据（`Scripts/anim/wp_45_lateral_verdict.py`，idle 静止帧做髋轴投影）：

| 骨 | 髋轴投影 | 解剖侧 |
| :--- | ---: | :--- |
| 源 `R_Hand` | **+48.4** | 右（自证项） |
| 源 `L_Hand` | −52.4 | 左 |
| 源 `Weapon` | **+41.0** | **右** ← 斧头在右手 |
| 目标 `hand_r` | **−51.3** | 左 |
| 目标 `hand_l` | **+45.3** | **右** ← 才是持斧手 |

两条独立目标动画（`LOL_Retarget_Test/A_Darius_idle1`、`Anims/A_Darius_Idle_Layered`）结论一致；
且源/目标数值一一吻合（48.4↔45.3、−52.4↔−51.3）。

⇒ **`SK_Darius_GodKing` 的 l/r 命名与解剖左右相反**：`hand_l` 才是解剖右手；
   而源 `R_Hand`（持斧手）对应的正是它（RTG mirror 映射下 `Target[LeftArm] ← Source[RightArm]`）。
⇒ **当前斧头挂在 `hand_rSocket`（父 = `hand_r`）⇒ 一直挂在解剖左手上，与源相反。**

**下文 §1~§7 中所有 `weapon_jnt_r` 请读作 `weapon_jnt_l`**，修复流程与门禁不变。
已执行的改动：`IK_Darius` 的 `Weapon` 链已改为 `weapon_jnt_l`（备份 `Saved/Attack/backup_20260921_234112/`）。

---

---

## 1. 根因：一直挂错了骨

目标骨架 `SK_Darius_GodKing` 自带**三个**武器锚点骨（2XKO 原设计）：

| 锚点骨 | 父级 | 设计用途 |
| :--- | :--- | :--- |
| `weapon_jnt` | **`root`** | 「插地 / 脱手」位 —— 实测在脚下 `(−2, −4, 3) cm`，离 `hand_r` **108 cm** |
| `weapon_jnt_r` | **`hand_r`** | **右手武器挂点** |
| `weapon_jnt_l` | **`hand_l`** | 左手武器挂点 |

而源骨架 `SK_LOL_Darius` 的武器骨层级是：

```
Axe_Head  <  Weapon  <  R_Hand          ← Weapon 的父级是 R_Hand
```

⇒ 与源**同构**的挂点是 **`weapon_jnt_r`**，不是 `weapon_jnt`。

但 `Scripts/retarget/clean_weapon_chains.py` 把目标 Weapon 链建在了 `weapon_jnt` 上：

```python
c_tgt.add_retarget_chain(unreal.Name("Weapon"), unreal.Name("weapon_jnt"),
                         unreal.Name("weapon_jnt"), unreal.Name("None"))
```

**两侧层级不对称**（源挂 `R_Hand`、目标挂 `root`）⇒ FK 重定向写出的局部变换被当作
「相对 `root`」解释 ⇒ 产物里 `weapon_jnt` 轨道**全程恒定、钉死在脚下**。

---

## 2. 证据

| # | 证据 | 出处 |
| :--- | :--- | :--- |
| 1 | `weapon_jnt` 父 = `root`、`weapon_jnt_r` 父 = `hand_r`、`weapon_jnt_l` 父 = `hand_l` | `AGENTS.md`；`Saved/Attack/recon.txt` |
| 2 | 源真实层级 `Axe_Head ← Weapon ← R_Hand` | `Docs/Retarget/复用LoL上半身_复盘与做法.md §4.3` |
| 3 | RTG 链映射 `"Weapon": "Weapon"`，而目标 Weapon 链 = `weapon_jnt` | `Saved/Attack/rtg_snapshot.json`、`clean_weapon_chains.py` |
| 4 | 全部重定向产物的 `weapon_jnt` 局部平移行程 = **0.000**（冻结） | `Saved/Attack/weapon_track_audit.json` |
| 5 | 斧头相对右手的位姿**是动画数据**：46 条源片段里 17 条刚性 / **29 条有漂移**（attack1 相对手转 82°、spell4_5 140°、death 脱手 404 cm） | `rtg_30_weapon_scan.py` |

---

## 3. 为什么现在「看起来还行」

斧头几何当前挂在 **`hand_rSocket`**（`hand_r` 上的 socket）—— 一个**刚性**挂点。
它 100% 跟手，但**握法是常量**：

| 片段类型 | 条数 | socket 方案 |
| :--- | ---: | :--- |
| 移动类（idle / walk / run / turn） | 17 | ✅ 无损（源里握法本来就恒定） |
| 攻击 / 技能 / 嘲讽 / 死亡 等 | 29 | ❌ **斧头被焊死在固定握法上，挥砍会发僵** |

所以「迁移的表现力尚可」是对的 —— 但目前只覆盖了 17/46。「所有动作正常显示」必须让握法变成数据。

---

## 4. 修复（5 步）

### Step 1 · 把 Weapon 链的落点改成 `weapon_jnt_r`
脚本：`Scripts/anim/wp_41_repoint_weapon_chain.py`（默认 dry-run，带备份 + 幂等 + 自检）

- 只改 `IK_Darius` 里 Weapon 链的 start/end 骨；**链名不变** ⇒ RTG 的 `Weapon ← Weapon` 映射不用动。
- 不动骨架层级 ⇒ **100× / socket 契约与布料、物理全部不受影响**。

### Step 2 · 对齐 `weapon_jnt_r` 的 retarget pose
⚠️ `weapon_jnt_r` 是**单骨链**（start = end），`Direction` / `CHAIN_TO_CHAIN` 自动对齐
**从原理上定不出方向**（和当初 `hand_l` / `foot_l` 翻车是同一个坑）。
必须在 RTG 里对这条链单独做 `Align Selected`（依次试 Mesh → Local Rotation Axes → Global Rotation Axes），
不理想就在视口里手转，然后 `Set Current Pose as Retarget Pose`。

### Step 3 · 重跑重定向 + 必备后处理

```bash
cd E:/UE/Fight/Scripts
echo mirror > E:/UE/Fight/Saved/Attack/rtg_fix_mode.txt
uv run --no-project python ue_remote.py retarget/rtg_20_fix_verify.py
uv run --no-project python ue_remote.py retarget/rtg_41_fix_outer_scale.py   # 删最外层骨假 scale 轨，必跑
```

### Step 4 · 复验（只读）
```bash
uv run --no-project python ue_remote.py anim/wp_40_weapon_anchor_recon.py
```
判据（脚本会自动对比源）：
- `weapon_jnt_r` 的局部平移行程 **> 0**（不再冻结）
- `A_Darius_idle1` 里 `weapon_jnt_r ↔ hand_r` 的距离 ≈ 源 `Weapon ↔ R_Hand` 的距离 × 骨架尺度
- `weapon_jnt ↔ hand_r` 若仍是 ~108 cm 属正常（那个锚点退役，只在需要「脱手」时用）

### Step 5 · 斧头几何改挂
`BP_DariusCharacter → Components → CharacterMesh0 → WeaponAxe → Details`：

| 项 | 改前 | 改后 |
| :--- | :--- | :--- |
| Parent Socket | `hand_rSocket` | **`weapon_jnt_r`** |
| Relative Location / Rotation | 旧值 | `Saved/Attack/weapon_migrate_offset.json` → `PROPOSED_weapon_jnt_rel` |
| Relative Scale | **0.01** | **0.01**（红线，抵消最外层 100×） |

> 那套 PROPOSED 值本来就是按 `weapon_jnt_r` 的局部量推出来的（`wp_12_set_rel_v2.py`），所以正好对得上。
> ⚠️ Parent Socket 没有 Python API，只能手点。

---

## 5. 备选方案：离线烘焙（不依赖 RTG 的 pose 对齐）

如果 Step 2 的手动对齐又搞不定，可绕开 RTG 的 Weapon 链，改为**重定向产物落盘后加一道烘焙**：

逐帧用源动画反算握持关系，再以目标 `hand_r` 为基准写成 `weapon_jnt_r` 的局部轨：

```
L_grip(t)   = W_R_Hand_src(t)⁻¹ ∘ W_Weapon_src(t)          # 源：斧头在右手系里的位姿（含握法变化）
M_hand      = W_hand_r_tgt(t₀)⁻¹ ∘ W_R_Hand_src(t₀)         # 手系对齐常量（取参考帧 t₀）
L_jnt(t)    = M_hand ∘ L_grip(t)                            # 目标 weapon_jnt_r 的局部轨
```

推导的一个漂亮副产品：只要按上式烘焙，斧头组件的相对变换就退化成**单位阵 + scale 0.01**
（因为 `weapon_jnt_r` 本身就携带了斧头的正确世界位姿）。

- ✅ 全脚本、可回归、不依赖任何手工姿态对齐
- ⚠️ 需要维护「源帧 ↔ 目标帧」一一对应（重定向产物帧数已与源逐一相等，满足）
- ⚠️ `M_hand` 取参考帧，需先验证 `W_hand_r_tgt(t)⁻¹ ∘ W_R_Hand_src(t)` 在多帧上是否稳定

---

## 6. 门禁

| 脚本 | 作用 |
| :--- | :--- |
| `Scripts/anim/wp_40_weapon_anchor_recon.py` | 只读裁决：父级 / 链定义 / 产物 travel / 锚点↔手世界距离（目标 vs 源） |
| `Scripts/anim/wp_20_weapon_audit.py` | 武器契约一键门禁：动画轨 + 装配（scale=0.01）+ 几何 + 骨架 |
| `Scripts/retarget/rtg_41_fix_outer_scale.py` | 重定向后必跑：删最外层骨假 scale 轨 |
| `Scripts/anim/wp_09_check_weapon_tracks.py` | 逐条动画的 `weapon_jnt` 轨道 & 局部平移行程 |

---

## 7. 一句话总结

> **把武器锚点从 `weapon_jnt`（`root` 的子）换成 `weapon_jnt_r`（`hand_r` 的子）——
> 它才是 2XKO 与 LoL 源 `Weapon` 同构的那一个。改完后握法就从「socket 常量」变回「动画数据」，
> 29 条攻击/技能/死亡片段的斧头才能跟着手走。**
