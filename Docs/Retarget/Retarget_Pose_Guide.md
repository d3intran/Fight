# Retarget Pose 标定 —— 「手脚七歪八扭」的成因与做法

> 2026-09-19 00:55 GMT+8
> 触发：用户反馈重定向产物「人物的手脚七歪八扭」，并问：是我能力不够吗？网上有教程吗？能不能教我手动做？

---

## 0. 先直接回答三个问题

**1. 是不是我没这个能力？**
**不是能力问题，是漏了一步。** 而这一步就写在我们自己的定稿计划里：
`FINAL_Retarget_Plan.html` 的 **M1-③ Retarget Pose 标定**，前面为了先打通链路被跳过了。

四份独立资料（含 Epic 官方文档）**一致**把「Retarget Pose 未标定」列为这类症状的**头号原因**。
原文措辞：*"This is the most consequential setting in the entire workflow... Get this wrong and
everything downstream is subtly broken in a way that **looks like an animation quality problem
rather than a setup problem**."*

**2. 有 skill / 教程吗？**
本机 `~/.workbuddy/skills/unreal-engine-skills` **只有索引（2.4 KB）**，唯一沾边的子技能是
`ue-animation-system`，讲的是状态机 / 混合空间 / 蒙太奇那类**运行时**动画，与骨骼重定向无关 —— 帮不上。
外部资料见 §4。

**3. 能不能手动？**
**能，而且官方明确说这一步的收尾必须人眼。** §3 是完整手动流程，照着点就行。
原因（官方原话）：自动对齐 *"gets you most of the way, but **reviewing it by eye is still the
difference between 'usable' and 'correct'**"*。

---

## 1. 实证：我们已经踩到的那个点

`ik_36_calibrate_retarget_pose.py` 实测读出的 retarget pose 旋转偏移（Target 侧）：

| 骨 | 标定前 | `auto_align_all_bones(Direction)` 之后 |
|---|---|---|
| `upperarm_l` | (−18.9°, **−55.5°**, −35.2°) ≈ **68°** | 几乎没变 |
| `thigh_l` | (−4.6°, **−72.0°**, −6.4°) ≈ **72°** | **明显变了**（+4.0°, −47.8°, +9.1°） |
| `calf_l` | (−20.9°, 52.4°, 42.5°) ≈ 71° | 略变 |
| `spine_01` | ≈ 0 | **新增**（6.9°, −25.7°, 15.3°） |
| **`hand_l`** | **0°** | **仍然是 0°** ← 关键 |
| **`foot_l`** | **0°** | **仍然是 0°** ← 关键 |
| `clavicle_l` / `head` | 0° | 0° |

**后三行就是「手脚扭曲」的直接原因。**

为什么自动对齐修不了它们：`Direction` 方法的原理是**用链里子骨的方向定义本骨朝向**。
而 `hand` / `foot` 是**链尾、没有子骨** ⇒ 定不出方向 ⇒ 偏移留 0。
可这两套骨架的手/脚局部轴本来就不同（上一轮实测：源与目标的前臂差 **39°**、锁骨 **43°**、
骨盆-胯 **41°**）。偏移为 0 就等于「假装它们一样」，于是手腕脚踝被拧成麻花。

⇒ **链尾关节必须单独处理**。这正是官方流程里「Auto Align 之后还要 Reset / Align Selected」的意义，
不是可选步骤。

---

## 2. 为什么这一步最容易被跳过

因为它**不报错**。

姿势不匹配时：重定向照跑、帧数照对、骨名照对应、脚也不穿地 —— 只有**朝向**是错的。
而我们之前所有的脚本验收（骨名对上 / 帧数相等 / 平移比值 1.00 / 缩放 100）**全都量不到朝向**。

这是本轮最该记住的一条：**「几何位置对了」不等于「姿势对了」**。
`AGENTS.md` §0.1 早就写了「相信数据，禁止主观臆断」，但我把「数据」窄化成了位置。

---

## 3. 手动流程（照着点）

