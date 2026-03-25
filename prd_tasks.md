<!-- Auto-generated from prd.md by Ralphster -->

# PRD Implementation Tasks

## Phase 1: Project Setup
- [x] Initialize Python project structure with `consume/` package directory and `__init__.py` files
  - Created `consume/` package directory
  - Created `consume/__init__.py` to mark it as a Python package
- [x] Create `pyproject.toml` or `setup.py` with dependencies: `requests`, `readability-lxml`, `anthropic` (or chosen LLM SDK)
  - Created `pyproject.toml` with dependencies: `requests`, `readability-lxml`, and `anthropic`
- [ ] Set up environment variable loading for LLM API key configuration

## Phase 2: CLI Entry Point
- [ ] Implement `cli.py` with argument parsing: positional `<url>` arg and optional `--mode short|long` flag
- [ ] Implement URL format validation (reject malformed URLs before making any network calls)
- [ ] Wire up the fetch → extract → summarize → output pipeline in `cli.py`
- [ ] Implement clean bullet-point terminal output formatter in `cli.py`

## Phase 3: Article Extraction
- [ ] Implement `extractor.py` with `fetch_html(url)` using `requests` (timeout, user-agent header)
- [ ] Implement `extract_content(html)` using `readability-lxml` to strip boilerplate and return main text
- [ ] Implement fallback extraction for minimal pages (e.g. strip all tags, return raw visible text)
- [ ] Add content length check — raise extraction failure if result is below a minimum threshold

## Phase 4: Summarization
- [ ] Implement `summarizer.py` with `summarize(text, mode)` that calls the configured LLM API
- [ ] Write the system prompt enforcing factual, bullet-only output (default: 5 bullets, ≤15 words each)
- [ ] Implement mode-based prompt variation: `short` → 3 bullets, `long` → 8–10 bullets, `default` → 5 bullets
- [ ] Make LLM provider/model configurable via environment variable

## Phase 5: Error Handling
- [ ] Handle invalid URL error with a clear user-facing message and non-zero exit code
- [ ] Handle network failure (connection error, timeout) with a clear user-facing message
- [ ] Handle extraction failure (no content parsed) with a clear user-facing message
- [ ] Handle empty content after extraction with a clear user-facing message
- [ ] Handle LLM API failure (auth error, rate limit, timeout) with a clear user-facing message

## Phase 6: Utilities
- [ ] Implement `utils.py` with shared helpers: text truncation (cap input tokens to LLM), whitespace normalization

## Phase 7: Testing
- [ ] Write unit tests for URL validation logic
- [ ] Write unit tests for `extract_content()` using fixture HTML files (normal page, minimal page)
- [ ] Write unit tests for `summarize()` by mocking the LLM API response
- [ ] Write an integration smoke test: run `consume <real_url>` and assert bullet output is returned

## Phase 8: Documentation
- [ ] Write `README.md` covering: installation, required env vars, usage examples, supported modes
