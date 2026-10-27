from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass(frozen=True)
class HashResult:
    path: Path
    algorithm: str
    digest: str
    size_bytes: int

    def to_dict(self):
        data = asdict(self)
        data["path"] = str(self.path)
        return data