### 3.1 进入姿势编辑模式
1. 打开 `/Game/Character/Darius/Retarget/RTG_LOL_to_Darius`
2. 工具栏把模式从 **Run Retargeter** 切到 **Edit Retarget Pose**（视口出现蓝色边框）
3. 面板切到 **Target** 一侧

### 3.2 自动对齐（先做，拿到大部分）
4. `Pose` 下拉 → **Auto Align** → **Align All Bones**
   - Alignment Method 选 **Direction**（= API 的 `CHAIN_TO_CHAIN`）
   - 该操作**会先重置** retarget pose 再对齐，是**非破坏性**的（改的是 Retarget Pose，不是 Bind Pose）

### 3.3 单独修链尾 ★ 这一步才是关键
5. 层级面板先把过滤器设为 **Hide Bones Not in a Chain**，方便找
6. 依次选 `hand_l` → `hand_r` → `foot_l` → `foot_r`
7. `Pose` → **Auto Align** → **Align Selected**，方法**依次试**：**Mesh** → **Local Rotation Axes** → **Global Rotation Axes**
   （`Mesh` 用顶点权重推方向，对没有子骨的末端最可能有效）
8. 若还不理想：**直接在视口里旋转该骨**，转到与源骨架对应骨朝向一致为止
9. 满意后 `Pose` → **Set Current Pose as Retarget Pose** 固定下来

### 3.4 脚与地面
10. 确认脚朝向无误后，`Pose` → **Snap Character to Ground**
    ⚠️ **不要传空骨名** —— 我实测传空串会让编辑器直接崩（`EXCEPTION_ACCESS_VIOLATION`）

### 3.5 左右互为镜像
11. 一侧调好后，另一侧**直接抄同一组数值**（左右骨骼轴向通常是镜像关系），比再调一遍准

### 3.6 重导出
12. **改完 retarget pose，之前导出的动画全部作废**（导出的是快照）⇒ 必须重跑批量重定向
    （`Scripts/ik_11_batch_retarget.py` → `Scripts/ik_31_fix_root_scale.py`）

### 3.7 一边调一边验
13. 在 Retargeter 的 Asset Browser 里双击源动画实时预览；
    把 `Retarget Pose Blend` 拉到 0/1 对比，能立刻看出是哪几根骨被改了

---

## 4. 参考来源

