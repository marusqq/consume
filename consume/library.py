"""Local library: persists summaries and tracks consumed URLs per output type."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .renderer import _url_to_slug, to_markdown

_INDEX_FILE = ".index.json"


def _library_dir(project_dir: Path) -> Path:
    return project_dir / "library"


def _output_dir(project_dir: Path, fmt: str) -> Path:
    return project_dir / fmt


def library_md_path(project_dir: Path, slug: str) -> Path:
    return _library_dir(project_dir) / f"{slug}.md"


def output_path(project_dir: Path, fmt: str, slug: str) -> Path:
    ext = {"markdown": "md", "pdf": "pdf", "audio": "mp3"}.get(fmt, fmt)
    return _output_dir(project_dir, fmt) / f"{slug}.{ext}"


def _index_path(project_dir: Path) -> Path:
    return _library_dir(project_dir) / _INDEX_FILE


def load_index(project_dir: Path) -> dict:
    path = _index_path(project_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_index(project_dir: Path, index: dict) -> None:
    path = _index_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def get_entry(project_dir: Path, url: str) -> dict | None:
    return load_index(project_dir).get(url)


def has_output(project_dir: Path, url: str, fmt: str) -> bool:
    """Return True if this URL has already been rendered to the given format."""
    entry = get_entry(project_dir, url)
    if not entry:
        return False
    if fmt == "text":
        # Text goes to terminal — always "available" if summary exists in library
        return library_md_path(project_dir, entry["slug"]).exists()
    return fmt in entry.get("outputs", {})


def read_library_summary(project_dir: Path, url: str) -> str | None:
    """Return raw bullet-point summary from the library file, or None if missing."""
    entry = get_entry(project_dir, url)
    if not entry:
        return None
    path = library_md_path(project_dir, entry["slug"])
    if not path.exists():
        return None
    # The library .md file starts with "# url\n\n- bullet\n- bullet\n"
    # Re-convert to the bullet format the rest of the pipeline expects
    lines = path.read_text(encoding="utf-8").splitlines()
    bullets = []
    for line in lines:
        if line.startswith("- "):
            bullets.append("• " + line[2:])
    return "\n".join(bullets) if bullets else None


def register(project_dir: Path, url: str, summary: str) -> str:
    """Save summary to library and return the slug.

    Creates library/{slug}.md if it doesn't exist yet.
    Does NOT overwrite an existing library entry.
    """
    index = load_index(project_dir)
    if url in index:
        return index[url]["slug"]

    slug = _url_to_slug(url)
    # Ensure slug is unique within this index
    existing_slugs = {v["slug"] for v in index.values()}
    base = slug
    counter = 2
    while slug in existing_slugs:
        slug = f"{base}_{counter}"
        counter += 1

    lib_path = library_md_path(project_dir, slug)
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    lib_path.write_text(to_markdown(url, summary), encoding="utf-8")

    index[url] = {
        "slug": slug,
        "consumed_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {},
    }
    _save_index(project_dir, index)
    return slug


def record_output(project_dir: Path, url: str, fmt: str, path: Path) -> None:
    """Mark a non-text output as generated in the index."""
    index = load_index(project_dir)
    if url not in index:
        return
    index[url].setdefault("outputs", {})[fmt] = str(path)
    _save_index(project_dir, index)
