"""
備份排程器

負責解析 backup.schedule 語法，並以獨立背景程序定時觸發備份。

支援的 schedule 語法：
    間隔式      "30m" / "6h" / "1d" / "90s"
    每日定時    "daily@04:00"
    每小時定時  "hourly@:30"
    Cron        "0 4 * * *"（分 時 日 月 週，支援 * , - 與 /）
"""

import json
import os
import re
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set

import psutil

from ..models.server_config import ServerInstanceConfig
from ..core.path_resolver import PathResolver


# ---------------------------------------------------------------------------
# Schedule 解析
# ---------------------------------------------------------------------------

class Schedule(ABC):
    """排程規則基底類別"""

    spec: str = ""

    @abstractmethod
    def next_run(self, after: datetime) -> datetime:
        """計算 after 之後的下一次執行時間"""

    @abstractmethod
    def describe(self) -> str:
        """人類可讀的描述"""


class IntervalSchedule(Schedule):
    """固定間隔排程"""

    def __init__(self, seconds: int, spec: str = ""):
        if seconds < 60:
            raise ValueError("備份間隔不得小於 60 秒")
        self.seconds = seconds
        self.spec = spec

    def next_run(self, after: datetime) -> datetime:
        return after + timedelta(seconds=self.seconds)

    def describe(self) -> str:
        days, rem = divmod(self.seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)

        parts = []
        if days:
            parts.append(f"{days} 天")
        if hours:
            parts.append(f"{hours} 小時")
        if minutes:
            parts.append(f"{minutes} 分鐘")
        if seconds:
            parts.append(f"{seconds} 秒")

        return f"每 {''.join(parts)} 備份一次"


class CronSchedule(Schedule):
    """Cron 風格排程（分 時 日 月 週）"""

    _FIELD_RANGES = [
        (0, 59),   # 分
        (0, 23),   # 時
        (1, 31),   # 日
        (1, 12),   # 月
        (0, 6),    # 週（0 = 星期日）
    ]

    def __init__(self, expression: str, spec: str = ""):
        fields = expression.split()
        if len(fields) != 5:
            raise ValueError(f"cron 運算式需要 5 個欄位（分 時 日 月 週），收到 {len(fields)} 個")

        self.minutes = self._parse_field(fields[0], 0)
        self.hours = self._parse_field(fields[1], 1)
        self.days = self._parse_field(fields[2], 2)
        self.months = self._parse_field(fields[3], 3)
        self.weekdays = self._parse_field(fields[4], 4)
        self.day_is_wildcard = fields[2] == "*"
        self.weekday_is_wildcard = fields[4] == "*"
        self.spec = spec or expression

    @classmethod
    def _parse_field(cls, field: str, index: int) -> Set[int]:
        low, high = cls._FIELD_RANGES[index]
        values: Set[int] = set()

        for part in field.split(","):
            part = part.strip()
            if not part:
                raise ValueError(f"cron 欄位格式錯誤: '{field}'")

            step = 1
            if "/" in part:
                part, step_str = part.split("/", 1)
                if not step_str.isdigit() or int(step_str) < 1:
                    raise ValueError(f"cron 步進值錯誤: '{step_str}'")
                step = int(step_str)

            if part == "*":
                start, end = low, high
            elif "-" in part:
                start_str, end_str = part.split("-", 1)
                start, end = int(start_str), int(end_str)
            else:
                start = end = int(part)

            # 星期日同時接受 0 與 7
            if index == 4:
                start = 0 if start == 7 else start
                end = 0 if end == 7 else end
                if end < start:
                    start, end = end, start

            if start < low or end > high or end < start:
                raise ValueError(f"cron 欄位 '{part}' 超出允許範圍 {low}-{high}")

            values.update(range(start, end + 1, step))

        if not values:
            raise ValueError(f"cron 欄位無有效值: '{field}'")
        return values

    def _match_date(self, day: datetime) -> bool:
        if day.month not in self.months:
            return False
        # cron 慣例：日與週皆非萬用字元時取聯集
        weekday = (day.weekday() + 1) % 7  # Python 週一=0 → cron 週日=0
        day_ok = day.day in self.days
        weekday_ok = weekday in self.weekdays

        if self.day_is_wildcard and self.weekday_is_wildcard:
            return True
        if self.day_is_wildcard:
            return weekday_ok
        if self.weekday_is_wildcard:
            return day_ok
        return day_ok or weekday_ok

    def next_run(self, after: datetime) -> datetime:
        cursor = (after + timedelta(minutes=1)).replace(second=0, microsecond=0)

        for offset in range(0, 1500):
            candidate_day = cursor + timedelta(days=offset)
            if not self._match_date(candidate_day):
                continue

            first_day = offset == 0
            for hour in sorted(self.hours):
                if first_day and hour < cursor.hour:
                    continue
                for minute in sorted(self.minutes):
                    if first_day and hour == cursor.hour and minute < cursor.minute:
                        continue
                    return candidate_day.replace(hour=hour, minute=minute, second=0, microsecond=0)

        raise ValueError(f"無法在四年內找到符合 '{self.spec}' 的執行時間")

    def describe(self) -> str:
        return f"cron: {self.spec}"


