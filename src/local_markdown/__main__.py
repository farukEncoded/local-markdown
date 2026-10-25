"""Main entry point for Local Markdown executable and module."""

from __future__ import annotations

import sys


def main() -> None:
    # Worker route: executed by child process without GUI initialization
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        from local_markdown.jobs.worker import run_worker_process
        manifest_path = sys.argv[2]
        code = run_worker_process(manifest_path)
        sys.exit(code)

    # Normal desktop application route
    from local_markdown.app import run_app
    sys.exit(run_app())


if __name__ == "__main__":
    main()
