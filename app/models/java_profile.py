"""
Java Profile 模型

對應 java_registry.yml 的結構
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import subprocess


@dataclass
class JavaProfile:
    """單個 Java Profile"""
    name: str
    path: str
    version: str
    description: str = ""
    
    def get_path(self) -> Path:
        """取得 Java 執行檔的 Path 物件"""
        return Path(self.path)
    
    def exists(self) -> bool:
        """檢查 Java 執行檔是否存在"""
        return self.get_path().exists()
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        驗證 Java 執行檔是否有效
        
        Returns:
            (是否有效, 錯誤訊息)
        """
        java_path = self.get_path()
        
        if not java_path.exists():
            return False, f"Java 執行檔不存在: {java_path}"
        
        if not java_path.is_file():
            return False, f"路徑不是檔案: {java_path}"
        
        # 嘗試執行 java -version
        try:
            result = subprocess.run(
                [str(java_path), "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, f"Java 執行失敗 (exit code {result.returncode})"
            return True, None
        except subprocess.TimeoutExpired:
            return False, "Java 執行逾時"
        except Exception as e:
            return False, f"執行 Java 時發生錯誤: {str(e)}"
    
    def get_version_string(self) -> Optional[str]:
        """
        取得實際的 Java 版本字串
        
        Returns:
            版本字串，失敗時回傳 None
        """
        try:
            result = subprocess.run(
                [str(self.get_path()), "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Java version 通常在 stderr 第一行
            if result.stderr:
                return result.stderr.split('\n')[0]
            return None
        except Exception:
            return None


@dataclass
class JavaRegistry:
    """Java Registry - 管理所有 Java Profiles"""
    profiles: Dict[str, JavaProfile]
    
    def get_profile(self, name: str) -> Optional[JavaProfile]:
        """根據名稱取得 Profile"""
        return self.profiles.get(name)
    
    def list_profiles(self) -> list[str]:
        """列出所有 Profile 名稱"""
        return list(self.profiles.keys())
    
    def validate_all(self) -> Dict[str, tuple[bool, Optional[str]]]:
        """
        驗證所有 Profiles
        
        Returns:
            {profile_name: (是否有效, 錯誤訊息)}
        """
        results = {}
        for name, profile in self.profiles.items():
            results[name] = profile.validate()
        return results
    
    def get_valid_profiles(self) -> list[str]:
        """取得所有有效的 Profile 名稱"""
        valid = []
        for name, profile in self.profiles.items():
            if profile.exists():
                valid.append(name)
        return valid
