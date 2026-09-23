import json
from pathlib import Path


class CodebookUnavailable(RuntimeError):
    pass


class UnknownCode(ValueError):
    pass


class Codebook:
    """
    Reads shared/codes.json without assuming an exact value shape.

    Gateway code shows that table entries may be either:
      "1": "Water"
    or:
      "1": {"label": "Water", "key": "WATER"}

    This class supports either form.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.tables = None
        self.reload()

    @property
    def available(self) -> bool:
        return self.tables is not None

    def reload(self):
        if not self.path.exists():
            self.tables = None
            return
        self.tables = json.loads(self.path.read_text(encoding="utf-8"))

    def require(self):
        if self.tables is None:
            raise CodebookUnavailable(
                f"Missing codebook: {self.path}. "
                "The gateway expects shared/codes.json; copy that file into the project."
            )

    def code_for(self, table: str, value) -> int:
        self.require()

        if isinstance(value, int):
            return value

        raw = str(value).strip()
        if raw.isdigit():
            return int(raw)

        entries = self.tables.get(table)
        if not isinstance(entries, dict):
            raise UnknownCode(f"Code table {table!r} is missing from {self.path}")

        wanted = self._normalize(raw)

        for code, entry in entries.items():
            candidates = []
            if isinstance(entry, dict):
                candidates.extend(
                    v for k, v in entry.items()
                    if k in {"label", "key", "name"} and v is not None
                )
            else:
                candidates.append(entry)

            if any(self._normalize(str(candidate)) == wanted for candidate in candidates):
                return int(code)

        raise UnknownCode(f"{value!r} is not defined in code table {table!r}")

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum())
