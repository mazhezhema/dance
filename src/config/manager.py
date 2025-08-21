"""
🎛️ 配置管理器
统一管理所有配置文件，支持动态加载和热更新
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

from .defaults import DEFAULT_CONFIG, merge_configs, validate_config, get_runtime_config

logger = logging.getLogger(__name__)

@dataclass
class ConfigSource:
    """配置源信息"""
    path: str
    priority: int  # 优先级，数字越大优先级越高
    required: bool = False
    
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.config_sources: List[ConfigSource] = []
        self.current_config: Dict[str, Any] = {}
        self.file_timestamps: Dict[str, float] = {}
        
        # 注册默认配置源
        self._register_default_sources()
        
    def _register_default_sources(self):
        """注册默认配置源"""
        # 配置文件优先级（从低到高）
        sources = [
            ConfigSource("config.json", 10),  # 主配置文件
            ConfigSource("config/viggle_config.json", 20),  # Viggle配置
            ConfigSource("config/accounts.json", 30),  # 账号配置
            ConfigSource("config/local.json", 40),  # 本地配置（可选）
            ConfigSource(".env.json", 50),  # 环境配置（可选）
        ]
        
        for source in sources:
            self.add_config_source(source)
    
    def add_config_source(self, source: ConfigSource):
        """添加配置源"""
        self.config_sources.append(source)
        # 按优先级排序
        self.config_sources.sort(key=lambda x: x.priority)
        
    def get_config_path(self, relative_path: str) -> Path:
        """获取配置文件完整路径"""
        return self.base_dir / relative_path
        
    def load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSON配置文件"""
        try:
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载配置文件失败: {file_path} - {e}")
            return None
            
    def save_json_file(self, file_path: Path, config: Dict[str, Any]):
        """保存JSON配置文件"""
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"配置文件已保存: {file_path}")
        except IOError as e:
            logger.error(f"保存配置文件失败: {file_path} - {e}")
            
    def check_file_changes(self) -> List[str]:
        """检查文件是否有变更"""
        changed_files = []
        
        for source in self.config_sources:
            file_path = self.get_config_path(source.path)
            if not file_path.exists():
                continue
                
            current_mtime = file_path.stat().st_mtime
            last_mtime = self.file_timestamps.get(source.path, 0)
            
            if current_mtime > last_mtime:
                changed_files.append(source.path)
                self.file_timestamps[source.path] = current_mtime
                
        return changed_files
        
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载完整配置"""
        if not force_reload and self.current_config:
            # 检查文件是否有变更
            changed_files = self.check_file_changes()
            if not changed_files:
                return self.current_config
            else:
                logger.info(f"检测到配置文件变更: {changed_files}")
        
        # 从默认配置开始
        config = get_runtime_config()
        
        # 按优先级加载配置文件
        for source in self.config_sources:
            file_path = self.get_config_path(source.path)
            
            if source.required and not file_path.exists():
                raise FileNotFoundError(f"必需的配置文件不存在: {file_path}")
                
            file_config = self.load_json_file(file_path)
            if file_config:
                config = merge_configs(config, file_config)
                logger.debug(f"已加载配置文件: {source.path}")
                
        # 验证配置
        errors = validate_config(config)
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  {k}: {v}" for k, v in errors.items())
            raise ValueError(error_msg)
            
        self.current_config = config
        logger.info("配置加载完成")
        return config
        
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点符号路径"""
        if not self.current_config:
            self.load_config()
            
        keys = key_path.split('.')
        value = self.current_config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key_path: str, value: Any, save_to_file: Optional[str] = None):
        """设置配置值"""
        if not self.current_config:
            self.load_config()
            
        keys = key_path.split('.')
        current = self.current_config
        
        # 导航到最后一级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # 设置值
        current[keys[-1]] = value
        
        # 可选：保存到指定文件
        if save_to_file:
            file_path = self.get_config_path(save_to_file)
            self.save_json_file(file_path, self.current_config)
            
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置区段"""
        return self.get(section, {})
        
    def update_section(self, section: str, updates: Dict[str, Any], save_to_file: Optional[str] = None):
        """更新配置区段"""
        current_section = self.get_section(section)
        updated_section = merge_configs(current_section, updates)
        self.set(section, updated_section, save_to_file)
        
    def create_config_template(self, template_path: str, template_data: Dict[str, Any]):
        """创建配置模板文件"""
        file_path = self.get_config_path(template_path)
        
        if file_path.exists():
            logger.warning(f"配置文件已存在，跳过创建: {file_path}")
            return
            
        self.save_json_file(file_path, template_data)
        logger.info(f"配置模板已创建: {file_path}")
        
    def backup_config(self, backup_dir: str = "config_backups"):
        """备份当前配置"""
        from datetime import datetime
        
        backup_path = self.base_dir / backup_dir
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for source in self.config_sources:
            source_path = self.get_config_path(source.path)
            if source_path.exists():
                backup_file = backup_path / f"{source.path.replace('/', '_')}_{timestamp}.json"
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                config_data = self.load_json_file(source_path)
                if config_data:
                    self.save_json_file(backup_file, config_data)
                    
        logger.info(f"配置已备份到: {backup_path}")
        
    def export_effective_config(self, output_path: str):
        """导出有效配置（合并后的最终配置）"""
        if not self.current_config:
            self.load_config()
            
        export_path = self.get_config_path(output_path)
        self.save_json_file(export_path, self.current_config)
        logger.info(f"有效配置已导出: {export_path}")

# 🌍 全局配置管理器实例
config_manager = ConfigManager()

# 🔧 便捷函数
def get_config(key_path: str = None, default: Any = None) -> Any:
    """获取配置值"""
    if key_path is None:
        return config_manager.load_config()
    return config_manager.get(key_path, default)

def set_config(key_path: str, value: Any, save_to_file: Optional[str] = None):
    """设置配置值"""
    config_manager.set(key_path, value, save_to_file)

def reload_config():
    """重新加载配置"""
    return config_manager.load_config(force_reload=True)

def get_accounts_config() -> List[Dict[str, Any]]:
    """获取账号配置"""
    accounts = get_config('accounts')
    if isinstance(accounts, list):
        return accounts
    elif isinstance(accounts, dict) and 'accounts' in accounts:
        return accounts['accounts']
    else:
        return []

def get_viggle_config() -> Dict[str, Any]:
    """获取Viggle配置"""
    return get_config('viggle', {})

def get_processing_config() -> Dict[str, Any]:
    """获取处理配置"""
    return get_config('processing', {})

def get_timeouts_config() -> Dict[str, Any]:
    """获取超时配置"""
    return get_config('timeouts', {})

if __name__ == "__main__":
    # 测试配置管理器
    print("🎛️ 配置管理器测试")
    print("=" * 50)
    
    # 创建测试配置管理器
    manager = ConfigManager(".")
    
    try:
        # 加载配置
        config = manager.load_config()
        print(f"✅ 配置加载成功，包含 {len(config)} 个顶级配置项")
        
        # 测试获取配置值
        daily_limit = manager.get('accounts.daily_limit')
        print(f"📊 每日限制: {daily_limit}")
        
        # 测试获取区段
        timeouts = manager.get_section('timeouts')
        print(f"⏱️ 超时配置: {len(timeouts)} 项")
        
        # 测试便捷函数
        batch_size = get_config('batch_processing.batch_size')
        print(f"📦 批次大小: {batch_size}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
