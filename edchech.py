import subprocess
import sys
from pathlib import Path


def check_ed_py() -> bool:
	"""Check if ed.py is valid and runs without errors."""
	ed_file = Path("/home/scripted/KamiLimu/serverless-pipeline/ed.py")
	
	if not ed_file.exists():
		print(f"Error: {ed_file} does not exist")
		return False
	
	# Check syntax
	result = subprocess.run(
		[sys.executable, "-m", "py_compile", str(ed_file)],
		capture_output=True,
		text=True
	)
	
	if result.returncode != 0:
		print(f"Syntax error in ed.py:\n{result.stderr}")
		return False
	
	print("✓ ed.py syntax is valid")
	
	# Check if it runs with --help
	result = subprocess.run(
		[sys.executable, str(ed_file), "--help"],
		capture_output=True,
		text=True
	)
	
	if result.returncode != 0:
		print(f"Error running ed.py:\n{result.stderr}")
		return False
	
	print("✓ ed.py runs successfully")
	print(f"\n{result.stdout}")
	return True


if __name__ == "__main__":
	success = check_ed_py()
	sys.exit(0 if success else 1)
