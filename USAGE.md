# VM Verifier Usage Guide

## Quick Start

```bash
# Setup (one time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify a student submission
python vm_verify.py --generator student_submission.zip
```

## What Gets Checked

### ✅ Step 1: File Structure
- Required files exist (`generator.py`, `config.py`, `prompts.py`, `requirements.txt`, `README.md`)
- Required directories exist (`src/`, `examples/`, `core/`)
- No template residue (chess keywords)
- Entry point exists (`examples/generate.py`)

### ✅ Step 2: Code Format
- **Domain naming**: Must be lowercase with underscores (e.g., `rolling_ball`, not `RollingBall`)
- **Task ID format**: Must use `{domain}_{i:04d}` (e.g., `rolling_ball_0000`)
- **Video filename**: Must be `ground_truth.mp4`
- **Output files**: Must include `first_frame.png`, `final_frame.png` or `goal.txt`, `prompt.txt`
- **Dependencies**: Checks for version pinning in `requirements.txt`

### ✅ Step 3: Output Validation
- **Creates isolated environment**: New venv for each submission
- **Installs dependencies**: Tests if `requirements.txt` works
- **Runs generator**: Executes `python examples/generate.py --num-samples N`
- **Checks output structure**:
  - Directory: `data/{domain}_task/{task_id}/`
  - Files: `first_frame.png`, `prompt.txt` (required)
  - Files: `final_frame.png` or `goal.txt` (at least one)
  - Video duration: ≤10 seconds
  - Prompt length: ≤200 words

## Command Options

```bash
# Basic usage
python vm_verify.py --generator submission.zip

# Generate more samples for thorough testing
python vm_verify.py --generator submission.zip --samples 10

# Verbose output to see all issues
python vm_verify.py --generator submission.zip --verbose

# Custom report location
python vm_verify.py --generator submission.zip --output my_report.json
```

## Outputs

Two files are generated:

1. **verification_report.json** - Machine-readable JSON format
2. **verification_report.txt** - Human-readable summary

## Exit Codes

- `0` = All checks passed ✅
- `1` = Verification failed ❌

## Examples

### Passing Submission
```
🔍 Starting verification for: rolling_ball.zip
============================================================
📁 Step 1: Checking file structure...
   ✅ PASS - 0 issue(s)

🔤 Step 2: Checking code format and naming...
   ✅ PASS - 0 issue(s)

▶️  Step 3: Running generator (3 samples)...
   ✅ PASS - 0 issue(s)

============================================================
✅ Verification complete!
Overall Status: ✅ PASS
```

### Failing Submission
```
🔍 Starting verification for: bad_generator.zip
============================================================
📁 Step 1: Checking file structure...
   ✅ PASS - 1 issue(s)
      ⚠️ Template keyword 'chess' found in code

🔤 Step 2: Checking code format and naming...
   ❌ FAIL - 2 issue(s)
      🔴 Invalid domain format: 'MyTask'
      🔴 Video file must be named 'ground_truth.mp4'

⏭️  Step 3: Skipped (previous steps failed)

============================================================
Overall Status: ❌ FAIL
```

## Common Issues

### Issue: "Could not extract 'domain' from config.py"
**Fix**: Make sure `config.py` has:
```python
domain: str = Field(default="your_task_name")
# or
domain: str = "your_task_name"
```

### Issue: "Invalid domain format"
**Fix**: Domain must be:
- Lowercase letters
- Underscores for spaces
- No special characters
- Example: `rolling_ball`, not `Rolling-Ball` or `RollingBall`

### Issue: "Task ID format incorrect"
**Fix**: In `core/base_generator.py`, use:
```python
task_id = f"{self.config.domain}_{i:04d}"  # Produces: task_0000, task_0001, ...
```

### Issue: "Missing required file"
**Fix**: Ensure your output includes:
- `first_frame.png` (always required)
- `prompt.txt` (always required)
- `final_frame.png` OR `goal.txt` (at least one)
- `ground_truth.mp4` (optional but recommended)

## Batch Verification

```bash
# Verify multiple submissions
for zip in assets/generators/*.zip; do
    echo "Verifying $zip..."
    python vm_verify.py --generator "$zip"
    echo "---"
done
```

## Tips

1. **Start small**: Test with `--samples 3` first
2. **Fix critical issues first**: Warnings won't fail the submission
3. **Check reports**: Read `verification_report.txt` for details
4. **Isolated testing**: Each generator runs in its own environment
5. **Template cleanup**: Remove all chess/template references before submission
