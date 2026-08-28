"""API FastAPI — backend ACC Nomad."""

from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from acc_nomad import __version__
from acc_nomad.config import settings
from acc_nomad.models import ProcessExtratoRequest
from acc_nomad.models_pmg import EnviarPmgRequest
from acc_nomad.pipeline import ProcessingError, process_extrato_pdf
from acc_nomad.services.pmg_delivery import DeliveryError, enviar_pmg

app = FastAPI(
    title="ACC Nomad API",
    description="Pipeline de extratos bancários",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_secret(x_api_secret: str | None = Header(default=None)) -> None:
    if settings.api_secret and x_api_secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="API secret inválido")


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, str]:
    from acc_nomad.services.llm_providers import active_provider_name

    return {
        "status": "ok",
        "version": __version__,
        "llm_provider": active_provider_name(),
    }


@app.post("/api/extratos/processar", dependencies=[Depends(verify_api_secret)])
async def processar_extrato(
    empresa_id: str = Form(...),
    extrato_id: str = Form(...),
    segmento: str | None = Form(default=None),
    instrucao_personalizada: str | None = Form(default=None),
    nome_arquivo: str = Form(default="extrato.pdf"),
    arquivo: UploadFile = File(...),
) -> JSONResponse:
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF")

    pdf_bytes = await arquivo.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="PDF vazio")

    request = ProcessExtratoRequest(
        empresa_id=empresa_id,
        extrato_id=extrato_id,
        segmento=segmento,
        instrucao_personalizada=instrucao_personalizada,
        nome_arquivo=nome_arquivo or arquivo.filename,
    )

    try:
        result = await process_extrato_pdf(pdf_bytes, request)
    except ProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JSONResponse(content=result.model_dump(mode="json"))


@app.post("/api/pmg/enviar", dependencies=[Depends(verify_api_secret)])
async def enviar_pmg_relatorio(body: EnviarPmgRequest) -> JSONResponse:
    if body.canal not in ("email", "whatsapp"):
        raise HTTPException(status_code=400, detail="Canal deve ser email ou whatsapp")

    try:
        result = await enviar_pmg(
            empresa_id=body.empresa_id,
            empresa_nome=body.empresa_nome,
            periodo=body.periodo,
            periodo_inicio=body.periodo_inicio,
            periodo_fim=body.periodo_fim,
            canal=body.canal,
            destinatario=body.destinatario,
            resumo=body.resumo,
            enviado_por=body.enviado_por,
        )
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JSONResponse(content=result)
