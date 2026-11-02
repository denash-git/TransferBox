from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"

    @property
    def is_healthy(self) -> bool:
        return self == ServiceStatus.ACTIVE

    @property
    def dot_symbol(self) -> str:
        return "●"

    @property
    def display_label(self) -> str:
        labels = {
            ServiceStatus.ACTIVE: "активен",
            ServiceStatus.INACTIVE: "отключен",
            ServiceStatus.FAILED: "ошибка",
            ServiceStatus.UNKNOWN: "неизвестно",
        }
        return labels.get(self, "неизвестно")


@dataclass
class ServiceInfo:
    name: str
    display_name: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    is_enabled: bool = False
    description: str = ""
