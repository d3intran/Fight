# 行走动画分层合并：`A_Darius_AxeWalk_Layered`

> 2026-09-20 · 上半身取 `A_Darius_AxeWalk_Mixamo`，下半身取 `A_Darius_Walk_Layered`

## 1. 产物

| 项 | 值 |
| :--- | :--- |
| 资产 | `/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered` |
| 骨架 | `SK_Darius_GodKing_Skeleton` |
| 长度 | 50 帧 / 51 key / 1.667 s @ 30fps（= `A_Darius_Walk_Layered` 的长度） |
| 骨骼轨道 | 310（= `A_Darius_Walk_Layered`） |
| 混合空间 | `BS_Darius_Locomotion` 的 5 个走路样本已从 `A_Darius_Walk_Layered` 切到它 |
| 生成脚本 | `Scripts/anim/axw_10_merge.py`（幂等，可重跑） |

## 2. 分层规则

在 UE 侧用 `UAnimationDataController` 直接改写骨骼轨道，**不经过 Blender**：

| 骨集 | 来源 | 处理 |
| :--- | :--- | :--- |
| `spine_01` 子树（**249** 根：脊柱 / 双臂 / 双手 / 头 / 脸 / 披风） | `A_Darius_AxeWalk_Mixamo` | 按比例重采样（41 key → 51 key，位移线性 / 旋转 slerp）+ **循环相位平移 −1.81 key**（见 §3.1） |
| `pelvis` + 双腿双脚 + 发链 + 相机骨（**61** 根） | `A_Darius_Walk_Layered` | 原样保留 |
| `weapon_jnt` | 重新解算 | 用 FK 把合并后的 `weapon_jnt_r`（右手）世界变换反解成局部键 |

相位平移量是脚本里的一个常量 `UPPER_PHASE_SHIFT`（`Scripts/anim/axw_10_merge.py`），设 `0` 即完全按原相位搬、不做任何对齐。

## 3. 验收数字

| 指标 | 结果 | 读法 |
| :--- | ---: | :--- |
| 下半身 vs `Walk_Layered`（角度 / 位移） | **0.000° / 0.0000 cm** | 逐 key 全等，下半身一字未改 |
| 上半身 vs 重采样源 | **0.000° / 0.0000 cm** | 写入无损耗 |
| `weapon_jnt` ↔ `weapon_jnt_r` 距离 | **0.0000 cm / 0.000°** | 斧头跟手（逐 key 抽查） |
| `pelvis` / `thigh_l` / `calf_l` / `foot_l` / `ball_l` / `toe_l` 落点 | 与 `Walk_Layered` **逐位相同** | 接地高度继承已知良好版本 |
| 每帧最低骨（排 camera/root/sync） | `toe_r` / `toe_l`，**10.5 ~ 23.9 cm** | 不穿地 |
| 逐帧网格包围盒 min z（Blender，地面 = 0） | **0.077 ~ 0.166 m** | 与 `Walk_Layered`（0.077 ~ 0.142）同量级 |
| 循环接缝（首 key vs 末 key 全骨） | **最大 0.00 cm** | 无接缝跳变 |
| 腿-臂相位差 | **185.3°**（理想 180°） | 见 §3.1 |

### 3.1 步态相位（为什么加了 −1.81 key 的平移）

用一阶谐波相位量「腿的交叉摆动」与「臂的交叉摆动」的相位差（自然走路应 ≈ **180°**，即对侧摆臂）：

| 版本 | 腿相位 | 臂相位 | **差值** | 距 180° |
| :---|---:|---:|---:|---:|
| `A_Darius_Walk_Layered`（上半身是冻结静止姿势，仅随骨盆漂移） | 92.3° | 107.7° | 15.3° | 164.7° |
| `A_Darius_AxeWalk_Mixamo`（原片，Mixamo 专业出品） | 92.0° | 265.7° | 173.7° | **6.3°** |
| 合并（相位平移 = 0） | 92.3° | 249.2° | 156.8° | 23.2° |
| **合并（相位平移 = −1.81 key）** | 92.3° | 277.7° | **185.3°** | **5.3°** |

