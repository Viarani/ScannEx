"""One-time (or resume) downloader for the SigLIP2 checkpoint.

Run it in its OWN terminal so you can watch the download progress:

    python warmup_model.py

Safe to re-run — HuggingFace resumes partial downloads.
When it prints READY, go to the Analyze page and press "Check again".
"""
import logging
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

# Silence the harmless bos/eos_token_id config warnings, keep download bars.
logging.getLogger("transformers").setLevel(logging.ERROR)

from app import SIGLIP_ID, get_siglip  # noqa: E402

print("=" * 60, flush=True)
print("Downloading + loading:", SIGLIP_ID, flush=True)
print("One-time ~1 GB download. Progress bars appear below.", flush=True)
print("=" * 60, flush=True)
try:
    get_siglip()
    print("=" * 60, flush=True)
    print("READY — model is cached. Go to Analyze page, press 'Check again'.", flush=True)
    print("=" * 60, flush=True)
except Exception as e:
    print("FAILED:", e, flush=True)
    raise SystemExit(1)
