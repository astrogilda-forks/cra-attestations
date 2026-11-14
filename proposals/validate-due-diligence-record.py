#!/usr/bin/env python3
"""Validate the due diligence record examples, and prove the schema refuses.

The valid example must pass. The invalid example must be refused, and the run lists
each reason. Six further mutations of the valid example are each records that a
free-text form cannot refuse and this schema does.

Run: python3 validate-due-diligence-record.py   (needs jsonschema)
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - dependency reported, never guessed
    sys.stderr.write("jsonschema is not installed; install it to run this check\n")
    raise SystemExit(2)

HERE = pathlib.Path(__file__).parent
SCHEMA = json.loads((HERE / "due-diligence-record.schema.json").read_text())
VALID = json.loads((HERE / "due-diligence-record.example.json").read_text())
INVALID = json.loads((HERE / "due-diligence-record.invalid.example.json").read_text())


def _entry(d: dict, i: int) -> dict:
    return d["properties_checked"][i]


def above_low_risk_without_properties(d: dict) -> None:
    del d["properties_checked"]


def low_risk_without_reason(d: dict) -> None:
    d["risk"] = {"level": "low"}
    del d["properties_checked"]


def purl_without_version(d: dict) -> None:
    d["component"]["purl"] = "pkg:github/example-org/libexample-parser"


def met_without_a_source(d: dict) -> None:
    del _entry(d, 0)["evidence_url"]


def failed_without_action(d: dict) -> None:
    del _entry(d, 2)["action_taken"]


def fuzzing_run_without_digest(d: dict) -> None:
    del _entry(d, 3)["evidence_digest"]


MUTATIONS = [
    ("a component above low risk with no property entries", above_low_risk_without_properties),
    ("a low risk level with no reason", low_risk_without_reason),
    ("a PURL that names no version", purl_without_version),
    ("a met property that names no source", met_without_a_source),
    ("a failed property with no action taken", failed_without_action),
    ("a manufacturer test run with no digest of its log", fuzzing_run_without_digest),
]


def errors(instance: dict) -> list[str]:
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def main() -> int:
    Draft202012Validator.check_schema(SCHEMA)
    failed = False

    found = errors(VALID)
    print(f"valid example: {'accepted' if not found else 'REFUSED'}")
    for line in found:
        print(f"  {line}")
    failed |= bool(found)

    found = errors(INVALID)
    print(f"invalid example: {'refused' if found else 'ACCEPTED'}, {len(found)} reasons")
    for line in found:
        print(f"  {line}")
    failed |= not found

    refused = 0
    for label, mutate in MUTATIONS:
        instance = copy.deepcopy(VALID)
        mutate(instance)
        if errors(instance):
            refused += 1
            print(f"refused: {label}")
        else:
            print(f"ACCEPTED (should be refused): {label}")
    print(f"{refused} of {len(MUTATIONS)} mutations refused")
    failed |= refused != len(MUTATIONS)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
