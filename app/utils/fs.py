"""
檔案系統工具
"""

from pathlib import Path
from typing import List, Optional
import shutil


def ensure_directory(path: Path) -> bool:
    """
    確保目錄存在，不存在則建立
    
    Args:
        path: 目錄路徑
    
    Returns:
        是否成功
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"錯誤: 無法建立目錄 {path} - {e}")
        return False


def create_instance_directories(instance_path: Path) -> bool:
    """
    建立標準的實例目錄結構
    
    Args:
        instance_path: 實例根目錄
    
    Returns:
        是否成功
    """
    directories = [
        instance_path / "server",
        instance_path / "runtime",
        instance_path / "backups",
        instance_path / "temp"
    ]
    
    for directory in directories:
        if not ensure_directory(directory):
            return False
    
    return True


def safe_delete(path: Path) -> bool:
    """
    安全刪除檔案或目錄
    
    Args:
        path: 要刪除的路徑
    
    Returns:
        是否成功
    """
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"錯誤: 刪除失敗 {path} - {e}")
        return False


def get_directory_size(path: Path) -> int:
    """
    計算目錄大小（遞迴）
    
    Args:
        path: 目錄路徑
    
    Returns:
        總大小（位元組）
    """
    total_size = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
    except Exception as e:
        print(f"警告: 計算目錄大小時發生錯誤 - {e}")
    
    return total_size


def find_files_by_pattern(directory: Path, pattern: str) -> List[Path]:
    """
    在目錄中尋找符合樣式的檔案
    
    Args:
        directory: 搜尋目錄
        pattern: 檔案樣式（glob pattern）
    
    Returns:
        符合的檔案列表
    """
    try:
        return list(directory.glob(pattern))
    except Exception as e:
        print(f"警告: 搜尋檔案時發生錯誤 - {e}")
        return []


def copy_file(source: Path, destination: Path) -> bool:
    """
    複製檔案
    
    Args:
        source: 來源檔案
        destination: 目標位置
    
    Returns:
        是否成功
    """
    try:
        ensure_directory(destination.parent)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"錯誤: 複製檔案失敗 - {e}")
        return False


def get_file_size_mb(file_path: Path) -> float:
    """
    取得檔案大小（MB）
    
    Args:
        file_path: 檔案路徑
    
    Returns:
        檔案大小（MB）
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0
