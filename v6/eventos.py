# eventos.py — a auditoria guardada no banco

from sqlalchemy.orm import Session

from modelos import Atendente, Evento


def registra_evento(sessao: Session, atendente: Atendente, acao: str, detalhe: str) -> None:
    """Acrescenta um evento à sessão. Ele é gravado no mesmo commit da operação."""
    sessao.add(Evento(usuario=atendente.usuario, acao=acao, detalhe=detalhe))
