import os, shutil, subprocess, tempfile
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

API_KEY = os.getenv("API_KEY")
PDF_ENGINE = "xelatex"

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"
    output_format: str
    content: str
    reference_docx_path: str | None = None
    defaults_yaml_path: str | None = None
    filters: list[str] | None = None

@app.get("/healthz")
def healthz():
    check = subprocess.run(["kpsewhich", "fontspec.sty"], capture_output=True, text=True)
    return JSONResponse({
        "ok": True,
        "pdf_engine": PDF_ENGINE,
        "fontspec_found": bool(check.stdout.strip()),
    })

@app.post("/convert")
def convert(job: Job, x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")
    if job.input_format not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail="input_format must be 'markdown' or 'html'")
    if job.output_format not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="output_format must be 'docx' or 'pdf'")

    td = tempfile.mkdtemp(prefix="pandoc_")
    cleanup_now = True
    try:
        in_ext = "md" if job.input_format == "markdown" else "html"
        in_path = os.path.join(td, f"in.{in_ext}")
        out_path = os.path.join(td, f"out.{job.output_format}")
        with open(in_path, "w", encoding="utf-8") as f:
            f.write(job.content)

        cmd = ["pandoc", "-f", job.input_format, in_path, "-o", out_path]
        if job.output_format == "pdf":
            cmd += ["--pdf-engine", PDF_ENGINE]
        if job.reference_docx_path and job.output_format == "docx":
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters:
                cmd += ["--filter", flt]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail=proc.stderr or proc.stdout)

        if not os.path.exists(out_path):
            raise HTTPException(status_code=500, detail="output file missing")

        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if job.output_format == "docx" else "application/pdf"
        )
        cleanup_now = False
        return FileResponse(out_path, media_type=media, filename=f"out.{job.output_format}",
                            background=BackgroundTask(shutil.rmtree, td, ignore_errors=True))
    finally:
        if cleanup_now:
            shutil.rmtree(td, ignore_errors=True)