_INTERVAL_RE = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)
_DAILY_RE = re.compile(r"^daily\s*@\s*(\d{1,2}):(\d{2})$", re.IGNORECASE)
_HOURLY_RE = re.compile(r"^hourly\s*@\s*:?(\d{1,2})$", re.IGNORECASE)

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_schedule(spec: Optional[str]) -> Optional[Schedule]:
    """
    解析排程字串

    Args:
        spec: 排程語法，None 或空字串回傳 None

    Returns:
        Schedule 物件；無排程時回傳 None

    Raises:
        ValueError: 語法無法解析
    """
    if spec is None:
        return None

    spec = str(spec).strip()
    if not spec:
        return None

    match = _INTERVAL_RE.match(spec)
    if match:
        amount, unit = int(match.group(1)), match.group(2).lower()
        return IntervalSchedule(amount * _UNIT_SECONDS[unit], spec=spec)

    match = _DAILY_RE.match(spec)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if hour > 23 or minute > 59:
            raise ValueError(f"時間超出範圍: '{spec}'")
        return CronSchedule(f"{minute} {hour} * * *", spec=spec)

    match = _HOURLY_RE.match(spec)
    if match:
        minute = int(match.group(1))
        if minute > 59:
            raise ValueError(f"分鐘超出範圍: '{spec}'")
        return CronSchedule(f"{minute} * * * *", spec=spec)

    if len(spec.split()) == 5:
        return CronSchedule(spec, spec=spec)

    raise ValueError(
        f"無法解析排程 '{spec}'。"
        "支援格式：'30m'、'6h'、'1d'、'daily@04:00'、'hourly@:30' 或 cron '0 4 * * *'"
    )


# ---------------------------------------------------------------------------
# 排程守護程序
# ---------------------------------------------------------------------------

