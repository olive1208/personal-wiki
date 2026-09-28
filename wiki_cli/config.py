"""Settings for the personal wiki: folder paths and which local model to use."""
from pathlib import Path

# The project folder (the folder that contains wiki_cli/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The Obsidian vault
VAULT_DIR = PROJECT_ROOT / "vault"
RAW_DIR = VAULT_DIR / "raw"      # original notes, never changed
WIKI_DIR = VAULT_DIR / "wiki"    # generated and reviewed wiki pages
INDEX_MD = VAULT_DIR / "index.md"

# Machine files live outside the vault
DATA_DIR = PROJECT_ROOT / "data"
CHUNKS_FILE = DATA_DIR / "chunks.json"   # passages used by search
PROMPTS_DIR = PROJECT_ROOT / "prompts"
WIKI_PLAN = PROJECT_ROOT / "wiki_plan.json"   # page names, folders, and links
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Local model served by Ollama on this computer
OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e2b"
