import os
from pathlib import Path

_BOT_DIR = Path(__file__).resolve().parent


def bot_data_dir() -> Path:
    custom = os.environ.get("TENSHI_DATA_DIR", "").strip()
    if custom:
        path = Path(custom)
        if not path.is_absolute():
            path = _BOT_DIR / path
        return path
    return _BOT_DIR / "data"


def data_file(name: str) -> str:
    return str(bot_data_dir() / name)


def configurar_diretorio_dados() -> None:
    """Garante pasta de dados gravavel; na Railway, use TENSHI_DATA_DIR=/data com volume."""
    target = bot_data_dir()
    target.mkdir(parents=True, exist_ok=True)
    local = _BOT_DIR / "data"
    if target.resolve() == local.resolve():
        return

    if local.is_symlink():
        return

    try:
        if local.is_dir() and not any(local.iterdir()):
            local.rmdir()
        if not local.exists():
            local.symlink_to(target, target_is_directory=True)
            print(f"[DATA] data/ vinculado a {target}")
    except OSError as exc:
        print(f"[AVISO] Nao foi possivel vincular data/ a {target}: {exc}")
