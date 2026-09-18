# 会话交接文档 —— LOL → 2XKO 动画重定向

> 生成时间：2026-09-18 22:40 GMT+8
> 上一会话工作区：`E:\UE\Fight`
> 交接原因：上下文过长，另开新会话继续
> **本文件是临时性的进度快照，不是长期文档。任务走完后请删除或归档。**

---

## 0. 一句话现状

**M1-② 走到一半：UE 侧的 IK Rig ×2 + IK Retargeter 已全部建成并落盘（链映射 9/9 成功），但因为一次编辑器崩溃，46 个源动画还没导入 UE，批量重定向一次都还没跑过。**

编辑器当前**未运行**（崩溃后未重启）。需要先启动它。

---

## 1. 立刻要做的三件事

### ① 启动 UE 编辑器（人工或脚本）

```bash
E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe "E:/UE/Fight/Fight.uproject"
```

等编辑器完全加载（含资产注册表扫描），再用 `ue_remote.py` 连。可用性检测：

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"; cd E:/UE/Fight
netstat -ano 2>/dev/null | grep -E "8000"   # unreal-mcp 端口在听 = 编辑器就绪
```

### ② 补导入 46 个源动画

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"; cd E:/UE/Fight
uv run --no-project python Scripts/ue_remote.py Scripts/ik_01_import_source.py
```

已验证过这个脚本能产出 48 资产（1 Skeleton + 1 Mesh + 46 AnimSequence），
但**上次崩溃前没落盘**（rename 干扰 + 崩溃）。本版已去掉 rename。

### ③ 跑批量重定向（先 2 个动作验证链路）

```bash
uv run --no-project python Scripts/ue_remote.py Scripts/ik_11_batch_retarget.py
```

默认只跑 `run` / `idle1`。**先看这 2 个动作是否正确，再放开全量 46 个。**

---

## 2. 资产状态表（实测于 22:40）

| 资产 | 路径 | 状态 |
|---|---|---|
| `IK_LOL_Source` | `/Game/Character/Darius/Retarget/` | ✅ 已落盘（59 骨 / 9 链 / root=`Root`） |
| `IK_Darius_Target` | 同上 | ✅ 已落盘（309 骨 / 29 链 / root=`pelvis`） |
| `RTG_LOL_to_Darius` | 同上 | ✅ 已落盘（5 个默认 op / **9-9 链已映射**） |
| `SK_LOL_Darius_Skeleton` + `SK_LOL_Darius` | `/Game/Character/Darius/LOL_Source/` | ✅ 已落盘 |
| **46 个源动画** | `/Game/Character/Darius/LOL_Source/` | ❌ **未落盘，需用 ik_01 补导入** |
| 10 个历史动画 | `/Game/Character/Darius/Anims/` | ⚠️ **bind pose 已损坏，待处理** |

源 FBX 产物：`Saved/Retarget/Clean/Darius_SrcClean.fbx`（59 骨 / 46 动作 / 30fps / 25.77 MB）

---

## 3. 完全打通的链路（不用重试，直接复用）

9 条链的映射关系（已实测成功）：

| 链名 | 源 | 目标 |
|---|---|---|
| `Spine` | `Spine1 → Spine2` | `spine_01 → spine_03` |
| `Neck` / `Head` | 单骨链 | 单骨链 |
| `LeftLeg` / `RightLeg` | `L/R_Hip → L/R_Foot` | `thigh_l/r → foot_l/r` |
| `LeftArm` / `RightArm` | `L/R_Shoulder → L/R_Hand` | `upperarm_l/r → hand_l/r` |
| `Left/RightClavicle` | 单骨链 | 单骨链 |

### 关键 API 用法（UE 5.8，四步缺一不可）

```python
# 1. 建 IK Rig（Enum 参数在前！）
ctrl = unreal.IKRigController.get_controller(rig)
ctrl.set_skeletal_mesh(mesh)
ctrl.set_retarget_root(unreal.Name("Root"), 0)          # 需 solver_index
ctrl.add_retarget_chain(name, start_bone, end_bone, goal_name)   # 4 个参数
ctrl.apply_auto_generated_retarget_definition()          # 目标侧专用

# 2. 绑定到 Retargeter（枚举在前！）
rctrl = unreal.IKRetargeterController.get_controller(rtg)
rctrl.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
rctrl.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)

# 3. ★ 必须先加 op 栈，否则 auto_map_chains 静默失效
rctrl.add_default_ops()

# 4. 才能映射（2 个参数）
rctrl.auto_map_chains(unreal.AutoMapChainType.EXACT, False)
```

---

## 4. 会再踩的坑（上一会话实测，已固化进 AGENTS.md §3.5 / §5）

| # | 坑 | 后果 | 规避 |
|---|---|---|---|
| 1 | **没加 op 栈就 `auto_map_chains()`** | 返回 `None`、映射 0、**不报任何错**（卡了两轮） | 先 `add_default_ops()` |
| 2 | **把 `list_assets()` 的返回值直接喂给 `rename_asset()`** | `EXCEPTION_ACCESS_VIOLATION`，**编辑器整个崩溃** | 一律 `pkg = a.split(".")[0]` |
| 3 | **`rename_asset()` 未 save** | 返回 `True` 但没改名（效果不落盘） | 源资产不改名，输出名交给 batch retarget 的 `search`/`replace` |
| 4 | **脚本 docstring 里写自己的文件名（含 `.py`）** | `ue_remote.py` 传内容时 UE 误判为路径，**整个脚本静默不执行** | 已在网关层修复；仍建议别在 docstring 写 `.py` |
| 5 | **Blender 导出 FBX 前未复位 rest pose** | bind pose 全错（实测关节间距偏 **15.4%**） | 4 个历史脚本已修；**不要用 `Batch/` `V3/` `V4/` 里的旧 FBX** |
| 6 | **纯骨架 FBX 导入 UE** | 产出 0 资产、不报错 | 必须带一个 SkeletalMesh 作载体 |
| 7 | **`unreal.Rotator` 位置参数顺序 = `(roll, pitch, yaw)`** | 相机朝向全错 | 一律用关键字参数 |

