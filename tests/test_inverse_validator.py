import subprocess
import sys


def test_inverse_validator_ok():
    # Run the repository inverse validator and assert it exits with 0
    proc = subprocess.run([sys.executable, 'scripts/validate_inverse_relations.py'], capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    print(out)
    assert proc.returncode == 0, "Inverse validator failed: \n" + out
