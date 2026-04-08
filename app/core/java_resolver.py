"""
Java 路徑解析器

負責管理和解析 Java profiles
"""

from pathlib import Path
from typing import Optional
from ..models.java_profile import JavaProfile, JavaRegistry
from ..utils.yaml_loader import load_java_registry


class JavaResolver:
    """Java 解析器"""
    
    def __init__(self, config_path: Path):
        """
        初始化解析器
        
        Args:
            config_path: java_registry.yml 的路徑
        """
        self.config_path = config_path
        self.registry: Optional[JavaRegistry] = None
        self.load_registry()
    
    def load_registry(self) -> bool:
        """
        載入 Java Registry
        
        Returns:
            是否成功
        """
        self.registry = load_java_registry(self.config_path)
        return self.registry is not None
    
    def get_profile(self, profile_name: str) -> Optional[JavaProfile]:
        """
        取得指定的 Java Profile
        
        Args:
            profile_name: Profile 名稱
        
        Returns:
            JavaProfile 物件，找不到時回傳 None
        """
        if not self.registry:
            return None
        
        return self.registry.get_profile(profile_name)
    
    def resolve_java_path(self, profile_name: str) -> Optional[Path]:
        """
        解析 Java 執行檔路徑
        
        Args:
            profile_name: Profile 名稱
        
        Returns:
            Java 執行檔路徑，失敗時回傳 None
        """
        profile = self.get_profile(profile_name)
        if not profile:
            print(f"錯誤: 找不到 Java profile '{profile_name}'")
            return None
        
        java_path = profile.get_path()
        if not java_path.exists():
            print(f"錯誤: Java 執行檔不存在: {java_path}")
            return None
        
        return java_path
    
    def validate_profile(self, profile_name: str) -> tuple[bool, Optional[str]]:
        """
        驗證 Java Profile
        
        Args:
            profile_name: Profile 名稱
        
        Returns:
            (是否有效, 錯誤訊息)
        """
        profile = self.get_profile(profile_name)
        if not profile:
            return False, f"找不到 profile '{profile_name}'"
        
        return profile.validate()
    
    def list_profiles(self) -> list[str]:
        """
        列出所有 Profile 名稱
        
        Returns:
            Profile 名稱列表
        """
        if not self.registry:
            return []
        
        return self.registry.list_profiles()
    
    def validate_all(self) -> dict[str, tuple[bool, Optional[str]]]:
        """
        驗證所有 Profiles
        
        Returns:
            {profile_name: (是否有效, 錯誤訊息)}
        """
        if not self.registry:
            return {}
        
        return self.registry.validate_all()
    
    def get_valid_profiles(self) -> list[str]:
        """
        取得所有有效的 Profile 名稱
        
        Returns:
            有效的 Profile 名稱列表
        """
        if not self.registry:
            return []
        
        return self.registry.get_valid_profiles()
    
    def get_default_profile(self) -> Optional[str]:
        """
        取得預設 Profile（優先順序: java21 > java17 > java8）
        
        Returns:
            預設 Profile 名稱，找不到時回傳 None
        """
        preferred = ["java21", "java17", "java8"]
        valid_profiles = self.get_valid_profiles()
        
        for profile_name in preferred:
            if profile_name in valid_profiles:
                return profile_name
        
        # 如果沒有偏好的，回傳第一個有效的
        if valid_profiles:
            return valid_profiles[0]
        
        return None
