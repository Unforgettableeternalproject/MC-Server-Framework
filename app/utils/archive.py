"""
壓縮檔案工具
"""

import zipfile
import tarfile
from pathlib import Path
from typing import Iterator, List, Optional
import fnmatch


def iter_matching_files(
    source_dir: Path,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> Iterator[Path]:
    """
    列舉來源目錄中符合條件的檔案

    Args:
        source_dir: 來源目錄
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表

    Yields:
        符合條件的檔案路徑（絕對路徑）
    """
    for file_path in source_dir.rglob('*'):
        if not file_path.is_file():
            continue

        rel_path_str = file_path.relative_to(source_dir).as_posix()
        if should_include_file(rel_path_str, include_patterns, exclude_patterns):
            yield file_path


def count_matching_files(
    source_dir: Path,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> int:
    """計算符合條件的檔案數量"""
    return sum(1 for _ in iter_matching_files(source_dir, include_patterns, exclude_patterns))


def create_zip_archive(
    source_dir: Path,
    output_file: Path,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> Optional[int]:
    """
    建立 ZIP 壓縮檔

    Args:
        source_dir: 來源目錄
        output_file: 輸出檔案
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表

    Returns:
        寫入的檔案數量；失敗時回傳 None
    """
    file_count = 0
    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in iter_matching_files(source_dir, include_patterns, exclude_patterns):
                rel_path = file_path.relative_to(source_dir)
                try:
                    zipf.write(file_path, arcname=rel_path)
                    file_count += 1
                except (PermissionError, OSError) as e:
                    # 伺服器執行中時個別檔案可能被鎖定，略過而非中斷整個備份
                    print(f"警告: 略過無法讀取的檔案 {rel_path} - {e}")

        return file_count

    except Exception as e:
        print(f"錯誤: 建立 ZIP 失敗 - {e}")
        return None


def create_tar_archive(
    source_dir: Path,
    output_file: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    compression: str = "gz"
) -> Optional[int]:
    """
    建立 TAR 壓縮檔

    Args:
        source_dir: 來源目錄
        output_file: 輸出檔案
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表
        compression: 壓縮格式 (gz, bz2, xz)

    Returns:
        寫入的檔案數量；失敗時回傳 None
    """
    file_count = 0
    try:
        mode_map = {
            "gz": "w:gz",
            "bz2": "w:bz2",
            "xz": "w:xz",
            "none": "w"
        }
        mode = mode_map.get(compression, "w:gz")

        with tarfile.open(output_file, mode) as tar:
            for file_path in iter_matching_files(source_dir, include_patterns, exclude_patterns):
                rel_path = file_path.relative_to(source_dir)
                try:
                    tar.add(file_path, arcname=str(rel_path))
                    file_count += 1
                except (PermissionError, OSError) as e:
                    print(f"警告: 略過無法讀取的檔案 {rel_path} - {e}")

        return file_count

    except Exception as e:
        print(f"錯誤: 建立 TAR 失敗 - {e}")
        return None


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """
    判斷單一相對路徑是否符合樣式

    規則：
      - 標準 glob 比對（'*' 亦可跨越 '/'，因此 'world*' 會涵蓋 'world/level.dat'）
      - 'dir/**' 視為「dir 目錄下的所有內容」
      - 樣式若指向目錄本身（如 'logs'），其底下所有檔案一併符合

    Args:
        file_path: 檔案相對路徑（POSIX 分隔符）
        pattern: 比對樣式

    Returns:
        是否符合
    """
    pattern = pattern.strip().replace('\\', '/')
    if not pattern:
        return False

    if fnmatch.fnmatch(file_path, pattern):
        return True

    # 'logs/**' → 目錄前綴 'logs/'
    if pattern.endswith('/**'):
        prefix = pattern[:-3]
        if file_path == prefix or file_path.startswith(prefix + '/'):
            return True
        # 前綴本身可能含萬用字元，例如 'world*/**'
        head = file_path.split('/', 1)[0]
        if fnmatch.fnmatch(head, prefix):
            return True
        return False

    # 'logs' → 視為目錄，涵蓋 'logs/latest.log'
    if not pattern.endswith('/'):
        pattern_as_dir = pattern + '/'
    else:
        pattern_as_dir = pattern

    if file_path.startswith(pattern_as_dir):
        return True

    return False


def should_include_file(
    file_path: str,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> bool:
    """
    判斷檔案是否應該被包含

    Args:
        file_path: 檔案相對路徑（POSIX 分隔符）
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表

    Returns:
        是否應該包含
    """
    file_path = file_path.replace('\\', '/')

    # 首先檢查排除樣式
    for pattern in exclude_patterns or []:
        if _matches_pattern(file_path, pattern):
            return False

    # 如果沒有包含樣式，則包含所有未排除的檔案
    if not include_patterns:
        return True

    # 檢查包含樣式
    for pattern in include_patterns:
        if _matches_pattern(file_path, pattern):
            return True

    return False


def list_archive_members(archive_file: Path) -> List[str]:
    """
    列出壓縮檔內的成員名稱

    Args:
        archive_file: 壓縮檔

    Returns:
        成員名稱列表；讀取失敗時回傳空列表
    """
    try:
        if archive_file.suffix == '.zip':
            with zipfile.ZipFile(archive_file, 'r') as zipf:
                return zipf.namelist()
        with tarfile.open(archive_file, 'r:*') as tar:
            return tar.getnames()
    except Exception as e:
        print(f"錯誤: 無法讀取壓縮檔 {archive_file.name} - {e}")
        return []


def _is_safe_member(name: str) -> bool:
    """檢查壓縮檔成員名稱是否安全（避免路徑穿越）"""
    normalized = name.replace('\\', '/')
    if normalized.startswith('/') or normalized.startswith('../'):
        return False
    if '/../' in normalized or normalized.endswith('/..'):
        return False
    # Windows 磁碟機代號，例如 'C:/...'
    if len(normalized) > 1 and normalized[1] == ':':
        return False
    return True


def extract_archive(archive_file: Path, destination: Path) -> bool:
    """
    解壓縮檔案

    Args:
        archive_file: 壓縮檔
        destination: 目標目錄

    Returns:
        是否成功
    """
    try:
        destination.mkdir(parents=True, exist_ok=True)

        if archive_file.suffix == '.zip':
            with zipfile.ZipFile(archive_file, 'r') as zipf:
                members = [n for n in zipf.namelist() if _is_safe_member(n)]
                skipped = len(zipf.namelist()) - len(members)
                if skipped:
                    print(f"警告: 略過 {skipped} 個路徑不安全的項目")
                zipf.extractall(destination, members=members)
        elif archive_file.suffix in ['.tar', '.gz', '.bz2', '.xz']:
            with tarfile.open(archive_file, 'r:*') as tar:
                members = [m for m in tar.getmembers() if _is_safe_member(m.name)]
                skipped = len(tar.getmembers()) - len(members)
                if skipped:
                    print(f"警告: 略過 {skipped} 個路徑不安全的項目")
                tar.extractall(destination, members=members)
        else:
            print(f"錯誤: 不支援的壓縮格式 {archive_file.suffix}")
            return False

        return True

    except Exception as e:
        print(f"錯誤: 解壓縮失敗 - {e}")
        return False
