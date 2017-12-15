from __future__ import print_function
import re
import sys
import time
import signal
import tempfile
from Queue import Empty
from multiprocessing import Process, Queue

import pyfaidx
import click

from dlo_hic.utils import read_args
from dlo_hic.utils import reverse_complement as rc
from dlo_hic.utils.wrap.tabix import sort_bed6, index_bed6


TIME_OUT = 1


def worker(task_queue, output_queue, count_queue, rest, fasta):
    rest_rc = rc(rest)
    faidx = pyfaidx.Fasta(fasta)
    while 1:
        c = 0
        try:
            chr_ = task_queue.get(timeout=TIME_OUT)
        except Empty:
            break
        print(chr_, file=sys.stderr)
        seq = faidx[chr_][:].seq
        for match in re.finditer(rest, seq, re.IGNORECASE):
            output_queue.put(
                (chr_, str(match.start()), str(match.end()), '.', '0', '+')
            )
            c += 1
        if rest_rc != rest: # find reverse complement restriction site
            for match in re.finditer(rest_rc, seq, re.IGNORECASE):
                output_queue.put(
                    (chr_, str(match.start()), str(match.end()), '.', '0', '-')
                )
                c += 1
        count_queue.put(c)


def outputer(output_file, output_queue):
    """ output extracted results """
    def signal_handeler(signal, frame):
        output_file.flush()
        sys.exit(0) 
    signal.signal(signal.SIGTERM, signal_handeler)
    while 1:
        record = output_queue.get()
        line = "\t".join(record) + "\n"
        output_file.write(line)


@click.command(name="extract_rest_sites")
@click.argument("fasta", nargs=1)
@click.option("--rest-seq", "-r", required=True,
    help="The sequence of restriction site")
@click.argument("output", nargs=1)
@click.option("--processes", "-p", default=1,
    help="Use how many processes to run. default 1")
def _main(fasta, rest, output, processes):
    """ Extract all restriction sites from fasta file, save to BED6 file format. """
    faidx = pyfaidx.Fasta(fasta)
    chrs = faidx.keys()
    task_queue   = Queue()
    output_queue = Queue()
    count_queue = Queue()
    processes = min(processes, len(chrs))
    workers = [Process(target=worker,
                       args=(task_queue, output_queue, count_queue, rest, fasta))
               for i in range(processes)]

    for chr_ in chrs:
        task_queue.put(chr_)

    with tempfile.NamedTemporaryFile() as tmp:
        output_p = Process(target=outputer, args=(tmp, output_queue))

        for w in workers:
            w.start()
        output_p.start()

        for w in workers:
            w.join()

        c = 0
        while not count_queue.empty():
            c += count_queue.get()
        print("%d restriction sites found"%c, file=sys.stderr)

        while not output_queue.empty():
            time.sleep(TIME_OUT)
        output_p.terminate()

        # sort output bed file
        print("sorting bed file ...", file=sys.stderr)
        sort_bed6(tmp.name, output)
        print("building tabidx...", file=sys.stderr)
        index_bed6(output)

main = _main.callback

if __name__ == "__main__":
    _main()