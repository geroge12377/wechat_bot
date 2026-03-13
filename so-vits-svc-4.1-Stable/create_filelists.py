import importlib.util
import random
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FILELIST_DIR = ROOT / "filelists"
DATASET_DIR = ROOT / "dataset" / "44k" / "unicorn"
SCRAPER_PATH = ROOT.parent / "python_scripts" / "unicorn_scraper.py"
LANG = "ZH"
SPLIT_RATIO = 0.9
SEED = 42


def _load_text_by_filename():
    """Load canonical line text from unicorn_scraper.py."""
    spec = importlib.util.spec_from_file_location("unicorn_scraper_mod", SCRAPER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    scraper = module.UnicornVoiceScraper()
    scraper.extract_voice_data_from_html("")
    voice_data = scraper.voice_data

    text_by_file = {}
    for idx, item in enumerate(voice_data, start=1):
        filename = f"unicorn_{item['type']}_{idx:02d}.wav"
        text_by_file[filename] = item["text"].strip()
    return text_by_file


def _text_for(filename, text_by_file):
    """Use filename as primary key, and map *_1.wav to its base name."""
    if filename in text_by_file:
        return text_by_file[filename]
    stem = Path(filename).stem
    base = re.sub(r"_1$", "", stem) + ".wav"
    return text_by_file.get(base, "")


def _build_line(filename, text_by_file):
    rel = f"dataset/44k/unicorn/{filename}"
    text = _text_for(filename, text_by_file)
    return f"{rel}|{LANG}|{text}"


def main():
    FILELIST_DIR.mkdir(parents=True, exist_ok=True)
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATASET_DIR}")
    if not SCRAPER_PATH.exists():
        raise FileNotFoundError(f"Text source not found: {SCRAPER_PATH}")

    text_by_file = _load_text_by_filename()
    wav_files = sorted(p.name for p in DATASET_DIR.glob("*.wav"))

    all_lines = [_build_line(name, text_by_file) for name in wav_files]

    rng = random.Random(SEED)
    shuffled = all_lines[:]
    rng.shuffle(shuffled)

    split_index = int(len(shuffled) * SPLIT_RATIO)
    train_lines = shuffled[:split_index]
    val_lines = shuffled[split_index:]

    (FILELIST_DIR / "train.txt").write_text("\n".join(train_lines) + "\n", encoding="utf-8")
    (FILELIST_DIR / "val.txt").write_text("\n".join(val_lines) + "\n", encoding="utf-8")
    (FILELIST_DIR / "unicorn.list").write_text("\n".join(all_lines) + "\n", encoding="utf-8")

    print("Created filelists with real transcript text:")
    print(f"  total: {len(all_lines)}")
    print(f"  train: {len(train_lines)}")
    print(f"  val: {len(val_lines)}")
    print("  files:")
    print(f"    - {FILELIST_DIR / 'train.txt'}")
    print(f"    - {FILELIST_DIR / 'val.txt'}")
    print(f"    - {FILELIST_DIR / 'unicorn.list'}")

    print("\nSample entries:")
    for line in train_lines[:3]:
        print(line)


if __name__ == "__main__":
    main()
