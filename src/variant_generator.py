"""
VariantGenerator — OCR 拼写变体生成器

拉丁学名在 OCR 扫描、PDF 文本提取、键盘输入时常出现拼写错误。
此模块自动生成常见 OCR 错误变体，作为搜索安全网。

核心规则（基于模糊物种搜索协议 v5.0）:
  1. 字符混淆: l↔1↔I, O↔0, r↔n, i↔j↔l, m↔rn
  2. 双字母变异: ll→l, tt→t 等
  3. 音节简化: 常见双字母→单字母
  4. 词尾变异: us→a, i→ii 等（拉丁文语法变体）

用法:
    from src.variant_generator import generate_variants
    variants = generate_variants("Ochetobius")
    # → ["Ochetobius", "Ochetobius", "Ochetobius", ...]
"""

from __future__ import annotations

from typing import List, Set


# ═══════════════════════════════════════════════════════════
# OCR 混淆规则
# ═══════════════════════════════════════════════════════════

# 单字符混淆映射
_CHAR_CONFUSIONS = {
    "l": "1I",      # l → 1, I
    "1": "lI",
    "I": "l1",
    "O": "0Q",      # O → 0, Q
    "0": "OQ",
    "r": "n",       # r → n
    "n": "r",
    "i": "jl",      # i → j, l
    "j": "i",
    "m": "rn",      # m → rn (双字符在 OCR 中常合并)
    "v": "u",       # v → u
    "u": "v",
}

# 常见双字母变异 (OCR 将双字母合并为单字母)
_DOUBLE_LETTER_PATTERNS = [
    ("ll", "l"),
    ("tt", "t"),
    ("ss", "s"),
    ("pp", "p"),
    ("ff", "f"),
    ("rr", "r"),
    ("nn", "n"),
    ("mm", "m"),
]

# 拉丁文词尾变异
_LATIN_SUFFIX_VARIANTS = [
    ("us", "i"),
    ("us", "a"),
    ("um", "a"),
    ("is", "e"),
    ("ae", "a"),
]


def _apply_char_confusion(name: str, idx: int) -> List[str]:
    """对指定位置的字符应用 OCR 混淆，返回所有可能的替换."""
    if idx >= len(name):
        return []
    char = name[idx]
    alternatives = _CHAR_CONFUSIONS.get(char, "")
    if not alternatives:
        return []
    results = []
    for alt in alternatives:
        variant = name[:idx] + alt + name[idx + 1:]
        if variant != name:
            results.append(variant)
    return results


def _apply_double_letter(name: str) -> List[str]:
    """应用双字母→单字母变异."""
    results = []
    for double, single in _DOUBLE_LETTER_PATTERNS:
        if double in name:
            results.append(name.replace(double, single, 1))
    return results


def _apply_suffix_variant(name: str) -> List[str]:
    """应用拉丁文词尾变异."""
    results = []
    lower = name.lower()
    for orig, variant in _LATIN_SUFFIX_VARIANTS:
        if lower.endswith(orig):
            # Preserve original case pattern
            suffix_len = len(orig)
            base = name[:-suffix_len]
            if name[-suffix_len:].isupper():
                results.append(base + variant.upper())
            elif name[-suffix_len:][0].isupper():
                results.append(base + variant.capitalize())
            else:
                results.append(base + variant)
    return results


def generate_variants(name: str) -> List[str]:
    """生成学名的所有 OCR 拼写变体.

    Args:
        name: 学名 (e.g. "Ochetobius", "Pseudaspius")

    Returns:
        去重的变体列表，包含原始名
    """
    variants: Set[str] = {name}

    # 逐字符 OCR 混淆
    for i in range(len(name)):
        confused = _apply_char_confusion(name, i)
        for v in confused:
            variants.add(v)

    # 双字母变异
    for v in list(variants):
        for dl_v in _apply_double_letter(v):
            variants.add(dl_v)

    # 词尾变异 (仅对完整属名/种加词)
    for v in list(variants):
        for sf_v in _apply_suffix_variant(v):
            variants.add(sf_v)

    # 首字母大写标准化
    result = []
    for v in variants:
        normalized = v[0].upper() + v[1:] if v else v
        if normalized not in result:
            result.append(normalized)

    return result


def generate_full_species_variants(genus: str, species: str) -> List[str]:
    """生成完整双名法学名的所有变体组合.

    Args:
        genus: 属名 (e.g. "Ochetobius")
        species: 种加词 (e.g. "elongatus")

    Returns:
        所有属名×种加词变体组合
    """
    genus_variants = generate_variants(genus)
    species_variants = generate_variants(species)

    result: Set[str] = set()
    for gv in genus_variants:
        for sv in species_variants:
            result.add(f"{gv} {sv}")
            result.add(f"{gv}. {sv}")
            result.add(f"{gv[0]}. {sv}")

    return sorted(result)
