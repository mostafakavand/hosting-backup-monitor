from dataclasses import dataclass

@dataclass
class BackupDetail:
    process_id: str
    type: str
    start_time: str
    end_time: str
    execution_time: str
    status: str