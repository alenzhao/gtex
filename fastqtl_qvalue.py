#!/usr/bin/env python

import argparse, sys
import gzip
from scipy import stats
from argparse import RawTextHelpFormatter

__author__ = "Colby Chiang (cchiang@genome.wustl.edu)"
__version__ = "$Revision: 0.0.1 $"
__date__ = "$Date: 2016-03-27 09:43 $"

# --------------------------------------
# define functions

def get_args():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description="\
fastqtl_qvalue.py\n\
author: " + __author__ + "\n\
version: " + __version__ + "\n\
description: compute q-values from FastQTL nominal p-values (stdin) \n\
             based on the beta distribution of permutations")
    parser.add_argument('-i', '--input',
                        metavar='FILE', dest='input_path',
                        type=str, default=None,
                        help='FastQTL file of nominal p-values [stdin]')
    parser.add_argument('-p', '--permutation',
                        metavar='FILE', dest='permutation_path',
                        required=True,
                        type=str, default=None,
                        help='FastQTL file of permutation p-values [stdin]')

    # parse the arguments
    args = parser.parse_args()

    # if no input file, check if part of pipe and if so, read stdin.
    if args.input_path == None:
        if sys.stdin.isatty():
            parser.print_help()
            exit(1)

    # send back the user input
    return args

# open file (either plaintext or zip)
def get_file(filename):
    if filename.endswith('.gz'):
        data = gzip.open(filename, 'rb')
    else:
        data = open(filename, 'r')
    return data    

class Permutation(object):
    def __init__(self, v):
        self.pid = v[0]
        self.nvar = int(v[1])
        self.shape1 = float(v[2])
        self.shape2 = float(v[3])
        self.true_df = float(v[4])
        self.sid = v[5]
        self.distance = v[6]
        self.nom_pval = float(v[7])
        self.beta = float(v[8])
        self.perm_pval_direct = float(v[9])
        self.perm_pval_beta = float(v[10])

class Nominal(object):
    def __init__(self, v):
        self.pid = v[0]
        self.sid = v[1]
        self.distance = int(v[2])
        self.r = float(v[3])
        self.r2 = self.r ** 2
        self.nom_pval = float(v[4])
        self.beta = float(v[5])

# primary function
def calc_q(nominal, permutation):
    perm_dict = {}
    for line in permutation:
        v = line.rstrip().split(' ')
        perm_dict[v[0]] = Permutation(v)

    for line in nominal:
        v = line.rstrip().split(' ')
        nom = Nominal(v)
        perm = perm_dict[nom.pid]

        # calculate a corrected p-value based on the
        # Pearson correlation and true degrees of freedom
        # from the permutation
        x = (nom.r2) * perm.true_df / (1 - nom.r2)
        p_corr = stats.f.sf(x, 1, perm.true_df)
        pval_beta = (stats.beta.cdf(p_corr, perm.shape1, perm.shape2)) # q-value

        # write out
        print ' '.join(map(str,
                           [nom.pid,
                            perm.nvar,
                            perm.shape1,
                            perm.shape2,
                            perm.true_df,
                            nom.sid,
                            nom.distance,
                            nom.nom_pval,
                            nom.beta,
                            'NA',
                            pval_beta]))
    return

# --------------------------------------
# main function

def main():
    # parse the command line args
    args = get_args()

    # if no input file, check if part of pipe and if so, read stdin.
    if args.input_path == None:
        input_file = sys.stdin
    else:
        input_file = get_file(args.input_path)

    # get permutation data
    permutation_file = get_file(args.permutation_path)

    # call primary function
    calc_q(
        input_file,
        permutation_file
        )

    # close the files
    input_file.close()
    


# initialize the script
if __name__ == '__main__':
    try:
        sys.exit(main())
    except IOError, e:
        if e.errno != 32:  # ignore SIGPIPE
            raise 
