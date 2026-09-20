# Scripts/archive —— 一次性诊断/探针/旧版脚本归档

> 2026-09-19 建立，**2026-09-20 按主题分了子目录**。
> **这里的东西不是死代码，是「踩坑过程的证据链」**：
> 每个编号脚本对应一次排查实验，坑的结论都已经沉淀进 `AGENTS.md` / `.workbuddy/memory/`。
> 要查「某一步当时是怎么做的、为什么」再来翻；**不要直接在 archive 里继续开发新功能**。

## 子目录（2026-09-20 起）

| 目录 | 内容 | 数量 |
| :--- | :--- | ---: |
| `audio/` | WAD/Wwise 音频解包管线（**整族必须放一起**：`audio_20` import `audio_10`、`audio_21` import `audio_11`） | 12 |
| `retarget/` | 重定向管线的诊断与**已被否掉**的路线（补链、Q 折 offset 等，别再试）+ Blender 早期版本 | 62 |
| `anim/` | 动画导入/渲染/截图的早期尝试、战斧装配排查、本轮分层合并的探针 | 78 |
| `ue_api/` | UE Python API 探查与状态诊断（`inspect_* / fix_* / diag_* / probe_* / check_* / test_* / shot_*`） | 113 |
| `misc/` | 其余 | 3 |

⚠️ 子目录里的脚本**路径引用已失效**（脚本本身没改，只是搬了位置）—— 要用请先看它的常量再改。

## 什么会进 archive
- `diag_* / probe_* / inspect_* / check_* / test_*`：UE API 探查、状态诊断（用完即弃）
- `fix_* / restore_* / save_* / set_* / setup_*`：一次性修复动作（结论已验证并固化）
- `shot_* / capture_* / play_* / take_* / stop_pie`：临时截图/PIE 控制（渲染方案已定稿为 SceneCapture2D）
- `blender_01~08 / 11 / 20 / 21 / 40 / 85`：DCC 侧早期探查与被取代版本
- `ik_02~10 / 12~22 / 24~26 / 28~30 / 32 / 33 / 35 / 38 / 39 / 41 / 44~47 / 49 / 50 / 55~57`：
  重定向管线的诊断与**已被否掉**的路线（补链 ik_55/56、Q 折 offset 等，别再试）
- `anim_01~12 / 42~45`：导入尝试与 tick 诊断
- `axe_*`（除 14/21）：战斧装配排查过程
- `axw_01/02/04/06/07/08/09/09b/13/14`：上下半身分层合并（2026-09-20）的 UE API 探查、导入来源、
  轨道/层级 dump、全骨差异、FBX 导出、材质槽自检 —— 结论已沉淀进 `AGENTS.md` 与
  `Docs/Locomotion/AxeWalk_Layered_Merge.md`
- ⚠️ `axw_05_capture.py`：**「在 slate post-tick 回调里销毁 actor」会 EXCEPTION_ACCESS_VIOLATION 崩编辑器**。
  留作反面教材，别照抄那个 `cleanup()`。
- `idle_01~14 / idle_21~23`、`cape_01~03 / cape_10~14`、`axe_30 / 32 / 33`：
  待机重建 + 披风物理 + 斧刃朝向的探针（2026-09-20 下午）。结论已沉淀进
  `Docs/Locomotion/AxeWalk_Layered_Merge.md` §9 与 `.workbuddy/memory/2026-09-20.md`。
  ★ 其中 **`idle_22_legcheck2.py` 的「锁骨线自校准」量法**值得复用 —— 直接拿 actor 轴量腿会量错。
- `audio_*`：WAD/Wwise 音频解包管线（资产已提取到 `E:\UE\Assets\Darius_GodKing_LOL_Original`；
  `audio_20` import `audio_10`、`audio_21` import `audio_11`，**整族放在一起才能跑**）

## 现役脚本清单（留在 `Scripts/` 顶层）见 `AGENTS.md` §0.3 / §3 与 `Docs/Retarget/HANDOFF.md` §9。
