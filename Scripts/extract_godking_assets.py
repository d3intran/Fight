import os
import sys
import struct
import subprocess
from pathlib import Path
from cdtb.wad import Wad

OUT_BASE = Path(r"E:\UE\Assets\Darius_GodKing_LOL_Original")
WAD_MAIN = r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.wad.client"
WAD_ZH = r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.zh_CN.wad.client"
WAD_EN = r"E:\WeGameApps\英雄联盟\Game\DATA\FINAL\Champions\Darius.en_US.wad.client"

LOL2GLTF = r"E:\UE\Fight\Scripts\lol2gltf.exe"
VGMSTREAM = r"E:\UE\Fight\Scripts\tools\vgmstream\vgmstream-cli.exe"

os.environ["DOTNET_ROLL_FORWARD"] = "Major"

def main():
    print(f"=== 1. Starting Full God-King Darius (Skin 15) Asset Extraction ===")
    dirs = {
        "anm_raw": OUT_BASE / "Animations_RAW",
        "anm_glb": OUT_BASE / "Animations_GLB",
        "sfx_wav": OUT_BASE / "Audio_SFX",
        "vo_zh": OUT_BASE / "Audio_VO_zh_CN",
        "vo_en": OUT_BASE / "Audio_VO_en_US",
        "vfx": OUT_BASE / "Particles_VFX",
        "textures": OUT_BASE / "Textures",
        "configs": OUT_BASE / "Configs_BIN",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # 1. Extract from Darius.wad.client
    print(f"\n[Phase 1] Scanning {WAD_MAIN}...")
    wad = Wad(WAD_MAIN)
    wad.sanitize_paths()

    skin15_files = [f for f in wad.files if f.path and "skin15" in f.path.lower()]
    print(f"Found {len(skin15_files)} files for Skin 15 in Main WAD.")

    sfx_bnk_data = None
    with open(WAD_MAIN, "rb") as f_in:
        for f in skin15_files:
            rel = f.path.lower()
            fname = os.path.basename(f.path)
            data = f.read_data(f_in)
            
            if rel.endswith(".anm") or rel.endswith(".skl") or rel.endswith(".skn"):
                dest = dirs["anm_raw"] / fname
                dest.write_bytes(data)
            elif "particle" in rel or rel.endswith(".scb"):
                dest = dirs["vfx"] / fname
                dest.write_bytes(data)
            elif rel.endswith(".tex") or rel.endswith(".dds"):
                dest = dirs["textures"] / fname
                dest.write_bytes(data)
            elif rel.endswith(".bin"):
                dest = dirs["configs"] / fname
                dest.write_bytes(data)
            elif rel.endswith("darius_skin15_sfx_audio.bnk"):
                sfx_bnk_data = data
                (dirs["sfx_wav"] / fname).write_bytes(data)
            elif rel.endswith(".bnk") or rel.endswith(".wpk"):
                (dirs["sfx_wav"] / fname).write_bytes(data)

    print(f"  Extracted RAW 3D & Particle & Texture files to {OUT_BASE}")

    # 2. Convert Animations to GLB via lol2gltf
    print(f"\n[Phase 2] Converting Animations to GLB via lol2gltf...")
    skn_path = dirs["anm_raw"] / "darius_skin15.skn"
    skl_path = dirs["anm_raw"] / "darius_skin15.skl"
    
    anm_files = list(dirs["anm_raw"].glob("*.anm"))
    print(f"  Found {len(anm_files)} .anm animation files to convert.")

    # Convert all animations in batch
    temp_anm_dir = dirs["anm_raw"]
    all_glb_path = dirs["anm_glb"] / "darius_skin15_all_anims.glb"
    cmd = [
        LOL2GLTF, "skn2gltf",
        "-m", str(skn_path),
        "-s", str(skl_path),
        "-a", str(temp_anm_dir),
        "-g", str(all_glb_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and all_glb_path.exists():
        print(f"  [SUCCESS] All-in-one GLB created: {all_glb_path.name} ({all_glb_path.stat().st_size // 1024} KB)")
    else:
        print(f"  [ERROR] lol2gltf batch failed: {res.stderr}")

    # Also convert key standalone animations
    key_anims = [
        "darius_skin15_run.anm",
        "darius_skin15_run_fast.anm",
        "darius_skin15_run_homeguard.anm",
        "darius_skin15_spell1_in_run.anm",
        "darius_skin15_spell2_idle.anm",
        "darius_skin15_spell3.anm",
        "darius_skin15_spell4_trans.anm",
        "darius_skin15_attack1.anm",
        "darius_skin15_dance.anm",
        "darius_skin15_recall.anm",
    ]
    standalone_dir = dirs["anm_glb"] / "standalone"
    standalone_dir.mkdir(exist_ok=True)
    for ka in key_anims:
        ka_path = dirs["anm_raw"] / ka
        if not ka_path.exists():
            continue
        temp_single = dirs["anm_raw"] / "_single_tmp"
        temp_single.mkdir(exist_ok=True)
        import shutil
        shutil.copy2(ka_path, temp_single / ka)
        out_single_glb = standalone_dir / (ka.replace(".anm", ".glb"))
        subprocess.run([
            LOL2GLTF, "skn2gltf",
            "-m", str(skn_path),
            "-s", str(skl_path),
            "-a", str(temp_single),
            "-g", str(out_single_glb)
        ], capture_output=True)
        shutil.rmtree(temp_single)
        if out_single_glb.exists():
            print(f"  Standalone GLB: {out_single_glb.name} ({out_single_glb.stat().st_size // 1024} KB)")

    # 3. Extract SFX BNK to WAV
    print(f"\n[Phase 3] Extracting Sound Effects (SFX) from BNK to WAV...")
    if sfx_bnk_data:
        # Extract embedded WEMs from BNK
        idx_didx = sfx_bnk_data.find(b"DIDX")
        idx_data = sfx_bnk_data.find(b"DATA")
        if idx_didx != -1 and idx_data != -1:
            didx_len = struct.unpack("<I", sfx_bnk_data[idx_didx+4:idx_didx+8])[0]
            count = didx_len // 12
            data_start = idx_data + 8
            print(f"  Found {count} SFX audio clips in BNK.")
            for i in range(count):
                entry_off = idx_didx + 8 + i * 12
                fid, foff, fsize = struct.unpack("<III", sfx_bnk_data[entry_off:entry_off+12])
                wem_bytes = sfx_bnk_data[data_start + foff : data_start + foff + fsize]
                wem_file = dirs["sfx_wav"] / f"sfx_{i:02d}_{fid}.wem"
                wav_file = dirs["sfx_wav"] / f"sfx_{i:02d}_{fid}.wav"
                wem_file.write_bytes(wem_bytes)
                # convert to wav with vgmstream
                subprocess.run([VGMSTREAM, "-o", str(wav_file), str(wem_file)], capture_output=True)
                if wem_file.exists():
                    wem_file.unlink() # cleanup wem, keep wav
            print(f"  Extracted and converted {len(list(dirs['sfx_wav'].glob('*.wav')))} SFX .wav files!")

    # 4. Extract Chinese Voice Lines (WPK to WAV)
    print(f"\n[Phase 4] Extracting Chinese Voice Lines (VO) from {WAD_ZH}...")
    if os.path.exists(WAD_ZH):
        wad_zh = Wad(WAD_ZH)
        wad_zh.sanitize_paths()
        wpk_zh = [f for f in wad_zh.files if f.path.endswith(".wpk") and "skin15" in f.path]
        if wpk_zh:
            with open(WAD_ZH, "rb") as f_in:
                zh_data = wpk_zh[0].read_data(f_in)
            magic, version, file_count = struct.unpack("<4sII", zh_data[:12])
            pos = 12
            offsets = struct.unpack(f"<{file_count}I", zh_data[pos:pos + file_count * 4])
            print(f"  Found {file_count} Chinese voice lines in WPK.")
            for i, off in enumerate(offsets):
                data_off, data_size, name_len = struct.unpack("<III", zh_data[off:off+12])
                name = zh_data[off+12 : off+12 + name_len * 2].decode("utf-16").rstrip("\x00")
                wem_bytes = zh_data[data_off : data_off + data_size]
                wem_name = dirs["vo_zh"] / f"vo_zh_{i:03d}_{name}"
                wav_name = dirs["vo_zh"] / f"vo_zh_{i:03d}_{Path(name).stem}.wav"
                wem_name.write_bytes(wem_bytes)
                subprocess.run([VGMSTREAM, "-o", str(wav_name), str(wem_name)], capture_output=True)
                if wem_name.exists():
                    wem_name.unlink()
            print(f"  Extracted and converted {len(list(dirs['vo_zh'].glob('*.wav')))} Chinese VO .wav files!")

    # 5. Extract English Voice Lines (WPK to WAV)
    print(f"\n[Phase 5] Extracting English Voice Lines (VO) from {WAD_EN}...")
    if os.path.exists(WAD_EN):
        wad_en = Wad(WAD_EN)
        wad_en.sanitize_paths()
        wpk_en = [f for f in wad_en.files if f.path.endswith(".wpk") and "skin15" in f.path]
        if wpk_en:
            with open(WAD_EN, "rb") as f_in:
                en_data = wpk_en[0].read_data(f_in)
            magic, version, file_count = struct.unpack("<4sII", en_data[:12])
            pos = 12
            offsets = struct.unpack(f"<{file_count}I", en_data[pos:pos + file_count * 4])
            print(f"  Found {file_count} English voice lines in WPK.")
            for i, off in enumerate(offsets):
                data_off, data_size, name_len = struct.unpack("<III", en_data[off:off+12])
                name = en_data[off+12 : off+12 + name_len * 2].decode("utf-16").rstrip("\x00")
                wem_bytes = en_data[data_off : data_off + data_size]
                wem_name = dirs["vo_en"] / f"vo_en_{i:03d}_{name}"
                wav_name = dirs["vo_en"] / f"vo_en_{i:03d}_{Path(name).stem}.wav"
                wem_name.write_bytes(wem_bytes)
                subprocess.run([VGMSTREAM, "-o", str(wav_name), str(wem_name)], capture_output=True)
                if wem_name.exists():
                    wem_name.unlink()
            print(f"  Extracted and converted {len(list(dirs['vo_en'].glob('*.wav')))} English VO .wav files!")

    print(f"\n=== Extraction Complete! All assets stored in {OUT_BASE} ===")

if __name__ == "__main__":
    main()
