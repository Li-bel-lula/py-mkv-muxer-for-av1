import os
import sys
import re
import json
import shutil
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')

def check_mkvtoolnix():
    if not shutil.which("mkvmerge"):
        print("Error: 'mkvmerge' not found in system PATH.")
        return False
    return True

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', '-', title).strip('. ')

def get_mkv_info(filepath):
    try:
        res = subprocess.run(
            ["mkvmerge", "-J", filepath],
            capture_output=True, text=True, encoding='utf-8', errors='replace', check=True
        )
        return json.loads(res.stdout)
    except Exception as e:
        print(f"Error probing metadata for '{filepath}': {e}")
        return None

def get_video_rank(filepath, info):
    # Codec priority: AV1 = 2, HEVC = 1, OTHER = 0
    if info and "tracks" in info:
        for t in info["tracks"]:
            if t.get("type") == "video":
                codec = (t.get("codec", "") + t.get("properties", {}).get("codec_id", "")).upper()
                track_id = t.get("id", 0)

                if "AV1" in codec:
                    return 2, track_id
                if "HEVC" in codec or "H.265" in codec or "MPEGH" in codec:
                    return 1, track_id
                return 0, track_id

    # Fallback to filename search if metadata probing fails
    fn = filepath.upper()
    if "AV1" in fn:
        return 2, 0
    if "HEVC" in fn or "H265" in fn or "H.265" in fn:
        return 1, 0

    return 0, 0

def find_pairs():
    mkv_files = [f for f in os.listdir('.') if f.lower().endswith('.mkv') and os.path.isfile(f)]
    pattern = re.compile(r'S\d{2}E\d{2}', re.IGNORECASE)

    groups = {}
    for f in mkv_files:
        match = pattern.search(f)
        if match:
            tag = match.group(0).upper()
            groups.setdefault(tag, []).append(f)

    return {tag: files for tag, files in groups.items() if len(files) == 2}

def main():
    if not check_mkvtoolnix():
        return

    pairs = find_pairs()
    if not pairs:
        print("No valid SxxExx file pairs found in current directory.")
        return

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Found {len(pairs)} pair(s) to process.\n")

    for tag, files in pairs.items():
        print(f">>> Processing Pair: {tag}")

        info0, info1 = get_mkv_info(files[0]), get_mkv_info(files[1])
        rank0, id0 = get_video_rank(files[0], info0)
        rank1, id1 = get_video_rank(files[1], info1)

        # Priority: AV1 (2) > HEVC (1) > OTHER (0)
        if rank0 == rank1:
            print(f"Skipping {tag}: Both files have the same codec priority level.\n")
            continue
        elif rank0 > rank1:
            v_file, v_info, v_id = files[0], info0, id0
            a_file, a_info = files[1], info1
        else:
            v_file, v_info, v_id = files[1], info1, id1
            a_file, a_info = files[0], info0

        title_v = v_info.get("container", {}).get("properties", {}).get("title", "").strip() if v_info else ""
        title_a = a_info.get("container", {}).get("properties", {}).get("title", "").strip() if a_info else ""
        mkv_title = title_a or title_v

        out_name = f"{sanitize_filename(mkv_title)}.mkv" if mkv_title else f"{tag}.mkv"
        out_path = os.path.join(output_dir, out_name)

        cmd = [
            "mkvmerge", "-o", out_path,
            "--title", mkv_title,
            "-d", str(v_id), "-A", "-S", "-B", "-M", "--no-chapters", "--no-global-tags", v_file,
            "-D", a_file
        ]

        print(f"  Video Source    : {v_file}")
        print(f"  Audio/Sub Source: {a_file}")
        if mkv_title:
            print(f"  Retained Title  : \"{mkv_title}\"")
        print(f"  Saving to       : '{out_path}'...")

        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        res = subprocess.run(cmd, text=True, encoding='utf-8', errors='replace', env=env)

        if res.returncode in (0, 1):
            print(f"--> Successfully created '{out_path}'\n")
        else:
            print(f"--> Failed to process {tag} (exit code {res.returncode})\n")

    print("Processing complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        input("\nPress Enter to exit...")