| 来源 | 要点 |
|---|---|
| [Epic 官方：IK Rig Retargeting](https://docs.unrealengine.com/ik-rig-animation-retargeting-in-unreal-engine/) | Retarget Pose 面板全部工具的定义：Auto Align 的四种 Alignment Method、Reset 的三种范围（Selected / Selected and Children / All）、Snap Character to Ground、Retarget Pose Blend |
| [StraySpark：Animation Retargeting 完整指南](https://www.strayspark.studio/blog/unreal-engine-animation-retargeting-ik-rig-complete-guide) | **「A-pose vs T-pose 是最致命的设置」**；四大失败模式表（手臂角度错 = 姿势不匹配 / 穿地 = root 与比例 / 手指僵 = 链没映射 / 位移消失 = root motion）；「导出后改 retarget pose，旧产物不更新」 |
| [Cosindra：UE5 IK Retargeter 指南](https://cosindra.ai/guides/ue5-ik-retargeter) | 同上，强调*"Edit the retarget pose until both skeletons match visually"* |
| [UE 论坛：fix for twisted feet](https://forums.unrealengine.com/t/fix-for-twisted-feet/2721385) | 脚部扭曲的常见成因与排查顺序；脚链终点、Translation Mode 改 Globally Scaled |
| [UE 论坛：IK bones not following the source](https://forums.unrealengine.com/t/ik-bones-are-not-following-the-source-when-i-retarget/2323930) | **Auto Align All Bones 之后必须手工 Reset Selected Bone and Its Children 保住脚的角度** —— 与我们的判断一致 |
| [CSDN：UE5 动画重定向实战](https://blog.csdn.net/weixin_34259232/article/details/90195862) | 「腿部或手臂扭曲成麻花 = 骨骼轴向不一致」；改 Rotation Mode / Static Offset；把无关骨加入 Excluded Bones 防抖 |

---

## 5. 我能自动化的部分（API 已全部探明）

`unreal.IKRetargeterController`（共 80 个接口）里可用的：

| 用途 | 调用 |
|---|---|
| 自动对齐全部 | `auto_align_all_bones(source_or_target, method)` |
| 自动对齐选定 | `auto_align_bones(source_or_target, [骨名], method)` |
| 读/写单骨偏移 | `get_rotation_offset_for_retarget_pose_bone(骨名, source_or_target)` / `set_rotation_offset_for_retarget_pose_bone(骨名, quat, source_or_target)` |
| 姿势管理 | `get_current_retarget_pose_name(side)` · `create_retarget_pose` · `duplicate_retarget_pose` · `remove_retarget_pose` · `rename_retarget_pose` |
| 贴地 | `snap_bone_to_ground(骨名, source_or_target)`（**骨名不能为空串**） |
| root 偏移 | `get_root_offset_in_retarget_pose` / `set_root_offset_in_retarget_pose` |

对齐方法枚举：`unreal.RetargetAutoAlignMethod = { CHAIN_TO_CHAIN, LOCAL_ROTATION_AXES, GLOBAL_ROTATION_AXES, MESH_TO_MESH }`

**所以「自动对齐 + 逐骨写偏移」是完全可以脚本化的**，
唯一需要人眼的是：**判断"对齐得对不对"**。

---

## 6. 为什么最后仍需要人眼（不是我推卸）

官方与第三方都指向同一句：自动对齐能把你带到 80%，剩下的 20% 是
*"the difference between 'usable' and 'correct'"* —— 而这个差别**没有客观真值**，
因为两套骨架的手指/脚趾骨骼数量与朝向本就不是一一对应的。

**但可以把它变成可量的**：我准备了朝向验收器 `ik_37_verify_orientation.py`
（逐关节比较源与产物的「关节连线方向」夹角，判据用 `FINAL_Retarget_Plan` 的 G1：
**均值 < 8° / P90 < 20° / max < 35°**）。
它有两个作用：① 把「调好了没」变成数字；② **指出哪几根骨最需要修**，让手动调整有的放矢。

> ⚠️ `ik_37` 首次运行触发了编辑器崩溃（`EXCEPTION_ACCESS_VIOLATION`），
> 发生在 `ik_36` 的 `snap_bone_to_ground("")` 之后 —— 怀疑是空骨名把 retargeter 内部状态搞坏了。
> 重启后再跑一次即可判断是「上一步的后遗症」还是 `ik_37` 自身的问题。

---

## 7. 建议路线

1. **先按 §3 手动走一遍**（唯一能立刻见效的办法，而且你眼睛在现场）
2. 我同步把 `ik_37` 朝向验收器跑通，用它定位最差的几根骨
3. 再决定「手工微调」还是「脚本化迭代对齐 + 验收器闭环」
4. 都通过后再重跑批量重定向（改过 retarget pose，旧产物已作废）

---

## 8. 另外三个会加剧「扭曲感」的已知问题（不是本次主因，但要知道）

| # | 问题 | 后果 |
|---|---|---|
| 1 | **20 条目标链没有源对应**：源 IK Rig 只有 **9 条链**，目标有 **29 条** | **十根手指 + 脚趾完全没被驱动**，会僵在 rest 姿势。手指出问题在近景里极显眼 |
| 2 | **24 根 twist 骨 + ~150 根面部骨 + 4 根 `camera_*`** 既不在链里、也没列入 Excluded Bones | 可能产生不可预测的抖动（CSDN 那篇明确提到要加 Excluded Bones） |
| 3 | **`Spine` 链 2 骨 vs 3 骨**（源 `Spine1→Spine2`，目标 `spine_01→spine_03`） | 躯干可能引入额外偏差，尚未量化 |
