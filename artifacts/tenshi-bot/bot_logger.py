"""
Sistema de logs limpo, estruturado e resiliente para o Tenshi Bot.
Permite rastreamento detalhado de eventos, comandos, chamadas de IA e erros com rotação segura.
"""
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path


class BotLogger:
    """Logger estruturado com saída para console e arquivo local."""

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Verde
        "WARNING": "\033[33m",  # Amarelo
        "ERROR": "\033[31m",    # Vermelho
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",
    }

    def __init__(self, name: str = "TenshiBot", log_dir: str = "data"):
        self.name = name
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "tenshi.log"
            self.error_file = self.log_dir / "errors.log"
        except Exception:
            self.log_file = None
            self.error_file = None

    def _format_time(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def _write_file(self, file_path: Path, text: str) -> None:
        if not file_path:
            return
        try:
            # Rotação simples se o arquivo passar de 5MB
            if file_path.exists() and file_path.stat().st_size > 5 * 1024 * 1024:
                backup = file_path.with_suffix(".old.log")
                if backup.exists():
                    backup.unlink()
                file_path.rename(backup)

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    def _log(self, level: str, message: str, exc: Exception = None, **kwargs) -> None:
        timestamp = self._format_time()
        extra_str = ""
        if kwargs:
            extra_items = [f"{k}={v}" for k, v in kwargs.items() if v is not None]
            if extra_items:
                extra_str = f" | {', '.join(extra_items)}"

        color = self.LEVEL_COLORS.get(level, "")
        reset = self.LEVEL_COLORS["RESET"]

        console_line = f"[{timestamp}] [{color}{level:<7}{reset}] [{self.name}] {message}{extra_str}"
        file_line = f"[{timestamp}] [{level:<7}] [{self.name}] {message}{extra_str}"

        # Saída no console
        stream = sys.stderr if level in ("ERROR", "CRITICAL") else sys.stdout
        try:
            stream.write(console_line + "\n")
            stream.flush()
        except Exception:
            pass

        # Saída em arquivo
        if self.log_file:
            self._write_file(self.log_file, file_line)

        if exc is not None:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            try:
                stream.write(f"{color}{tb}{reset}\n")
                stream.flush()
            except Exception:
                pass

            if self.error_file:
                self._write_file(self.error_file, f"{file_line}\nTraceback:\n{tb}")

    def debug(self, message: str, **kwargs) -> None:
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, exc: Exception = None, **kwargs) -> None:
        self._log("ERROR", message, exc=exc, **kwargs)

    def critical(self, message: str, exc: Exception = None, **kwargs) -> None:
        self._log("CRITICAL", message, exc=exc, **kwargs)

    def command(self, user_name: str, user_id: int, command_name: str, guild: str = "DM", success: bool = True, duration_ms: float = None) -> None:
        status = "SUCESSO" if success else "FALHA"
        dur = f" ({duration_ms:.1f}ms)" if duration_ms is not None else ""
        self.info(
            f"Comando executado: {command_name}{dur}",
            usuario=f"{user_name}#{user_id}",
            servidor=guild,
            status=status,
        )

    def ai_request(self, model: str, prompt_preview: str, duration_ms: float, success: bool = True, error: str = None) -> None:
        status = "OK" if success else "ERRO"
        preview = prompt_preview.replace("\n", " ")[:60]
        if success:
            self.info(
                f"Chamada IA concluída em {duration_ms:.0f}ms",
                modelo=model,
                status=status,
                preview=f"'{preview}...'"
            )
        else:
            self.warning(
                f"Chamada IA falhou ({duration_ms:.0f}ms): {error}",
                modelo=model,
                status=status,
                preview=f"'{preview}...'"
            )


# Instância global compartilhada
bot_logger = BotLogger("Tenshi")
