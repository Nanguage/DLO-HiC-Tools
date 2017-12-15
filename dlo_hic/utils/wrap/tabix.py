import sys
import subprocess

from dlo_hic.utils.parse_text import parse_line_bed6

def sort_bed6(file_in, file_out):
    """ sort bed file. """
    cmd = "sort -k1,1V -k2,2n -k3,3n {} > {}".format(file_in, file_out)
    subprocess.check_call(cmd, shell=True)

def sort_bedpe_reads1(file_in, file_out):
    """ sort bedpe file according to first 3 col(reads1). """
    cmd = "sort -k1,1V -k2,2n -k3,3n {} > {}".format(file_in, file_out)
    subprocess.check_call(cmd, shell=True)

def index_bed6(bedfile):
    """ build tabix index for bedfile.
    please ensure bed file is sorted """
    cmd = "cat {} | bgzip > {}".format(bedfile, bedfile+'.gz')
    subprocess.check_call(cmd, shell=True)
    cmd = "tabix -s 1 -b 2 -e 3 {}".format(bedfile+'.gz')
    subprocess.check_call(cmd, shell=True)

def query_bed6(bedfile, chr_, start, end):
    """ query to indexed bed file """
    start, end = str(start), str(end)
    cmd = "tabix {} {}:{}-{}".format(bedfile+'.gz', chr_, start, end)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        yield parse_line_bed6(line)

def sort_pairs(file_in, file_out):
    """ sort pairs file. """
    cmd = "sort -k2,2 -k4,4 -k3,3n -k5,5n {} > {}".format(file_in, file_out)
    subprocess.check_call(cmd, shell=True)

def index_pairs(pairs_file):
    """ build index for pairs file. """
    cmd = "cat {} | bgzip > {}".format(pairs_file, pairs_file+".gz")
    subprocess.check_call(cmd, shell=True)
    cmd = "pairix -f {}".format(pairs_file+".gz")
    subprocess.check_call(cmd, shell=True)