# Fight 项目长期笔记

> 工程全景/契约 → `AGENTS.md`；重定向进度 → `Docs/Retarget/HANDOFF.md`；每日过程 → `memory/YYYY-MM-DD.md`。
> 本文件只留「不看就会返工」的硬约束。

## 环境与目录
- Python 走 `uv run --no-project python`；JS/TS 走 `deno`。
- Bash PATH 残缺：每条命令前 `export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"`；`/tmp` 与 python 不互通，临时脚本写项目内文件。
- 报告→`Docs/<主题>/`；中转→`Saved/`（不进 git，**交付物严禁**）；改资产前备份 + git 检查点。
- **`Scripts/` 布局（2026-09-20 重构，详见 `Scripts/README.md`）**：
  - **顶层只留入口/运维**：`ue_remote.py`（唯一网关）、`editor.deno.ts`、`editor_dialog.py`、`editor_focus.py`、`disable_throttling.py` —— **别移走**（`deno.json` / `exp_cycle.py` 按这些路径调用）。
  - 主题子目录：`retarget/`（重定向环+验收器+实验回路）、`anim/`（动画生产/验收：分层合并、待机、披风、战斧、跳跃）、`dcc/`（Blender）、`asset/`（解包/导入）、`core/`（工程维护）。
  - `archive/` 再分 `audio/ retarget/ anim/ ue_api/ misc/`（**证据链，不是死代码**；子目录里脚本的路径引用已失效）。
- 关卡基线 **7 actor**；跑完 UE 脚本必须清临时 actor 与 `/Game/Temp*`（`Scripts/core/plan_99_clean_temp.py`）；清理时 name/label 都要匹配。

## 动画分层合并（2026-09-20 打通，见 `Docs/Locomotion/AxeWalk_Layered_Merge.md`）
- **UE 侧直接改骨骼轨道**（`AnimationDataController`）比进 Blender 省事：`duplicate_asset` 基准 → 按 `spine_01` 子树切上下半身 → `set_bone_track_keys` → FK 反解约束骨（`weapon_jnt`）。
- `AnimationLibrary.get_raw_track_data` 对压缩动画返回空 ⇒ 用 `get_bone_poses_for_frame`（一次取全部骨）。
- **FK 必须把最外层骨补进链**，否则丢掉 ref pose 的 `scale=100`，所有距离缩 100 倍、跨资产比高度就错。
- `find_bone_path_to_root` 返回 `[骨,父,…,root]`；FName **大小写敏感**（轨道名小写 vs 路径里的 `LOD0`）⇒ 建 `.lower()` 映射。
- 拼上下半身**必须量腿-臂相位**（一阶谐波，自然走路 ≈180°）；相位对位移**非线性**，改完必须复测；用**循环**平移还能顺带把循环接缝收到 0。
- 量腿是否交叉**必须自校准**：用锁骨线定角色右轴（actor 轴与网格轴差 90°，直接用会得出相反结论）。
- 武器世界姿态 = **SkeletalMesh 上那个 socket** 的姿态（`mesh.find_socket`，不在 Skeleton）；socket `relative_scale` 必须 0.01；改 socket 的脚本**必须幂等**（从原始常量算，别读当前值）。

## UE 自动化坑
- `ue_remote.py` 是唯一网关：脚本 docstring 里写自己的 .py 文件名 ⇒ **静默不执行**。
- `unreal.Rotator` 一律关键字参数（roll,pitch,yaw）；socket 组合 World=Compose(Rel,Parent)；MathLibrary 缺逆旋转等 4 函数（坐标下降求解）。
- FBX 导入走 Interchange：**目标包名已存在 ⇒ 静默跳过动画工厂**（46→0 个）；导入前必须清空。
- `run_batch_retarget` 不幂等不写盘：输出目录有同名 ⇒ **崩编辑器**；必须逐个 save_asset。
- `list_assets()` 返回 `pkg.object` ⇒ 喂 find_asset_data/rename_asset 会崩；一律 `split(".")[0]`。
- 编辑器必须 `deno task editor:up -- --hold` 启动；**停那个后台任务=杀编辑器**。
- 截图：SceneCapture2D+export_render_target（EXR）+ ffmpeg tonemap；HighResShot 不可靠。

