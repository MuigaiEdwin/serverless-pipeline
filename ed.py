
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_step(name: str, command: str, cwd: str) -> int:
	print(f"==> {name}: {command}")
	result = subprocess.run(command, shell=True, cwd=cwd, env=os.environ.copy())
	if result.returncode != 0:
		print(f"{name} failed with exit code {result.returncode}")
	return result.returncode


def main() -> int:
	parser = argparse.ArgumentParser(description="CI/CD pipeline runner")
	parser.add_argument("--project-dir", default=str(Path.cwd()), help="Project directory")
	parser.add_argument("--lint-command", default="python -m compileall .", help="Lint/static check command")
	parser.add_argument("--test-command", default="pytest -q", help="Test command")
	parser.add_argument("--build-command", default="", help="Optional build command")
	args = parser.parse_args()

	project_dir = str(Path(args.project_dir).resolve())
	steps = [
		("lint", args.lint_command),
		("test", args.test_command),
	]
	if args.build_command.strip():
		steps.append(("build", args.build_command))

	for name, command in steps:
		code = run_step(name, command, project_dir)
		if code != 0:
			return code

	print("Pipeline completed successfully.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
