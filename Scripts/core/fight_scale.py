"""Fight 项目 scale=100 契约的唯一常量源。

== 这个 100 是什么 ==
LoL 源资产是米制，UE 是 cm。导入器把 100x 的换算**全部压在骨架最外层骨**
`darius_godking_mesh_LOD0_Skeleton` 的 scale 上，因此：

    - 该骨 scale = 100.0，local 平移恒为 (0, 0, 0)
    - 其余所有骨的 rest 局部平移是「米」级（pelvis ~= 1.0967）
    - 网格顶点是「cm」级（全高 202 cm，见 get_bounds）
    - 世界 = 局部 x 100

数学上这是自洽的：视觉完全正确。代价是**四类隐式换算**，每次都要记得：
  1. 重定向器会给最外层骨写一条 scale=1 的轨道，覆盖 100 -> 角色缩成 1.85 cm
     -> 每批重定向产物必须紧跟 `retarget/rtg_41_fix_outer_scale.py`
  2. 挂在骨下的 socket / 挂件，其 RelativeScale 必须为 0.01（SOCKET_SCALE）
  3. pelvis 局部基线 1.0967；`weapon_jnt` 烘焙时 17.37 cm 要写成 0.1737
  4. Chaos Cloth 约束距离、PhysicsAsset body 位置都活在 100x 空间里

== 使用约定 ==
任何涉及这一换算的脚本**必须**从这里取常量，禁止再写裸 100 / 0.01 / 1.0967。
门禁脚本：`Scripts/core/scale_audit.py`（扫全部动画 + socket + 蓝图）。
"""

OUTER_BONE = "darius_godking_mesh_LOD0_Skeleton"
OUTER_SCALE = 100.0
OUTER_LOCAL = (0.0, 0.0, 0.0)

LOCAL_PER_CM = 1.0 / OUTER_SCALE
CM_PER_LOCAL = OUTER_SCALE

PELVIS_LOCAL_BASELINE = 1.0967

SOCKET_SCALE = LOCAL_PER_CM
WEAPON_LOCAL_SCALE = LOCAL_PER_CM

SOCKET_SCALE_ABS_TOL = 1e-4
OUTER_SCALE_REL_TOL = 1e-3


def cm_to_local(cm):
    """cm -> 骨骼局部单位（pelvis 局部平移、weapon_jnt 轨道写值用这个）。"""
    return float(cm) * LOCAL_PER_CM


def local_to_cm(local):
    """骨骼局部单位 -> cm。"""
    return float(local) * CM_PER_LOCAL


def scale3_to_local(v):
    """unreal.Vector 形式的 cm 位移 -> 局部三元组。"""
    return (v.x * LOCAL_PER_CM, v.y * LOCAL_PER_CM, v.z * LOCAL_PER_CM)


def outer_scale_ok(value):
    """最外层骨 scale 是否合规（100，允许极小的压缩误差）。"""
    try:
        return abs(float(value) - OUTER_SCALE) <= OUTER_SCALE * OUTER_SCALE_REL_TOL
    except (TypeError, ValueError):
        return False


def socket_scale_ok(value):
    """socket / 挂件相对缩放是否合规（0.01）。"""
    try:
        return abs(float(value) - SOCKET_SCALE) <= SOCKET_SCALE_ABS_TOL
    except (TypeError, ValueError):
        return False
