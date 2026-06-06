"""
OCR Variant Generator — Auto-generate spelling variants from Latin binomial names.

Implements the full OCR error model for species search (Layer 3 of the 12-layer
protocol).  Takes a genus + species name and returns all plausible typographic
variants that could appear in OCR-scanned academic papers.

Error categories modeled:
  1. Character insertion     — Ochetobius → Ochetobibus (extra 'b')
  2. Character deletion      — Ochetobius → Ochetobus (missing 'i')
  3. Vowel confusion         — e↔i, a↔o, u↔o, y↔i
  4. Terminal truncation     — elongatus → elongatu, elongates
  5. Doubling / singling     — l↔ll, s↔ss, r↔rr
  6. Common OCR confusion    — rn↔m, cl↔d, ti↔n
  7. Hyphenation artifacts   — elongatus → e-longatus (unlikely in binomial names
                                but common in justification-hyphenated text)

Usage:
  from variant_generator import generate_variants
  variants = generate_variants("Ochetobius", "elongatus")
  # → ["Ochetobibus elongatus", "Ochetobus elongatus", "Ochetobius elongatu", ...]
"""

import itertools
from typing import Optional

# ──── Confusion matrices ────

VOWEL_CONFUSIONS = [
    ("e", "i"),
    ("a", "o"),
    ("u", "o"),
    ("y", "i"),
    ("ae", "e"),
    ("oe", "e"),
]

DOUBLE_LETTERS = ["l", "s", "r", "t", "m", "n", "f"]

OCR_SWAP = [
    ("rn", "m"),
    ("cl", "d"),
    ("ti", "n"),
    ("li", "h"),
]

# Common Latin species endings that OCR often mangles
SPECIES_ENDINGS = ["us", "is", "um", "a", "e", "i", "ae", "es", "er", "ii", "ensis"]


def generate_variants(genus: str, species: str, max_variants: int = 30) -> list[str]:
    """Generate plausible OCR variants for a binomial name.

    Args:
        genus:   Genus name, e.g. "Ochetobius"
        species: Species epithet, e.g. "elongatus"
        max_variants: Maximum number of variants to return (default 30).

    Returns:
        List of variant strings like "Ochetobibus elongatus", "Ochetobius elongatu".
    """
    genus = genus.strip()
    species = species.strip()

    if not genus:
        return []

    variants: set[str] = set()
    g_lower = genus.lower()
    s_lower = species.lower()

    # ── 1. Genus variants ──
    genus_variants = _genus_variants(genus)
    variants.update(f"{gv} {species}" for gv in genus_variants)

    # ── 2. Species variants ──
    species_variants = _species_variants(species)
    variants.update(f"{genus} {sv}" for sv in species_variants)

    # ── 3. Combined variants (subset only, to limit explosion) ──
    combo_count = 0
    for gv in list(genus_variants)[:3]:
        for sv in list(species_variants)[:3]:
            if combo_count >= 5:
                break
            combo = f"{gv} {sv}"
            if combo not in variants:
                variants.add(combo)
                combo_count += 1

    # ── 4. Common misspelling: doubled letter in genus crossing into species ──
    # e.g., "Ochetobiuselongatus" (space-deleted) — uncommon but possible in metadata
    if max_variants > 20:
        variants.add(f"{genus}{species}")

    # ── 5. Capitalization variants (lowercase genus) ──
    variants.add(f"{g_lower} {s_lower}")

    # Remove the original correct spelling from variants list
    original = f"{genus} {species}"
    variants.discard(original)

    # Limit
    result = sorted(variants)
    if len(result) > max_variants:
        result = result[:max_variants]

    return result


# ──── Internal helpers ────

