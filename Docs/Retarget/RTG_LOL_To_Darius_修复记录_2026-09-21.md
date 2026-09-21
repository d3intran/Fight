# RTG_LOL_To_Darius 修复记录（2026-09-21）

> 目的：把 `SK_LOL_Darius`（英雄联盟源）的 46 条动画重定向到 `SK_Darius_GodKing`（2XKO 目标）。
> 本文件记录**当前可用状态**、修复配方、验收数字、回滚路径与未决项。接手前先读这份。

## 1. 结论摘要

- **重定向映射现在可用**：朝向一致、左右一致、运动量传递正常、不翻不飘。
- 修复方式 = **两个旋钮同时生效**，缺一不可（详见 §2）。任何"只拧一个"的方案实测都会反向出问题。
- 正式产物：`/Game/Character/Darius/Animations/LOL_Retarget/`（修复前生成的 `A_Darius_idle1` 仍在，需按新配方重跑覆盖）。
- 验证用测试产物：`/Game/Character/Darius/Animations/LOL_Retarget_Test/`（`A_Darius_run`、`A_Darius_idle1`）。

## 2. 修复配方（两个旋钮）

### 旋钮 A —— 源 retarget-pose 的 `Root` 施加「世界空间 yaw 180°」的局部化偏移

```python
R = IKRigController.get_ref_pose_transform_of_bone("Root").rotation   # IK_LOL_Darius 的参考姿态世界旋转
off = qconj(R) * (Rotator(0, 180, 0).quaternion() * R)                # 共轭到骨骼自身坐标系
IKRetargeterController.set_rotation_offset_for_retarget_pose_bone("Root", off, SOURCE)
```

- 实测落地值：四元数 `(-0.129, -0.893, 0.432, 0.000)`，读回欧拉 `(pitch -6.39, yaw 166.63, roll 129.09)`。
- ⚠️ **必须共轭**：`set_rotation_offset_for_retarget_pose_bone` 的偏移作用在**骨骼自身坐标系**。
  直接写 `Rotator(0,180,0)` 会沿该骨局部轴翻 → 实测把角色掀成头朝下（`pelvis_z = -237 cm`）。
- 作用：让源的校准姿态与目标同向 ⇒ 输出朝向一致。

### 旋钮 B —— 全身左右链交叉映射（26 条）

原因：`SK_Darius_GodKing` 的 l/r 命名与解剖左右相反（`foot_l` 在角色右侧、`hand_r` 在左侧），
按名字直连必然镜像。用 `IKRetargeterController.set_source_chain(source_chain, target_chain)` 交叉映射：

| 目标链 | 源链 | 目标链 | 源链 |
|---|---|---|---|
| LeftLeg | **RightLeg** | RightLeg | **LeftLeg** |
| LeftFoot | **RightFoot** | RightFoot | **LeftFoot** |
| LeftArm | **RightArm** | RightArm | **LeftArm** |
| LeftClavicle | **RightClavicle** | RightClavicle | **LeftClavicle** |
| LeftThumb / Index / Ring / Pinky | **Right…** | RightThumb / Index / Ring / Pinky | **Left…** |
| Spine / Neck / Head / Weapon | 同名 | Pelvis / *Metacarpal / *Middle | `None`（未映射） |

## 3. 最终验收数字（源 `A_LOL_Darius_run` vs 修复后产物 `A_Darius_run`）

| 指标 | 源 | 产物 | 判定 |
|---|---|---|---|
| `hand_score`（持斧手左右，与朝向无关） | −51.99 | −44.46 | ✅ 同号 ⇒ 斧头在正确的手上 |
| `lr_score`（双脚左右，与朝向无关） | +20.95 | +28.56 | ✅ 同号 |
| 脚位移幅度 | L 87.74 cm | foot_l 93.09 cm | ✅ 同量级（腿长比 ≈1.25×） |
| `pelvis_z`（站立不翻/不离地） | 103.99 cm | 76.30 cm | ✅ 在 60~160 区间 |

> ⚠️ **判朝向不能用"单只脚 `foot_l` 的脚尖"**：交叉映射后该骨由源的**另一只脚**驱动，指标会被污染。
> 可信指标是 `hand_score` + 对应脚的脚尖同号。

## 4. 现场状态（`Saved/Attack/rtg_state_after_fix.json` 有完整快照）