**为什么合并会掉 23°**：`A_Darius_Walk_Layered` 的骨盆**在转**（带着整个躯干一起转），而 `A_Darius_AxeWalk_Mixamo` 的骨盆**全程静止**（`pelvis` 局部旋转恒定 = 静止姿势，位移也恒定）。
把 UP 的臂骨挂到 LOW 的转骨盆上 ⇒ 躯干跟着髋**同向**转，而真实走路肩带应与髋**反向**转
⇒ 手臂的对侧摆幅被抵消掉一部分。相位平移 1.81 key（≈23°）把它补回来。

### 3.2 已知特征：**这个走路没有髋部上下起伏**

| | pelvis component-space z |
| :--- | :--- |
| `A_Darius_Walk_Layered` | **105.72 cm 恒定**（起伏 0.00 cm） |
| 合并产物 | **105.72 cm 恒定**（起伏 0.00 cm） |

`pelvis` 在垂直方向**完全不动**，脚/趾最低 z 只在 10.45 ~ 22.51 cm 之间变化。
这很可能就是之前判「**轻飘飘**」的主因 —— 重心没有上下，走起来像滑行。

**不建议**直接给 `pelvis` 加 Z 键：没有 IK / 脚部锁定的话，骨盆一沉整条腿链跟着沉，支撑脚会穿地。
正确做法是给支撑脚加接触约束（Control Rig / Foot IK）后再补骨盆起伏；或者换一个**源本身带髋部起伏**的走路。

## 4. 关于「`A_Darius_AxeWalk_Mixamo` 单独打开人物掉进地底」

**逐层实测后，这个说法在数据上无法复现。**

| 检查项 | 实测 |
| :--- | :--- |
| 逐帧网格包围盒 min z（地面 = 0） | `AxeWalk_Mixamo` **0.043 ~ 0.106 m**；`Walk_Layered` 0.077 ~ 0.142 m —— **同一量级，都在地面之上** |
| `pelvis` component-space z | `AxeWalk_Mixamo` **109.54 cm 恒定**；`Walk_Layered` 109.54 cm ⇒ 差 < 4 cm |
| `Skeleton` 的 preview mesh | `SK_Darius_GodKing`（正常） |
| `SK_Darius_GodKing` 材质槽 | **只剩 7 个（0~6）**，斧头槽 7 已删 |

### 唯一查实的缺陷（已在新产物里修掉）

`A_Darius_AxeWalk_Mixamo` 里 **`weapon_jnt` / `weapon_jnt_offset` 全程停在静止姿势**，
component-space `(0, −4.0, 3.4)` —— 也就是 2XKO 那把「插地死斧」的位置，**比右手低 111 cm**。
`A_Darius_Walk_Layered` 里它们严格跟手（dist = 0.000 cm）。

⇒ 任何挂到 `weapon_jnt` 的几何（例如把斧头槽 7 加回来）都会掉到地上。
当前因为斧头槽已删，**它没有可见几何**，所以解释不了「掉进地底」这个现象。

合并产物**不受这个缺陷影响**（`weapon_jnt` 是重新解算的，实测与 `weapon_jnt_r` 差 0.0000 cm）。
**源资产 `A_Darius_AxeWalk_Mixamo` 我没有改动** —— 你还在排查「掉进地底」，
保持原样便于对照。要修的话同一套 FK 反解逻辑直接套上去即可（约 20 行）。

**需要用户补充**：具体是哪个资产、在哪个视图（Persona / 关卡 / PIE）里看到的，最好给一张截图。

## 5. 预览

- 视频（Blender 渲染，灰模，无战斧 —— 战斧是挂在 `hand_rSocket` 的独立资产，不在动画里）
  - `Saved/Preview/video/darius_axewalk_layered_side.mp4`
  - `Saved/Preview/video/darius_axewalk_layered_front34.mp4`
- 接触表：`Saved/Shots/AxwMerge/sheet_*.png`
- 逐帧骨位 JSON：`Saved/Preview/AxwExport/bones_{merged,low,up}.json`

## 6. 复现 / 回退

```
# 重新合并（幂等，改 UPPER_PHASE_SHIFT 即可调相位；设 0 = 完全按原相位搬）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/axw_10_merge.py

# 导出 FBX + 逐帧骨位
uv run --no-project python Scripts/ue_remote.py Scripts/anim/axw_11_export.py

# 离线复核相位 / 接缝 / 落地高度
uv run --no-project python Scripts/anim/axw_17_phase.py

# 渲染（Blender）
"<Blender 5.2>" -b -P Scripts/anim/axw_12_bl_render.py -- \
  "E:/UE/Assets/Darius_Walk_Layered.fbx" \
  "Saved/Preview/AxwExport/A_Darius_AxeWalk_Layered.fbx" \
  "Saved/Shots/AxwMergeFull" "merged" 51
```

