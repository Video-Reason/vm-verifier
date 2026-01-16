# VM Verifier 🔍

Automated verification tool for student data generator submissions.

## Features

✅ **File Structure Validation** - Ensures all required files and directories exist  
✅ **Code Format Checking** - Validates naming conventions, domain format, task_id patterns  
✅ **Output Format Validation** - Runs generator in isolated environment and checks output structure  
✅ **Isolated Testing** - Each generator runs in its own subprocess with dedicated virtual environment  

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Usage

### Basic Usage

```bash
python vm_verify.py --generator path/to/generator.zip
```

### Advanced Options

```bash
python vm_verify.py \
  --generator my_task_generator.zip \
  --samples 10 \
  --output report.json \
  --verbose
```

**Options:**
- `--generator`: Path to generator zip file (required)
- `--samples`: Number of samples to generate for testing (default: 5)
- `--output`: Output report path (default: verification_report.json)
- `--verbose`: Enable detailed logging

## Verification Steps

The verifier performs three main checks:

### 1️⃣ File Structure Check
- ✓ Required files: `generator.py`, `config.py`, `prompts.py`, `requirements.txt`, `README.md`
- ✓ Required directories: `src/`, `examples/`, `core/`
- ✓ Entry point: `examples/generate.py`
- ✓ Template residue detection

### 2️⃣ Code Format Check
- ✓ Domain naming (lowercase, underscores)
- ✓ Task ID format (`{domain}_{i:04d}`)
- ✓ Output file naming (`ground_truth.mp4`, `first_frame.png`, etc.)
- ✓ Dependency version pinning

### 3️⃣ Output Format Check
- ✓ Generator execution (installs deps and runs)
- ✓ Output directory structure: `data/{domain}_task/{task_id}/`
- ✓ Required output files per task
- ✓ Video duration (≤10 seconds)
- ✓ Prompt length (≤200 words)

## Output

The tool generates two reports:

**JSON Report** (`verification_report.json`):
```json
{
  "timestamp": "2026-01-16T10:30:00",
  "generator": "maze_generator.zip",
  "domain": "maze",
  "status": "PASS",
  "summary": {
    "total_issues": 2,
    "critical_issues": 0,
    "warning_issues": 2
  },
  "steps": [...]
}
```

**Text Summary** (`verification_report.txt`):
```
============================================================
VERIFICATION REPORT
============================================================
Generator: maze_generator.zip
Domain: maze
Status: ✅ PASS
...
```

## Exit Codes

- `0`: All checks passed
- `1`: Verification failed (critical issues found)

## How It Works

1. **Extraction**: Unzips the submitted generator
2. **Isolation**: Creates a dedicated virtual environment for testing
3. **Validation**: Runs three verification steps
4. **Cleanup**: Removes temporary files and environment
5. **Reporting**: Generates JSON and text reports

## Development

### Project Structure

```
vm-verifier/
├── vm_verify.py              # Main CLI entry point
├── src/
│   ├── models.py             # Pydantic data models
│   ├── structure_validator.py   # File structure checks
│   ├── format_validator.py      # Code format checks
│   ├── output_validator.py      # Output generation checks
│   ├── verification_engine.py   # Main orchestrator
│   └── report_generator.py      # Report generation
├── template-data-generator/  # Template submodule
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Test with the template generator
cd template-data-generator
zip -r ../test_generator.zip .
cd ..
python vm_verify.py --generator test_generator.zip --samples 3 --verbose
```

## Requirements

- Python 3.8+
- pydantic 2.6.0
- opencv-python-headless 4.9.0.80

## License

MIT License
