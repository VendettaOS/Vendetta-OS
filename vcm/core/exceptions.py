class VCMError(Exception):
    """Error esperado del Vendetta Case Manager."""

class ManifestError(VCMError):
    """Manifiesto ausente, dañado o incompatible."""

class FileChangedError(VCMError):
    """Un archivo cambió mientras era leído."""