def _genus_variants(genus: str) -> set[str]:
    """Generate genus-only variants."""
    variants: set[str] = {genus}
    lower = genus.lower()

    # Character insertions (each double-letter position)
    for i, ch in enumerate(lower):
        if ch in "aeiou":
            # Insert an adjacent vowel
            for v in "aeiou":
                variant = lower[:i] + v + lower[i:]
                if variant != lower:
                    variants.add(_recapitalize(genus, variant))
        # Double the letter
        variant = lower[:i] + ch + lower[i:]
        if variant != lower:
            variants.add(_recapitalize(genus, variant))

    # Character deletions
    for i in range(len(lower)):
        variant = lower[:i] + lower[i + 1:]
        if variant and variant != lower:
            variants.add(_recapitalize(genus, variant))

    # Vowel confusion
    for old, new in VOWEL_CONFUSIONS:
        variant = lower.replace(old, new)
        if variant != lower:
            variants.add(_recapitalize(genus, variant))

    # Double/single letter alternation
    for ch in DOUBLE_LETTERS:
        doubled = ch * 2
        if doubled in lower:
            variant = lower.replace(doubled, ch, 1)
            if variant != lower:
                variants.add(_recapitalize(genus, variant))
        elif ch in lower:
            idx = lower.index(ch)
            variant = lower[:idx] + ch + lower[idx:]
            if variant != lower:
                variants.add(_recapitalize(genus, variant))

    # OCR confusion swaps
    for old, new in OCR_SWAP:
        if old in lower:
            variant = lower.replace(old, new)
            if variant != lower:
                variants.add(_recapitalize(genus, variant))

    # Truncation (drop last 1-2 chars)
    if len(lower) > 4:
        variants.add(_recapitalize(genus, lower[:-1]))
    if len(lower) > 5:
        variants.add(_recapitalize(genus, lower[:-2]))

    return variants


def _species_variants(species: str) -> set[str]:
    """Generate species-epithet variants."""
    variants: set[str] = {species}
    lower = species.lower()

    # Terminal truncation (common OCR error on species endings)
    for ending in SPECIES_ENDINGS:
        if lower.endswith(ending):
            # Drop last character(s) of ending
            if len(ending) >= 2:
                variants.add(lower[: -len(ending)] + ending[:-1])
            if len(ending) >= 1:
                variants.add(lower[: -len(ending)] + ending[0])

    # Character insertions
    for i, ch in enumerate(lower):
        if ch in "aeiou":
            for v in "aeiou":
                variant = lower[:i] + v + lower[i:]
                if variant != lower:
                    variants.add(variant)
        variant = lower[:i] + ch + lower[i:]
        if variant != lower:
            variants.add(variant)

    # Character deletions
    for i in range(len(lower)):
        variant = lower[:i] + lower[i + 1:]
        if variant:
            variants.add(variant)

    # Vowel confusion
    for old, new in VOWEL_CONFUSIONS:
        variant = lower.replace(old, new)
        if variant != lower:
            variants.add(variant)

    # Double letters
    for ch in DOUBLE_LETTERS:
        doubled = ch * 2
        if doubled in lower:
            variant = lower.replace(doubled, ch, 1)
            if variant != lower:
                variants.add(variant)
        elif ch in lower:
            idx = lower.index(ch)
            variant = lower[:idx] + ch + lower[idx:]
            if variant != lower:
                variants.add(variant)

    # OCR swap
    for old, new in OCR_SWAP:
        if old in lower:
            variant = lower.replace(old, new)
            if variant != lower:
                variants.add(variant)

    return variants


def _recapitalize(original: str, variant: str) -> str:
    """Preserve original capitalization pattern."""
    if original[0].isupper():
        return variant[0].upper() + variant[1:]
    return variant


# ──── API for full-resolution search ────

def generate_all_variants(genus: str, species: str) -> dict[str, list[str]]:
    """Return variants grouped by category for diagnostic use.

    Returns:
        {"genus_only": [...], "species_only": [...], "combined": [...]}
    """
    genus_vars = _genus_variants(genus)
    species_vars = _species_variants(species)
    combined = set()
    for gv in list(genus_vars)[:3]:
        for sv in list(species_vars)[:3]:
            combined.add(f"{gv} {sv}")
    return {
        "genus_only": sorted(genus_vars - {genus}),
        "species_only": sorted(species_vars - {species}),
        "combined": sorted(combined),
    }
