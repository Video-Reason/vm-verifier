#!/usr/bin/env python3
"""
VM Data Generator Verifier
Automated verification tool for data generator submissions
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.verification_engine import VerificationEngine
from src.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Verify data generator submissions against quality standards"
    )
    parser.add_argument(
        "--generator",
        type=str,
        required=True,
        help="Path to generator zip file (e.g., xx.zip)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="verification_report.json",
        help="Output report path (default: verification_report.json)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10,
        help="Number of samples to generate and verify (default: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate input
    generator_path = Path(args.generator)
    if not generator_path.exists():
        print(f"❌ Error: Generator file not found: {args.generator}")
        sys.exit(1)
    
    if not generator_path.suffix == ".zip":
        print(f"❌ Error: Generator must be a .zip file")
        sys.exit(1)
    
    # Run verification
    print(f"🔍 Starting verification for: {args.generator}")
    print(f"📊 Will generate {args.samples} samples for testing")
    print("=" * 60)
    
    engine = VerificationEngine(verbose=args.verbose)
    results = engine.verify(generator_path, num_samples=args.samples)
    
    # Generate report
    report_gen = ReportGenerator()
    report_gen.save_report(results, Path(args.output))
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"✅ Verification complete!")
    print(f"📄 Report saved to: {args.output}")
    print(f"Overall Status: {'✅ PASS' if results.passed else '❌ FAIL'}")
    print(f"Total Issues: {results.total_issues}")
    print(f"  - Critical: {results.critical_issues}")
    print(f"  - Warnings: {results.warning_issues}")
    
    # Exit with appropriate code
    sys.exit(0 if results.passed else 1)


if __name__ == "__main__":
    main()