- `TargetRootSettings`：rotation/translation offset 全 0；`blend_to_source=0`，`rotation_alpha=1`。
- 两侧 retarget-pose root offset：TARGET `(0,0,0)`、SOURCE `(0,0,0)`。
- op 栈（`get_num_retarget_ops` / `get_op_name(i)`）：
  | # | op | enabled | 关键设置 |
  |---|---|---|---|
  | 0 | Pelvis Motion | True | `rotation_offset_global/local = 0` |
  | 1 | FK Chains | True | 31 条链，`rotation_mode = INTERPOLATED` |
  | 2 | Run IK Rig | True | IK 链 = LeftLeg / LeftArm / RightLeg / RightArm |
  | 3 | Root Motion | **False**（默认关闭） | — |
  | 4 | Remap Curves | True | — |
- 未映射目标链：4×2 个 `*Metacarpal`、`LeftMiddle`、`RightMiddle`、`Pelvis`（→ `None`）。
  源 rig 没有中指链、没有腕骨链，也没有 `Pelvis` 链（只作 retarget root），所以这些链只能留空。
- 源 rig 的链有 **39 条 = 20 条正式链 + 19 条 `_0` 重名副本**，属于重复添加留下的脏数据，建议清理。

## 5. 工具与命令

```bash
cd E:/UE/Fight/Scripts
echo "mirror" > E:/UE/Fight/Saved/Attack/rtg_fix_mode.txt      # 修复 mode
uv run --no-project python ue_remote.py retarget/rtg_20_fix_verify.py      # 施加修复 + 重定向 + 三件套验收
uv run --no-project python ue_remote.py retarget/rtg_22_delta_probe.py     # 动画 vs 参考姿态旋转差
uv run --no-project python ue_remote.py retarget/rtg_31_state_dump.py      # 只读落盘当前状态
uv run --no-project python ue_remote.py retarget/rtg_30_weapon_scan.py     # 武器刚性扫描
```

⚠️ `rtg_20_fix_verify.py` 每次运行前会把**两侧** `Root`/`Pelvis` 的姿态偏移归零（基线卫生），
所以**不要用 mode=none 去"看一眼现状"**——那会抹掉修复。看现状用 `rtg_31_state_dump.py`。
可用 mode：`mirror`（定稿）、`src_root_yaw180_world`、`src_root_yaw180_world_legcross`、`legcross`、
`align_src`、`no_run_ik`、`fk_onetoone`、`restore`（全面还原）。

## 6. 备份与回滚

- `Saved/Attack/backup_20260921_1740/`：`RTG_LOL_To_Darius.uasset` / `IK_LOL_Darius.uasset` / `IK_Darius.uasset` 的修复前副本。
- 回滚 = 把这三个文件复制回 `Content/Character/Darius/IK/` 后重启编辑器（或跑 `mode=restore` + 手工复原链映射）。
- 崩溃抢救：`Saved/Autosaves/Game/...` 下有同名 `.uasset`，可复制回 `Content/` 还原（今天已用过一次）。

## 7. 未决项

1. **武器（见 §8）**：源动画的握法是动画数据，socket 方案对 29/46 条片段有损。
2. `weapon_jnt` 父级是 `root`，FK 旋转重定向**无法**把它带到手上（实测全程钉死在脚下 `(−2,−4,3) cm`）。
3. 源 rig 的 19 条 `_0` 重复链待清理。
4. 正式目录 `Animations/LOL_Retarget/` 里的 `A_Darius_idle1` 是修复前版本，需按新配方重跑覆盖。

## 8. 武器扫描结论（`rtg_30_weapon_scan.py`，46 条源片段）

量的是 `Weapon` 骨相对 `R_Hand` 的**手内**位移/旋转漂移：

- **17 条刚性**（漂移 0.000 cm / 0.000°）：`turn*`、`idle*`、`run*`、`walk` 等移动类。
- **29 条有漂移**：`attack1` 42.3cm/82.4°、`attack2` 46.0cm/90.4°、`crit` 28.7cm/50.4°、
  `spell1` 19.6cm、`spell3` 48.7cm、`spell4_5` 54.8cm/140°、`taunt` 52.0cm/137°、
  `dance` 184cm/101°、`death` **404cm/179.8°**、`recall` 4.4cm/29.3° …

⇒ **斧头的握法在 LoL 原版里本来就是动画数据**（挥砍时斧头相对手会转 80~140°、死亡时脱手 4 米）。
只用 `hand_rSocket` 挂载 ⇒ 这 29 条片段的斧头会被"焊死"在固定握法上，攻击动作会明显发僵。
移动类（17 条）用 socket 无损。
