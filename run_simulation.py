import sys
import os


def _set_threads_pre_import():
    # NumPy (MKL) and Numba fix the thread count at import time. Since setup_env
    # in cli.main runs after NumPy is imported by cli.py, it does not affect MKL
    # threads. Set the values here before importing NumPy. Preserve any externally
    # configured environment variables by using setdefault.
    nt = str(os.cpu_count() or 1)
    for i, a in enumerate(sys.argv):
        if a == '--n-threads' and i + 1 < len(sys.argv):
            nt = sys.argv[i + 1]
        elif a.startswith('--n-threads='):
            nt = a.split('=', 1)[1]
    for k in ('MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS'):
        os.environ.setdefault(k, nt)


_set_threads_pre_import()

from pymnpbem_simulation.cli import main


if __name__ == '__main__':
    sys.exit(main())
