"""
File hashing utilities for DMLClean.

Uses xxhash for fast, non-cryptographic file fingerprinting.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import xxhash
from loguru import logger


def hash_file(
    path: Path,
    algorithm: str = "xxh64",
    chunk_size: int = 8192,
    callback: Callable[[int], None] | None = None,
) -> str:
    """
    Compute hash of a file synchronously.

    Args:
        path: Path to file to hash.
        algorithm: Hash algorithm ('xxh32', 'xxh64', 'xxh3_64', 'xxh128').
        chunk_size: Number of bytes to read at a time.
        callback: Optional callback(bytes_processed) for progress.

    Returns:
        str: Hexadecimal hash string.

    Raises:
        FileNotFoundError: If file doesn't exist.
        OSError: If file cannot be read.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if algorithm == "xxh64":
        hasher = xxhash.xxh64()
    elif algorithm == "xxh32":
        hasher = xxhash.xxh32()  # type: ignore[assignment]  # xxh32 returns different type
    elif algorithm == "xxh3_64":
        hasher = xxhash.xxh3_64()
    elif algorithm == "xxh128":
        hasher = xxhash.xxh128()  # type: ignore[assignment]  # xxh128 returns different type
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    bytes_processed = 0

    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
            bytes_processed += len(chunk)
            if callback:
                callback(bytes_processed)

    hash_hex = hasher.hexdigest()
    logger.debug(f"Hashed {path} ({bytes_processed} bytes) -> {hash_hex[:16]}...")
    return hash_hex


async def hash_file_async(
    path: Path,
    algorithm: str = "xxh64",
    chunk_size: int = 8192,
    callback: Callable[[int], None] | None = None,
) -> str:
    """
    Compute hash of a file asynchronously.

    Args:
        path: Path to file to hash.
        algorithm: Hash algorithm ('xxh32', 'xxh64', 'xxh3_64', 'xxh128').
        chunk_size: Number of bytes to read at a time.
        callback: Optional async callback(bytes_processed) for progress.

    Returns:
        str: Hexadecimal hash string.

    Raises:
        FileNotFoundError: If file doesn't exist.
        OSError: If file cannot be read.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Run sync hashing in executor to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hash_file, path, algorithm, chunk_size, callback)


def hash_files_parallel(
    paths: list[Path],
    algorithm: str = "xxh64",
    max_workers: int | None = None,
) -> dict[Path, str]:
    """
    Hash multiple files in parallel.

    Args:
        paths: List of file paths to hash.
        algorithm: Hash algorithm to use.
        max_workers: Maximum number of worker threads.

    Returns:
        dict[Path, str]: Mapping of path to hash string.
    """
    from concurrent.futures import ThreadPoolExecutor

    results: dict[Path, str] = {}

    def hash_with_path(path: Path) -> tuple[Path, str]:
        try:
            return (path, hash_file(path, algorithm))
        except Exception as e:
            logger.warning(f"Failed to hash {path}: {e}")
            return (path, "")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for path, hash_hex in executor.map(hash_with_path, paths):
            if hash_hex:
                results[path] = hash_hex

    return results


async def hash_files_concurrent(
    paths: list[Path],
    algorithm: str = "xxh64",
    max_concurrent: int = 10,
) -> dict[Path, str]:
    """
    Hash multiple files concurrently with semaphore.

    Args:
        paths: List of file paths to hash.
        algorithm: Hash algorithm to use.
        max_concurrent: Maximum concurrent hashing operations.

    Returns:
        dict[Path, str]: Mapping of path to hash string.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def hash_with_semaphore(path: Path) -> tuple[Path, str]:
        async with semaphore:
            try:
                hash_hex = await hash_file_async(path, algorithm)
                return (path, hash_hex)
            except Exception as e:
                logger.warning(f"Failed to hash {path}: {e}")
                return (path, "")

    tasks = [hash_with_semaphore(path) for path in paths]
    results_list = await asyncio.gather(*tasks)

    return {path: hash_hex for path, hash_hex in results_list if hash_hex}


def find_duplicates(
    paths: list[Path],
    algorithm: str = "xxh64",
) -> dict[str, list[Path]]:
    """
    Find duplicate files by hash.

    Args:
        paths: List of file paths to check.
        algorithm: Hash algorithm to use.

    Returns:
        dict[str, list[Path]]: Mapping of hash to list of duplicate paths.
            Only includes hashes with more than one file.
    """
    # First, group by size (quick filter)
    size_groups: dict[int, list[Path]] = {}
    for path in paths:
        if path.is_file():
            try:
                size = path.stat().st_size
                if size not in size_groups:
                    size_groups[size] = []
                size_groups[size].append(path)
            except OSError:
                continue

    # Only hash files with matching sizes
    candidates = [p for group in size_groups.values() if len(group) > 1 for p in group]

    if not candidates:
        return {}

    # Hash candidates
    hashes = hash_files_parallel(candidates, algorithm)

    # Group by hash
    hash_groups: dict[str, list[Path]] = {}
    for path, hash_hex in hashes.items():
        if hash_hex:
            if hash_hex not in hash_groups:
                hash_groups[hash_hex] = []
            hash_groups[hash_hex].append(path)

    # Return only groups with duplicates
    return {h: paths for h, paths in hash_groups.items() if len(paths) > 1}
