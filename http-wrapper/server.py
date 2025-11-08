import os, subprocess, tempfile, json
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import FileResponse

API_KEY = os.getenv("API_KEY")

app = FastAPI()

class Job(BaseModel):
    input_format: str = "markdown"   # or "html"
    output_format: str               # "docx" or "pdf"
    content: str
    reference_docx_path: str | None = None
    defaults_yaml_path: str | None = None
    filters: list[str] | None = None

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.post("/convert")
def convert(job: Job, x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "invalid API key")

    if job.output_format not in ("docx","pdf"):
        raise HTTPException(400, "output_format must be docx or pdf")

    with tempfile.TemporaryDirectory() as td:
        in_ext = "md" if job.input_format == "markdown" else "html"
        in_path = os.path.join(td, f"in.{in_ext}")
        out_path = os.path.join(td, f"out.{job.output_format}")
        open(in_path,"w",encoding="utf-8").write(job.content)

        cmd = ["pandoc", in_path, "-o", out_path]
        if job.reference_docx_path and job.output_format == "docx":
            cmd += ["--reference-doc", job.reference_docx_path]
        if job.defaults_yaml_path:
            cmd += ["--defaults", job.defaults_yaml_path]
        if job.filters:
            for flt in job.filters: cmd += ["--filter", flt]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        except subprocess.CalledProcessError as e:
            raise HTTPException(500, f"pandoc failed: {e.stderr or e.stdout or str(e)}")
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "pandoc timed out")

        media = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                 if job.output_format == "docx" else "application/pdf")
        return FileResponse(out_path, media_type=media, filename=f"out.{job.output_format}")