class BackupScheduler:
    """
    備份排程守護程序

    以獨立背景程序執行，定時呼叫 BackupManager.create_backup()。
    狀態寫入 runtime/backup_schedule.json，PID 寫入 runtime/backup_daemon.pid。
    """

    def __init__(self, config: ServerInstanceConfig):
        self.config = config
        self.paths = PathResolver(config)

    # -- 路徑 --------------------------------------------------------------

    def get_pid_file(self) -> Path:
        return self.paths.get_runtime_path() / "backup_daemon.pid"

    def get_state_file(self) -> Path:
        return self.paths.get_runtime_path() / "backup_schedule.json"

    def get_log_file(self) -> Path:
        return self.paths.get_runtime_path() / "backup_daemon.log"

    # -- 排程 --------------------------------------------------------------

    def get_schedule(self) -> Optional[Schedule]:
        """
        取得此伺服器的排程；未啟用排程模式時回傳 None

        Raises:
            ValueError: schedule 語法錯誤
        """
        backup_config = self.config.backup
        if not backup_config.enabled:
            return None
        if str(backup_config.mode).lower() != "scheduled":
            return None
        return parse_schedule(backup_config.schedule)

    # -- 程序控制 ----------------------------------------------------------

    def is_running(self) -> bool:
        """守護程序是否正在執行"""
        pid = self._load_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)
            if not process.is_running():
                self._clear_pid()
                return False
            # 避免 PID 重用誤判：確認是 Python 程序
            name = (process.name() or "").lower()
            if "python" not in name and "mc-host" not in name:
                self._clear_pid()
                return False
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._clear_pid()
            return False

    def start(self) -> bool:
        """以背景程序啟動排程守護"""
        try:
            schedule = self.get_schedule()
        except ValueError as e:
            print(f"✗ 備份排程設定錯誤: {e}")
            return False

        if schedule is None:
            return False

        if self.is_running():
            print(f"備份排程已在執行中 (PID: {self._load_pid()})")
            return True

        self.paths.get_runtime_path().mkdir(parents=True, exist_ok=True)

        project_root = _find_project_root()
        command = _build_daemon_command(self.config.meta.name)

        try:
            log_handle = open(self.get_log_file(), "a", encoding="utf-8")
            log_handle.write(
                f"\n===== 備份排程啟動 {datetime.now():%Y-%m-%d %H:%M:%S} =====\n"
            )
            log_handle.flush()

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                command,
                cwd=str(project_root),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except Exception as e:
            print(f"✗ 備份排程啟動失敗: {e}")
            return False

        self._save_pid(process.pid)
        self._write_state(
            {
                "pid": process.pid,
                "spawn_pid": process.pid,
                "schedule": schedule.spec,
                "description": schedule.describe(),
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "next_run": schedule.next_run(datetime.now()).isoformat(timespec="seconds"),
                "last_run": None,
                "last_status": None,
            }
        )

        print(f"✓ 備份排程已啟動 (PID: {process.pid}) — {schedule.describe()}")
        return True

    def stop(self) -> bool:
        """停止排程守護程序"""
        pid = self._load_pid()
        state = self.read_state()

        # venv 的 python.exe 是轉發用的 stub，實際直譯器是它的子程序，
        # 因此 spawn 時的 PID 與守護迴圈自己記錄的 PID 可能不同，兩者都要清掉。
        candidates = [p for p in (pid, state.get("pid"), state.get("spawn_pid")) if p]
        if not candidates:
            return False

        stopped = []
        for candidate in dict.fromkeys(candidates):
            try:
                if self._terminate_tree(int(candidate)):
                    stopped.append(candidate)
            except Exception as e:
                print(f"⚠️  備份排程停止失敗 (PID {candidate}): {e}")
                self._clear_pid()
                return False

        self._clear_pid()

        if stopped:
            print(f"✓ 備份排程已停止 (PID: {', '.join(str(p) for p in stopped)})")

        state["pid"] = None
        state["spawn_pid"] = None
        state["stopped_at"] = datetime.now().isoformat(timespec="seconds")
        self._write_state(state)
        return True

    @staticmethod
    def _terminate_tree(pid: int) -> bool:
        """終止程序及其子程序；回傳是否真的有終止到東西"""
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return False

        # PID 可能已被系統回收再指派給別的程序，先確認是 Python 才動手
        try:
            if "python" not in (process.name() or "").lower():
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

        try:
            targets = process.children(recursive=True) + [process]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            targets = [process]

        for target in targets:
            try:
                target.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        _, alive = psutil.wait_procs(targets, timeout=10)
        for target in alive:
            try:
                target.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return True

    # -- 守護迴圈 ----------------------------------------------------------

    def run_forever(self) -> int:
        """
        在前景執行排程迴圈（由背景程序呼叫，不應直接互動使用）

        Returns:
            結束代碼
        """
        from ..core.backup_manager import BackupManager

        try:
            schedule = self.get_schedule()
        except ValueError as e:
            print(f"備份排程設定錯誤: {e}", flush=True)
            return 1

        if schedule is None:
            print("備份排程未啟用（需 backup.mode: scheduled 且設定 schedule）", flush=True)
            return 1

        self._save_pid(os.getpid())
        print(f"備份排程守護啟動: {schedule.describe()}", flush=True)

        next_run = schedule.next_run(datetime.now())
        self._patch_state(
            {
                "pid": os.getpid(),
                "schedule": schedule.spec,
                "description": schedule.describe(),
                "next_run": next_run.isoformat(timespec="seconds"),
            }
        )
        print(f"下次備份時間: {next_run:%Y-%m-%d %H:%M:%S}", flush=True)

        manager = BackupManager(self.config)

        try:
            while True:
                now = datetime.now()

                if now < next_run:
                    # 分段睡眠，讓終止訊號能較快生效
                    time.sleep(min(30.0, max(1.0, (next_run - now).total_seconds())))
                    continue

                should_run, reason = self.should_run_now(manager)
                if should_run:
                    print(f"[{now:%Y-%m-%d %H:%M:%S}] 觸發排程備份（{reason}）", flush=True)
                    record = manager.create_backup(trigger="scheduled")

                    status = "success" if record and record.is_success() else "failed"
                    if record and not record.is_success():
                        print(f"備份失敗: {record.error_message}", flush=True)

                    updates = {
                        "last_run": datetime.now().isoformat(timespec="seconds"),
                        "last_status": status,
                        "last_skip_reason": None,
                    }
                else:
                    print(f"[{now:%Y-%m-%d %H:%M:%S}] 跳過排程備份（{reason}）", flush=True)
                    updates = {
                        "last_run": datetime.now().isoformat(timespec="seconds"),
                        "last_status": "skipped",
                        "last_skip_reason": reason,
                    }

                next_run = schedule.next_run(datetime.now())
                updates["next_run"] = next_run.isoformat(timespec="seconds")
                self._patch_state(updates)
                print(f"下次備份時間: {next_run:%Y-%m-%d %H:%M:%S}", flush=True)
        except KeyboardInterrupt:
            print("備份排程守護已中止", flush=True)
        finally:
            self._clear_pid()

        return 0

    # -- 玩家活動 ----------------------------------------------------------

    def get_activity_report(self, manager) -> dict:
        """
        彙整判斷所需的玩家活動資訊

        Args:
            manager: BackupManager 實例

        Returns:
            含 reference（上次備份時間）、last_activity、online 的字典
        """
        backups = manager.list_backups()

        reference = None
        if backups:
            # 以最新一份備份的時間為基準，手動備份也會自然更新這個基準
            reference = datetime.fromtimestamp(backups[0].stat().st_mtime)

        return {
            "has_backup": bool(backups),
            "reference": reference,
            "last_activity": manager.get_last_player_activity(),
            "online": manager.get_online_player_count(),
        }

    def should_run_now(self, manager, report: Optional[dict] = None) -> tuple:
        """
        判斷這次排程是否該真的執行備份

        無人玩過就跳過，避免長期無人的伺服器一直堆積內容相同的備份。
        判斷依據是 world/playerdata 等玩家存檔的 mtime（伺服器在玩家登出與
        自動存檔時寫入），因此不需要輪詢，短暫上線也抓得到。

        任何「無法確定」的情況一律照常備份——漏備份的代價遠大於多備份一次。

        Args:
            manager: BackupManager 實例
            report: 已取得的活動資訊，避免重複查詢 RCON

        Returns:
            (是否執行, 原因說明)
        """
        if not self.config.backup.skip_if_no_players:
            return True, "未啟用無人跳過"

        if report is None:
            report = self.get_activity_report(manager)

        # 還沒有任何備份時先建立基準
        if not report["has_backup"]:
            return True, "尚無任何備份，先建立基準"

        # 現在就有人在線
        online = report["online"]
        if online:
            return True, f"目前有 {online} 位玩家在線"

        last_activity = report["last_activity"]
        if last_activity is None:
            return True, "找不到玩家存檔，無法判斷，照常備份"

        reference = report["reference"]
        if reference is None or last_activity > reference:
            return True, f"上次備份後有玩家活動（{last_activity:%Y-%m-%d %H:%M:%S}）"

        return False, f"自上次備份（{reference:%m-%d %H:%M}）以來無玩家活動"

    # -- 狀態 --------------------------------------------------------------

    def read_state(self) -> dict:
        """讀取排程狀態檔"""
        state_file = self.get_state_file()
        if not state_file.exists():
            return {}
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def get_status(self) -> dict:
        """取得完整排程狀態"""
        state = self.read_state()

        schedule_spec = self.config.backup.schedule
        error = None
        description = None
        try:
            schedule = parse_schedule(schedule_spec)
            description = schedule.describe() if schedule else None
        except ValueError as e:
            error = str(e)

        return {
            "enabled": self.config.backup.enabled,
            "mode": self.config.backup.mode,
            "schedule": schedule_spec,
            "description": description,
            "error": error,
            "running": self.is_running(),
            "pid": self._load_pid(),
            "last_run": state.get("last_run"),
            "last_status": state.get("last_status"),
            "last_skip_reason": state.get("last_skip_reason"),
            "next_run": state.get("next_run"),
            "log_file": str(self.get_log_file()),
            "skip_if_no_players": self.config.backup.skip_if_no_players,
        }

    def _write_state(self, state: dict):
        try:
            self.paths.get_runtime_path().mkdir(parents=True, exist_ok=True)
            self.get_state_file().write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"警告: 無法寫入排程狀態 - {e}")

    def _patch_state(self, updates: dict):
        state = self.read_state()
        state.update(updates)
        self._write_state(state)

    # -- PID ---------------------------------------------------------------

    def _save_pid(self, pid: int):
        try:
            self.paths.get_runtime_path().mkdir(parents=True, exist_ok=True)
            self.get_pid_file().write_text(str(pid), encoding="utf-8")
        except Exception as e:
            print(f"警告: 無法寫入 PID 檔案 - {e}")

    def _load_pid(self) -> Optional[int]:
        pid_file = self.get_pid_file()
        if not pid_file.exists():
            return None
        try:
            return int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            return None

    def _clear_pid(self):
        try:
            self.get_pid_file().unlink(missing_ok=True)
        except Exception:
            pass


def _find_project_root() -> Path:
    """取得框架根目錄（含 servers/ 的目錄）"""
    return Path(__file__).resolve().parents[2]


def _build_daemon_command(server_name: str) -> List[str]:
    """組出啟動守護程序的指令"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "backup", "daemon", server_name]
    return [sys.executable, "-m", "app.main", "backup", "daemon", server_name]
