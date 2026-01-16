#!/bin/bash
# Example usage of vm-verifier

# Basic usage
python vm_verify.py --generator my_generator.zip

# With custom sample size and verbose output
python vm_verify.py --generator my_generator.zip --samples 10 --verbose

# Custom output location
python vm_verify.py \
    --generator my_generator.zip \
    --samples 5 \
    --output my_report.json \
    --verbose

# Check exit code
python vm_verify.py --generator my_generator.zip
if [ $? -eq 0 ]; then
    echo "✅ Verification passed!"
else
    echo "❌ Verification failed!"
fi
