import os, subprocess, tempfile
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import FileResponse

API_KEY = os.getenv("API_KEY")  # optional: set in Railway Variables to require x-api-key

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"          # "markdown" or "html"
    output_format: str                      # "docx" or "pdf"
    content: str
    reference_docx_path: str | None = None  # e.g., "/templates/reference.docx"
    defaults_yaml_path: str | None = None   # e.g., "/templates/defaults.yaml"
    filters: list[str] | None = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/convert")
def convert(job: Job, x_api_key: str | None = Header(default=None)):
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "invalid API key")

    if job.output_format not in ("docx", "pdf"):
        raise HTTPException(400, "output_format must be docx or pdf")
    if job.input_format not in ("markdown", "html"):
        raise HTTPException(400, "input_format must be markdown or html")

    with tempfile.TemporaryDirectory() as td:
        in_ext = "md" if job.input_format == "markdown" else "html"
        in_path = os.path.join(td, f"in.{in_ext}")
        out_path = os.path.join(td, f"out.{job.output_format}")

        with open(in_path, "w", encoding="utf-8") as f:
            f.write(job.content)

        # Build pandoc command with explicit flags
        cmd = ["pandoc", "-f", job.input_format, in_path, "-o", out_path]

        # PDF needs a TeX engine; use xelatex (installed in Dockerfile)
        if job.output_format == "pdf":
            cmd += ["--pdf-engine", "xelatex"]

        if job.reference_docx_path and job.output_format == "docx":
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters:
                cmd += ["--filter", flt]

        # Run pandoc and capture output for diagnostics
        try:
            proc = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=180
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "pandoc timed out")

        # If pandoc failed, surface stderr/stdout
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "pandoc failed"
            raise HTTPException(500, detail)

        # Assert the output file exists
        if not os.path.exists(out_path):
            detail = (proc.stderr or proc.stdout or "").strip()
            if not detail:
                detail = "pandoc reported success but no output file was produced"
            raise HTTPException(500, detail)

        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if job.output_format == "docx" else "application/pdf"
        )
        return FileResponse(out_path, media_type=media, filename=f"out.{job.output_format}")
