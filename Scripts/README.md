# UE5 Fight 项目自动化与管线脚本库 (Scripts)

本目录汇总了在虚幻引擎项目（God-King Darius 角色接入与武器管线处理）中开发与沉淀的高价值自动化脚本，供后续学习、复用与参考。

---

## 核心管线脚本 (Core Pipeline)

### 1. `blender_split_weapon.py`
- **功能**: 无头（Headless）Blender 脚本，自动从合体/绑骨角色 FBX 中提取武器网格。
- **关键技术**:
  - `bpy.ops.import_scene.fbx`: 无界面导入复杂模型。
  - 网格分离与 LOD 筛选: 识别武器子网格（`LOD0.007`）并解除与骨骼的硬绑定。
  - **旋转轴心重校准 (Pivot Calibration)**: 默认导出的模型轴心往往在原点或脚底。该脚本计算武器局部 Bounds，自动将 Pivot 平移对齐至主手握持点（手柄约 35% 黄金分割处），使挂接到角色 `hand_rSocket` 时天然贴合掌心。
  - **坐标系转换**: Blender `+Z Up` 转虚幻引擎标准坐标系（厘米制、法线重计算与变换应用）。
  - **无头执行方法**:
    ```bash
    blender -b -P blender_split_weapon.py -- <FBX_IN> <FBX_OUT>
    ```

### 2. `import_weapon_asset.py`
- **功能**: 虚幻引擎内 Python 资产自动化导入与配置。
- **关键技术**:
  - 使用 `unreal.FbxFactory` 与 `unreal.AssetImportTask` 程序化导入 FBX。
  - 自动创建 StaticMesh 碰撞体（Simplified Collision）。
  - **程序化插槽添加 (Sockets)**: 通过 `unreal.StaticMeshSocket` 自动在武器 StaticMesh 上添加刀刃尖端（`Socket_Blade_Tip`）、刀刃中段打击点（`Socket_Blade_Edge`）和握柄底部（`Socket_Pommel`），为后续近战攻击判定（Trace/Hitbox）做好数据准备。
  - 自动绑定材质实例 `MI_Darius_Axe`。

### 3. `ue_remote.py`
- **功能**: **轻量级虚幻引擎 Python 远程执行网关**。
- **原理与机制**:
  - 无需安装第三方 HTTP 插件，利用 UE 内置的 `Python Remote Execution` 协议。
  - 发送 UDP 组播广播（Multicast 239.0.0.1:6766）寻找活跃的 Editor 实例节点。
  - 建立 TCP Socket，以 JSON 协议发送 Python 代码字符串并在 GameThread 上无缝执行，捕获标准输出和异常。
  - **使用方式**:
    ```bash
    python Scripts/ue_remote.py "import unreal; print(unreal.EditorLevelLibrary.get_editor_world().get_name())"
    ```

---

## 视口与渲染调试脚本 (Viewport & Diagnostics)

### 4. `disable_throttling.py`
- **痛点解决**: 当 UE 处于后台时，编辑器视口默认会降低帧率甚至冻结渲染缓冲区（`HighResShot` 抓取到的帧 md5 完全一致，出现“假连续帧”）。
- **执行命令**:
  - `t.IdleWhenNotForeground 0` (后台不节流)
  - `r.Editor.Viewport.Throttle 0`
  - `Editor.bThrottleWhenHidden 0`
  - 将所有 Viewport 客户端置为 `Realtime=True`。

### 5. `shot_showcase_frontal.py` / `capture_axe_in_hand.py`
- **机位与构图推导**:
  - 在 UE 中，`CharacterMesh0` 的默认相对旋转通常为 `Yaw = -90°`（以面向正 X 轴）。
  - 该脚本演示了如何使用几何推导计算摄影机世界坐标与 `LookAt` 俯仰角，自动对焦角色上半身、右手握持的战斧刃面与材质发光细节，完成自验抓图。

---

## 快速回顾：诺手武器分离流程 SOP
1. **DCC 阶段**: 使用 `blender_split_weapon.py` 切分网格并重新定义手柄握持原点。
2. **UE 资产化**: 通过 `import_weapon_asset.py` 导入 `SM_Darius_GodKing_Axe`，附加 3 个打击判定 Socket。
3. **骨骼挂接**: 在 `SK_Darius_GodKing` 骨骼的 `hand_r` 骨骼下创建 `hand_rSocket`，设定初始握持朝向补偿。
4. **原模型隐藏**: 在 `SK_Darius_GodKing` 的 Material Slot 7（原地面斧头网格）赋予全透明 Masked 材质 `M_Invisible`，原地面斧头完全消失。
5. **角色蓝图挂载**: 在 `BP_DariusCharacter` 中添加 `StaticMeshComponent`（武器），Attach 到 `hand_rSocket`。
