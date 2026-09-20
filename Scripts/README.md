# Scripts —— 脚本库索引

> 2026-09-20 重构：按主题分目录；删掉 101 个一次性 UE API 探针（清单见 `archive/_deleted_step_probes.md`）。
> 删除前的完整快照：`Saved/_backup_scripts_20260920_165857.zip`（本地备份，不进 git）。

## 三条铁律

1. **UE 侧一律走 `ue_remote.py`**（唯一网关，UDP 发现 + TCP 执行）。
2. **Python 一律 `uv run --no-project python <脚本>`**。
3. **Bash 工具的 PATH 残缺** —— 每条命令前加 `export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"`。

## 目录结构

| 目录 | 内容 | 代表脚本 |
| :--- | :--- | :--- |
| **（顶层）** | 入口 / 运维工具，**别移走**（全员按这个路径在用） | `ue_remote.py`（★ 网关）、`ue_mcp.py`（内置 MCP 客户端）、`editor.deno.ts`（启停编辑器，`deno.json` 引用）、`editor_dialog.py`（关模态框）、`editor_focus.py`（窗口前置）、`disable_throttling.py` |
| **`retarget/`** | LOL → 2XKO 重定向管线：IK Rig / Retargeter 标定、逐骨偏移实验回路、离线验收 | `ik_36_calibrate_retarget_pose`、`ik_37_verify_orientation`（★ 朝向验收器）、`ik_60_contact_audit`（★ 接触/落点审计）、`exp_cycle`（实验回路驱动器）、`blender_51_retarget_v4`、`plan_13/16/17` |
| **`anim/`** | 动画资产的生产与验收：分层合并、待机、披风、战斧、行走移动体验、跳跃、渲染检查 | `axw_10_merge`（★ 上/下半身分层合并器）、`axw_17_phase`（步态相位/接缝复核）、`loco_02_tune_character`（★ 相机阻尼与 CMC 动力学调参）、`loco_03_tune_blendspace`（★ 混合空间速度轴适配）、`loco_04_pie_verify`（★ PIE 动力学测量探针）、`loco_05_cleanup`（关卡清理）、`cape_35_build_and_bind`（★ 披风布料 Dataflow 绑定）、`cape_33_cloth_probe`（★ 布料 PIE 探针）、`idle_20_build2`、`axe_42_tune`（握斧调参）、`jump_02_fix` |
| **`dcc/`** | Blender 侧工具（无头执行） | `blender_23_strip_cape_shell`（★ 剔披风描边壳）、`blender_04_render`（预览渲染）、`blender_22_strip_all`（剔斧头几何）、`blender_split_weapon`、`blender_80_orient_verify` |
| **`asset/`** | 资产解包 / 导入 | `extract_godking_assets`（一键解包全套 LOL 资产）、`import_weapon_asset`、`glb_list_anims` |
| **`core/`** | 工程维护 | `plan_99_clean_temp`（清临时 actor 与 `/Game/Temp*`） |
| **`archive/`** | **踩坑过程的证据链**，不是死代码 | 见 `archive/README.md`；子目录 `audio/ retarget/ anim/ ue_api/ misc/` |
| `tools/`、`darius_extracted/` | 第三方二进制与解包中间产物 | **已 gitignore** |

## 常用命令

```bash
# 编辑器
deno task editor:up -- --hold        # 启动（停这个后台任务 = 杀编辑器）
deno task editor:status
uv run --no-project python Scripts/editor_dialog.py --auto      # 卡模态框时

# 跑一个 UE 侧脚本
uv run --no-project python Scripts/ue_remote.py Scripts/anim/axw_16_final.py

# 跑一个 Blender 脚本
"<Blender 5.2>" -b -P Scripts/dcc/blender_04_render.py -- <FBX> <OUTDIR> <LABEL>
```

## 关键技术笔记（历史沉淀，值得复用）

### 武器分离与挂接 SOP

1. **DCC**：`dcc/blender_split_weapon.py` 切分网格并**重定义握持原点**
   （算武器局部 bounds，把 pivot 平移到手柄约 35% 处，挂到 `hand_rSocket` 时天然贴合掌心）。
2. **UE 资产化**：`asset/import_weapon_asset.py` 导入 `SM_Darius_GodKing_Axe`，
   自动加简化碰撞 + 3 个打击判定 socket（`Blade_Tip` / `Blade_Edge` / `Pommel`）+ 绑材质实例。
3. **骨骼挂接**：在 `SK_Darius_GodKing` 的 `hand_r` 下建 `hand_rSocket`，设定握持朝向补偿。
   ⚠️ socket 的 `relative_scale` 必须是 **0.01**（抵消骨架最外层 100× 缩放）。
4. **隐藏原模**：`SK_Darius_GodKing` 材质槽 7（原地面斧头）指向全透明 Masked 材质 `M_Invisible`；
   描边壳（槽 0）里的斧头副本要用 `blender_22_strip_all.py` 从几何上剔除（材质挡不住）。
5. **蓝图挂载**：`BP_DariusCharacter` 里加 `StaticMeshComponent`，Attach 到 `hand_rSocket`。

### `ue_remote.py` 的两个坑

- **脚本内容里出现 `xxx.py` 字样** ⇒ UE 会把整段内容误判成文件路径，**静默不执行**。
  `ue_remote.py` 已修（先落盘再传路径），但**写脚本时别在 docstring 里写自己的文件名**。
- **PIE 期间** `EditorAssetLibrary.load_asset` 会被拒（`The Editor is currently in a play mode`），
  但 `unreal.load_object` / `unreal.find_object` 照常可用；`save_asset` 会返回 False。

### 编辑器运维

- **世界 tick 由 Realtime 视口的绘制驱动**：窗口被遮挡/最小化 ⇒ 世界不 tick ⇒
  `SceneCapture2D.capture_scene()` 产出**姿势完全相同的假帧**（md5 全同）。
  `disable_throttling.py` 治不了（那不是节流问题）。判据：`get_game_time_in_seconds()` 是否前进。
- **Slate 模态框会阻塞游戏线程** ⇒ Remote Execution 完全无响应，现象像「编辑器没起来」。
  `editor_dialog.py --auto`：先 `PostMessage WM_CLOSE`（Esc 对部分 Slate 框无效）。
- **别在 slate post-tick 回调里 `destroy_actor`** —— 会 `EXCEPTION_ACCESS_VIOLATION` 崩编辑器。

## 历史

- `archive/README.md` —— 归档规则与分类说明
- `archive/_deleted_step_probes.md` —— 2026-09-20 删除的 101 个一次性探针清单（含各自在探什么）
- 过程日志：`.workbuddy/memory/YYYY-MM-DD.md`；长期约束：`.workbuddy/memory/MEMORY.md`
