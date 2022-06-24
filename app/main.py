from fastapi import BackgroundTasks, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import nextflow
import secrets
import json
import os

app = FastAPI()

# In-memory cache for started pipelines
@app.on_event('startup')
async def startup_event():
  app.blast_runs = {}

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

# Function for launching the BLAST pipeline
# Input: submission ID, submission payload
def run_blast(run_id: str, payload: dict) -> str:
  # Prepare workdir
  run_path = f"./work/{run_id}"
  payload_file = f"{run_path}/payload.json"
  os.makedirs(run_path, exist_ok=True)
  with open(payload_file, 'w') as fh:
    json.dump(payload, fh)
  # Launch the pipeline and cahce the instance
  pipeline = nextflow.Pipeline("blast_pipeline.nf")
  blast_run = pipeline.run(location=run_path, params={"datafile": payload_file})
  app.blast_runs[run_id] = blast_run
  return blast_run

# Endpoint for submitting a BLAST job
@app.post('/blast/job')
async def submit_blast(payload: dict, background: BackgroundTasks) -> dict:
  run_id = secrets.token_urlsafe(16)
  # Launch the BLAST job pipeline in the background
  background.add_task(run_blast, run_id, payload)
  # Return the reference ID for accessing the pipeline instance later
  return {'submission_id': run_id}

# Endpoint for querying a job status
@app.get("/blast/jobs/status/{submission_id}")
async def blast_job_status(submission_id: str) -> dict:
  try:
    execution = app.blast_runs[submission_id]
  except KeyError:
    return {'error': f'Submission {submission_id} not found'}

  try:
    # Get pipeline step 2 (jDispatcher BLAST job polling)
    status_process = execution.process_executions[1]
    # Get last job status update
    job_status = status_process.stdout.split('\n')[-2]
  except KeyError:
    job_status = 'WAITING'
  # Alternative: use the status of the pipeline itself:
  # Execution.status or Execution.process_executions[N].status

  return {'submission_id': submission_id, 'status': job_status}

# Endpoint for querying multiple job statuses
@app.post("/blast/jobs/status")
async def blast_job_statuses(payload: JobIDs) -> dict:
  payload = jsonable_encoder(payload)
  statuses = [blast_job_status(job_id) for job_id in payload['job_ids']]
  return {'statuses': statuses}

# Endpoint for retrieving the results (processed json)
@app.get("/blast/jobs/result/{submission_id}")
async def blast_result(submission_id: str) -> dict:
  try:
    execution = app.blast_runs[submission_id]
  except KeyError:
    return {'error': f'Submission {submission_id} not found'}

  try:
    # Get file path from the last line of finished pipeline output
    result_file = execution.stdout.split('\n')[-2]
    if not result_file.startswith('/'):
      raise KeyError
  except KeyError:
    return {'error': 'Results file not available'}

  with open(result_file) as f:
    results = json.load(f)

  return results
