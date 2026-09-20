# Fight 项目 Agent 上下文 (AGENTS.md)

接手本项目的 Agent **开工前必读 §0 与 §1**，再读 [`Docs/Retarget/HANDOFF.md`](Docs/Retarget/HANDOFF.md)（战术快照）。

---

## 0. 当前路线（2026-09-19 修正版）

**目标（收窄版）**：一个正常站立 + 一个正常移动，握斧在训练场里跑通。**不是凑齐 6 个，更不是 46 个。**

**客观进度**：导入 / 重定向 / 导出 / 修缩放 等基础链路已打通；
**动作质量与游戏内运动闭环尚未通过**。所有 `Anims_TP_*`（含 v2）目前都算**实验产物**，不算验收合格的动画。

**已暂停**：角度扫描（`exp_cycle.py` 的 c/d 系列）。局部角度降低 ≠ 动作可用，理由见下。

### 0.1 已确认的验收盲区（改判据前不要再调参）

1. **汇总只取 `idle1`**：`exp_cycle.py:477/483` 只汇总 `idle1`，但 `ik_37` 同时验 `run`。
   v2 实测：颈面 `idle1` 6.01° / **`run` 73.77°（最大 141.69°）**；锁骨L `idle1` 2.85° / **`run` 29.96°**。
   ⇒ 任何「修好了」的结论必须**同时报两个动作**的数字。
2. **动作是误筛的**：`ik_11_batch_retarget.py:53` 用 `endswith("run")`，实际选中
   `idle1 / run / spell1_in_run / spell2_activaterun / spell2_run / spell3_torun` ——
   4 个技能动作没进验收。「产出 6 个」≠「验证 6 个可用」。
3. **方向对 ≠ 落点对**：现有判据只比 `dir(父→子)`，不检查髋间距、脚的横向次序/间距、腿段相交、
   支撑脚漂移、循环接缝。目标髋宽比源窄 **22%** ⇒ 两条腿方向都对也可能夹腿/交叉。

### 0.2 新验收顺序（先过前 4 项，再看角度）

1. 无异常交叉 / 无膝翻转 → 2. 脚底朝向合理、支撑脚不漂 → 3. 整个循环连续（接缝无跳变）
→ 4. 握持稳定（双手 ≤2cm）→ 5. 方向误差（**idle1 与 run 都要报**）

### 0.3 下一步四步（按顺序，不跳步）

1. **定位错误第一次出现在哪一层**：同一 `run` 同帧，对照 源动画 → 净化后 UE 源 → 重定向预览 → 导出资产 → 角色
2. **只校准 `idle1 + run`**，两个同时验收；先敲定左右/前向/单位/`root` 与 `pelvis` 的语义（名字像 ≠ 语义同）
3. **校准与适配分开**：步宽/落脚/膝向/骨盆起伏属于**适配**，必要时用 IK/Control Rig 接触约束；
   原地动画 ≠ 骨盆没有有效平移
4. **换验收标准后再恢复批处理**；任一关键项失败就停止扩动作数量

---

## 1. 铁律（违反 = 返工）

**1.1 相信数据，禁止主观臆断** —— 没数值指标不得宣布完成。
历史翻车：只验「骨名对上/动画能导入/脚不穿地」就交付，结果系统性角度偏斜 26.8°，被一眼看出。
标准流程：`建立指标 → 测基线 → 提假设 → 数据检验 → 被否就换方向 → 改动 → 复测 → 记录数字`。

**1.2 数字必须能证伪结论本身** —— 已知三种自欺方式（本项目都发生过）：
| 自欺 | 实例 |
|:---|:---|
| 只报最好看的样本 | 只汇总 `idle1`，`run` 73.77° 被藏掉 |
| 用「数量/链路成功」冒充「质量合格」 | 「6/6 缩放正确、动画在动」≠ 姿态正常 |
| 指标写超它能证明的结论 | 「腿方向 0.01°」被写成「腿完美」（落点/交叉根本没测） |

