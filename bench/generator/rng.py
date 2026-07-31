"""Seeding and the counter-mode blake2b PRNG.

Everything here is copied field for field from `bench/generator/README.md`
("Determinism" section): the corpus root seed, the key-derivation function,
and `SeededRng` itself. `random`, `secrets`, and `os.urandom` are forbidden
in the entire `bench/` tree; blake2b is stdlib, byte-exact by specification,
and identical on every platform and every Python version, which is what a
correctness property with a CI job attached requires.
"""

from __future__ import annotations

import hashlib

CORPUS_SEED = "critique-skills/bench/corpus/v1"
PERSON = b"critique-bench"


def root_seed() -> bytes:
    """The single root of the whole corpus's key material."""
    return hashlib.blake2b(CORPUS_SEED.encode("utf-8"), digest_size=16, person=PERSON).digest()


def derive(parent: bytes, *parts: object) -> bytes:
    """Derive a 128-bit child key from `parent` and an ordered tuple of parts.

    Each part is separated by a unit separator byte before hashing, so
    `("ab", "c")` and `("a", "bc")` derive different keys even though their
    naive string concatenation is identical.
    """
    h = hashlib.blake2b(digest_size=16, person=PERSON)
    h.update(parent)
    for part in parts:
        h.update(b"\x1f")  # unit separator
        h.update(str(part).encode("utf-8"))
    return h.digest()


class SeededRng:
    """Counter-mode blake2b. Fully specified by the hash, so stable across
    Python versions and platforms forever, unlike the `random` module's
    Mersenne Twister internals.

    `below`, `choice`, `shuffle`, `sample`, and `child` are the whole
    surface a domain module is permitted to use. There is no float API on
    purpose: float arithmetic in generated content is platform-dependent
    rounding, forbidden in the entire `bench/` tree.
    """

    def __init__(self, seed: bytes) -> None:
        self._seed = seed
        self._counter = 0
        self._buf = b""

    def _refill(self) -> None:
        h = hashlib.blake2b(digest_size=32, person=PERSON)
        h.update(self._seed)
        h.update(self._counter.to_bytes(8, "big"))
        self._counter += 1
        self._buf += h.digest()

    def bits(self, k: int) -> int:
        """k uniform bits, big-endian, taken from whole bytes and right-shifted."""
        if k < 0:
            raise ValueError("bits(k) requires k >= 0")
        nbytes = (k + 7) // 8
        while len(self._buf) < nbytes:
            self._refill()
        chunk, self._buf = self._buf[:nbytes], self._buf[nbytes:]
        if k == 0:
            return 0
        return int.from_bytes(chunk, "big") >> (8 * nbytes - k)

    def below(self, n: int) -> int:
        """Uniform integer in [0, n) by rejection sampling. No modulo bias, no floats."""
        if n < 1:
            raise ValueError("below(n) requires n >= 1")
        if n == 1:
            return 0
        k = (n - 1).bit_length()
        while True:
            v = self.bits(k)
            if v < n:
                return v

    def choice(self, seq):
        return seq[self.below(len(seq))]

    def shuffle(self, items) -> None:
        """Fisher-Yates, descending, in place."""
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]

    def sample(self, seq, k):
        """Shuffle a copy, take a prefix."""
        pool = list(seq)
        self.shuffle(pool)
        return pool[:k]

    def child(self, *parts: object) -> "SeededRng":
        """An independent derived stream. A pure function of this stream's
        own seed and `parts`: it does not consume from this stream (no call
        to `bits`), so the order in which callers create children never
        matters, only the parts each one is keyed by."""
        return SeededRng(derive(self._seed, *parts))
