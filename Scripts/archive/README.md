# Scripts/archive —— 一次性诊断/探针/旧版脚本归档

> 2026-09-19 整理。**这里的东西不是死代码，是「踩坑过程的证据链」**：
> 每个编号脚本对应一次排查实验，坑的结论都已经沉淀进 `AGENTS.md` / `.workbuddy/memory/MEMORY.md`。
> 要查「某一步当时是怎么做的、为什么」再来翻；**不要直接在 archive 里继续开发新功能**。

## 什么会进 archive
- `diag_* / probe_* / inspect_* / check_* / test_*`：UE API 探查、状态诊断（用完即弃）
- `fix_* / restore_* / save_* / set_* / setup_*`：一次性修复动作（结论已验证并固化）
- `shot_* / capture_* / play_* / take_* / stop_pie`：临时截图/PIE 控制（渲染方案已定稿为 SceneCapture2D）
- `blender_01~08 / 11 / 20 / 21 / 40 / 85`：DCC 侧早期探查与被取代版本
- `ik_02~10 / 12~22 / 24~26 / 28~30 / 32 / 33 / 35 / 38 / 39 / 41 / 44~47 / 49 / 50 / 55~57`：
  重定向管线的诊断与**已被否掉**的路线（补链 ik_55/56、Q 折 offset 等，别再试）
- `anim_01~12 / 42~45`：导入尝试与 tick 诊断
- `axe_*`（除 14/21）：战斧装配排查过程
- `audio_*`：WAD/Wwise 音频解包管线（资产已提取到 `E:\UE\Assets\Darius_GodKing_LOL_Original`；
  `audio_20` import `audio_10`、`audio_21` import `audio_11`，**整族放在一起才能跑**）

## 现役脚本清单（留在 `Scripts/` 顶层）见 `AGENTS.md` §0.3 / §3 与 `Docs/Retarget/HANDOFF.md` §9。
