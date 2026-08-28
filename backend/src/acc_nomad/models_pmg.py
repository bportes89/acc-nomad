from datetime import date
import calendar

from pydantic import BaseModel, Field


class EnviarPmgRequest(BaseModel):
    empresa_id: str
    empresa_nome: str
    periodo: str = Field(description="YYYY-MM")
    canal: str = Field(description="email ou whatsapp")
    destinatario: str
    resumo: dict[str, float]
    enviado_por: str | None = None

    @property
    def periodo_inicio(self) -> date:
        year, month = map(int, self.periodo.split("-"))
        return date(year, month, 1)

    @property
    def periodo_fim(self) -> date:
        year, month = map(int, self.periodo.split("-"))
        last = calendar.monthrange(year, month)[1]
        return date(year, month, last)
