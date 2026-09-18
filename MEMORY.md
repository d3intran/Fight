# Fight 项目避坑血泪史与技术记忆 (MEMORY.md)

本文件记录在虚幻引擎 5.8《Fight》项目开发中亲历、实测并验证过的重大技术陷阱、底层原理（RCA）及工程契约。供后续开发及所有接手 Agent 严格遵守。

---

## 1. 骨骼 100 倍缩放继承陷阱（The 100x Bone Scale Trap）—— 极高危！

### 1.1 案发现象
从外部导出的静态网格体战斧（`SM_Darius_GodKing_Axe`）Attach 到德莱厄斯右手插槽（`hand_rSocket`）后，在关卡中瞬间膨胀成一根 **172 米高的通天摩天柱/烟囱**（斧柄底座比一辆公交车还粗，直插云霄）。

### 1.2 根因剖析 (RCA)
1. **DCC 米制 vs 引擎厘米制**：2XKO 原始模型在 DCC 软件中制作时是以“米”（Meters）为单位（身高 2.47m）。
2. **UE FBX 导入补偿机制**：当 UE 将其作为骨骼网格体（SkeletalMesh）导入时，为了将米制换算为虚幻标准的厘米制（Centimeters），引擎会在最顶层根骨骼（`darius_godking_mesh_LOD0_Skeleton` / `root`）上附加一个 **`Scale = (100.0, 100.0, 100.0)`** 的变换矩阵。
3. **变换逐级传递**：人体所有骨骼（`pelvis -> spine -> clavicle -> arm -> hand_r`）在组件空间（Component Space）中**无条件继承了 100 倍的缩放**。
4. **插槽连带放大**：战斧在切分时本身已经是厘米制（全长 172 cm）。一旦挂接到 `hand_rSocket`，战斧直接被父级骨骼乘以 100：
   $$172\text{ cm} \times 100 = 17,200\text{ cm} = \mathbf{172\text{ 米}}$$

### 1.3 工业级标准解法（红线契约）
- **严禁在 C++ / 蓝图组件上硬写魔法缩放**（违背全局规范第 4 条）。
- **必须在插槽（Socket）资产层做逆向归一化**：
  在 `SK_Darius_GodKing` 的 `hand_rSocket` 上，将其 **`RelativeScale` 设为 `(0.01, 0.01, 0.01)`**。
  $$\text{根骨骼缩放 (100.0)} \times \text{插槽补偿 (0.01)} = \mathbf{1.0}\text{ (绝对 1:1 真实物理世界尺寸)}$$
- **效果**：任何挂接到 `hand_rSocket` 的武器、特效、粒子，其组件 `RelativeScale3D` 均可保持默认的 `(1.0, 1.0, 1.0)`，完美闭环。

---

## 2. 俯视角 MOBA 动画移植到第三人称的特调契约

从《英雄联盟》端游解包出的动画（`.anm` / `.glb`）**绝对不可直接硬拷（Hard-Paste）给次时代写实高模**，必须通过 **IK Retargeter** 按以下三条 SOP 特调：

1. **脊椎俯仰角补偿（Spine Pitch Offset）**：
   - **成因**：MOBA 动画师为了让俯视角 45° 摄像机看清面部与胸甲，故意将脊椎后仰、脖子向上挺拔 15°~20°。
   - **特调**：在 AnimGraph 或重定向姿态中，给 `spine_01` / `spine_02` 叠加向前俯倾 **10°~15°**，将仰面感修正为猎狼前倾的威压感。
2. **双脚开启 Foot IK 锁地**：
   - **成因**：MOBA 步幅是按照短腿与高移速调谐的，放到 2.47 米大长腿身上会导致明显的“搓地滑步”。
   - **特调**：开启 Full Body IK / TwoBoneIK 锁地解算器，脚掌触地帧坐标锁死，步幅由长腿物理自动延伸。
3. **手臂下垂与拖斧姿态**：
   - 右肩胛骨（`clavicle_r`）适度下压，让手柄握持点处于腰下身侧，形成自然的单手拖斧重力感。

---

