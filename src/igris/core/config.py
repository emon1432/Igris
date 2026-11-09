"""Configuration management for Igris."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class DisplayConfig(BaseModel):
    primary: str = ":0"
    virtual: str = ":99"
    virtual_width: int = 1920
    virtual_height: int = 1080
    virtual_depth: int = 24


class SafetyConfig(BaseModel):
    enable_mouse_override: bool = True
    mouse_move_threshold: int = 12
    emergency_keys: list[str] = Field(default_factory=lambda: ["Escape"])


class AppConfig(BaseModel):
    name: str = "Igris"
    version: str = "0.1.0"
    env: str = "development"
    default_mode: str = "ghost"  # "live" or "ghost"
    gemini_api_key: Optional[str] = None
    displays: DisplayConfig = Field(default_factory=DisplayConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        config_data = {}
        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            config_data["gemini_api_key"] = gemini_key

        return cls(**config_data)