回退混合空间：把 `BS_Darius_Locomotion` 的 5 个走路样本改回 `A_Darius_Walk_Layered`
（`Scripts/anim/axw_15_wire_bs.py` 里 `NEW` 换成旧路径即可）。

## 7. 终检（`Scripts/anim/axw_19_audit.py`）

| 检查项 | 结果 |
| :--- | :--- |
| `weapon_jnt_offset` 是否仍贴在 `weapon_jnt` 上（它的局部键取自 LOW） | 最大偏差 **0.0000 cm** ✓ |
| 与 LOW 有差别的骨 | **44 根**，子树外只有 `weapon_jnt` ✓（其余 205 根子树骨两边都是静止姿势，所以数值相同；实际写入 249 根） |
| 上半身形状 vs UP（`spine_01→head` / `→hand_r` / `→hand_l`） | 5.76° / 6.89° / 23.79° —— **不是缺陷**：前者来自 LOW 骨盆与 UP 骨盆的差，后者还叠加了故意加的相位平移（手臂摆得比躯干快） |
| `ABP_Darius_Test` | 编译通过；`Idle → A_Darius_idle1`、`Walk / Run → BS_Darius_Locomotion` ✓ |
| `BP_DariusCharacter` 模板 `CharacterMesh0.anim_class` | `ABP_Darius_Test_C` ✓ |
| 关卡 actor / 脏包 / 临时对象 | 7 个基线 actor；`dirty maps=[] dirty content=[]`；关卡包里无残留 RT |

⚠️ 顺带发现：ABP 的 `Jump / Fall Loop / Land` 三个状态还挂着 **Mannequin 的 `MM_*` 蒙太奇**（骨架不匹配）。
这三个状态当前没被用到，但哪天真走跳跃流程会直接失效。

## 8. 2026-09-20 下午：PIE 实机问题（待机歪 / 披风穿模无物理 / 走路确认）

### 8.1 「行动时是组合动画吗」→ 是

`BS_Darius_Locomotion` 的 5 个走路样本全部指向 `A_Darius_AxeWalk_Layered`（速度 250/500、方向 ±90/180）。
PIE 里实读：`CharacterMesh0.anim_class = ABP_Darius_Test_C`，`Walk / Run` 状态用该混合空间。

### 8.2 「披风没有物理」→ 根因找到并修好

| 检查 | 结果 |
| :--- | :--- |
| ABP 的 `RigidBody` 节点 | **已存在且已接线**，`override_physics_asset = SK_Darius_GodKing_Physics`，`alpha = 1.0` |
| `SK_Darius_GodKing_Physics` 内容 | **已含 27 根披风骨的刚体**（`cape_chain_01..09 × l/m/r`，各带 sphere 图元） |
| **`SK_Darius_GodKing.physics_asset`** | **`None`** ← ★ 这就是「没有物理效果」的原因 |

**修法**：`SkeletalMeshEditorSubsystem.assign_physics_asset(mesh, physics_asset)`
（`is_physics_asset_compatible` 返回 True，assign 返回 True，`save_asset` 返回 True）。

⚠️ **PIE 期间引擎拒绝存盘**（`save_asset` 返回 False，日志 `The Editor is currently in a play mode`），
且运行中的 PIE 实例不会重新读取该属性 ⇒ **必须退出 PIE 再存，然后重进 PIE 才能看到效果**。
另外 PIE 期间 `EditorAssetLibrary.load_asset` 会被拒，但 **`unreal.load_object` / `unreal.find_object` 仍可用** ——
要读资产就换这两个。

### 8.3 「待机动画是歪的」→ 量化确认，已重建

实读 PIE 内姿态（用脚尖方向定前向）：`neck_01→head` 段 **45.5° 离竖直**，脊柱是锯齿状的。

`Anims_TP_v2/A_Darius_idle1` 逐帧（component space，前向 = 右轴 × 上）：

| 段 | 离竖直 | 方向分解 |
| :---|---:| :--- |
| spine_01 | 8.1° | 90% 向后 + 44% 右 |
| spine_02 | 13.8° | 41% 前 + **91% 左** |
| spine_03 | 12.4° | 66% 前 + **75% 右** |
| neck_01 | 25.3° | 93% 向后 |
| **head** | **48.7°** | **97% 向后** |