## 3. 虚幻编辑器运行时状态机与安全法则

1. **后台节流假帧（Viewport Throttling）**：
   - 编辑器失去焦点时，视口默认节流降低刷新率，`HighResShot` 会截取到 MD5 完全一样的冻结旧帧。
   - 自愈命令：执行 `t.IdleWhenNotForeground 0`、`r.Editor.Viewport.Throttle 0`、`Editor.bThrottleWhenHidden 0`。
2. **PIE 运行中资产写入锁（Asset Save Lock）**：
   - 在 Play In Editor (PIE) 运行期间，调用 `unreal.EditorAssetLibrary.save_loaded_asset()` 会被引擎安全机制拒绝（返回 `False`）。
   - **法则**：凡涉及永久保存资产到 `.uasset` 磁盘文件的操作，必须等待退出 PIE 之后再执行。
3. **启动时的“Restore Packages”弹窗处理**：
   - 若非正常退出触发该弹窗，**一律点击 `Skip Restore`（跳过恢复）**。
   - 因为所有已验证成果均已实时存盘并受 Git 版本控制保护，点击 Restore 反而会被陈旧的自动保存缓存污染覆盖。

---

## 4. 本机工具链与环境路径速查表

| 工具 | 绝对路径 / 环境变量 | 避坑要点 |
| :--- | :--- | :--- |
| **Python** | 严禁全局，必须通过 `uv run python` 运行 | 脚本调用必须纯 ASCII 路径 |
| **Blender** | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` | 命令行参数统一为 `-b -P <script.py>` |
| **lol2gltf** | `E:\UE\Fight\Scripts\lol2gltf.exe` | 本机安装的是 .NET 10，必须前置 `$env:DOTNET_ROLL_FORWARD = "Major"` |
| **vgmstream** | `E:\UE\Fight\Scripts\tools\vgmstream\vgmstream-cli.exe` | 解码 Wwise 专有 Vorbis（Codec 0xFFFF）为标准 WAV 的唯一利器 |
| **FFmpeg** | `C:\ffmpeg\bin\ffmpeg.exe` | 已加入 PATH |
| **UE Python** | `E:\UE\Fight\Scripts\ue_remote.py` | 纯 Python 实现 UDP 广播 + TCP 通信，跨进程秒级连接 GameThread |

---

## 5. LOL 俯视角动画 → 2XKO 骨架 离线重定向铁律（2026-09-18 新增）

### 5.1 两套骨架的硬差异（必须先量化，不能凭感觉）

| 对比项 | LOL 源（.anm → .glb） | 2XKO 目标（SK_Darius_GodKing） |
| :--- | :--- | :--- |
| 骨骼数 | 179 | 309 |
| 命名体系 | Riot 自有（`Spine1` / `L_Hip` / `L_KneeUpper`） | UE Mannequin（`spine_01` / `thigh_l` / `calf_l`） |
| 脊柱结构 | **`Spine1` 挂在 `Root` 上，与 `Pelvis` 平级** | `pelvis → spine_01 → spine_02 → spine_03` |
| 腿链 | Hip → KneeUpper → KneeLower → Foot → Toe | thigh → calf → foot → ball → toe |
| 手臂链 | Clavicle → Shoulder → ElbowUpper → Elbow → Hand | clavicle → upperarm → lowerarm → hand |
| **朝向** | **面朝 +Y**（左手在 −X） | **面朝 −Y**（左手在 +X） |
| 单位 | 身高 185.22 单位 | 身高 1.80 单位（米），换算比 ≈ 0.0097 |

> ⚠️ **朝向一栏待复核（2026-09-18 新增测量，与本表冲突）**
>
> 本表声称「LOL 源面朝 **+Y**」。当晚用物理锚点独立测了两遍，结论相反：
>
> | 锚点 | 测量（LOL `skin15_all_anims.glb`，Blender glTF 导入帧） | 推论 |
> | :--- | :--- | :--- |
> | 披风链（必然在身后） | `C_Cape1/2/3` 相对 pelvis 的 Y = **+25.5 / +40.2 / +53.0**，Z 由 −27 降到 −97 | 身后在 +Y ⇒ **面朝 −Y** |
> | 脚尖（必然在身前） | `L_Foot` Y = +9.96 → `L_Toe` Y = **−0.63**（前移 10.6 个单位） | **面朝 −Y** |
> | 插地斧头（在身前） | `Axe_Head` Y = **−85.2**，`Axe_Handle` Y = +7.5 | **面朝 −Y** |
> | 左右手骨命名 | `L_Shoulder/Hand` 在 **−X**，`R_Shoulder/Hand` 在 +X | 若面朝 +Y 则左手应为 −X ✓ |
>
> 前三项物理锚点一致指向 **−Y**，只有「骨头 L/R 命名」支持 +Y。二者不可能同时成立，
> 嫌疑是 **GLB 导出/导入链路对 Y 做过一次翻转**，或 **LOL 骨名的 L/R 是"观察者视角"而非角色视角**。
> 另一个支持 **+Y** 的旁证：本表 5.3 的 Q 实测为「绕 Z 180°」；若两套骨架真的都面朝 −Y，Q 应≈单位阵。
>
> **行动项**：M0 阶段用一次专门的朝向判定测试（把源/目标都摆到同一场景、同侧相机渲染正/背面）敲定，
> 敲定后回来更新本表与 Q 值。**在那之前，不要依赖本表的朝向一栏做符号推断。**

### 5.2 五个致命坑（踩过，勿重蹈）

0. 🔴 **Blender 导出带动画的 FBX 前，必须把 armature 复位到 rest pose**（2026-09-18 实测发现）。
   **现象**：产物的 `matrix_world` 是单位阵，但**骨骼 head 本身整体错位** —— 实测 `R_Hand` 偏
   **58.5 单位**、`Root` 偏 **20.8**、肩宽差 2.0%、躯干链差 3.9%。不是数值噪声，是形状改变。
   **根因**：导出时 `animation_data.action` 还挂着某个 action、frame 停在某帧，
   Blender 把**当前 pose** 写成骨架的节点变换，而不是 rest pose。
   **修法**：
   ```python
   if arm.animation_data:
       arm.animation_data.action = None
   for pb in arm.pose.bones:
       pb.matrix_basis = Matrix.Identity(4)     # 必须逐个清，光设 action=None 不够稳
   bpy.context.view_layer.update()
   ```
   **影响面（已排查本仓库）**：`blender_51_retarget_v4.py`（第 286 行设了 `action = None`，
   **但循环内第 289 行又挂回去**，且循环里没有 `frame_set`）、`blender_30_batch_retarget.py`、
   `blender_50_retarget_v3.py`、`blender_10_retarget.py` —— **四个脚本全部中招**。
   ⇒ 此前导入 UE 的每一批重定向动画，其 Skeleton bind pose 都是某个动画的某一帧。
   IK Retargeter 会用这个错误的 bind pose 建参考系，足以独立造成显著的系统性角度误差，
   **很可能是 26.8° 翻车事件的共因**。`blender_21/22_strip_*.py` 因 `bake_anim=False` 不受影响。

1. 🔴 **纯骨架 FBX 导进 UE 会「导入成功但产出 0 个资产」**（2026-09-18 实测）。
   UE 报 `imported_object_paths = 0`、不抛错、不生成任何东西 —— 最阴的一种失败。
   **根因**：UE 的 FBX 导入需要**至少一个 SkeletalMesh 作骨架载体**才能建出 Skeleton + AnimSequence。
   **修法**：导出时保留源网格，但 `obj.data.materials.clear()` 且删除失效顶点组
   （骨架裁过就必须清，否则顶点组指向不存在的骨）；`use_selection` 要**同时选中 armature 与网格**。

2. 🔴 **`ue_remote.py` 的「`.py` 字样」陷阱**（2026-09-18，已在网关修复）。
   **现象**：`[Error] Could not load Python file '<整段脚本内容>'`，脚本完全不执行。
   **根因**：`MODE_EXEC_FILE` 下若向 UE 传脚本**内容**，UE 会在内容里嗅探形如 `xxx.py` 的字样
   并误判为文件路径 ⇒ **只要 docstring / 注释里写了自己的文件名（如用法示例），整个脚本静默失败**。
   二分对照已排除「文件长度」因素（4964 B 纯 ASCII 长脚本通过，691 B 含 `.py` 字样的失败）。
   **修法**：网关内先落盘到 `Scripts/_ue_remote_run.py` 再传**路径**，失败时回退传内容。

3. **两套骨架朝向相差 180°**。直接搬运世界旋转 → 角色左右镜像 + 前后反着跑（实测最大偏差 161°）。
   **解法**：用各自的「胯骨轴（R_hip.head − L_hip.head，抹平 Z）+ 世界上方 (0,0,1)」叉乘构建基准坐标系
   `B = [right, forward, up]`，求对齐矩阵 `Q = B_tgt · B_src⁻¹`（实测 Q = 绕 Z 轴 180°）。
   旋转增量必须先共轭变换：`D_tgt = Q · D_src · Q⁻¹`。
4. **中间骨必须继承父级旋转**。只对映射表内的骨骼赋值，会漏掉 `spine_03`、`ball_l` 这类源里没有的中间骨，
   导致手臂变僵尸直伸。
   **解法**：按目标骨架**全层级**遍历（父级在前，共 309 根），未映射骨骼用 `final_rot = Rp · rest_rel` 递推，
   映射骨骼再用 `basis = rest_rel⁻¹ · Rp⁻¹ · W_tgt` 写入。

### 5.3 核心算法（v4 正式版，世界旋转增量 + 静止基准补偿）

```
D_src = F_src_pose · F_src_rest⁻¹          # 源骨骼世界旋转增量（F = 关节坐标构造的几何朝向帧）
D'    = Q · D_src · Q⁻¹                     # Q = 两套骨架基准系对齐矩阵（实测绕 Z 180°）
K     = u_tgt.rotation_difference(u_src)    # ★ 逐骨骼「静止基准对齐」最小弧旋转
W_tgt = D' · K · R_tgt_rest                 # 目标骨骼世界朝向
basis = Rest_rel⁻¹ · Rp⁻¹ · W_tgt           # 换算成 Blender 局部 basis 写入关键帧

  F 的构造（三点 a→b→c）：y = normalize(Pb−Pa)；z = normalize(cross(y, Pc−Pb))；x = cross(y,z)
  u_tgt = F_tgt_rest · (0,1,0)              # 目标静止骨方向
  u_src = Q · F_src_rest · (0,1,0)          # 源静止骨方向（映射到目标系）
