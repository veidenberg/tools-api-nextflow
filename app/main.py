from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import nextflow
import secrets
import json
import os

app = FastAPI()

# Override response format for input payload validation error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exception):
  return JSONResponse(content={'error': str(exception)}, status_code=422)

# Override 404 response
@app.exception_handler(404)
async def invalid_path_handler(request, exception):
  return JSONResponse(content={'error': 'Invalid endpoint'}, status_code=404)

# Endpoint for serving the BLAST input config
@app.get('/blast/config')
async def serve_config() -> dict:
  with open('data/blast_config.json') as f:
    config = json.load(f)
  return config

# Here be datamodels for validating incoming payloads
class JobIDs(BaseModel):
  job_ids: list[str]

# Endpoint for submitting a BLAST job
@app.post('/blast/job')
async def submit_blast(payload: dict) -> dict:
  run_id = secrets.token_urlsafe(16)
  run_path = f"work/{run_id}"
  payload_file = f"{run_path}/payload.json"
  # Precreate the running dir and the input payload file
  os.makedirs(run_path, exist_ok=True)
  with open(payload_file, 'w') as fh:
    json.dump(payload, fh)
  # Launch the NextFlow pipeline in the background
  pipeline = nextflow.Pipeline("blast_pipeline.nf")
  pipeline.run_and_poll(sleep=1, location=f"./{run_path}", params={"datafile": payload_file})
  # Return the job dir ID. Other endpoints need to later access the pipeline by its ID.
  return {'submission_id': run_id}

# Endpoint for querying a job status
@app.get("/blast/jobs/status/{job_id}")
async def blast_job_status(job_id: str) -> dict:
  #TODO: fetch job status from the nextflow pipeline
  return {'job_id': job_id, 'status': 'RUNNING'}

# Endpoint for querying multiple job statuses
@app.post("/blast/jobs/status")
async def blast_job_statuses(payload: JobIDs) -> dict:
  payload = jsonable_encoder(payload)
  statuses = [blast_job_status(job_id) for job_id in payload['job_ids']]
  return {'statuses': statuses}

# Proxy for JD BLAST REST API endpoints (/status/:id, /result/:id/:type)
@app.get("/blast/jobs/result/{job_id}")
async def blast_result(job_id: str) -> dict:
  #TODO: fetch final output file from the nextflow pipeline
  result_file = 'data/blast_payload.json'
  with open(result_file) as f:
    results = json.load(f)
  return results