对照 `AxeWalk_Mixamo` / 合并走路：3.1 / 8.7 / 18.2 / 25.6 / 33.5°，**单调前倾、脊柱是直的**。
⇒ 待机的问题在**上脊柱与头**（LOL 重定向的残留），下半身是好的。

**产物**：`/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered`（65 帧 / 66 key，309 轨道）

| 项 | 做法 |
| :--- | :--- |
| `pelvis` + 双腿双脚 | 原样保留原待机（实测差 **0.000° / 0.0000 cm**） |
| `spine_01` 子树（249 根，含披风链） | 取 `A_Darius_AxeIdle_Mixamo`（Mixamo 持斧静止姿） |
| 呼吸 | 程序化：`spine_02` 1.5° + `neck_01` 1.0°，1 个周期（常量在脚本 `BREATH`，设 0 即静止） |
| `weapon_jnt` | 同走路，FK 反解跟手 |

校验：`NEW~AXEIDLE = 0.00°`（脊柱链逐骨等于 Mixamo 源）；`NEW~OLDIDLE = 18.6 / 20.6 / 38.9 / 41.6 / 53.0°`
（确实改了）；骨盆/腿脚 `NEW~OLDIDLE = 0.00°`；循环接缝 **0.0007 cm**。
`ABP_Darius_Test` 的 `Idle` 状态已从 `A_Darius_idle1` 切到它，编译 + 存盘通过。

### 8.4 ⚠️ 新量出来的问题：**待机与走路的接地高度差 ~15 cm**

（component space，已把最外层骨的 `scale=100` 补进来算，所以数值可比）

| 资产 | pelvis z | ball_l z | ball_r z | head z |
| :---|---:|---:|---:|---:|
| `A_Darius_AxeIdle_Layered`（新待机） | 102.03 | **−0.42** | **−3.29** | 177.94 |
| `Anims_TP_v2/A_Darius_idle1`（旧待机） | 102.03 | −0.42 | −3.29 | 174.27 |
| `A_Darius_AxeWalk_Layered`（走路） | 105.72 | **21.48** | **14.66** | 178.58 |

网格 bind pose 的鞋底在 **+3.8 cm**（09-18 实测）。据此换算鞋底高度：
待机 ≈ **−5 cm**（略沉），走路 ≈ **+10 cm**（浮空）。

⇒ **待机↔走路切换时角色会上下跳 ~15 cm**；走路本身是「蹲着走」的姿态（骨盆只高 3.7 cm，
脚却高 22 cm ⇒ 腿的垂直投影短了 22 cm）。这是 `Walk_Layered` 从 Mixamo 源搬**旋转**时
腿长比例不匹配留下的，**没有修** —— 修法有两条，代价不同，需要定方向：
① 只做整体高度偏移（最省事，但走路会变成明显下蹲）；
② 给支撑脚加接触约束 / 腿长适配（正确，但要 IK）。

## 9. 复现 / 回退（补充）

### 9.1 第二轮实机问题（16:15~16:30）：腿交叉 / 斧刃朝上 / 披风仍无重力

#### ★ 量腿部左右次序必须**自校准**（我第一版量错了）

用「actor 的右轴」量会得出错误结论 —— 因为 `CharacterMesh0.relative_rotation.yaw = -90`，
网格的局部轴与 actor 轴差 90°。**正确做法：用「锁骨线」定角色右轴**
（`clavicle_r − clavicle_l` 的水平分量 —— 锁骨 L/R 的左右是骨架保证的，不依赖任何约定），
再用 `hand_l/hand_r` 做自检（必须左<0、右>0）。

| 版本 | 髋 | 膝 | 踝 | 掌 | 趾 | 判定 |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| 旧待机（`Anims_TP_v2/A_Darius_idle1`） | −3.8 | −14.5 | −25.5 | −30.0 | −29.3 | **全部交叉** |
| **新待机（下半身换成走路第 2 帧）** | **+0.2** | **+0.5** | **+0.7** | **+0.7** | **+0.7** | **全部正常** |

（表中为「次序差」= lat(右) − lat(左)，负 = 交叉）

