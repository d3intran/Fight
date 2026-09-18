# Fight 项目 Agent 开发上下文与工程全景 (AGENTS.md)

本文件是为接入本项目的 AI Agent（如 WorkBuddy、Antigravity、Qoder CN 等）定制的全局上下文。接手本项目的 Agent 必须在开启新会话时首先阅读本文档。

---

## 1. 项目基础信息

- **项目名称**: `Fight`
- **引擎版本**: Unreal Engine 5.8
- **工程根路径**: `E:\UE\Fight`
- **主要主关卡**: `/Game/Level/Lv-FIght.umap`
- **代码与脚本**: C++ 模块 (`Source/Fight/`) + 自动化管线工具库 (`Scripts/`)
- **Git 远程仓库**: [d3intran/Fight](https://github.com/d3intran/Fight)（主分支：`main`）
- **开发规范**: 严格遵循用户全局规范（Python 走 `uv`，JS/TS 走 `deno`，杜绝未自验交付，遵守美术尺度与法线防御原则）。

---

## 2. 核心架构与各系统当前落地状态

### 2.1 训练场与视觉基座 (Stellar Blade 风格)
- **关卡**: `/Game/Level/Lv-FIght`
- **科技地砖**: 六边形程序化材质 `M_TrainingGround_Grid`（已去除杂乱环线，调谐为《剑星》风格高质感浅灰，消除刺眼白边）。
- **环境光照**: 远景雾霭虚化地平线，消除死黑。

### 2.2 角色系统：神王 德莱厄斯 (God-King Darius)
- **蓝图类**: `/Game/Character/Darius/Blueprints/BP_DariusCharacter` (基于 `ACharacter`)
- **高模来源**: `2XKO`（原 Project L）次时代写实高模，标准 1:1 物理身高 **2.47 米**。
- **骨骼网格体**: `/Game/Character/Darius/SK_Darius_GodKing` (309 根骨骼，兼容 UE Mannequin 命名规范)。
- **PBR 材质体系**: `/Game/Character/Darius/Materials/`
  - 8 个材质槽位全量绑定（`M_Darius_Master` + 贴图解包 Albedo / MPO 金属粗糙度遮罩 / Emissive）。
  - 肩甲狼头眼睛与胸甲菱石配置了橙红狂怒微光（Emissive）。
  - 原 FBX 自带的地面死斧（Material Slot 7）赋予了透明遮罩材质 `M_Invisible`，原地面重影斧头已被完全隐藏。
- **控制与输入**: 现代 Enhanced Input (`IMC_Default` + `IA_Move`, `IA_Look`, `IA_Jump`)。
- **当前默认状态**: `BP_ThirdPersonGameMode` 的 `DefaultPawnClass` 已设为 `BP_DariusCharacter_C`，点击 Play 直接进入操控。

### 2.3 武器管线：神王战斧 (SM_Darius_GodKing_Axe)
- **静态网格体**: `/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe`（从 2XKO 中通过无头 Blender 脚本剥离，Pivot 对齐至手柄 35% 主握持点）。
- **插槽埋点**: 武器自带 `Socket_Blade_Tip`、`Socket_Blade_Edge`、`Socket_Pommel`，为后续近战 Box Trace 命中判定预留。
- **角色装配**: 在 `BP_DariusCharacter` 中注册 `WeaponAxe` (StaticMeshComponent)，挂接到骨骼的 `hand_rSocket` 上。
- **尺度契约**: `hand_rSocket` 的 `RelativeScale` 设为 `(0.01, 0.01, 0.01)`，用于抵消根骨骼的 100 倍 FBX 换算，确保战斧世界尺寸保持标准 1:1（长约 1.72 米，见 MEMORY.md）。

### 2.4 神王原版资产备用库 (`E:\UE\Assets\Darius_GodKing_LOL_Original`)
从本地《英雄联盟》客户端（`E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.wad.client`）全量解包与格式转换完毕的官方原版资产：
- `Animations_GLB/`: 11 个 GLB（含 46 动作全集成 `darius_skin15_all_anims.glb`，以及 `run`, `run_fast`, `spell1_in_run` [Q], `spell2` [W], `spell3` [E], `spell4` [R] 等独立动作文件）。
- `Audio_SFX/`: 56 个无损 `.wav` 打击/狼嚎/断头台挥斩音效。
- `Audio_VO_zh_CN/`: 225 个无损 `.wav` 神王全套国服中文台词。
- `Audio_VO_en_US/`: 225 个无损 `.wav` 美服英文语音。
- `Particles_VFX/`: 107 个技能特效网格（`.scb`）、贴图与粒子定义。

---

## 3. 自动化与开发工具库 (`E:\UE\Fight\Scripts`)

| 脚本文件 | 作用与使用方式 |
| :--- | :--- |
| **`ue_remote.py`** | **虚幻引擎 Python 远程执行网关**。通过 UDP 组播发现 + TCP JSON 协议，无需插件即可在外部终端向活跃 Editor 发送 Python 代码并捕获日志。`uv run python Scripts/ue_remote.py <script.py>` |
| **`extract_godking_assets.py`** | 一键全量扫描本地 LOL WAD 包，利用 `cdtb` + `lol2gltf` + `vgmstream` 提取并转码动画、音效、中英文语音。 |
| **`blender_split_weapon.py`** | 无头 Blender 5.2 脚本，解绑 FBX、剥离武器网格、计算 Bounds 并将 Pivot 校准至握柄处。 |
| **`import_weapon_asset.py`** | UE Python 脚本，自动化导入 StaticMesh、生成碰撞体、绑定材质并添加判定 Sockets。 |
| **`disable_throttling.py`** | 关闭视口后台节流（`t.IdleWhenNotForeground 0` 等），解决截图冻结假帧问题。 |

---

## 4. 下一阶段开发路线图 (Roadmap for Next Sessions)

1. **相位 2.1：动画特调与 IK 重定向 (IK Retargeting)**
   - 目标：将 `darius_skin15_run.glb` 的单手拖斧动作应用至 `BP_DariusCharacter`。
   - 特调要求：
     - 脊椎俯仰角（Pitch）加性补偿前倾 10°~15°，消除俯视角“望天感”。
     - 开启双腿 Foot IK，脚踏实地，消除 MOBA 步幅滑步。
     - 右臂自然下垂，大斧拖行于身侧。
2. **相位 2.2：攻击连招与打击判定 (Melee Combat & Trace)**
   - 利用战斧上的 3 个 Sockets 进行 Box / Sphere Trace 碰撞扫描。
   - 挂载挥刀刀光拖尾粒子（Ribbon Trail）。
   - 接入普攻（`attack1`）与打击音效（`Audio_SFX`）。
3. **相位 2.3：GAS (Gameplay Ability System) 技能全复刻**
   - 被动：流血（Hemorrhage）1~5 层状态机 + 血怒（Noxian Might）攻击力爆发与狼灵特效。
   - Q技能：大杀四方（Decimate）内外圈双重几何判定。
   - W技能：致残打击（Crippling Strike）普攻重置与减速。
   - E技能：无情铁手（Apprehend）扇形抓取拉回。
   - R技能：诺克萨斯断头台（Noxian Guillotine）飞天狼扑斩杀与刷新机制。
