`context.md` created at `/Users/marus/dev/consume/context.md`. Key things captured:

- The project is a Python CLI (`tldr <url>`) that summarizes articles via LLM — currently **pre-implementation** (only PRD exists, no code yet)
- The `ralph-once.sh` / `afk-ralph.sh` scripts are an autonomous build loop: Claude Code reads the PRD, implements one task, commits, and repeats until done
- `.ralphster/state.json` tracks agent XP/progress state for that automation
