"""
Data Transfer Objects (DTOs) for DMLClean Service Layer.

Pydantic v2 models for all service request/response types.
Provides:
- Type safety
- Validation
- Serialization
- Consistent API boundaries

Architecture:
    ```
    CLI → Request DTO → Service → Result DTO → CLI
    ```

Example:
    ```python
    from dmlclean.dtos import CleanRequest, CleanResult

    # Create request
    request = CleanRequest(
        paths=[Path("/tmp")],
        mode="trash",
        profile="developer",
    )

    # Service processes request
    result: CleanResult = service.execute_clean(request)

    # Access typed result
    print(f"Deleted {result.files_deleted} files")
    ```
"""

from dmlclean.dtos.clean import CleanProfile, CleanRequest, CleanRequestMode, CleanResult
from dmlclean.dtos.history import HistoryEntry, HistoryListResult, HistoryRequest
from dmlclean.dtos.protect import ProtectionEntry, ProtectRequest, ProtectResult
from dmlclean.dtos.scan import ScanMode, ScanRequest, ScanResult, ScanStats
from dmlclean.dtos.schedule import ScheduleEntry, ScheduleListResult, ScheduleRequest

__all__ = [
    "CleanProfile",
    # Clean DTOs
    "CleanRequest",
    "CleanRequestMode",
    "CleanResult",
    "HistoryEntry",
    "HistoryListResult",
    # History DTOs
    "HistoryRequest",
    # Protect DTOs
    "ProtectRequest",
    "ProtectResult",
    "ProtectionEntry",
    "ScanMode",
    # Scan DTOs
    "ScanRequest",
    "ScanResult",
    "ScanStats",
    "ScheduleEntry",
    "ScheduleListResult",
    # Schedule DTOs
    "ScheduleRequest",
]
