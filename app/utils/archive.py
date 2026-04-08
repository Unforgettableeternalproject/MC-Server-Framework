"""
壓縮檔案工具
"""

import zipfile
import tarfile
from pathlib import Path
from typing import List, Optional
import fnmatch


def create_zip_archive(
    source_dir: Path,
    output_file: Path,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> bool:
    """
    建立 ZIP 壓縮檔
    
    Args:
        source_dir: 來源目錄
        output_file: 輸出檔案
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表
    
    Returns:
        是否成功
    """
    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # 取得相對路徑
                rel_path = file_path.relative_to(source_dir)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                # 檢查是否應該包含
                if not should_include_file(rel_path_str, include_patterns, exclude_patterns):
                    continue
                
                # 加入壓縮檔
                zipf.write(file_path, arcname=rel_path)
        
        return True
    
    except Exception as e:
        print(f"錯誤: 建立 ZIP 失敗 - {e}")
        return False


def create_tar_archive(
    source_dir: Path,
    output_file: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    compression: str = "gz"
) -> bool:
    """
    建立 TAR 壓縮檔
    
    Args:
        source_dir: 來源目錄
        output_file: 輸出檔案
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表
        compression: 壓縮格式 (gz, bz2, xz)
    
    Returns:
        是否成功
    """
    try:
        mode_map = {
            "gz": "w:gz",
            "bz2": "w:bz2",
            "xz": "w:xz",
            "none": "w"
        }
        mode = mode_map.get(compression, "w:gz")
        
        with tarfile.open(output_file, mode) as tar:
            for file_path in source_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # 取得相對路徑
                rel_path = file_path.relative_to(source_dir)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                # 檢查是否應該包含
                if not should_include_file(rel_path_str, include_patterns, exclude_patterns):
                    continue
                
                # 加入壓縮檔
                tar.add(file_path, arcname=rel_path)
        
        return True
    
    except Exception as e:
        print(f"錯誤: 建立 TAR 失敗 - {e}")
        return False


def should_include_file(
    file_path: str,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> bool:
    """
    判斷檔案是否應該被包含
    
    Args:
        file_path: 檔案相對路徑
        include_patterns: 包含樣式列表
        exclude_patterns: 排除樣式列表
    
    Returns:
        是否應該包含
    """
    # 首先檢查排除樣式
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_path, pattern) or file_path.startswith(pattern.rstrip('/**')):
            return False
    
    # 如果沒有包含樣式，則包含所有未排除的檔案
    if not include_patterns:
        return True
    
    # 檢查包含樣式
    for pattern in include_patterns:
        if fnmatch.fnmatch(file_path, pattern) or file_path.startswith(pattern.rstrip('/**')):
            return True
    
    return False


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
                zipf.extractall(destination)
        elif archive_file.suffix in ['.tar', '.gz', '.bz2', '.xz']:
            with tarfile.open(archive_file, 'r:*') as tar:
                tar.extractall(destination)
        else:
            print(f"錯誤: 不支援的壓縮格式 {archive_file.suffix}")
            return False
        
        return True
    
    except Exception as e:
        print(f"錯誤: 解壓縮失敗 - {e}")
        return False
