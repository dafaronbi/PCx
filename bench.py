#!/usr/bin/python
import os
import re

class PTInfo():
    def __init__(self, name):
        self.name = name
        self.brows = 0
        self.bcols = 0
        self.arows = 0
        self.acols = 0
        self.rel_infeas = 0
        self.rel_compl = 0
        self.prim_obj = 0
        self.max_corr = 0
        self.it = 0
        self.cpu = 0

    def add_status(self, status):
        self.status = status

    def add_brows(self, rows):
        self.brows = rows

    def add_bcols(self, cols):
        self.bcols = cols

    def add_arows(self, rows):
        self.arows = rows

    def add_acols(self, cols):
        self.acols = cols

    def add_rel_infeas(self, rel_infeas):
        self.rel_infeas = rel_infeas

    def add_rel_compl(self, rel_compl):
        self.rel_compl = rel_compl

    def add_prim_obj(self, prim_obj):
        self.prim_obj = prim_obj

    def add_max_corr(self, max_corr):
        self.max_corr = max_corr

    def add_it(self, it):
        self.it = it

    def add_cpu(self, cpu):
        self.cpu = cpu

    def csv_header(self):
        return ("Name,Rows b.p.,Cols b.p.,Rows a.p.,Cols a.p.,Relative Infeas,"
                "Relative Compl,Primal Objective,Max Add. Corr.,Iters,CPU Time"
                " [secs]\n")

    def csv(self):
        return "{},{},{},{},{},{},{},{},{},{},{}\n".format(self.name, self.brows,
                self.bcols, self.arows, self.acols, self.rel_infeas,
                self.rel_compl, self.prim_obj, self.max_corr, self.it, self.cpu)

def bench(p, o, mf, n, s, i, x):
    """
    Run the benchmark.

    :param p: Path of the files to be used.
    :type p: str
    :param o: Output file name.
    :type o: str
    :param mf: Maximum number of files to be used.
    :type mf: int
    :param n: Sort list of files to be used by name.
    :type n: bool
    :param s: Sort list of files to be used by size.
    :type n: bool
    :param i: List of files to be used for the benchmark.
    :type i: list of str
    :param x: List of files to be exclude from the benchmark.
    :type i: list of str
    """
    import subprocess

    # Check if path exist.
    if not os.path.exists(p):
        raise FileNotFoundError("can't find directory '{0}'".format(p))

    of = open(o, 'w')
    of.write(PTInfo('').csv_header())

    # Process list of files to be used in the benchmark.
    if i:
        fl = i
    else:
        fl = os.listdir(p)
        if n:
            fl.sort()
        elif s:
            fl.sort(key=lambda fname: os.path.getsize('{0}/{1}'.format(p,fname)))
        if mf:
            fl = fl[0:mf]
        if x:
            for r in x:
                try:
                    fl.remove(r)
                except ValueError:
                    pass

    # Run PCx for every file in ``fl``.
    for f in fl:
        call_stdout = open("/dev/null", 'w')
        print("Running PCx for {0}. It can take some minutes.".format(f))
        subprocess.call(["./PCx", f], stdout=call_stdout)
        print("End running PCx.")
        call_stdout.close()
        with open(f.replace("mps", "log"), 'r') as log:
            info = PTInfo(f)
            step = 0  # step is responsible to select the regex to be used.
            for l in log:
                if step == 0:
                    m = re.match('Iterations=(?P<it>[0-9]*), Termination Code=(?P<status>[0-9])', l)
                    if m:
                        info.add_status(m.group('status'))
                        info.add_it(m.group('it'))
                        step += 1
                elif step == 1:
                    m = re.match('.*Before Presolving:.* (?P<rows>[0-9]*) rows,.* (?P<cols>[0-9]*) columns', l)
                    if m:
                        info.add_brows(m.group('rows'))
                        info.add_bcols(m.group('cols'))
                        step += 1
                elif step == 2:
                    m = re.match('.*After  Presolving:.* (?P<rows>[0-9]*) rows,.* (?P<cols>[0-9]*) columns', l)
                    if m:
                        info.add_arows(m.group('rows'))
                        info.add_acols(m.group('cols'))
                        step += 1
                elif step == 3:
                    m = re.match('Primal Objective = (?P<po>[ -][0-9]*.[0-9]*e[+-][0-9]*).*', l)
                    if m:
                        info.add_prim_obj(m.group('po'))
                        step += 1
                elif step == 4:
                    m = re.match('Relative Complementarity = (?P<rc>[ -][0-9]*.[0-9]*e[+-][0-9]*).*', l)
                    if m:
                        info.add_rel_compl(m.group('rc'))
                        step += 1
                elif step == 5:
                    m = re.match('Primal =(?P<rip>[ -][0-9]*.[0-9]*e[+-][0-9]*).*', l)
                    if m:
                        info.add_rel_infeas(m.group('rip'))
                        step += 1
                elif step == 6:
                    m = re.match('Time to solve.*:= (?P<cpu>[0-9]*.\.[0-9]*).*', l)
                    if m:
                        info.add_cpu(m.group('cpu'))
                        step += 1
            of.write(info.csv())
        subprocess.call(["rm", f.replace(".mps", ".log")])
    of.close()

