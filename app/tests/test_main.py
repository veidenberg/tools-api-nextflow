from fastapi.testclient import TestClient
import json
import pytest
from ..main import app

# Test config endpoint
def test_read_config():
	client = TestClient(app)
	with open('data/blast_config.json') as f:
		config = json.load(f)
	response = client.get('/blast/config')
	assert response.status_code == 200
	assert response.json() == config

# Load example BLAST job payload
@pytest.fixture
def blast_payload():
	with open('app/tests/blast_payload.json') as f:
		return json.load(f)

# Test single BLAST job submission with a valid payload
def test_blast_job(blast_payload):
	with TestClient(app) as client:
		response = client.post('/blast/job', json=blast_payload)
		assert response.status_code == 200
		resp = response.json()
		assert 'submission_id' in resp
		assert 'jobs' in resp
		assert len(resp['jobs']) == 1
		job = resp['jobs'][0]
		assert 'sequence_id' in job
		assert 'genome_id' in job
		assert 'job_id' in job
		assert job['job_id'].startswith('ncbiblast-')
		assert 'sequence_id' in job and job['sequence_id'] == 1

# Test BLAST job status endpoint
def test_blast_job_status():
	with TestClient(app) as client:
		response = client.get('/blast/jobs/status/ncbiblast-12345')
		assert response.status_code == 200
		assert 'status' in response.json()

# Test multiple jobs status endpoint
def test_blast_job_statuses():
	with TestClient(app) as client:
		job_ids = {'job_ids': ['ncbiblast-1234', 'ncbiblast-5678']}
		response = client.post('/blast/jobs/status', json=job_ids)
		assert response.status_code == 200
		resp = response.json()
		assert 'statuses' in resp
		assert len(resp['statuses']) == 2
		assert 'job_id' in resp['statuses'][0]
		assert 'status' in resp['statuses'][0]

# Test invalid endpoint error response
def test_404_error():
	with TestClient(app) as client:
		response = client.get('/blast/invalid_path')
		assert response.status_code == 404
		assert response.json() == {'error': 'Invalid endpoint'}