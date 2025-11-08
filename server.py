import os
import shutil
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

API_KEY = os.getenv("API_KEY")  # optional
PDF_ENGINE = "xelatex"          # we run xelatex with a custom template

TEMPLATE_PATH = "/app/latex-template.tex"
MAINFONT = "DejaVu Serif"
SANSFONT = "DejaVu Sans"
MONOFONT = "DejaVu Sans Mono"

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"          # "markdown" or "html"
    output_format: str                      # "docx" or "pdf"
    content: str
    reference_docx_path: str | None = None  # e.g., "/templates/reference.docx"
    defaults_yaml_path: str | None = None   # e.g., "/templates/defaults.yaml"
    filters: list[str] | None = None        # e.g., ["/path/to/filter"]

def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

@app.get("/healthz")
def healthz():
    rc_xe, xe_out, xe_err = _run(["xelatex", "--version"])
    rc_pd, pd_out, pd_err = _run(["pandoc", "-v"])
    return JSONResponse({
        "ok": True,
        "pdf_engine": PDF_ENGINE,
        "template_present": os.path.exists(TEMPLATE_PATH),
        "xelatex": (xe_out or xe_err).splitlines()[0] if (xe_out or xe_err) else "",
        "pandoc": (pd_out or pd_err).splitlines()[0] if (pd_out or pd_err) else "",
    })

@app.post("/convert")
def convert(job: Job, x_api_key: str | None = Header(default=None)):
    # Optional API key
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")

    if job.input_format not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail="input_format must be 'markdown' or 'html'")
    if job.output_format not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="output_format must be 'docx' or 'pdf'")

    # Temp dir we delete AFTER sending the file
    td = tempfile.mkdtemp(prefix="pandoc_")
    cleanup_now = True
    try:
        in_ext = "md" if job.input_format == "markdown" else "html"
        in_path = os.path.join(td, f"in.{in_ext}")
        out_path = os.path.join(td, f"out.{job.output_format}")

        with open(in_path, "w", encoding="utf-8") as f:
            f.write(job.content)

        # Build pandoc command
        cmd = ["pandoc", "-f", job.input_format, in_path, "-o", out_path]

        if job.output_format == "pdf":
            # Use our template that does NOT load lmodern + set fonts
            cmd += [
                "--pdf-engine", PDF_ENGINE,
                "--template", TEMPLATE_PATH,
                "-V", f"mainfont:{MAINFONT}",
                "-V", f"sansfont:{SANSFONT}",
                "-V", f"monofont:{MONOFONT}",
                "-V", "geometry:margin=1in",
            ]

        if (job.reference_docx_path and job.output_format == "docx"):
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters:
                cmd += ["--filter", flt]

        try:
            proc = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=240
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="pandoc timed out")

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "pandoc failed").strip()
            raise HTTPException(status_code=500, detail=detail)

        if not os.path.exists(out_path):
            detail = (proc.stderr or proc.stdout or "").strip() \
                     or "pandoc reported success but no output file was produced"
            raise HTTPException(status_code=500, detail=detail)

        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if job.output_format == "docx" else "application/pdf"
        )

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
