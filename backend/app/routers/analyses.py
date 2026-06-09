import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import os
from datetime import datetime
from .. import models, schemas, database
from .auth import get_current_user
from ..services import github_fetcher, context_builder, doc_generator
from ..logging_config import get_custom_logger

logger = get_custom_logger("analyses", "analyses.log")

ANALYSIS_TIMEOUT_SECONDS = int(os.environ.get("ANALYSIS_TIMEOUT_SECONDS", "300"))

router = APIRouter(prefix="/analyses", tags=["analyses"])


# ---------------------------------------------------------------------------
# Helper: appends a timestamped step entry to the job's steps_json column.
# Safe to call from any background thread (opens its own implicit transaction).
# ---------------------------------------------------------------------------
def _add_step(db: Session, job: models.AnalysisJob, message: str) -> None:
    """Append a progress step entry to the job's steps_json array."""
    try:
        steps: list = json.loads(job.steps_json) if job.steps_json else []
    except (json.JSONDecodeError, TypeError):
        steps = []
    steps.append({
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "message": message,
    })
    job.steps_json = json.dumps(steps, ensure_ascii=False)
    db.commit()
    logger.info(f"[Job {job.id}] Step: {message}")


# ---------------------------------------------------------------------------
# Background pipeline
# ---------------------------------------------------------------------------
async def run_analysis_pipeline(job_id: int, repo_url: str):
    logger.info(f"Background task run_analysis_pipeline triggered for Job ID: {job_id} | Repo: '{repo_url}'")

    db = database.SessionLocal()
    try:
        job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"Job ID {job_id}: not found in database. Exiting pipeline.")
            return

        # ── Step 1: RUNNING ──────────────────────────────────────────────────
        job.status = models.JobStatus.RUNNING
        _add_step(db, job, "Status alterado para EM EXECUÇÃO.")

        try:
            # ── Step 2: Download ─────────────────────────────────────────────
            _add_step(db, job, "Baixando o repositório do GitHub (arquivo ZIP)...")
            repo_path = await asyncio.wait_for(
                github_fetcher.fetch_repo_zip(repo_url, str(job_id)),
                timeout=ANALYSIS_TIMEOUT_SECONDS
            )
            _add_step(db, job, f"Download concluído. Arquivos extraídos em: {repo_path}")

            # ── Step 3: Index ────────────────────────────────────────────────
            _add_step(db, job, "Mapeando a estrutura de diretórios e arquivos do projeto...")
            evidence = context_builder.build_context(repo_path)
            num_files = evidence.get("stats", {}).get("files", "?")
            _add_step(db, job, f"Estrutura mapeada: {num_files} arquivo(s) encontrado(s).")

            # ── Step 4: Load key files ───────────────────────────────────────
            _add_step(db, job, "Carregando conteúdo dos arquivos principais (README, dependências, código-fonte)...")
            num_loaded = len(evidence.get("files_content", {}))
            _add_step(db, job, f"{num_loaded} arquivo(s) principal(is) carregado(s) para o pacote de evidências.")

            # Save evidence snapshot
            job.evidence_json = json.dumps(evidence)
            db.commit()

            # ── Step 5: LLM ─────────────────────────────────────────────────
            _add_step(db, job, "Enviando pacote de evidências para o modelo de IA local...")
            markdown_doc = await asyncio.wait_for(
                doc_generator.generate_documentation(evidence, repo_path=repo_path),
                timeout=ANALYSIS_TIMEOUT_SECONDS
            )
            _add_step(db, job, f"Documentação gerada pelo LLM com sucesso ({len(markdown_doc)} caracteres).")

            # ── Step 6: Save document ────────────────────────────────────────
            _add_step(db, job, "Salvando documentação técnica gerada no banco de dados...")
            doc = models.Document(job_id=job.id, content_md=markdown_doc)
            db.add(doc)

            # ── Step 7: DONE ─────────────────────────────────────────────────
            job.status = models.JobStatus.DONE
            job.finished_at = datetime.utcnow()
            _add_step(db, job, "✅ Análise finalizada com sucesso!")
            logger.info(f"Job ID {job_id}: pipeline completed successfully.")

        except Exception as e:
            job.status = models.JobStatus.ERROR
            job.error_message = str(e)
            _add_step(db, job, f"❌ Erro crítico na análise: {e}")
            logger.error(f"Job ID {job_id}: pipeline failed. Exception: {e}")

    finally:
        db.close()
        logger.info(f"Job ID {job_id}: database session closed.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/", response_model=schemas.JobResponse)
def start_analysis(
    repository_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    logger.info(f"User '{current_user.email}' requested analysis for Repository ID: {repository_id}")
    repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
    if not repo:
        logger.warning(f"Repository ID {repository_id} not found for user '{current_user.email}'")
        raise HTTPException(status_code=404, detail="Repository not found")

    job = models.AnalysisJob(repository_id=repo.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Analysis Job created. ID: {job.id} | Status: PENDING")

    background_tasks.add_task(run_analysis_pipeline, job.id, repo.url)
    logger.info(f"Background task queued for Job ID: {job.id}")

    return job


@router.get("/{id}", response_model=schemas.JobResponse)
def get_analysis_status(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    logger.info(f"User '{current_user.email}' queried status of Job ID: {id}")
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job:
        logger.warning(f"Job ID {id} not found.")
        raise HTTPException(status_code=404, detail="Job not found")
    logger.info(f"Job ID {id} | Status: '{job.status}'")
    return job


@router.get("/{id}/steps")
def get_analysis_steps(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Lightweight endpoint returning current status + parsed steps list for a job.
    Used by frontend AJAX polling to render the real-time progress timeline.
    """
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        steps = json.loads(job.steps_json) if job.steps_json else []
    except (json.JSONDecodeError, TypeError):
        steps = []

    return {
        "job_id": job.id,
        "status": job.status,
        "steps": steps,
        "error_message": job.error_message,
    }


@router.get("/{id}/document")
def get_analysis_document(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    logger.info(f"User '{current_user.email}' requested documentation markdown for Job ID: {id}")
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job or not job.documents:
        logger.warning(f"Documentation not found for Job ID: {id}")
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info(f"Documentation retrieved for Job ID: {id}. Size: {len(job.documents[0].content_md)} chars.")
    return {"markdown": job.documents[0].content_md}


@router.get("/{id}/download_pdf")
def download_pdf(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    logger.info(f"User '{current_user.email}' requested PDF download for Job ID: {id}")
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job or not job.documents:
        logger.warning(f"Document not found for Job ID: {id} during PDF download.")
        raise HTTPException(status_code=404, detail="Document not found")

    doc = job.documents[0]
    pdf_filename = f"report_{id}.pdf"
    pdf_path = os.path.join("storage/docs", pdf_filename)
    os.makedirs("storage/docs", exist_ok=True)

    logger.info(f"Generating PDF at: '{pdf_path}'")
    from ..services.pdf_generator import convert_md_to_pdf
    convert_md_to_pdf(doc.content_md, pdf_path)

    from fastapi.responses import FileResponse
    logger.info(f"Serving PDF to user '{current_user.email}': '{pdf_path}'")
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_filename)


@router.delete("/{id}")
def delete_analysis(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    logger.info(f"User '{current_user.email}' requested deletion of Analysis Job ID: {id}")
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    # Verify ownership through the repository
    repo = db.query(models.Repository).filter(models.Repository.id == job.repository_id).first()
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    db.delete(job)
    db.commit()
    logger.info(f"Analysis Job ID {id} deleted successfully.")
    return {"ok": True}
