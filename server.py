import os
import shutil
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

# Optional API key (set in Railway → Variables → API_KEY)
API_KEY = os.getenv("API_KEY")

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"          # "markdown" or "html"
    output_format: str                      # "docx" or "pdf"
    content: str
    reference_docx_path: str | None = None  # e.g., "/templates/reference.docx"
    defaults_yaml_path: str | None = None   # e.g., "/templates/defaults.yaml"
    filters: list[str] | None = None        # e.g., ["/path/to/filter"]

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/convert")
def convert(job: Job, x_api_key: str | None = Header(default=None)):
    # Optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")

    if job.input_format not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail="input_format must be 'markdown' or 'html'")
    if job.output_format not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="output_format must be 'docx' or 'pdf'")

    # Create a temp directory that we control and clean up AFTER sending the file
    td = tempfile.mkdtemp(prefix="pandoc_")
    cleanup_now = True  # flip to False if we hand cleanup to BackgroundTask

    try:
        in_ext = "md" if job.input_format == "markdown" else "html"
        in_path = os.path.join(td, f"in.{in_ext}")
        out_path = os.path.join(td, f"out.{job.output_format}")

        with open(in_path, "w", encoding="utf-8") as f:
            f.write(job.content)

        # Build pandoc command with explicit flags
        cmd = ["pandoc", "-f", job.input_format, in_path, "-o", out_path]
        if job.output_format == "pdf":
            cmd += ["--pdf-engine", "xelatex"]

        if job.reference_docx_path and job.output_format == "docx":
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters:
                cmd += ["--filter", flt]

        try:
            proc = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=180
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="pandoc timed out")

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "pandoc failed").strip()
            raise HTTPException(status_code=500, detail=detail)

        if not os.path.exists(out_path):
            detail = (proc.stderr or proc.stdout or "").strip()
            if not detail:
                detail = "pandoc reported success but no output file was produced"
            raise HTTPException(status_code=500, detail=detail)

        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if job.output_format == "docx" else "application/pdf"
        )

        # Let Starlette send the file, then delete the temp directory afterwards
        cleanup_now = False
        return FileResponse(
            out_path,
            media_type=media,
            filename=f"out.{job.output_format}",
            background=BackgroundTask(shutil.rmtree, td, ignore_errors=True),
        )

    finally:
        if cleanup_now:
            shutil.rmtree(td, ignore_errors=True)
