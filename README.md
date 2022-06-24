## Nextflow pipeline for Tools API

A proof-of-concept Tools API service that runs BLAST jobs through Nextflow pipelines.

This repo contains:

- REST microservice (FastAPI app) with current Tools API endpoints (`2020.ensembl.org/api/tools/blast/...`)
- A 4-step NextFlow pipeline for running a BLAST job from submission to processed results file

This repo needs:

- A task management layer between the nextflow pipeline and the Tools API REST service

NextFlow runs a BLAST job from start to finish, storing all data to files.
Tools API needs a way to launch, inspect and manage the pipelines (e.g. to get a BLAST job status from the step 2 of a specific pipeline run).  FastAPI currently uses the [nextflow python module](https://github.com/goodwright/nextflow.py) for this, but it's quite limited and lacks features like a jobs database, track/trace, dashboard, etc.

### Setup

- See the [docs](https://www.nextflow.io) to install Nextflow
- Optional: create [Nextflow Tower](https://tower.nf) user account and add its access token to `nextflow.config` file

### Usage

Run the pipeline locally (uses the included BLAST job submission payload):
```
nextflow run blast_pipeline.nf
```
Add `-with-tower` to send the pipeline status to Nextflow Tower dashboard.
Add `-with-docker` to run the pipeline in a container.
Nextflow's docker option only includes the pipeline. 
Needs a custom setup to add nextflow runtime, Tools API server etc.

Run the pipelne through Tools API:

- Start the REST server (e.g. in python virtualenv):

```
pip3 install --no-cache-dir -r requirements.txt
uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port 8000
```
See `http://localhost:8000/docs` for available endpoints.

- Start the pipeline (submit a BLAST job to the Tools API REST ednpoint):

```
curl -H 'Content-Type: application/json' -d @data/blast_payload.json http://localhost:8000/blast/job
```
Returns submission ID.

- Get status of the BLAST job: `http://localhost:8000/blast/jobs/status/:submission_id`
- Get processed BLAST results file: `http://localhost:8000/blast/jobs/result/:submission_id`


See `blast_pipeline.nf` script and [Nextflow docs](https://www.nextflow.io/docs/latest/index.html) for more details about the pipeline.