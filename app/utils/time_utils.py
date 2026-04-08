"""
時間工具
"""

from datetime import datetime, timedelta
from typing import Optional


def format_timestamp(dt: Optional[datetime], format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化時間戳記
    
    Args:
        dt: datetime 物件
        format: 格式字串
    
    Returns:
        格式化後的字串
    """
    if dt is None:
        return "N/A"
    return dt.strftime(format)


def format_duration(seconds: float) -> str:
    """
    格式化時間長度為人類可讀格式
    
    Args:
        seconds: 秒數
    
    Returns:
        如 "2h 15m 30s"
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    解析時間字串（如 "2h", "30m", "1d"）
    
    Args:
        time_str: 時間字串
    
    Returns:
        timedelta 物件，失敗時回傳 None
    """
    try:
        time_str = time_str.strip().lower()
        
        if time_str.endswith('d'):
            days = int(time_str[:-1])
            return timedelta(days=days)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return timedelta(hours=hours)
        elif time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return timedelta(minutes=minutes)
        elif time_str.endswith('s'):
            seconds = int(time_str[:-1])
            return timedelta(seconds=seconds)
        else:
            # 嘗試當作秒數
            seconds = int(time_str)
            return timedelta(seconds=seconds)
    except Exception:
        return None


def get_time_ago_string(dt: Optional[datetime]) -> str:
    """
    取得相對時間字串（如 "2 小時前"）
    
    Args:
        dt: datetime 物件
    
    Returns:
        相對時間字串
    """
    if dt is None:
        return "從未"
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} 秒前"
    elif seconds < 3600:
        return f"{int(seconds / 60)} 分鐘前"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} 小時前"
    else:
        return f"{int(seconds / 86400)} 天前"
