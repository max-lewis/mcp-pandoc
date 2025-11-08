import os, shutil, subprocess, tempfile
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

API_KEY = os.getenv("API_KEY")            # optional
PDF_ENGINE = "wkhtmltopdf"                # <- force non-LaTeX engine

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"        # "markdown" or "html"
    output_format: str                    # "docx" or "pdf"
    content: str
    reference_docx_path: str | None = None
    defaults_yaml_path: str | None = None
    filters: list[str] | None = None

def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr

@app.get("/healthz")
def healthz():
    rc_wk, wk_out, wk_err = run(["wkhtmltopdf", "--version"])
    rc_pd, pd_out, pd_err = run(["pandoc", "-v"])
    return JSONResponse({
        "ok": True,
        "pdf_engine": PDF_ENGINE,
        "wkhtmltopdf": (wk_out or wk_err).splitlines()[0] if (wk_out or wk_err) else "",
        "pandoc": (pd_out or pd_err).splitlines()[0] if (pd_out or pd_err) else "",
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

        # Build pandoc command
        cmd = ["pandoc", "-f", job.input_format, in_path, "-o", out_path]

        if job.output_format == "pdf":
            # Force HTML → PDF via wkhtmltopdf (no LaTeX at all)
            cmd += [
                "--pdf-engine", "wkhtmltopdf",
                "-t", "html5",
                "--metadata", "pagetitle=Document",
                "--standalone"
            ]

        if job.reference_docx_path and job.output_format == "docx":
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters:
                cmd += ["--filter", flt]

        rc, out, err = run(cmd)
        if rc != 0:
            raise HTTPException(status_code=500, detail=(err or out or "pandoc failed"))

        if not os.path.exists(out_path):
            raise HTTPException(status_code=500, detail="output file missing")

        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if job.output_format == "docx" else "application/pdf"
        )
        cleanup_now = False
        return FileResponse(
            out_path, media_type=media, filename=f"out.{job.output_format}",
            background=BackgroundTask(shutil.rmtree, td, ignore_errors=True)
        )
    finally:
        if cleanup_now:
            shutil.rmtree(td, ignore_errors=True)

