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
