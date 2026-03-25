"""Integration smoke test: run `consume <real_url>` end-to-end."""

import subprocess
import sys

import pytest

# A stable, lightweight page that is unlikely to disappear.
REAL_URL = "https://example.com"


@pytest.mark.integration
def test_consume_returns_bullet_output():
    result = subprocess.run(
        [sys.executable, "-m", "consume.cli", REAL_URL],
        capture_output=True,
        text=True,
        timeout=60,
    )

    stderr = result.stderr.strip()

    # Skip rather than fail when the environment has no network or API access.
    if result.returncode != 0:
        skip_triggers = (
            "Could not connect",
            "timed out",
            "authentication failed",
            "rate limit",
        )
        if any(trigger.lower() in stderr.lower() for trigger in skip_triggers):
            pytest.skip(f"Skipping integration test due to environment limitation: {stderr}")

    assert result.returncode == 0, (
        f"consume exited with code {result.returncode}.\nstderr: {stderr}"
    )

    output = result.stdout.strip()
    assert output, "consume produced no output"

    lines = output.splitlines()
    bullet_lines = [line for line in lines if line.startswith("•")]
    assert bullet_lines, (
        f"Expected at least one bullet line starting with '•', got:\n{output}"
    )
