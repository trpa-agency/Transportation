"""
Run all Alternative forecast notebooks sequentially.

Each notebook is executed in-place (outputs are saved back to the .ipynb file)
with its working directory set to the notebook's own folder, matching the
`pathlib.Path().absolute()` path logic used inside each notebook.

Usage:
    python run_all_alternatives.py
    python run_all_alternatives.py --alternatives 1 3   # run specific alternatives
    python run_all_alternatives.py --timeout 7200       # override timeout (seconds)
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

ALTERNATIVES = {
    1: SCRIPT_DIR / "Alternative_1" / "Alternative_1_Forecast.ipynb",
    2: SCRIPT_DIR / "Alternative_2" / "Alternative_2_Forecast.ipynb",
    3: SCRIPT_DIR / "Alternative_3" / "Alternative_3_Forecast.ipynb",
    4: SCRIPT_DIR / "Alternative_4" / "Alternative_4_Forecast.ipynb",
}

DEFAULT_TIMEOUT = 3600  # seconds per notebook


def run_notebook(notebook_path: Path, timeout: int) -> bool:
    """Execute a notebook in-place using nbconvert. Returns True on success."""
    notebook_dir = notebook_path.parent
    print(f"\n{'='*60}")
    print(f"Running: {notebook_path.name}")
    print(f"Directory: {notebook_dir}")
    print(f"{'='*60}")

    cmd = [
        sys.executable, "-m", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--inplace",
        f"--ExecutePreprocessor.timeout={timeout}",
        f"--ExecutePreprocessor.kernel_name=python3",
        str(notebook_path),
    ]

    start = time.time()
    result = subprocess.run(cmd, cwd=notebook_dir)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"  Completed in {elapsed:.1f}s")
        return True
    else:
        print(f"  FAILED after {elapsed:.1f}s (exit code {result.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Alternative forecast notebooks.")
    parser.add_argument(
        "--alternatives", "-a",
        nargs="+",
        type=int,
        choices=list(ALTERNATIVES.keys()),
        default=list(ALTERNATIVES.keys()),
        metavar="N",
        help="Which alternatives to run (default: all). E.g. --alternatives 1 2",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to allow per notebook (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        default=False,
        help="Stop immediately if any notebook fails (default: continue)",
    )
    args = parser.parse_args()

    results = {}
    overall_start = time.time()

    for alt in sorted(args.alternatives):
        nb_path = ALTERNATIVES[alt]
        if not nb_path.exists():
            print(f"\nWARNING: Notebook not found: {nb_path}")
            results[alt] = False
            if args.stop_on_error:
                break
            continue

        success = run_notebook(nb_path, args.timeout)
        results[alt] = success

        if not success and args.stop_on_error:
            print("\nStopping due to --stop-on-error.")
            break

    total_elapsed = time.time() - overall_start

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for alt, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"  Alternative {alt}: {status}")
    print(f"\nTotal time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
