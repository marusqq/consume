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


def _unique_slug(slug: str, existing_slugs: set[str]) -> str:
    base, counter = slug, 2
    while slug in existing_slugs:
        slug = f"{base}_{counter}"
        counter += 1
    return slug


def register(project_dir: Path, url: str, summary: str) -> str:
    """Save summary to library and return the slug.

    Creates library/{slug}.md if it doesn't exist yet.
    Does NOT overwrite an existing library entry.
    Uses Claude to generate a descriptive filename.
    """
    from .summarizer import generate_filename

    index = load_index(project_dir)
    if url in index:
        return index[url]["slug"]

    existing_slugs = {v["slug"] for v in index.values()}
    slug = _unique_slug(generate_filename(summary), existing_slugs)

    lib_path = library_md_path(project_dir, slug)
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    lib_path.write_text(to_markdown(url, summary), encoding="utf-8")

    index[url] = {
        "slug": slug,
        "named": True,
        "consumed_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {},
    }
    _save_index(project_dir, index)
    return slug


def relabel(project_dir: Path) -> list[tuple[str, str, str]]:
    """Rename library and output files for entries that still use URL-based slugs.

    Returns a list of (url, old_slug, new_slug) for every entry that was renamed.
    """
    from .summarizer import generate_filename

    index = load_index(project_dir)
    renamed = []

    for url, entry in list(index.items()):
        if entry.get("named"):
            continue  # already has a descriptive name

        old_slug = entry["slug"]

        # Read existing summary from library file
        old_lib = library_md_path(project_dir, old_slug)
        if not old_lib.exists():
            continue

        lines = old_lib.read_text(encoding="utf-8").splitlines()
        bullets = [l[2:] for l in lines if l.startswith("- ")]
        if not bullets:
            continue
        summary = "\n".join(f"• {b}" for b in bullets)

        existing_slugs = {v["slug"] for v in index.values()} - {old_slug}
        new_slug = _unique_slug(generate_filename(summary), existing_slugs)

        if new_slug == old_slug:
            entry["named"] = True
            continue

        # Rename library file
        new_lib = library_md_path(project_dir, new_slug)
        old_lib.rename(new_lib)

        # Rename each output file and update sources.json
        new_outputs = {}
        for fmt, old_path_str in entry.get("outputs", {}).items():
            old_out = Path(old_path_str)
            if old_out.exists():
                new_out = old_out.parent / (new_slug + old_out.suffix)
                old_out.rename(new_out)
                _update_sources(new_out, url)
                # Remove old entry from sources.json
                _remove_source(old_out)
                new_outputs[fmt] = str(new_out)
            else:
                new_outputs[fmt] = old_path_str  # keep stale path as-is

        entry["slug"] = new_slug
        entry["named"] = True
        entry["outputs"] = new_outputs
        renamed.append((url, old_slug, new_slug))

    _save_index(project_dir, index)
    return renamed


def record_output(project_dir: Path, url: str, fmt: str, path: Path) -> None:
    """Mark a non-text output as generated in the index and update sources.json."""
    index = load_index(project_dir)
    if url not in index:
        return
    index[url].setdefault("outputs", {})[fmt] = str(path)
    _save_index(project_dir, index)
    _update_sources(path, url)


def _remove_source(output_file: Path) -> None:
    """Remove an entry from sources.json when a file is renamed."""
    sources_path = output_file.parent / "sources.json"
    if not sources_path.exists():
        return
    try:
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
        sources.pop(output_file.name, None)
        sources_path.write_text(
            json.dumps(dict(sorted(sources.items())), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def _update_sources(output_file: Path, url: str) -> None:
    """Add or update an entry in sources.json next to the output file.

    sources.json lives in the same directory as the output and maps
    filename → source URL for easy lookup without touching the library index.
    """
    sources_path = output_file.parent / "sources.json"
    try:
        sources = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}
    except Exception:
        sources = {}
    sources[output_file.name] = url
    sources_path.write_text(
        json.dumps(dict(sorted(sources.items())), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
