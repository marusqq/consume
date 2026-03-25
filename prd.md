# CONSUME --- PRD (v1)

## 1. Overview

Consume is a personal CLI tool that transforms article URLs into
concise, high-signal summaries.

Goal: enable fast information intake with minimal effort.

------------------------------------------------------------------------

## 2. Goals

### Primary

-   Input: URL
-   Output: short bullet summary
-   Fast execution (\<5s target)
-   Reliable article extraction

### Secondary

-   Multiple summary modes (short/long)

------------------------------------------------------------------------

## 3. Non-Goals (v1)

-   No UI
-   No mobile app
-   No Twitter/X support
-   No authentication
-   No feed aggregation

------------------------------------------------------------------------

## 4. User Flow

User runs CLI:

tldr `<url>`{=html}

System: Fetch → Extract → Clean → Summarize → Output

------------------------------------------------------------------------

## 5. Functional Requirements

### 5.1 Input

-   Single URL argument
-   Validate URL format
-   Handle unreachable URLs

### 5.2 Extraction

-   Fetch HTML
-   Extract main content (remove boilerplate)
-   Fallback for minimal pages

### 5.3 Summarization

-   LLM-based summarization
-   Default: 5 bullets, max \~15 words each
-   Strict, factual output

Modes: - short (3 bullets) - long (8--10 bullets)

### 5.4 Output

-   Terminal output only
-   Clean bullet formatting

### 5.5 Error Handling

-   invalid URL
-   network failure
-   extraction failure
-   empty content
-   API failure

------------------------------------------------------------------------

## 6. Non-Functional Requirements

-   fast (\<5s typical)
-   modular design
-   easy extensibility
-   minimal dependencies

------------------------------------------------------------------------

## 7. Tech Stack

-   Python
-   requests
-   readability-lxml or newspaper3k
-   LLM API (configurable)

------------------------------------------------------------------------

## 8. Architecture

consume/ cli.py extractor.py summarizer.py utils.py

------------------------------------------------------------------------

## 9. CLI Spec

consume `<url>`{=html}

Future: consume `<url>`{=html} --mode short\|long

------------------------------------------------------------------------

## 10. Success Criteria

-   works on 80%+ of articles
-   useful enough for daily use
-   fast and predictable output

------------------------------------------------------------------------

## 11. Future Ideas

-   Telegram bot integration
-   RSS ingestion
-   Chrome extension
-   batch processing
