"""`python -m bench.baseline postprocess --raw FILE --artifact PATH
(--artifact-sha256 HEX | --artifact-file FILE) --model ID --timestamp TS
--out FILE`

A thin convenience CLI over `postprocess.postprocess`: maps one raw
baseline response, already saved to a file, into a contract-valid
envelope. This is not the P3 baseline runner itself (obtaining the raw
response by invoking the frozen prompt against a pinned model is out of
this module's scope, see `README.md`); it exists so the mapping rule can
be exercised and reproduced by hand, one response at a time, without
writing a throwaway script each time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from bench.baseline.postprocess import postprocess


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bench.baseline",
        description="Frozen baseline: map a raw response to a contract-valid envelope.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("postprocess", help="Map a raw baseline response to a contract-valid envelope.")
    cmd.add_argument("--raw", required=True, type=Path, help="File holding the model's raw response text.")
    cmd.add_argument("--artifact", required=True, help="Repository-relative POSIX path to the critiqued artifact.")
    cmd.add_argument(
        "--artifact-sha256", default=None, help="sha256 of the artifact bytes; required unless --artifact-file is given."
    )
    cmd.add_argument(
        "--artifact-file", type=Path, default=None, help="Compute --artifact-sha256 from this file instead of passing it."
    )
    cmd.add_argument("--model", required=True, help="Pinned model id.")
    cmd.add_argument("--timestamp", required=True, help="RFC 3339 UTC timestamp, e.g. 2026-07-31T00:00:00Z.")
    cmd.add_argument("--out", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command != "postprocess":
        print(f"usage error: unknown command {args.command!r}", file=sys.stderr)
        return 1

    if args.artifact_sha256 is None and args.artifact_file is None:
        print("usage error: one of --artifact-sha256 or --artifact-file is required", file=sys.stderr)
        return 1
    artifact_sha256 = args.artifact_sha256
    if args.artifact_file is not None:
        artifact_sha256 = hashlib.sha256(args.artifact_file.read_bytes()).hexdigest()

    raw = args.raw.read_text(encoding="utf-8")
    envelope = postprocess(
        raw, artifact=args.artifact, artifact_sha256=artifact_sha256, model=args.model, timestamp=args.timestamp
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(envelope, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote {args.out} ({len(envelope['findings'])} findings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
