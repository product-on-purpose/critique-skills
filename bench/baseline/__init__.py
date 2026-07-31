"""The frozen baseline comparison: `prompt.txt` (the generic "critique
this document" prompt text, unchanged for the life of v0.1.0) plus
`postprocess.py` (the documented, fixed rule that maps its free-text
output to a contract-valid envelope carrying `skill: "baseline-generic"`).

See `README.md` in this directory for the runner spec: how a P3
measurement agent invokes the prompt through `critique-critic` and calls
`postprocess()` on what comes back. This package does not itself call a
model; `postprocess()` is a pure function of text.
"""
