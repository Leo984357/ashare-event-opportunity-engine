from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .pipeline import read_announcements, read_financials, run_pipeline, write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Link A-share announcements into capital events and generate auditable research leads."
    )
    parser.add_argument("input", type=Path, help="Announcement CSV")
    parser.add_argument("--financials", type=Path, help="Optional company financial snapshot CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--as-of", help="Research reference date in YYYY-MM-DD; defaults to latest announcement date")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None
    announcements, input_errors = read_announcements(args.input)
    financials = read_financials(args.financials)
    result = run_pipeline(announcements, financials=financials, as_of=as_of)
    write_outputs(result, args.output_dir, input_errors=input_errors)

    audit = result["audit"]
    print(f"Announcements: {audit['unique_announcements']}")
    print(f"Capital events: {audit['linked_event_count']}")
    print(f"Research leads: {audit['opportunity_lead_count']}")
    print(f"Unknown product rate: {audit['unknown_product_rate']:.1%}")
    print(f"Unknown state rate: {audit['unknown_state_rate']:.1%}")
    print(f"Output: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
