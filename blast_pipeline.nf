#!/usr/bin/env nextflow
nextflow.enable.dsl = 2 

/*
 * Simple linear pipeline for submitting a BLAST job and processing its results.
 * Input: path to job payload file
 * Ouput: path to processed BLAST results file
 */

// Input parameters (defaults can be overriden in config file or in at launch time)
params.datafile = "data/blast_payload.json" //default: example job submission payload
params.hostname = "wwwdev.ebi.ac.uk" //jDispatcher REST service hostname
params.outformat = "json" //BLAST results file output format (text|json|xml|html|...)

//Submit a BLAST job to jDispatcher REST endpoint
process submitBlast {
    //debug true //uncomment to print out job ID
    input:
      path datafile //path to json file containing the job payload
    output:
    	stdout //response from JD endpoint (job ID)

    script:
      """
      #!/usr/bin/env python3
      import requests
      import json

      payload = json.loads(open('$datafile').read())
      # requests module converts json (dict) to multipart/formdata
      resp = requests.post('http://$params.hostname/Tools/services/rest/ncbiblast/run', data=payload)
      # check submission response and exit with stack trace on failure
      assert resp.status_code==200 and resp.text.startswith('ncbiblast-'), f'Job submission failed: {resp.text}'
      # send job ID to stdout
      print(resp.text, end='')
      """
}

//Ping a jDispatcher job status until completion
process checkStatus {
    //debug true //print status polling responses
    input:
      val job_id
    output:
      val job_id //pass job ID to the next step
      val task.workDir.resolve('job_status').text //output file contains the last status string

    script:
      """
      python3 $baseDir/check_job.py $job_id --host $params.hostname --timeout 10 --outfile job_status
      """
}

//Download the job results file from jDispatcher
process getResults {
    input:
      val job_id
      val job_status
    output:
      path 'job_results'
    when:
      //Pipeline checkpoint. Drawback: on failure, rest of the pipeline skips silently. 
      job_status.trim() == 'FINISHED'
    
    script:
      """
      curl http://$params.hostname/Tools/services/rest/ncbiblast/result/$job_id/$params.outformat > job_results
      """
}

//Post-process the job results file
process processResults {
    input:
      path job_results
    output:
      path 'processed_results'
    
    script:
      """
      sed 's/Amel_HAv3.1/bumble_bee/g' $job_results > processed_results
      """
}

// Run the pipeline processes as a workflow, passing the intermediate values/files via channels
// Pipeline output: path to the final output file
workflow{
  data_ch = Channel.fromPath("$baseDir/$params.datafile", checkIfExists: true)
  output_ch = submitBlast(data_ch) | checkStatus | getResults | processResults
  output_ch.view{ "Processed output file: $it" } //print the pipeline output value
}