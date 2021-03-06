import logging
import subprocess
from itertools import tee

import click

from dlo_hic.utils.wrap.tabix import index_pairs
from dlo_hic.utils.stream import (read_file, write_to_file,
                                  upper_triangle, bedpe2pairs,
                                  sort_bedpe, sort_pairs)
from dlo_hic.utils.stream import remove_redundancy as rr

log = logging.getLogger(__name__)


@click.command(name="bedpe2pairs")
@click.argument("bedpe", nargs=1)
@click.argument("pairs", nargs=1)
@click.option("--keep/--no-keep",
    default=False,
    help="keep uncompressed pairs file, if you need create '.hic' file use --keep option.")
@click.option("--remove-redundancy/--not-remove-redundancy",
    default=False,
    help="Remove redundancy or not.")
@click.option("--ncpu",
    default=1,
    help="cpu numbers used for sort pairs.")
def _main(bedpe, pairs, keep, remove_redundancy, ncpu):
    """
    Transform BEDPE format file to pairs format, and index it use pairix

    \b
    about pairs format:
    https://github.com/4dn-dcic/pairix/blob/master/pairs_format_specification.md
    """

    if remove_redundancy:
        log.info("Remove redundancy in the Pairs file.")
        log.info("sort bedpe ...")
        line_iter = sort_bedpe(bedpe, ncpu=ncpu, by_etag=True)
        line_iter = upper_triangle(line_iter, fmt='bedpe')
        line_iter = rr(line_iter, 'bedpe', 0, by_etag=True)
    else:
        line_iter = read_file(bedpe)

    log.info("convert %s to pairs file %s ..."%(bedpe, pairs))
    line_iter = bedpe2pairs(line_iter)

    tmp = bedpe + ".tmp"
    write_to_file(line_iter, tmp, mode="w")

    log.info("sort pairs.")
    line_iter = sort_pairs(tmp, ncpu=ncpu)

    # add header
    header = "## pairs format v1.0\n" +\
             "#columns: readID chr1 position1 chr2 position2 strand1 strand2\n"
    with open(pairs, 'w') as f:
        f.write(header)

    write_to_file(line_iter, pairs, mode='a')

    subprocess.check_call(['rm', tmp])

    log.info("index and compress the Pairs")
    index_pairs(pairs)
    if keep:
        log.info("pairs file with header storaged at %s"%pairs)
        log.info("bgzip compressed and pairix indexed Pairs file storage at %s"%(pairs+'.gz'))
    else:
        log.info("bgzip compressed and pairix indexed Pairs file storage at %s"%(pairs+'.gz'))
        subprocess.check_call(['rm', pairs])  # remove uncompressed file

    log.info("BEDPE to Pairs done.")


main = _main.callback


if __name__ == "__main__":
    eval("_main()")