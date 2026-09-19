#!/usr/bin/env -S deno run -A
/**
 * editor.deno.ts —— 自主启停 UE 编辑器 + 就绪轮询
 *
 *   deno task editor:up      启动编辑器，轮询到「资产可用」才返回 0
 *   deno task editor:down    优雅退出（先存脏包）；--force 才强杀进程
 *   deno task editor:status  报告进程 + 就绪探针
 *
 * 为什么需要它：
 *   编辑器崩溃后必须人工重启，每次「改脚本 → 跑验证」的循环都被打断。
 *
 * 就绪判据（关键）：
 *   进程活着 ≠ 就绪。UDP 发现端口能连 ≠ 资产已注册。
 *   唯一可靠判据 = 通过 ue_remote 网关跑一次真实脚本，
 *   能列出 /Game 下的资产才算好。
 */

const PROJECT_DIR = "E:/UE/Fight";
const UPROJECT = `${PROJECT_DIR}/Fight.uproject`;
const EDITOR_EXE = "E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe";
const UV_EXE = "C:/Users/29226/.local/bin/uv.exe";
const GATEWAY = `${PROJECT_DIR}/Scripts/ue_remote.py`;
const PROBE = `${PROJECT_DIR}/Saved/_probe_editor_ready.py`;
const LAUNCH_LOG_DIR = `${PROJECT_DIR}/Saved/Logs`;

// ---------------------------------------------------------------- 探针脚本
// 注意：不要在这里出现 ".py" 字样以外的花活；ue_remote 会把整段落盘再传路径。
const PROBE_SRC = `import unreal
eal = unreal.EditorAssetLibrary
ok = False
n = -1
try:
    ok = eal.does_directory_exist("/Game")
    n = len(eal.list_assets("/Game", recursive=True, include_folder=False))
except Exception as ex:
    unreal.log_warning("PROBE_EXC %s" % ex)
unreal.log("PROBE_RESULT ok=%s assets=%d" % (ok, n))
`;

// 优雅退出：先存脏包，再退出。注意 quit_editor 会让本次连接断开，
// 所以日志可能收不全 —— 这是预期行为，不当失败处理。
const QUIT_SRC = `import unreal
L = unreal.log
LW = unreal.log_warning
try:
    elsu = unreal.EditorLoadingAndSavingUtils
    nm = len(elsu.get_dirty_map_packages())
    nc = len(elsu.get_dirty_content_packages())
    L("DIRTY map=%d content=%d" % (nm, nc))
    if nm or nc:
        L("saving dirty packages ...")
        elsu.save_dirty_packages(True, True)
        L("saved")
except Exception as ex:
    LW("save_dirty failed: %s" % ex)
L("QUIT_NOW")
unreal.SystemLibrary.quit_editor()
`;

// ---------------------------------------------------------------- 小工具
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// ⚠️ 不要用 `env: {...}` 整体替换环境：那会把 SystemRoot / PATHEXT / TEMP 一并抹掉，
//    实测导致 `tasklist` 报 `NotFound: Failed to spawn 'tasklist': entity not found`。
//    正确做法 = 继承完整环境，只往 PATH 前面补几个目录。
const SYSROOT = Deno.env.get("SystemRoot") ?? "C:\\Windows";
const CHILD_ENV = {
  ...Deno.env.toObject(),
  PATH: [
    `${SYSROOT}\\System32`,
    SYSROOT,
    "C:\\Users\\29226\\.local\\bin",
    Deno.env.get("PATH") ?? "",
  ].join(";"),
};
const TASKLIST = `${SYSROOT}\\System32\\tasklist.exe`;
const TASKKILL = `${SYSROOT}\\System32\\taskkill.exe`;

async function sh(cmd: string, args: string[], timeoutMs = 60_000) {
  const p = new Deno.Command(cmd, {
    args,
    cwd: PROJECT_DIR,
    stdout: "piped",
    stderr: "piped",
    env: CHILD_ENV,
  }).spawn();
  const t = setTimeout(() => {
    try { p.kill(); } catch { /* ignore */ }
  }, timeoutMs);
  const out = await p.output();
  clearTimeout(t);
  const dec = new TextDecoder();
  return {
    code: out.code,
    stdout: dec.decode(out.stdout),
    stderr: dec.decode(out.stderr),
  };
}

/** 列出 UnrealEditor.exe 的 PID。 */
async function editorPids(): Promise<number[]> {
  const r = await sh(TASKLIST, [
    "/FI",
    "IMAGENAME eq UnrealEditor.exe",
    "/FO",
    "CSV",
    "/NH",
  ]);
  const pids: number[] = [];
  for (const line of r.stdout.split(/\r?\n/)) {
    const m = line.match(/^"UnrealEditor\.exe","(\d+)"/i);
    if (m) pids.push(Number(m[1]));
  }
  return pids;
}

type Probe = { reachable: boolean; ok: boolean; assets: number; raw: string };

/** 通过 ue_remote 网关跑一次真实脚本，作为就绪判据。 */
async function probe(): Promise<Probe> {
  await Deno.mkdir(PROJECT_DIR + "/Saved", { recursive: true });
  await Deno.writeTextFile(PROBE, PROBE_SRC);
  const r = await sh(
    UV_EXE,
    ["run", "--no-project", "python", GATEWAY, PROBE],
    120_000,
  );
  const raw = (r.stdout + r.stderr).trim();
  const m = raw.match(/PROBE_RESULT ok=(\w+) assets=(-?\d+)/);
  if (!m) return { reachable: false, ok: false, assets: -1, raw };
  return {
    reachable: true,
    ok: m[1] === "True",
    assets: Number(m[2]),
    raw,
  };
}

