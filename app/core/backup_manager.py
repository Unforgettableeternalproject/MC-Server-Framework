"""
備份管理器

負責執行和管理伺服器備份
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json
import re
import shutil

from ..models.server_config import ServerInstanceConfig
from ..models.backup_policy import BackupPolicy, BackupRecord, BackupStatus, BackupMode, BackupProvider
from ..core.path_resolver import PathResolver
from ..core.launcher import ServerLauncher
from ..utils.archive import (
    create_zip_archive,
    create_tar_archive,
    count_matching_files,
    extract_archive,
    list_archive_members,
)
from ..utils.process import send_command


HISTORY_LIMIT = 100


class BackupManager:
    """備份管理器"""

    def __init__(self, config: ServerInstanceConfig, launcher: Optional[ServerLauncher] = None):
        """
        初始化備份管理器

        Args:
            config: 伺服器設定
            launcher: 伺服器啟動器（用於發送備份鉤子指令與檢查執行狀態）
        """
        self.config = config
        self.launcher = launcher
        self.paths = PathResolver(config)
        self.policy = self._create_policy_from_config()

    def _create_policy_from_config(self) -> BackupPolicy:
        """從設定建立備份策略"""
        backup_config = self.config.backup

        return BackupPolicy(
            enabled=backup_config.enabled,
            mode=BackupMode(backup_config.mode),
            provider=BackupProvider(backup_config.provider),
            keep_last=backup_config.retention.keep_last,
            keep_days=backup_config.retention.keep_days,
            compression=backup_config.compression,
            include_patterns=backup_config.include,
            exclude_patterns=backup_config.exclude
        )

    def should_backup(self) -> bool:
        """判斷是否應該執行備份"""
        if not self.config.features.allow_internal_backup:
            return False
        return self.policy.should_backup()

    def get_skip_reason(self) -> Optional[str]:
        """
        取得無法備份的原因

        Returns:
            原因說明；可以備份時回傳 None
        """
        if not self.config.features.allow_internal_backup:
            return "features.allow_internal_backup 為 false"
        if not self.policy.enabled:
            return "backup.enabled 為 false"
        if self.policy.provider == BackupProvider.DISABLED:
            return "backup.provider 為 disabled"
        if self.policy.provider == BackupProvider.EXTERNAL:
            return "backup.provider 為 external（由外部系統負責備份）"
        return None

    def create_backup(
        self,
        force: bool = False,
        trigger: str = "manual",
        cleanup: bool = True
    ) -> Optional[BackupRecord]:
        """
        建立備份

        Args:
            force: 忽略 enabled / provider 設定強制備份
            trigger: 觸發來源（manual / scheduled / pre-restore），僅用於記錄
            cleanup: 完成後是否套用保留策略清理舊備份

        Returns:
            備份記錄，未執行時回傳 None
        """
        skip_reason = self.get_skip_reason()
        if skip_reason and not force:
            print(f"備份未執行: {skip_reason}")
            print("（可加上 --force 強制備份）")
            return None

        server_name = self.config.meta.name
        print(f"開始備份 {server_name}...")

        start_time = datetime.now()
        record = BackupRecord(
            server_name=server_name,
            backup_file=Path(),  # 暫時
            created_at=start_time,
            status=BackupStatus.RUNNING
        )

        hooks_ran = False
        try:
            # 先確認真的有東西可以備份，避免產生空壓縮檔
            server_root = self.paths.get_server_root()
            if not server_root.exists():
                record.status = BackupStatus.FAILED
                record.error_message = f"伺服器目錄不存在: {server_root}"
                print(f"備份失敗: {record.error_message}")
                self._append_history(record, trigger)
                return record

            match_count = count_matching_files(
                server_root,
                self.policy.include_patterns,
                self.policy.exclude_patterns
            )
            if match_count == 0:
                record.status = BackupStatus.FAILED
                record.error_message = (
                    "沒有任何檔案符合 backup.include / backup.exclude 設定，"
                    "已中止以免產生空備份"
                )
                print(f"備份失敗: {record.error_message}")
                self._append_history(record, trigger)
                return record

            print(f"符合條件的檔案: {match_count} 個")

            # 執行 before_backup 鉤子（save-off / save-all）
            hooks_ran = self._run_hooks(self.config.backup.hooks.before_backup, "before_backup")

            # 建立備份檔案
            backup_file, written = self._create_backup_archive()

            # 無論成功與否都要還原 save-on
            if hooks_ran:
                self._run_hooks(self.config.backup.hooks.after_backup, "after_backup")
                hooks_ran = False

            if not backup_file:
                record.status = BackupStatus.FAILED
                record.error_message = "建立備份檔案失敗"
                print(f"備份失敗: {record.error_message}")
                self._append_history(record, trigger)
                return record

            record.backup_file = backup_file
            record.size_bytes = int(backup_file.stat().st_size)

            # 成功
            end_time = datetime.now()
            record.status = BackupStatus.SUCCESS
            record.duration_seconds = (end_time - start_time).total_seconds()

            size_mb = record.get_size_mb()
            print(f"備份完成: {backup_file.name} ({written} 個檔案, {size_mb:.2f} MB)")

            # 清理舊備份（還原前的安全備份不清理，以免刪掉正要還原的那一份）
            if cleanup:
                self.cleanup_old_backups()

            self._append_history(record, trigger)
            return record

        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            print(f"備份失敗: {e}")
            self._append_history(record, trigger)
            return record

        finally:
            # 例外路徑也要確保伺服器恢復存檔
            if hooks_ran:
                self._run_hooks(self.config.backup.hooks.after_backup, "after_backup")

    def _create_backup_archive(self) -> tuple[Optional[Path], int]:
        """
        建立備份壓縮檔

        Returns:
            (備份檔路徑, 寫入檔案數)；失敗時路徑為 None
        """
        server_root = self.paths.get_server_root()
        backup_dir = self.paths.get_backup_path()
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 產生檔案名稱（時間戳只到秒，同秒內的備份需加序號避免覆蓋既有備份）
        filename = self.policy.get_backup_filename(self.config.meta.name)
        backup_file = backup_dir / filename

        if backup_file.exists():
            stem, suffix = backup_file.stem, backup_file.suffix
            for counter in range(2, 1000):
                candidate = backup_dir / f"{stem}-{counter}{suffix}"
                if not candidate.exists():
                    backup_file = candidate
                    break
            else:
                print("錯誤: 無法產生不重複的備份檔名")
                return None, 0

        # 清掉先前被中斷留下的暫存檔
        for stale in backup_dir.glob("*.part"):
            try:
                stale.unlink()
            except OSError:
                pass

        # 先寫入 .part 暫存檔，完成後才改名。
        # 這樣即使備份途中程序被終止，也只會留下不會被誤認為備份的殘檔。
        temp_file = backup_file.with_name(backup_file.name + ".part")

        # 建立壓縮檔
        compression = self.policy.compression.lower()

        if compression == "zip":
            written = create_zip_archive(
                source_dir=server_root,
                output_file=temp_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns
            )
        elif compression in ["tar", "tar.gz", "gz"]:
            written = create_tar_archive(
                source_dir=server_root,
                output_file=temp_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns,
                compression="gz"
            )
        else:
            print(f"警告: 不支援的壓縮格式 '{compression}'，使用 zip")
            written = create_zip_archive(
                source_dir=server_root,
                output_file=temp_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns
            )

        if written is None:
            temp_file.unlink(missing_ok=True)
            return None, 0

        if written == 0:
            print("錯誤: 備份內容為空，已刪除產生的壓縮檔")
            temp_file.unlink(missing_ok=True)
            return None, 0

        # 完成後才讓它成為一份正式備份
        try:
            temp_file.replace(backup_file)
        except OSError as e:
            print(f"錯誤: 無法完成備份檔命名 - {e}")
            temp_file.unlink(missing_ok=True)
            return None, 0

        return backup_file, written

    # ------------------------------------------------------------------
    # 鉤子執行
    # ------------------------------------------------------------------

    def _server_is_running(self) -> bool:
        """檢查伺服器是否執行中"""
        if self.launcher:
            return self.launcher.is_running()

        # 沒有 launcher 時（例如排程守護程序），直接依 PID 檔案判斷
        from ..utils.process import is_process_running

        pid = self._read_server_pid()
        if pid is None:
            return False
        return is_process_running(pid)

    def _read_server_pid(self) -> Optional[int]:
        """
        讀取伺服器 PID 檔案

        launcher 寫入的是 JSON（{"pid": ..., ...}），此處同時容忍純數字格式。
        """
        pid_file = self.paths.get_pid_file()
        if not pid_file.exists():
            return None

        try:
            content = pid_file.read_text(encoding='utf-8').strip()
        except Exception:
            return None

        if not content:
            return None

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                pid = data.get("pid")
                return int(pid) if pid is not None else None
            return int(data)
        except (ValueError, TypeError):
            pass

        try:
            return int(content)
        except ValueError:
            return None

    def _get_rcon(self):
        """
        建立並連線 RCON；不可用時回傳 None

        優先讀取 server.properties 中的實際設定（密碼可能是自動生成的）
        """
        from ..core.rcon_manager import RCONManager, RCONError, get_rcon_config_from_properties

        if not self.config.rcon.enabled:
            return None

        host = self.config.rcon.host or "localhost"
        port = self.config.rcon.port
        password = self.config.rcon.password

        props_config = get_rcon_config_from_properties(self.paths.get_server_properties())
        if props_config:
            if not props_config.get('enabled'):
                return None
            port = props_config.get('port', port)
            if props_config.get('password'):
                password = props_config['password']

        if not password:
            return None

        try:
            rcon = RCONManager(host=host, port=port, password=password)
            rcon.connect()
            return rcon
        except RCONError as e:
            print(f"警告: RCON 連線失敗 ({e})")
            return None
        except Exception as e:
            print(f"警告: RCON 連線失敗 ({e})")
            return None

    def get_online_player_count(self) -> Optional[int]:
        """
        透過 RCON 查詢目前在線玩家數

        Returns:
            在線人數；無法查詢時（伺服器未執行、RCON 不可用、回應無法解析）回傳 None
        """
        if not self._server_is_running():
            return None

        rcon = self._get_rcon()
        if not rcon:
            return None

        try:
            response = rcon.send_command("list")
        except Exception:
            return None
        finally:
            rcon.disconnect()

        # 典型回應: "There are 2 of a max of 20 players online: Alice, Bob"
        match = re.search(r'\d+', response or "")
        if not match:
            return None
        return int(match.group())

    # 伺服器寫入玩家狀態的位置：玩家登出、自動存檔時都會更新這些檔案的 mtime
    PLAYER_DATA_DIRS = ("playerdata", "stats", "advancements")

    def get_last_player_activity(self) -> Optional[datetime]:
        """
        取得最後一次玩家資料被寫入的時間

        以 world/playerdata、world/stats、world/advancements 的最新 mtime 為準。
        伺服器會在玩家登出與每次自動存檔時寫入這些檔案，因此不需要輪詢就能得知
        「上次備份之後有沒有人玩過」——短暫上線又離線也抓得到。

        Returns:
            最後活動時間；找不到任何玩家資料時回傳 None
        """
        latest: Optional[float] = None

        for world_path in self.paths.get_world_paths():
            for dir_name in self.PLAYER_DATA_DIRS:
                data_dir = world_path / dir_name
                if not data_dir.is_dir():
                    continue
                for entry in data_dir.iterdir():
                    if not entry.is_file():
                        continue
                    # .dat_old 是上一版存檔，時間戳同樣代表玩家活動
                    try:
                        mtime = entry.stat().st_mtime
                    except OSError:
                        continue
                    if latest is None or mtime > latest:
                        latest = mtime

        return datetime.fromtimestamp(latest) if latest is not None else None

    def _run_hooks(self, commands: List[str], hook_type: str) -> bool:
        """
        執行鉤子指令

        優先透過 RCON 發送（可跨程序運作），失敗時退回 stdin。

        Args:
            commands: 指令列表
            hook_type: 鉤子類型

        Returns:
            指令是否確實送達伺服器
        """
        if not commands:
            return False

        if not self._server_is_running():
            print(f"伺服器未執行，略過 {hook_type} hooks（離線備份不需要 save-off）")
            return False

        print(f"執行 {hook_type} hooks...")

        # 策略 1: RCON
        rcon = self._get_rcon()
        if rcon:
            try:
                for cmd in commands:
                    print(f"  > {cmd}")
                    response = rcon.send_command(cmd)
                    if response:
                        print(f"    {response}")
                return True
            except Exception as e:
                print(f"警告: RCON 指令執行失敗 - {e}")
            finally:
                rcon.disconnect()

        # 策略 2: stdin（僅在本程序親自啟動伺服器時可用）
        if self.launcher and self.launcher.process:
            all_sent = True
            for cmd in commands:
                print(f"  > {cmd} (stdin)")
                if not send_command(self.launcher.process, cmd):
                    print(f"警告: 指令發送失敗: {cmd}")
                    all_sent = False
            if all_sent:
                import time
                time.sleep(2)
                return True

        print(
            f"⚠️  警告: 無法送出 {hook_type} hooks（RCON 不可用且無 stdin 通道）。\n"
            "    備份將在伺服器持續寫入的狀態下進行，存檔可能不一致。\n"
            "    建議在 server.yml 啟用 rcon 後重試。"
        )
        return False

    # ------------------------------------------------------------------
    # 備份清單與保留
    # ------------------------------------------------------------------

    def list_backups(self) -> List[Path]:
        """
        列出所有備份檔案

        Returns:
            備份檔案列表（依時間由新到舊）
        """
        backup_dir = self.paths.get_backup_path()
        if not backup_dir.exists():
            return []

        backups = []
        for file in backup_dir.iterdir():
            if file.is_file() and file.suffix in ['.zip', '.tar', '.gz']:
                backups.append(file)

        # 依修改時間排序（新到舊）
        backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return backups

    def cleanup_old_backups(self) -> int:
        """
        清理舊備份

        保留規則（兩者皆生效）：
          - 僅保留最新的 keep_last 個備份（<= 0 表示不限數量）
          - 刪除超過 keep_days 天的備份（<= 0 表示不限天數）

        最新的一份永遠保留：伺服器長期無人時不會產生新備份，若照 keep_days
        清理會把僅存的備份也刪掉，等於完全沒有備份。

        Returns:
            刪除的備份數量
        """
        backups = self.list_backups()
        keep_last = self.policy.keep_last
        keep_days = self.policy.keep_days
        now = datetime.now()

        to_delete = []
        for index, backup_file in enumerate(backups):
            # 永遠保留最新一份
            if index == 0:
                continue

            over_count = keep_last > 0 and index >= keep_last

            over_age = False
            if keep_days > 0:
                age_days = (now - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
                over_age = age_days > keep_days

            if over_count or over_age:
                to_delete.append(backup_file)

        if not to_delete:
            return 0

        print(f"清理 {len(to_delete)} 個舊備份...")
        deleted = 0
        for backup_file in to_delete:
            try:
                print(f"  刪除: {backup_file.name}")
                backup_file.unlink()
                deleted += 1
            except Exception as e:
                print(f"  警告: 無法刪除 {backup_file.name} - {e}")

        return deleted

    def get_backup_info(self, backup_file: Path) -> dict:
        """
        取得備份資訊

        Args:
            backup_file: 備份檔案

        Returns:
            備份資訊字典
        """
        stat = backup_file.stat()

        return {
            "name": backup_file.name,
            "path": str(backup_file),
            "size_mb": stat.st_size / (1024 * 1024),
            "created_at": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (now_minus(stat.st_mtime)),
        }

    def resolve_backup(self, identifier: Optional[str]) -> Optional[Path]:
        """
        依名稱或編號找出備份檔

        Args:
            identifier: 檔名、路徑或 1 起算的編號（None 表示最新一份）

        Returns:
            備份檔路徑；找不到時回傳 None
        """
        backups = self.list_backups()
        if not backups:
            return None

        if identifier is None or str(identifier).strip() == "":
            return backups[0]

        identifier = str(identifier).strip()

        # 編號
        if identifier.isdigit():
            index = int(identifier) - 1
            if 0 <= index < len(backups):
                return backups[index]
            return None

        # 完整路徑
        candidate = Path(identifier)
        if candidate.is_file():
            return candidate

        # 檔名（允許省略副檔名）
        for backup_file in backups:
            if backup_file.name == identifier or backup_file.stem == identifier:
                return backup_file

        return None

    # ------------------------------------------------------------------
    # 還原
    # ------------------------------------------------------------------

    def restore_backup(self, backup_file: Path, safety_backup: bool = True) -> bool:
        """
        還原備份到伺服器目錄

        Args:
            backup_file: 要還原的備份檔
            safety_backup: 還原前是否先備份現況

        Returns:
            是否成功
        """
        if not backup_file.exists():
            print(f"錯誤: 備份檔不存在 - {backup_file}")
            return False

        if self._server_is_running():
            print("錯誤: 伺服器執行中，請先停止伺服器再還原")
            return False

        members = list_archive_members(backup_file)
        if not members:
            print("錯誤: 備份檔為空或無法讀取，已中止還原")
            return False

        server_root = self.paths.get_server_root()

        # 還原前先保存現況
        if safety_backup:
            print("還原前先備份目前狀態...")
            record = self.create_backup(force=True, trigger="pre-restore", cleanup=False)
            if not record or not record.is_success():
                print("警告: 安全備份失敗")
                return False

            # 保險：確認要還原的檔案沒有被安全備份影響
            if not backup_file.exists():
                print(f"錯誤: 要還原的備份在安全備份後消失了 - {backup_file}")
                return False

        # 移走將被覆蓋的頂層項目，避免新舊世界檔案混雜
        top_level = {name.replace('\\', '/').split('/', 1)[0] for name in members}
        trash_dir = self.paths.get_temp_path() / f"restore_{datetime.now():%Y%m%d_%H%M%S}"
        moved = []

        try:
            for entry in sorted(top_level):
                target = server_root / entry
                if not target.exists():
                    continue
                trash_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(trash_dir / entry))
                moved.append(entry)

            print(f"解壓縮 {backup_file.name} → {server_root}")
            if not extract_archive(backup_file, server_root):
                raise RuntimeError("解壓縮失敗")

        except Exception as e:
            print(f"還原失敗: {e}")
            # 盡力回滾
            for entry in moved:
                source = trash_dir / entry
                target = server_root / entry
                if not source.exists():
                    continue
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        target.unlink(missing_ok=True)
                shutil.move(str(source), str(target))
            print("已回滾到還原前的狀態")
            return False

        print(f"✓ 還原完成（{len(members)} 個項目）")
        if moved:
            print(f"  被覆蓋的原始檔案保留在: {trash_dir}")
        return True

    # ------------------------------------------------------------------
    # 歷史紀錄
    # ------------------------------------------------------------------

    def get_history_file(self) -> Path:
        """備份歷史紀錄檔路徑"""
        return self.paths.get_runtime_path() / "backup_history.json"

    def read_history(self) -> List[dict]:
        """讀取備份歷史（新到舊）"""
        history_file = self.get_history_file()
        if not history_file.exists():
            return []
        try:
            data = json.loads(history_file.read_text(encoding='utf-8'))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _append_history(self, record: BackupRecord, trigger: str):
        """寫入一筆備份歷史"""
        try:
            history = self.read_history()
            history.insert(0, {
                "created_at": record.created_at.isoformat(timespec="seconds"),
                "trigger": trigger,
                "status": record.status.value,
                "file": record.backup_file.name if record.backup_file.name else None,
                "size_mb": round(record.get_size_mb(), 2),
                "duration_seconds": round(record.duration_seconds, 1),
                "error": record.error_message,
            })
            history = history[:HISTORY_LIMIT]

            self.paths.get_runtime_path().mkdir(parents=True, exist_ok=True)
            self.get_history_file().write_text(
                json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8'
            )
        except Exception as e:
            print(f"警告: 無法寫入備份歷史 - {e}")


def now_minus(timestamp: float) -> int:
    """計算距今天數"""
    return (datetime.now() - datetime.fromtimestamp(timestamp)).days