---

## 5. 未决项 / 待评估

1. **`Spine` 链骨数不等**：源 2 骨（`Spine1→Spine2`）vs 目标 3 骨（`spine_01→spine_03`）。
   需要评估是否要改成 `spine_01 → spine_02` 对齐，或让 Chain Scaling 处理。
2. **10 个历史动画**（`Anims/`）基于损坏的 bind pose，需要决定：删除 / 用新产物覆盖。
3. **比例补偿量未定**：按定稿计划，先在 Retarget Pose 里对齐站姿，
   **仅当实测膝间距比偏差 > 10% 才加偏移**，幅度反解而非手填。
4. **根 `MEMORY.md` §5.1 的「源面朝 +Y / −Y」冲突未敲定**。
   上一会话三个物理锚点测出 **−Y**，只有骨名命名支持 +Y。
   列为 M0 行动项：源/目标同场景、同侧相机渲染正背面，一次敲定。
   **敲定前不要依赖那一栏做符号推断。**
5. **`CharacterMesh0.anim_class` 仍是 `ABP_Unarmed`**（骨架不匹配），阶段 6 要换成 `ABP_Darius`。

---

## 6. 工具改进待办（用户 22:40 提出）

**写一个 Deno 脚本自主启动 / 关闭 UE 编辑器 + 就绪轮询。**
动机：本轮编辑器崩溃后必须人工重启；每次改脚本—跑验证的循环都被这个打断。
建议形态（`Scripts/editor.deno.ts`）：

```
deno task editor:up     # 启动 + 轮询 8000 端口直到就绪
deno task editor:down   # 优雅退出（先试 ue_remote 请求退出，超时再杀进程）
deno task editor:status
```

注意点：
- 启动后**必须等资产注册表扫描完**（`unreal-mcp` 8000 端口在听 ≠ 资产已加载），
  建议轮询时用一次 `unreal.load_asset(<已知资产>)` 探针确认。
- 关闭要区分「优雅退出」与「崩溃后强杀」（后者不带保存，会丢未存资产）。
- **不要**在编辑器有未保存资产时强杀。

---

## 7. 里程碑与门禁（来自定稿计划）

定稿计划全文：`Docs/Retarget/FINAL_Retarget_Plan.html`

**里程碑**：M0 尺子与基线(0.5d) → **M1 垂直切片 idle+run(3.5d)** → M2 全量动作与风格(4d)

**当前在 M1 内部**：
- ✅ M1-① 源骨架净化（`Docs/Retarget/M1-1_Source_Clean_Report.html`）
- ✅ M1-② 第 1 步 修历史脚本 FBX 导出（`Docs/Retarget/FBX_Export_Fix_Report.html`）
- ⏳ M1-② 第 2 步 UE 侧 IK Rig / Retargeter —— **主体完成，批量重定向待跑**
- ⬜ M1-③ Retarget Pose 标定
- ⬜ M1-④ 比例补偿 + 去倾斜 + 步幅闭环
- ⬜ M1-⑤ ABP_Darius 落地

**门禁 G1~G7**（一票否决）：G1 朝向 / **G2 关节世界位置误差（主判据）** / G3a 支撑相脚滑 <2cm /
**G3b 隐含速度 vs `MaxWalkSpeed` 误差 <5%** / G4 视线（只约束慢变基线 + 相对躯干偏置标准差 <4°）/
G5 生理限位且幅度保留 ≥85% / **G6 融合平滑（角速度连续、峰值 <600°/s）** / G7 双手握斧 ≤2cm + 无穿模

---

## 8. 工程卫生（每次都遵守）

- 关卡基线 actor **只有 7 个**，任何脚本跑完必须清理临时 actor 回到基线
- 临时 UE 资产清理：`uv run --no-project python Scripts/ue_remote.py Scripts/plan_99_clean_temp.py`
- **交付物禁止放 `Saved/`**（`.gitignore` 含 `Saved/*`）⇒ 报告放 `Docs/<主题>/`
- 改资产前先备份到 `Saved/Backup_*/`
- 代码规范：Python 走 `uv`，JS/TS 走 `deno`

## 9. Git 状态

`main` 领先 `origin/main` **5 个提交（未推送）**，工作区干净。

```
09fad41  feat(retarget): M1-② 第 2 步 —— UE 侧 IK Rig x2 + IK Retargeter 建成（9/9 链已映射）
424ecad  fix(retarget): 修复 4 个重定向脚本的 FBX 导出 bind pose 污染（偏差 15.4% -> 5.9e-07）
0198357  feat(retarget): M1-① 源骨架净化完成（179→59 骨）+ 修三个静默毁交付的陷阱
166a1d6  docs(memory): 记录 git 检查点、目录红线二次复发的自查，以及朝向一栏待复核项
719958f  feat(darius): 修复战斧手持显示 + 重定向方案定稿（动手前检查点）
```

随时可 `git reset --hard 09fad41` 回到当前检查点。