```

**⚠️ 铁律：K 必须用最小弧旋转 `rotation_difference`，绝不能用整个矩阵 `Q·F_src·F_tgt⁻¹`。**
几何帧的滚转参考方向在两套骨架间天然相差 180°，用整矩阵对齐会把骨骼直接翻转 180°。
（这是实测出来的：K 角度打印出来全是 175°~180°，才发现。）

**为什么必须有 K**：旋转增量法 `W_t = D·R_t_rest` 只能搬"增量"，**搬不动"基准差"**。
两套骨架的 A-Pose 本来就不同（实测：前臂 39°、锁骨 43°、骨盆-胯 41°、小腿 20°），
不补偿的话每帧都恒定带着这个偏斜 —— 这就是用户肉眼看到的"整体角度偏斜"。

脚本：`Scripts/blender_51_retarget_v4.py`（`blender -b -P <script> -- <SRC_GLB> <TGT_FBX> <spine_pitch> <OUTDIR> <anim1,anim2,...>`）。

**精度实测（run，504 样本）**：均值 9.7° / 中位 6.0° / P90 24.2°。
躯干（脊椎 4.7°、颈头 7.4°）与右臂（4.0°~5.2°）已达"优秀"；**腿部仍有残留**（左小腿 22.2°、右大腿 17.3°），待优化。

### 5.4 重定向精度验证器（★ 必用，勿凭肉眼判断）

**核心判据**：`绝对朝向误差 = angle(Q · 源骨方向, 目标骨方向)`，方向一律用**关节坐标**计算
（`bone.head` 经姿态变换后的世界坐标），**不依赖 `bone.matrix_local`**（glTF 导入的骨骼朝向实测不可靠，
源骨架平均偏差 84.9°）。

| 脚本 | 用途 |
| :--- | :--- |
| **`blender_80_orient_verify.py`** | **★ 绝对朝向误差（最终判据，首选）** |
| `blender_41_axis_audit.py` | 骨骼朝向自检（matrix_local Y 轴 vs 真实几何方向） |
| `blender_42_fidelity.py` | Swing 保真度 `angle(Q·Swing_src·Q⁻¹, Swing_tgt)` |
| `blender_70_joint_audit.py` | 逐关节弯曲角逐帧对比表（定位到具体关节） |

**验收门槛**：全部关节平均误差 < 8°，最大 < 30°。

### 5.4 第三人称特调参数（可调）

- 脊椎俯仰补偿：`spine_01/02/03` 按 45% / 35% / 20% 权重叠加前倾（默认 12°），
  `neck_01` 做 60% 反向补偿保持视线水平。**+X 轴旋转 = 向 −Y 前倾**（目标骨架面朝 −Y）。
- 根位移等比缩放：由两套骨架静止身高自动求得（实测 0.009726），也可命令行强制指定。

---

## 6. 虚幻编辑器运行时状态机与安全法则（续）

4. **⚠️ 严禁在 GameThread 上写等待循环**：
   `while les.is_in_play_in_editor(): les.editor_request_end_play(); time.sleep(0.5)`
   会让编辑器**永久 Not Responding** —— `editor_request_end_play()` 需要 tick 才能生效，
   而脚本正占着 GameThread 死循环，永远等不到。**本次已因此强制重启编辑器一次。**
   正确做法：单独发一次 `editor_request_end_play()` 立即返回，在外部 shell 里 `sleep` 等待。
5. **`EditorAssetLibrary.load_asset()` 可能返回 `None`**（即使资产存在）。
   稳妥做法：改用 `unreal.load_asset(path)`，它对 Skeleton / SkeletalMesh / AnimSequence 都可靠。
6. **编辑器视口截图（HighResShot）依赖编辑器窗口处于前台**；窗口在后台时会静默失败或延迟数十秒才落盘。
   需要稳定抓图时优先用 **PIE**（PIE 窗口独立渲染，不受前台焦点影响）。
   另：`AutomationLibrary.take_high_res_screenshot(w, h, path, camera_actor, force_game_view)` 第 4 参是
   **CameraActor 对象**，不是 bool。
7. **`FbxImportUI` 导入动画到已有骨架**：必须显式设 `ui.skeleton = <已有 Skeleton 资产>`，
   否则 UE 会**另建一个同名后缀骨架**，动画挂不上去。
   同时 `import_mesh=False` + `import_animations=True` + `mesh_type_to_import=FBXIT_ANIMATION`。
8. **`EditorActorSubsystem.spawn_actor_from_class` 只能作用于编辑器世界**；PIE 世界无法用 Python 直接 spawn
   （`GameplayStatics.spawn_actor_from_class` / `begin_spawn_actor_from_class` 在 Python 里均不存在）。
   想在 PIE 里取景，改用 `PlayerController.set_control_rotation()` + 调 `SpringArmComponent.target_arm_length`。
9. **⚠️ 导入 SkeletalMesh 前必须退出 PIE**：否则 Interchange 会报
   `Cannot import SkeletalMeshNode asset at runtime. This is an editor-only feature.`，
   静默只创建材质资产、不创建网格。**动画（AnimSequence）导入不受此限制。**
10. **重新导入 SkeletalMesh 比想象中安全**（`replace_existing=True`）：
    - 材质覆盖**按槽名完整保留**（`import_materials=False` 时尤其干净）
    - `hand_rSocket` **连同 relative_scale 一起自动保留**
    - 但**槽位数量会随 FBX 材质数变化**，多余槽位会被截断
    - 重导前务必先 `cp` 备份 `.uasset`（本项目备份在 `Saved/Backup_20260918/`）

---

## 7. 2XKO 模型的「描边壳」陷阱 —— 极高危！（2026-09-18 实测）

### 7.1 案发现象
把 `SK_Darius_GodKing` 的 Material Slot 7（`Darius_Godking_Axe_C000_MI`，FBX 自带的插地待机斧）
赋予全透明 `M_Invisible` 后，**人物脚下的斧头黑影依然存在**。

### 7.2 根因剖析 (RCA)
`SK_Darius_GodKing` 的 8 个材质槽，**Slot 0 = `Darius_Godking_Outline_MI` 的网格对象
（`darius_godking_mesh_LOD0`，50827 顶点）是整个模型的完整复制品 —— 包括那把插地斧头**。

| 网格对象 | 顶点数 | 材质 | 地面以下顶点 |
| :--- | ---: | :--- | ---: |
| `darius_godking_mesh_LOD0` | 50827 | `Darius_Godking_Outline_MI`（描边壳） | **2444** |
| `darius_godking_mesh_LOD0.007` | 5661 | `Darius_Godking_Axe_C000_MI`（斧头本体） | 2526 |

`M_Invisible` 只能挡住槽 7 的斧头本体，**挡不住槽 0 描边壳里的那份副本**。
描边材质是反向外壳（inverted hull）着色，渲染出来就是**纯黑剪影**。

### 7.3 附带发现：Masked 材质的阴影
`M_Invisible` 的 `cast_dynamic_shadow_as_masked` 默认为 **False**，
意味着 masked 材质虽然自身不可见，**却仍按实体投出完整阴影**。
属性名（Python）：`cast_dynamic_shadow_as_masked`（**没有 `b_` 前缀**）。
已改为 `True` 并落盘。

### 7.4 工业级解法（红线契约）
**必须在 DCC 阶段真正删除几何，不能只靠材质隐藏。**
脚本 `Scripts/blender_22_strip_all.py`：
1. 以斧头本体顶点建 `mathutils.kdtree.KDTree`
2. 描边壳中「到最近斧头顶点距离 < 5cm」的顶点判为斧头，删除其所属面
   （实测距离分布**完美双峰**：斧头顶点 p10 = 3.3mm，其余 p20 已有 684mm，阈值极易选取）
3. 再把斧头本体网格对象整体删除
4. 验收指标：**全部网格 `z < -0.02` 的顶点数必须为 0**

### 7.5 验收清单（重导 SK 后必查）
- [ ] 材质槽数量与名称，且每个槽指向正确的 `MI_*`
- [ ] `root` 骨骼 ComponentSpace 缩放仍为 `100`
- [ ] `hand_rSocket` 存在、bone = `hand_r`、relative_scale = `(0.01,0.01,0.01)`
- [ ] `WeaponAxe` 世界缩放 = `1`，战斧世界尺寸 ≈ `21 × 172 × 77 cm`
- [ ] `SK.get_bounds()` 的 z 下界 ≈ `+3.8`（不再是 `-41`）
- [ ] 已有 AnimSequence 仍挂在 `SK_Darius_GodKing_Skeleton` 上

---

## 8. 目录与产出位置契约（2026-09-18 新增）

### 8.1 红线：交付物严禁放 `Saved/`

`.gitignore` 里含 `Saved/*`。放进去 = **不进 git、团队与 CI 永远看不到**。
`Saved/` 是 UE 引擎运行时目录（`Logs` / `Autosaves` / `Crashes` / `Screenshots` / `Interchange`），
只适合放**中间产物与截图**。

### 8.2 目录职责表

| 内容 | 位置 | 进 git |
| :--- | :--- | :--- |
| 报告 / 文档 / 数据表 | `Docs/<主题>/` | ✅ |
| 中间产物 / 日志 / dump | `Docs/<主题>/_intermediate/` | ✅（可删可重生成） |
| 截图 / 临时导出 / FBX 中转 | `Saved/` | ❌ |
| 外部资产库（LOL 解包产物等） | `E:/UE/Assets/` | 独立仓库 |
| 管线脚本 | `Scripts/` | ✅ |

> 已纠正的历史遗留：`Saved/Reports/`（两份重定向报告）→ `Docs/Retarget/`。
>
> ⚠️ **2026-09-18 二次复发**：当晚「修战斧显示」会话又把报告写回 `Saved/Reports/`，
> 已再次迁出到 `Docs/Axe/`（`Axe_Display_Fix_Report.html` + `assets_axe/`）。
> **下次写报告前先看本表**：只要不是截图/日志/dump，一律落 `Docs/<主题>/`。
> `Saved/` 允许放：截图、渲染中间帧、blender/UE 的中转 FBX、导出 OBJ、日志、备份 `.uasset`。

---

## 9. LOL 音频触发架构与「双哈希」陷阱（2026-09-18 实测）

### 9.1 核心事实：音效不绑在技能上，绑在**动画帧**上

`data/characters/darius/darius.bin`（含 Q/W/E/R 全部数值）里**没有任何音频事件字段**，
唯一的音频相关字段是 `mApplyMaterialOnHitSound`（材质命中音）。真正的绑定在动画配置 bin：

```
data/characters/<Champ>/animations/skin<N>.bin
  Characters/<Champ>/Animations/Skin<N>
    mClipDataMap[<动画名>]
      mEventDataMap[<事件标记>]
        ├ __type = SoundEventData            -> mSoundName  ★
        ├ __type = ParticleEventData         -> mEffectKey  （刀光/特效）
        ├ __type = SubmeshVisibilityEventData
        └ __type = JointSnapEventData
        （附 mStartFrame / mEndFrame = 触发帧）
```

语音事件名则明文存在 `data/characters/<Champ>/skins/skin<N>.bin` 里。

### 9.2 ★ 两个哈希算法，极易搞混

| 用途 | 算法 | 实现 |
| :--- | :--- | :--- |
| **Wwise 音频事件名 → Event id** | **FNV-1**（先乘后异或） | `h=2166136261` → `h=(h*16777619)&0xFFFFFFFF` → `h^=b` |
| **LOL bin 字段/条目名 → 哈希** | **FNV-1a**（先异或后乘） | `h=0x811c9dc5` → `h=((h^b)*0x01000193)%0x100000000` |

两者输入均转小写。验证锚点：
`Play_sfx_DariusSkin15_DariusBasicAttack_foley` —FNV-1→ `4103663980`（命中 bank）；
`AFKDetection2` —FNV-1a→ `e4460934`。

### 9.3 bank 无 STID 名字表

`*_events.bnk` 只有 `BKHD` + `HIRC` 两个 chunk，**名字表被 Riot 剥离**。
事件名只能从 bin 侧取明文，再用 FNV-1 与 bank 里的匿名 ID 缝合。

### 9.4 ⚠️ base 与 skin bank 是**叠加**关系，不是替换

神王（skin15）bank 里**没有** W 技能的命中音 `DariusNoxianTacticsONHAttack_OnHit`，
它只存在于 **base** bank。只导 skin bank 会导致 W 命中没声音。

### 9.5 命名规范

```
Play_sfx_<英雄><皮肤>_<技能>_<阶段>
Play_vo_<英雄><皮肤>_<触发场景><2D|3D><变体>
```
阶段 = `OnCast` / `OnHit` / `hit_inner` / `hit_outter` / `hit_kill` / `swing` /
`foley` / `buffactivate` / `loop` / `leadin` / `leadout` / `oba`；
`2D` = 非定位播报音，`3D` = 角色位置衰减音。

### 9.6 产物与复现

- 报告：`Docs/Audio/德莱厄斯_音频触发逻辑探明报告.html`
- 主表：`Docs/Audio/audio_master.csv`（145 条事件 / 623 个 wav）
- 脚本：`Scripts/audio_01~40_*.py`
- 环境：`E:/uv_env/Scripts/python.exe`（cdtb 1.3.0）+ `Scripts/tools/vgmstream/vgmstream-cli.exe`