// ---------------------------------------------------------------- 命令
async function cmdUp(timeoutSec: number, hold: boolean) {
  const existing = await editorPids();
  if (existing.length) {
    console.log(`编辑器已在运行 PID=${existing.join(",")}，直接探测就绪 ...`);
  } else {
    await Deno.mkdir(LAUNCH_LOG_DIR, { recursive: true });
    console.log(`启动 ${EDITOR_EXE}`);
    // cmd /c start 生成的进程完全脱离父 shell，不会被回收。
    // ⚠️ 这里也必须用 cmd.exe 的绝对路径：裸 `"cmd"` 在本工具沙箱里报
    //    `NotFound: Failed to spawn 'cmd'`（同 tasklist 那个坑）。
    new Deno.Command(`${SYSROOT}\\System32\\cmd.exe`, {
      args: ["/c", "start", "", "UnrealEditor.exe", UPROJECT.replace(/\//g, "\\")],
      cwd: "E:\\UE_5.8\\Engine\\Binaries\\Win64",
      stdin: "null",
      stdout: "null",
      stderr: "null",
      env: CHILD_ENV,
    }).spawn();
    await sleep(5000);
    if (!(await editorPids()).length) {
      console.error("启动失败：未看到 UnrealEditor.exe 进程。检查路径与日志。");
      Deno.exit(1);
    }
  }

  const deadline = Date.now() + timeoutSec * 1000;
  let last = "";
  while (Date.now() < deadline) {
    const p = await probe();
    if (p.reachable) {
      // 端口通了，但资产注册表可能还没扫完。
      if (p.ok && p.assets > 0) {
        console.log(`就绪。进程 PID=${(await editorPids()).join(",")}，/Game 下资产 ${p.assets} 个。`);
        if (!hold) return;
        // ⚠️ 关键：从本工具的 shell 里启动的进程属于同一个 Windows Job 对象，
        // 启动命令一退出，编辑器就被连坐杀掉（实测：任务结束 0.5s 内日志截断）。
        // 所以 --hold 让本进程一直活着，把编辑器焊在它的进程树里。
        console.log("HOLDING —— 本进程常驻以维持编辑器存活（结束本任务会连带杀掉编辑器）。");
        while (true) {
          await sleep(30_000);
          if (!(await editorPids()).length) {
            console.log("编辑器已退出，HOLD 结束。");
            return;
          }
        }
      }
      last = `已响应，但资产数=${p.assets}（注册表仍在扫）`;
    } else {
      last = "未响应";
    }
    console.log(`[等待] ${last}  (${Math.round((deadline - Date.now()) / 1000)}s 剩余)`);
    await sleep(10_000);
  }
  console.error(`超时 ${timeoutSec}s：编辑器仍未就绪（最后状态：${last}）。`);
  Deno.exit(1);
}

async function cmdDown(force: boolean) {
  const pids = await editorPids();
  if (!pids.length) {
    console.log("编辑器未在运行。");
    return;
  }
  console.log(`请求优雅退出 (PID=${pids.join(",")}) ...`);
  await Deno.writeTextFile(PROBE, QUIT_SRC);
  const r = await sh(UV_EXE, ["run", "--no-project", "python", GATEWAY, PROBE], 120_000);
  for (const line of (r.stdout + r.stderr).split(/\r?\n/)) {
    if (line.includes("DIRTY") || line.includes("save") || line.includes("QUIT")) {
      console.log("  " + line.trim());
    }
  }

  for (let i = 0; i < 24; i++) {
    await sleep(5000);
    if (!(await editorPids()).length) {
      console.log("已优雅退出。");
      return;
    }
  }

  const still = await editorPids();
  if (!force) {
    console.error(
      `仍未退出 (PID=${still.join(",")})。未保存资产可能丢失，故不自动强杀。\n` +
        `确认无未保存改动后，用：deno task editor:down -- --force`,
    );
    Deno.exit(1);
  }
  console.warn(`强杀 PID=${still.join(",")}`);
  for (const pid of still) {
    await sh(TASKKILL, ["/PID", String(pid), "/F", "/T"]);
  }
  await sleep(2000);
  console.log("已强杀。");
}

async function cmdStatus() {
  const pids = await editorPids();
  console.log(`进程：${pids.length ? `UnrealEditor.exe PID=${pids.join(",")}` : "未运行"}`);
  const p = await probe();
  if (!p.reachable) {
    console.log("网关：无响应（编辑器未跑，或 Python 插件未加载）");
    Deno.exit(1);
  }
  console.log(`网关：已响应`);
  console.log(`资产：/Game 下 ${p.assets} 个（ready=${p.ok && p.assets > 0}）`);
  if (!(p.ok && p.assets > 0)) Deno.exit(1);
}

// ---------------------------------------------------------------- 入口
const argv = Deno.args;
const cmd = argv[0];
const force = argv.includes("--force");
const hold = argv.includes("--hold");
const tIdx = argv.indexOf("--timeout");
const timeoutSec = tIdx >= 0 ? Number(argv[tIdx + 1]) : 1200;

switch (cmd) {
  case "up":
    await cmdUp(timeoutSec, hold);
    break;
  case "down":
    await cmdDown(force);
    break;
  case "status":
    await cmdStatus();
    break;
  default:
    console.log(`用法：
  deno task editor:up   [-- --hold] [-- --timeout 900]
  deno task editor:down [-- --force]
  deno task editor:status`);
    Deno.exit(2);
}
