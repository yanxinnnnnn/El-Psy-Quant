"""Symbol-universe primitives for local research inputs."""

from collections.abc import Iterable


def normalize_symbol(symbol: str) -> str:
    """Normalize one local research symbol."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must not be empty")
    return symbol.strip().upper()


def build_symbol_universe(symbols: Iterable[str]) -> tuple[str, ...]:
    """Build an immutable, order-preserving local research universe."""
    if isinstance(symbols, str):
        raise ValueError(
            "symbols must be an iterable of symbol strings, not a single symbol"
        )

    normalized_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = normalize_symbol(symbol)
        if normalized in seen:
            raise ValueError(f"duplicate symbol: {normalized}")
        seen.add(normalized)
        normalized_symbols.append(normalized)

    if not normalized_symbols:
        raise ValueError("symbols must not be empty")
    return tuple(normalized_symbols)
