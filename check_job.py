#!/usr/bin/python

"""Ping a status of JDispatcher BLAST job until completion."""

import argparse
from time import sleep, time
from typing import TextIO
import requests


def main():
    """Parse input arguments and run the job status pinging loop."""

    parser = argparse.ArgumentParser(
        description="Pings a status of JDispatcher BLAST job until completion."
    )
    parser.add_argument("job_id", type=str, help="Job ID.")
    parser.add_argument(
        "-i", "--interval", type=int, default=1, help="Pinging time interval (in sec)."
    )
    parser.add_argument(
        "-w",
        "--host",
        type=str,
        default="wwwdev.ebi.ac.uk",
        help="JDispatcher REST endpoint hostname.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=60,
        help="Max. time (timeout, in minutes) to keep pinging an unfinished job.",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        default="job_status",
        help="Output file for storing the latest job status.",
    )
    args = parser.parse_args()

    finished = False
    started = time()
    with open(args.outfile, "w", encoding="utf-8") as fh:
        while not finished:
            finished = ping_job(args.job_id, args.host, fh)
            if args.timeout * 60 > time() - started:
                sleep(args.interval)


def ping_job(job_id: str, host: str, outfile: TextIO) -> str:
    """
    Fetch job status from JD REST endpoint

    Args:
        job_id (str): jDispatcher job ID
        host (str): REST endpoint hostname
        outfile (TextIO): file handle for storing the job status

    Returns:
        str: job status from JD
    """

    req = requests.get(f"http://{host}/Tools/services/rest/ncbiblast/status/{job_id}")
    status = req.text
    done = ["FINISHED", "CANCELLED", "NOT_FOUND"]
    outfile.truncate(0) # overwrite with the latest status
    print(status, file=outfile, end="")
    print(status)
    return req.status_code != 200 or status in done


if __name__ == "__main__":
    main()
