from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable


CallbackConfirmacao = Callable[[object], Awaitable[None]]


@dataclass
class ConfirmacaoPendente:
    usuario_id: int
    acao: str
    confirmar: CallbackConfirmacao
    cancelar: CallbackConfirmacao | None
    expira_em: datetime


_PENDENTES: dict[int, ConfirmacaoPendente] = {}


def registrar_confirmacao(
    usuario_id: int,
    acao: str,
    confirmar: CallbackConfirmacao,
    cancelar: CallbackConfirmacao | None = None,
    minutos: int = 10,
) -> ConfirmacaoPendente:
    pendente = ConfirmacaoPendente(
        usuario_id=usuario_id,
        acao=acao,
        confirmar=confirmar,
        cancelar=cancelar,
        expira_em=datetime.now(UTC) + timedelta(minutes=minutos),
    )
    _PENDENTES[usuario_id] = pendente
    return pendente


def obter_confirmacao(usuario_id: int) -> ConfirmacaoPendente | None:
    pendente = _PENDENTES.get(usuario_id)
    if pendente and datetime.now(UTC) >= pendente.expira_em:
        _PENDENTES.pop(usuario_id, None)
        return None
    return pendente


def remover_confirmacao(usuario_id: int) -> None:
    _PENDENTES.pop(usuario_id, None)


def texto_confirmacao(acao: str) -> str:
    return (
        f"**Ação aguardando confirmação:** {acao}\n\n"
        "Responda com `Tenshi, confirmar` para executar ou `Tenshi, cancelar` para desistir."
    )


async def processar_resposta(message, confirmar: bool) -> bool:
    pendente = obter_confirmacao(message.author.id)
    if not pendente:
        await message.channel.send("> ⚠️ Você não possui nenhuma ação aguardando confirmação.")
        return True

    _PENDENTES.pop(message.author.id, None)
    if confirmar:
        await pendente.confirmar(message)
    elif pendente.cancelar:
        await pendente.cancelar(message)
    else:
        await message.channel.send(f"> Ação cancelada: **{pendente.acao}**")
    return True


def limpar_confirmacoes() -> None:
    """Auxiliar para testes e reinicializações controladas."""
    _PENDENTES.clear()