**做法**：`idle_20_build2.py` 的 `LB_FRAME` 常量 —— 下半身（非 `spine_01` 子树那 60 根）
不再用原待机，改成**走路资产某一帧冻成常量**。选帧标准：左右次序正确 + 两脚都接近贴地 + 站姿尽量窄。
走路全帧扫描结果：脚间距 **71.2 ~ 118.7 cm**（`Walk_Layered` 本身就是宽站姿），
取 **f2**（74.7cm、鞋底高差 5.3cm、次序正确）。

同时给待机**补了最外层骨轨道**（`darius_godking_mesh_lod0_skeleton` = 走路的常量值），
让待机与走路的接地基准一致 —— 实测两者网格最低点都是 **+0.082 / +0.077 m**，不再有 ~23cm 的高度差。

#### 斧刃朝向：已改成朝下

斧头是 `BP_DariusCharacter` 上的 `WeaponAxe`（StaticMeshComponent，relative_rotation = 0）
⇒ 斧头世界旋转 = **`hand_rSocket` 的世界旋转**。而 `hand_rSocket` 只在 **`SK_Darius_GodKing`（网格）**上
（不是 Skeleton，`mesh.find_socket("hand_rSocket")`，该网格总共就这 1 个 socket）。

改法：算出「让斧头 +Y 指向 component 空间 −Z」的最小弧修正，折进 socket 的相对旋转：

| | socket 相对旋转 | 斧头 +Y（大刃）世界方向 | 与朝下夹角 |
| :--- | :--- | :--- | ---: |
| 改前 | pitch −106.334 / yaw −70.982 / roll 9.342 | (−0.545, 0.639, 0.544) | **123.0°** |
| **改后** | **pitch −16.942 / yaw −35.529 / roll 121.338** | **(−0.005, −0.001, −1.000)** | **0.3°** ✓ |

（PIE 实测复核。原始值已记在 `AGENTS.md §3.2`，要回退就填回去。）

#### 披风：节点与资产都对，但**本机编辑器只有 ~3 fps，判不了**

- `RigidBody` 节点**确实接在链上**：`Slot → LocalToComponentSpace → RigidBody → ComponentToLocalSpace → Root`
  （`AnimGraphNode_Base.list_input_pins()` + `BlueprintGraphPin.list_connected_pins()` 可读连线）。
- 网格已挂物理资产，物理资产含 27 根披风骨刚体。
- 但本机 PIE 实测 **15 tick = 5 秒 ⇒ ~3 fps**；UE 物理有 `MaxPhysicsDeltaTime` 钳制，
  3 fps 下模拟约 10× 慢放 ⇒ 采样到的披风相对骨盆高度恒定（+69 / −3 / −70）。
  **这个环境下无法判断物理是否生效**，需要在正常帧率下（编辑器前台、不被节流）再看。

### 9.4 第三轮（16:31~）：握斧手感 / 空格跳太高

#### ★ 斧头怎么「握在手上」——两个旋钮 + 手动调法

**先理清结构**：`WeaponAxe` 是 `BP_DariusCharacter` 上的一个 StaticMeshComponent，
`relative_location / relative_rotation / relative_scale` **全是默认值（0/0/1）**，
它挂在 `SK_Darius_GodKing` 的 **`hand_rSocket`** 上
⇒ **斧头的世界姿态 = `hand_rSocket` 的世界姿态**。所以「握斧方式」= **改这个 socket**。

| 旋钮 | 位置 | 作用 |
| :--- | :--- | :--- |
| `relative_rotation` | `SK_Darius_GodKing` → Sockets → `hand_rSocket` | 斧头朝向（刃朝上/朝下/侧） |
| `relative_location` | 同上 | 斧头在手里的位置（含沿斧柄滑动 = 握哪儿） |
| `relative_scale` | 同上 | ⚠️ **必须保持 0.01**（抵消骨架最外层 100× 缩放），别动 |

**手动调（推荐，所见即所得）**：
1. 双击打开 `SK_Darius_GodKing` → 左下 **Skeleton Tree** 面板展开 **Sockets** → 选中 `hand_rSocket`
   → 右侧 Details 里改 Relative Location / Rotation，视口里 socket 的 gizmo 与预览**实时更新**。
2. 或打开 `BP_DariusCharacter` → Components 里选 `WeaponAxe` → 视口里用移动/旋转 gizmo 直接拖。

**脚本调（快速迭代）**：`Scripts/anim/axe_42_tune.py`，顶部三个常量：