## 资产契约
- SK_Darius_GodKing：310 骨 / 7 材质槽（Slot 0=描边壳=整模复制品，删斧头副本必须 DCC 删几何）。
- 最外层 scale=100 ⇒ pelvis 局部平移必须 1.0967；socket scale=0.01 为抵消它，**动根骨缩放就要重标定武器**（见 AGENTS.md §3）。

## 重定向（LOL 俯视 → 2XKO TP）硬约束
- 源：`Saved/Retarget/Clean/Darius_SrcClean.fbx`（59 骨/46 动作/30fps）；**没有 walk**（run 放慢 0.70）；真值只取 `head_local`；目标 310 骨、24 twist 骨源无对应。
- FBX 导出：复位 rest pose + `bake_anim_use_all_actions=True`（逐 action 导必坏 bind pose）；纯骨架导入产出 0 资产，必须带网格载体。
- Retargeter：先 `add_default_ops()` 再 `auto_map_chains()`；目标 retarget root=`root`+Pelvis 单骨链（修 pelvis 平移 ×100；停 op/调 alpha 没用）。
- 产物坑：最外层骨假 scale 轨道（310 vs 309）⇒ `remove_bone_track`（参数=骨名，小写）。
- 动画改写三铁律：量数值+量是否还在动；危险改写先 /Game/Temp 副本；禁用 `remove_bone_animation`/`finalize_bone_animation`；后处理放在存盘之后。
- Retarget Pose：**先 auto_align_all_bones 定大面，再逐骨修**（顺序反=没写）；pose 存在 **IK Rig** 里 ⇒ 三个资产都存；**验收必须跟在导出之后**。
- twist 与方向判据正交；修 twist 约定=**self**（ik_53）；`unreal.Vector` 没有 rotation_difference。
- 上半身（已验证）：`spine_03` yaw≈+48° 修锁骨/颈/头 + `upperarm_l/r` **镜像 ±yaw** 补偿；基线用 SET_BONE 写 ik36 表（CHAIN 输出已漂）。
- 「补链/拉长链」修 CHAIN_TO_CHAIN **已被否**（ik_55/56）≠ 链映射不重要。
- 验证器 `ik_37`（朝向+twist）；实验回路 `exp_cycle.py <tag>`。
- **★ 现状（2026-09-19 路线修正）**：基础链路打通，**动作质量未过**；`Anims_TP_*` 全是**实验产物**，已暂停角度扫描。三条验收盲区：① 汇总只取 `idle1`（v2 颈面 idle1 6.0 / **run 73.8**）；② `ik_11` 用 `endswith("run")` 误筛技能动作；③ 判据只比方向，**不测落点/交叉**（髋窄 22%）。新顺序：无交叉→脚底/支撑→接缝→握持→方向误差。详 AGENTS.md §0。

## 编辑器状态坑
- 姿势不对先查 **AnimBP target_skeleton 兼容性**（已改挂 ABP_Darius_Test；旧坑 ABP_Unarmed⇒停 ref pose）。查 anim_46/47，修 anim_48。
- Slate 模态框阻塞游戏线程 ⇒ Remote Execution 无响应；`editor_dialog.py --auto`（**先 WM_CLOSE**，Esc 常无效）。
- **编辑器世界可能不 tick** ⇒ `capture_scene()`（延迟到 TickComponent）永不更新，按帧截图是死路；对 tick 无效：节流 CVar/前台化/realtime 开关/invalidate。
- 动态加组件用 `SubobjectDataSubsystem.add_new_subobject`（PoseableMeshComponent 只有它能造）。

## 工具选型定稿
UE5 IK Retargeter 主力（FK Globally Scaled；腿链到踝 Depth=2；Pelvis Z 权重 0）；**2XKO 本体 `darius_base_nav_std_*` 可零误差替代 locomotion（优先）**；
不做：去倾斜烘进 FBX/逐帧头部硬约束/root motion/手填魔数。