**1.3 用现成轮子** —— 几何查询用 Blender `KDTree`/`bmesh`；旋转用 `mathutils`；转码用 `ffmpeg`；
引擎内批处理用 UE Python（`ue_remote.py`）；GLB 结构直接解析 glTF JSON chunk。

**1.4 验证器必须与先验假设无关** —— 用 `angle(Q·源骨方向, 目标骨方向)`（只用关节坐标），
不要用 `angle(源骨朝向矩阵, 目标骨朝向矩阵)`（会把约定差异当错误）。
跨会话比对；标尺用固定骨集 + 只用 `head`；优先缩放不变量（关节间距）。

---

## 2. 项目基础

- UE 5.8 / 工程根 `E:\UE\Fight` / 主关卡 `/Game/Level/Lv-FIght.umap`
- 代码：C++ (`Source/Fight/`) + 脚本 (`Scripts/`，**顶层只留现役，一次性脚本在 `Scripts/archive/`**)
- Git 远程 [d3intran/Fight](https://github.com/d3intran/Fight)，分支 `main`
- Python 走 `uv run --no-project python`；JS/TS 走 `deno`
- Bash 工具 PATH 残缺：每条命令前 `export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"`

---

## 3. 资产契约

### 3.1 角色 SK_Darius_GodKing（2XKO 高模）
- **309 骨**（UE 侧 310，最外层 NULL 根），主干兼容 UE Mannequin 命名；~150 面部骨 + 披风链 + `weapon_jnt`
- **7 材质槽**。**Slot 0「描边壳」= 整模复制品**：删斧头必须 DCC 删几何，材质隐藏挡不住（会出纯黑剪影）
- 两套骨架最外层都有 **scale=100** ⇒ 目标 `pelvis` 局部平移必须 **1.0967**；武器 socket `scale=0.01`
  正为抵消它 —— **动根骨缩放就要重标定武器**
- 蓝图 `BP_DariusCharacter`；`CharacterMesh0.anim_class` 现挂 `ABP_Darius_Test`（曾挂骨架不匹配的
  `ABP_Unarmed` ⇒ 显示参考姿势。**注意：它只能解释关卡里的 A-pose，解释不了 Persona 单独播放时的交叉腿**）

### 3.2 战斧 SM_Darius_GodKing_Axe
- `hand_rSocket`：`rot=(-106.334,-70.982,9.342)`，`loc=(0.18965,0.10080,0.00982)`，`scale=0.01`
- UE 局部 **+Y = 大刃**；世界尺寸 21×172×77 cm；Socket：Blade_Tip / Blade_Edge / Pommel

### 3.3 关卡
基线 **7 actor**：`TrainingGround_Floor/KeyLight/Softbox/SkyLight/Fog/PostProcess` + `PlayerStart`。
跑完 UE 脚本必须清临时 actor 与 `/Game/Temp*`（`plan_99_clean_temp.py`，白名单持续补）。

### 3.4 源资产
- 净化版源 FBX：`Saved/Retarget/Clean/Darius_SrcClean.fbx`（59 骨 / 46 动作 / 30fps）
- LOL 原版解包：`E:\UE\Assets\Darius_GodKing_LOL_Original\`（动画/音效/语音/VFX）
- 2XKO 本体可解包，`darius_base_nav_std_*` 第三人称动画存在 ⇒ **locomotion 的备选源（零重定向误差）**

---

## 4. 现役脚本索引（`Scripts/`；一次性脚本见 `archive/`）

> **2026-09-20 重构**：按主题分了子目录，并删掉 101 个一次性 UE API 探针。
> **顶层只留入口/运维工具**（`ue_remote.py` / `editor.deno.ts` / `editor_dialog.py` / `editor_focus.py` / `disable_throttling.py`），
> 其余在 `retarget/` `anim/` `dcc/` `asset/` `core/`。完整索引见 **`Scripts/README.md`**。

| 目录 | 类别 | 脚本 |
|:---|:---|:---|
| 顶层 | 网关 / 编辑器 | `ue_remote.py`（唯一网关）、`editor.deno.ts`（`deno task editor:up -- --hold`）、`editor_dialog.py --auto`、`editor_focus.py`、`disable_throttling.py` |
| `retarget/` | 实验回路 | `exp_cycle.py` `<tag>`、`exp_reparse.py`（**⚠️ 汇总只取 idle1，见 §0.1**） |
| `retarget/` | 重定向现役环 | `ik_11_batch_retarget.py`（⚠️ `endswith` 筛选，见 §0.1）、`ik_23_purge_animstp.py`、`ik_27_optionB_config.py`、`ik_31_fix_root_scale.py`、`ik_36_calibrate_retarget_pose.py`、`ik_48_restore_pose.py`、`ik_43_align_probe.py`、`ik_53_fix_twist.py` |
| `retarget/` | 验收器 | **`ik_37_verify_orientation.py`**（朝向+twist；**对「落点/交叉」盲**）、`ik_60_contact_audit.py`（★ 接触/落点，需自校准）、`ik_61_raw_dump.py` |
| `retarget/` | 跨会话/离线验收 | `plan_13_verify_fbx.py`、`plan_16_audit_fbx.py`、`plan_17_export_probe.py`、`plan_12_rest_stability.py`、`plan_10_src_clean.py` |
| `dcc/` | DCC 产线（Blender） | `blender_51_retarget_v4.py`（重定向主力）、`blender_30_batch_retarget.py`、`blender_22_strip_all.py`、`blender_split_weapon.py`、`blender_04_render.py`、`blender_80_orient_verify.py`、`blender_41/42/70`、`blender_60/61/62` |
| `anim/` | **分层合并（上下半身拼装）** | `axw_10_merge.py`（★ 合并器，幂等，相位常量 `UPPER_PHASE_SHIFT`）、`axw_11_export.py`（AnimSequence→FBX + 逐帧骨位 JSON）、`axw_17_phase.py`（离线步态相位/循环接缝/落地复核）、`axw_19_audit.py`（武器偏置骨 + 引用链终检）、`axw_15_wire_bs.py`（混合空间换源）、`axw_16_final.py`（编辑器/资产状态自检）、`axw_12_bl_render.py` + `axw_03_bl_bbox.py`（Blender 渲染与网格包围盒审计） |
| `anim/` | 待机 / 披风 / 战斧 / 跳跃 | `idle_20_build2.py`（★ 待机重建）、`idle_12_wire_abp.py`、`cape_04_save.py`（挂披风物理资产）、`axe_42_tune.py`（★ 握斧调参，幂等）、`axe_43_verify.py`、`axe_31_socket.py`、`jump_02_fix.py`、`axe_14_scene_capture_char.py`、`axe_21_apply_and_verify.py` |
| `anim/` | 动画渲染/检查 | `anim_40_render_check.py`、`anim_47_abp_audit.py`、`anim_48_set_animclass.py`、`anim_51_pose_render.py`、`anim_78_make_videos.py`、`anim_80_axe_retarget.py`、`anim_81_layered_walk.py` |
| `asset/` `core/` | 解包/导入/清理 | `extract_godking_assets.py`、`glb_list_anims.py`、`import_weapon_asset.py`、`core/plan_99_clean_temp.py` |
| `archive/` | 一次性/已否路线 | 分子目录 `audio/ retarget/ anim/ ue_api/ misc/`；删除清单见 `archive/_deleted_step_probes.md` |

---

## 5. 已知陷阱速查（踩过才写的，别再试）

| 陷阱 | 表现 / 规避 |
|:---|:---|
| 🔴 目标包名已存在 ⇒ Interchange **静默跳过动画工厂** | 46 动画 → 0 个，不报错。导入前必须 `ik_12_purge_source.py` 清空 |
| 🔴 `run_batch_retarget` 不幂等 + 不写盘 | 目录有同名 ⇒ 崩编辑器；必须逐个 `save_asset` |
| 🔴 最外层骨多一条 `scale=1` 轨道 | 角色缩到 1.85cm；`ik_31` 整条删轨道（参数是骨名，小写） |
| 🔴 `pelvis` 平移 ×100 | 角色甩到 147m；retarget root 改 `root` + 两边加 Pelvis 单骨链（停 op/调 alpha 无用） |
| 🔴 动画改写会清空动作 | 禁用 `remove_bone_animation` / `finalize_bone_animation`；改完必须**同时验数值 + 是否还在动**；危险改写先 `/Game/Temp` 副本 |
| 🔴 `list_assets()` 返回 `package.object` | 喂给 `find_asset_data`/`rename_asset` ⇒ 崩编辑器。一律 `split(".")[0]` |
| 🔴 纯骨架 FBX 导入 UE 产出 0 资产 | 必须带 SkeletalMesh 载体 |
| 🔴 FBX 导出前未复位 rest pose | bind pose 全错。清 pose + `bake_anim_use_all_actions=True`；逐 action 导出必坏 |
| 🔴 `ue_remote.py` 脚本内容里出现 `xxx.py` 字样 | UE 误判为路径 ⇒ **静默不执行**。不要在 docstring 里写自己的文件名 |
| 🔴 编辑器不 tick ⇒ `capture_scene()` 永不更新 | 按帧截图死路；节流 CVar/前台化/realtime 开关全无效 |
| 🔴 远程执行脚本里的 `time.sleep` **阻塞游戏线程** | `get_game_time_in_seconds` 不动是**测量假象**，不代表世界真没 tick；要跨 tick 分步执行用 `register_slate_post_tick_callback` |
| 🔴 **在 slate post-tick 回调里 `destroy_actor` 会崩编辑器** | `EXCEPTION_ACCESS_VIOLATION`（已实测踩过）。清理放回主线程脚本，别写在回调里 |
| 🔴 Slate 模态框阻塞游戏线程 | Remote Execution 完全无响应。`editor_dialog.py --auto`：**先 `PostMessage WM_CLOSE`**（Esc 对部分框无效）。该脚本的 `WM_CLOSE` 常量曾漏定义（崩溃重启卡 `Restore Packages` 时抛 `NameError`），已补 `0x0010` |
| `unreal.Rotator` 位置参数 = (roll, pitch, yaw) | 一律关键字参数 |
| socket 旋转组合 `World = Compose(Rel, Parent)` | 与直觉相反 |
| `MathLibrary` 缺 `invert_rotator`/`rotate_vector`/`quat_*` | 坐标下降 + `compose_rotators` 纯数值求解 |
| 编辑器必须用 `editor:up -- --hold` 启动 | 停那个后台任务 = 杀编辑器 |
| 改资产前备份 + git 检查点 | 编辑器崩过多次；`Saved/` 不进 git，**交付物严禁放 `Saved/`** |
| 并行 Edit 同一文件会互相覆盖 | 多次修改必须串行（吃过亏） |

---

## 6. 相关文档

- `Docs/Retarget/HANDOFF.md` —— 战术快照：现状数字、已证/已否、下一步
- `Docs/Locomotion/AxeWalk_Layered_Merge.md` —— ★ 行走动画分层合并：产物、验收数字、步态相位、髋部零起伏
- `Docs/Retarget/FOUNDATIONS.md`、`Retarget_Pose_Guide.md`、`FINAL_Retarget_Plan.html`
- `Docs/Axe/Axe_Display_Fix_Report.html`
- `.workbuddy/memory/` —— 每日过程日志 + `MEMORY.md`（长期硬约束）