| 常量 | 含义 |
| :--- | :--- |
| `BLADE_DOWN` | True = 刃朝下；False = 用原始朝向 |
| `GRIP_FROM_HEAD_CM` | 手握在「离斧头多少厘米」处。斧头全长 172cm、网格原点在正中间 ⇒ **86 = 握正中**（推荐起点）、40 = 握靠近斧头、0 = 握在斧头上 |
| `PALM_PULL_CM` | 把斧柄往掌心收多少 cm（0 = 不动；15 ≈ 收到掌心） |

⚠️ 脚本**幂等**（一律从 `ORIG_ROT` / `ORIG_LOC` 常量出发算），重复跑不会累积偏移。

**本次结果**（PIE 实测）：

| 指标 | 改前 | 改后 |
| :--- | ---: | ---: |
| 斧头 +Y（大刃）与「朝下」夹角 | 123.0° | **0.6°** ✓ |
| 手腕到斧柄轴线距离 | 20.4 cm（≈指尖外） | **9.2 cm**（≈掌心） ✓ |
| 斧头端 / 尾端高度（手在 105cm） | — | **≈29 cm / ≈201 cm** |

⚠️ 实测这个 socket 的 `relative_location` **单位不是干净的 cm**（本次量到约 30cm/单位，
不是骨架的 100×）—— 所以**要精确对位请用编辑器视口拖**，或者告诉我目标
（例如「斧头离地 20cm、握在离斧头 60cm 处」）我用数值解出来。

#### 空格跳太高：`jump_z_velocity` 550 → 420

`BP_DariusCharacter` → `CharMoveComp` → **`JumpZVelocity`**。
跳高公式 `h = v² / (2g)`，g = 980：

| | JumpZVelocity | 理论跳高 |
| :--- | ---: | ---: |
| 改前 | 550 | **154 cm** |
| **改后** | **420**（UE 默认） | **90 cm** |

其余正常：`gravity_scale = 1.0`、`air_control = 0.35`、`jump_max_hold_time = 0`（长按不会持续上升）、
`jump_max_count = 1`、`IA_Jump` 是 BOOLEAN + Pressed 触发（不会每帧重复触发）。

#### 顺带核实：角色没有陷进地板

地面 `TrainingGround_Floor` 是个**平面**（extent_z = 0）⇒ 顶面 z = 0。
角色胶囊 半径 45 / 半高 125，actor z = 127.2 ⇒ **胶囊底 z = 2.2cm** ✓ 正常站立。
鞋底 ≈ 10.2cm ⇒ **角色悬空约 10cm**（就是 §9.3 那条遗留），不是陷地。

### 9.5 复现 / 回退命令

```
# 披风物理：挂物理资产（PIE 外执行）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/cape_04_save.py

# 重建待机（LB_FRAME 决定站姿来源帧；BREATH 设 0 即不呼吸）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/idle_20_build2.py

# 握斧方式（BLADE_DOWN / GRIP_FROM_HEAD_CM / PALM_PULL_CM 三个常量；幂等）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/axe_42_tune.py

# 跳高（JumpZVelocity）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/jump_02_fix.py

# 斧头几何复核（PIE 内；第一次调用会起 PIE，隔 20 秒再调一次读结果）
uv run --no-project python Scripts/ue_remote.py Scripts/anim/axe_43_verify.py

# 斧刃改回原始朝向：BLADE_DOWN=False，或把 hand_rSocket 填回
#   rot=(-106.334, -70.982, 9.342)  loc=(0.18965, 0.10080, 0.00982)
```

### 9.3 已知遗留

1. **待机与走路的鞋底都悬空 ~8 cm**（网格最低点 +0.082 / +0.077 m；bind pose 鞋底在 +3.8cm）。
   这是 `Walk_Layered` 腿长比例不匹配留下的，修法二选一（整体高度偏移 vs 支撑脚 IK），**待定**。
2. `Walk_Layered` 的站姿本身很宽（71~119cm），待机跟着宽。
3. 披风物理需要在正常帧率下确认。

## 10. 脚本归档

一次性探针 11 个已移到 `Scripts/archive/`（`axw_01/02/04/05/06/07/08/09/09b/13/14`），
顶层只留 8 个现役。⚠️ `archive/axw_05_capture.py` 是「在 slate post-tick 回调里销毁 actor 崩编辑器」的
反面教材，别照抄。