def check_spc_file(f2check, p):
    """
    This function check if a given specification file can be used.

    :param f2check: Name of the file to be checked.
    :type f2check: str
    :param p: Path to be used when check the file.
    :type p: str
    """
    with open(f2check, 'r') as f:
        for l in f:
            m = re.match('history.*(?P<toggle>(yes|no|))', l)
            if m:
                if m.group('toggle') in ['yes', '']:
                    history = True
                elif m.group('toggle') == 'no':
                    history == False
            m = re.match('inputdirectory (?P<dir>.*)', l)
            if m:
                if m.group('dir') == p:
                    path = True
                else:
                    path = False
    return history and path

def check_spc(path):
    """
    This function check if the specifications file can be used.

    :param p: Path to be used when check the file.
    :type p: str
    """
    spc_correct = False
    if os.path.isfile('spc'):
        spc_correct = check_spc_file('spc', path)
    elif os.path.isfile('specs'):
        spc_correct = check_spc_file('sepcs', path)
    elif os.path.isfile('PCx.specs'):
        spc_correct = check_spc_file('PCx.specs', path)
    return spc_correct

if __name__ == "__main__":
    """Benchmark for PCx. ::

        $ bench.py --help
    """
    import sys
    import argparse
    from argparse import RawTextHelpFormatter

    if sys.version_info[0] < 3:
        raise Exception('It require Python 3.0 or later.')

    # Parse of flags.
    parser = argparse.ArgumentParser(description='Benchmark for PCx.',
            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-p', '--path', type=str, default='./mps',
            help='Path of the files to be used.')
    parser.add_argument('-o', '--output', type=str, default='bench.out',
            help='Output file name.')
    parser.add_argument('--max', type=int, default=None,
            help="Maximum number of files to be used.")
    bench_sort = parser.add_mutually_exclusive_group()
    bench_sort.add_argument('-n', '--name', action='store_true',
            help='Sort list of files to be used by name.')
    bench_sort.add_argument('-s', '--size', action='store_true',
            help='Sort list of files to be used by size.')
    bench_file = parser.add_mutually_exclusive_group()
    bench_file.add_argument('-i', '--input', nargs='+', type=str, default=[],
            help="List of files to be used for the benchmark.")
    bench_file.add_argument('-x', '--exclude', nargs='+', type=str, default=[],
            help="List of files to be exclude from the benchmark.")

    args = parser.parse_args()

    if check_spc(args.path):
        pass
        bench(args.path, args.output, args.max, args.name, args.size,
                args.input, args.exclude)
    else:
        print("The specification file must contain 'history yes'.\n")