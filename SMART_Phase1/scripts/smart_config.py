"""
Configuration loading for the SMART Phase 1 ETL.

Resolves config.yaml and .env relative to the package root rather than the
working directory, so the scripts behave the same whether they are launched
from a scheduled task, an IDE, or a notebook.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
    from dotenv import load_dotenv
except ImportError as exc:  # pragma: no cover - environment guidance only
    raise ImportError(
        f"Missing dependency: {exc.name}.\n"
        "Install with:  pip install -r requirements.txt\n"
        "Do NOT pip install into the ArcGIS Pro env (arcgispro-py3) -- clone it first:\n"
        "  conda create --name smart-etl --clone arcgispro-py3"
    ) from exc


# Package root: the SMART_Phase1 directory (this file lives in scripts/).
ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = ROOT / "config.yaml"
ENV_PATH = ROOT / ".env"

# Working directories. Everything under data/ is gitignored; the capitalised
# Data/ directory holds the committed Phase 1 record and is never written to.
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STATE_DIR = DATA_DIR / "state"
EXPORT_DIR = DATA_DIR / "exports"
LOG_DIR = ROOT / "logs"

METADATA_DIR = ROOT / "metadata"
TEMPLATE_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "Documentation"


class ConfigError(RuntimeError):
    """Raised when configuration or credentials are missing or malformed."""


@dataclass
class Settings:
    """Parsed config.yaml plus the secrets pulled from .env."""

    arcgis: dict
    derq: dict
    locations: dict
    run: dict
    email: dict
    datasets: dict

    derq_api_key: str | None = None
    arcgis_username: str | None = None
    arcgis_password: str | None = None
    arcgis_portal_url: str | None = None
    dry_run: bool = True

    email_from: str | None = None
    email_to: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 25

    # Datasets pulled straight from the DERQ API, in the order they are loaded.
    # daily_counts is excluded -- it is derived from vehicle_counts.
    fetched_datasets: list[str] = field(default_factory=list)

    # ---- convenience accessors -------------------------------------------

    @property
    def service_url(self) -> str:
        return self.arcgis["service_url"].rstrip("/")

    @property
    def derq_url(self) -> str:
        return self.derq["api_url"].rstrip("/")

    def dataset(self, name: str) -> dict:
        try:
            return self.datasets[name]
        except KeyError:
            raise ConfigError(
                f"Unknown dataset '{name}'. Configured: {sorted(self.datasets)}"
            ) from None

    def derq_headers(self) -> dict:
        if not self.derq_api_key:
            raise ConfigError(
                "derq-api-key not found. Set it as a machine environment "
                "variable (or DERQ_API_KEY in .env)."
            )
        return {"x-api-key": self.derq_api_key}

    def require_arcgis_credentials(self) -> None:
        """Fail fast, naming the specific missing key."""
        missing = [
            name
            for name, value in (
                ("agol-username", self.arcgis_username),
                ("agol-password", self.arcgis_password),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                f"{' and '.join(missing)} not found. Set them as machine "
                "environment variables (or ARCGIS_USERNAME/ARCGIS_PASSWORD in "
                f"{ENV_PATH}). See .env.template."
            )


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in ("false", "0", "no", "off")


def _from_env(*names: str) -> str | None:
    """
    First non-empty value among several environment variable names.

    Credentials live in machine-level environment variables on TRPA machines
    (`derq-api-key`, `agol-username`, `agol-password`); the underscore names
    are also accepted so a .env file or CI secrets can override per-checkout.
    Windows env vars are case-insensitive, and dashes are legal in names.
    """
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def ensure_working_dirs() -> None:
    """Create the gitignored working directories if they don't exist."""
    for path in (RAW_DIR, STATE_DIR, EXPORT_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: Path | None = None) -> Settings:
    """
    Read config.yaml and .env into a Settings object.

    Raises:
        ConfigError : if config.yaml is missing, unparseable, or missing a
                      required top-level section.
    """
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ConfigError(f"{path} did not parse to a mapping.")

    required = ("arcgis", "derq", "locations", "run", "datasets")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ConfigError(f"{path} is missing section(s): {', '.join(missing)}")

    # Optional: a .env here overrides the machine-level environment variables
    # for this checkout. Absent .env, credentials come from the machine env
    # (derq-api-key / agol-username / agol-password).
    load_dotenv(dotenv_path=ENV_PATH)

    datasets = raw["datasets"]
    email_cfg = raw.get("email") or {}
    # Datasets carrying enabled: false (e.g. speed, dropped from the Derq
    # subscription Aug 2026) stay in the config for documentation and tests
    # but are excluded from every run.
    fetched = [
        name
        for name, cfg in datasets.items()
        if not cfg.get("derived_from") and cfg.get("enabled", True)
    ]

    return Settings(
        arcgis=raw["arcgis"],
        derq=raw["derq"],
        locations=raw["locations"],
        run=raw["run"],
        email=email_cfg or {"enabled": False},
        datasets=datasets,
        derq_api_key=_from_env("DERQ_API_KEY", "derq-api-key"),
        arcgis_username=_from_env("ARCGIS_USERNAME", "agol-username"),
        arcgis_password=_from_env("ARCGIS_PASSWORD", "agol-password"),
        arcgis_portal_url=os.getenv("ARCGIS_PORTAL_URL", raw["arcgis"]["portal_url"]),
        dry_run=_as_bool(os.getenv("DRY_RUN"), True),
        email_from=os.getenv("EMAIL_FROM", email_cfg.get("from")),
        email_to=os.getenv("EMAIL_TO", email_cfg.get("to")),
        smtp_host=os.getenv("SMTP_HOST", email_cfg.get("smtp_host")),
        smtp_port=int(os.getenv("SMTP_PORT", str(email_cfg.get("smtp_port", 25)))),
        fetched_datasets=fetched,
    )
