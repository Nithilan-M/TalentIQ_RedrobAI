import os
import subprocess
from typing import Dict, Any, List

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OFFICIAL_VALIDATOR_PATH = os.path.join(project_root, "India_runs_data_and_ai_challenge", "validate_submission.py")

class SubmissionValidator:
    @staticmethod
    def validate_csv(csv_path: str) -> Dict[str, Any]:
        """
        Executes the official validate_submission.py script using subprocess.
        Parses the console output and returns status indicators.
        """
        if not os.path.exists(csv_path):
            return {
                "passed": False,
                "errors": [f"CSV file not found at: {csv_path}"],
                "warnings": []
            }
            
        if not os.path.exists(OFFICIAL_VALIDATOR_PATH):
            return {
                "passed": False,
                "errors": [f"Official validation script not found at: {OFFICIAL_VALIDATOR_PATH}"],
                "warnings": []
            }

        # Run script using virtual env Python
        # Command: python India_runs_data_and_ai_challenge/validate_submission.py <csv_path>
        python_exe = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            # Fallback to general python if venv path is different
            python_exe = "python"

        try:
            result = subprocess.run(
                [python_exe, OFFICIAL_VALIDATOR_PATH, csv_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            stdout_lines = result.stdout.strip().split("\n")
            stderr_lines = result.stderr.strip().split("\n")
            
            passed = result.returncode == 0
            errors = []
            warnings = []

            # Parse lines to identify specific errors
            for line in stdout_lines:
                if line.startswith("- "):
                    errors.append(line[2:].strip())
                elif "failed" in line.lower() or "error" in line.lower():
                    # Check if it's the failure summary line
                    if not line.startswith("Validation failed"):
                        errors.append(line.strip())
                        
            for line in stderr_lines:
                if line.strip():
                    errors.append(line.strip())

            # If validator returned success and no errors listed
            if passed and not errors:
                return {
                    "passed": True,
                    "errors": [],
                    "warnings": ["Ensure that reasoning strings refer to actual candidate attributes."]
                }
            else:
                return {
                    "passed": False,
                    "errors": errors if errors else ["Submission validation failed with unknown error."],
                    "warnings": []
                }

        except Exception as e:
            return {
                "passed": False,
                "errors": [f"Validator subprocess exception: {str(e)}"],
                "warnings": []
            }
