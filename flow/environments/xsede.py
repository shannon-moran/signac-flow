# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""Environments for XSEDE supercomputers."""
from __future__ import print_function
import sys
import logging

from ..environment import DefaultSlurmEnvironment
from ..errors import SubmitError


logger = logging.getLogger(__name__)


class CometEnvironment(DefaultSlurmEnvironment):
    """Environment profile for the Comet supercomputer.

    http://www.sdsc.edu/services/hpc/hpc_systems.html#comet
    """
    hostname_pattern = 'comet'
    cores_per_node = 24

    @classmethod
    def calc_num_nodes(cls, np_total, ppn, force, partition, **kwargs):
        if 'shared' in partition:
            return 1
        else:
            try:
                return super(CometEnvironment, cls).calc_num_nodes(np_total, ppn, force)
            except SubmitError as error:
                if error.args[0] == "Bad node utilization!":
                    print("Use a shared partition for incomplete node utilization!",
                          file=sys.stderr)
                    raise error

    @classmethod
    def script(cls, _id, ppn, partition, memory=None, job_output=None, **kwargs):
        js = super(CometEnvironment, cls).script(_id=_id, ppn=ppn, **kwargs)
        js.writeline('#SBATCH -A {}'.format(cls.get_config_value('account')))
        js.writeline('#SBATCH --partition={}'.format(partition))
        if memory is not None:
            js.writeline('#SBATCH --mem={}G'.format(memory))
        if job_output is not None:
            js.writeline('#SBATCH --output="{}"'.format(job_output))
            js.writeline('#SBATCH --error="{}"'.format(job_output))
        return js

    @classmethod
    def mpi_cmd(cls, cmd, np):
        return "ibrun -v -np {np} {cmd}".format(cmd=cmd, np=np)

    @classmethod
    def add_args(cls, parser):
        super(CometEnvironment, cls).add_args(parser)

        parser.add_argument(
          '-p', '--partition',
          choices=['compute', 'gpu', 'gpu-shared', 'shared', 'large-shared', 'debug'],
          default='shared',
          help="Specify the partition to submit to.")

        parser.add_argument(
            '--memory',
            help=("Specify how much memory to reserve per node in GB. "
                  "Only relevant for shared queue jobs."))

        parser.add_argument(
            '--job-output',
            help=('What to name the job output file. '
                  'If omitted, uses the system default '
                  '(slurm default is "slurm-%%j.out").'))


class Stampede2Environment(DefaultSlurmEnvironment):
    """Environment profile for the Stampede2 supercomputer.

    https://www.tacc.utexas.edu/systems/stampede2
    """
    hostname_pattern = '.*stampede2'
    cores_per_node = 48

#    @classmethod
#    def calc_num_nodes(cls, np_total, ppn, force=False, **kwargs):
#        # Always just the number of nodes
#        return np_total

    @classmethod
    def script(cls, _id, tpn, ppn, partition, job_output=None, **kwargs):
        js = super(Stampede2Environment, cls).script(_id=_id, ppn=ppn, **kwargs)
        # Stampede does not require account specification if you only
        # have one, so it is optional here.
        acct = cls.get_config_value('account', None)
        if acct is None:
            logger.debug(
                    "No account found, assuming you can submit without one")
        else:
            js.writeline('#SBATCH -A {}'.format(acct))
        js.writeline('#SBATCH --partition={}'.format(partition))
        js.writeline('#SBATCH --ntasks-per-node={}'.format(tpn))
        if job_output is not None:
            js.writeline('#SBATCH --output="{}"'.format(job_output))
            js.writeline('#SBATCH --error="{}"'.format(job_output))
        return js

    @classmethod
    def mpi_cmd(cls, cmd, np):
        return "ibrun {cmd}".format(cmd=cmd)

    @classmethod
    def add_args(cls, parser):
        super(Stampede2Environment, cls).add_args(parser)
        # Hack to remove the undesirable ppn argument in this case
        parser.add_argument(
            '-p', '--partition',
            choices=['development', 'normal', 'large', 'flat-quadrant',
                     'skx-dev', 'skx-normal', 'skx-large'],
            default='skx-normal',
            help="Specify the partition to submit to.")
        parser.add_argument(
            '--tpn',
            type=int,
            default=1,
            help="The number of tasks per node. Note that this is NOT "
                 "the number of processors you are allocated; you are "
                 "always allocated complete nodes on stampede. This "
                 "arg is passed to ibrun to control MPI jobs.")
        parser.add_argument(
            '--job-output',
            help=('What to name the job output file. '
                  'If omitted, uses the system default '
                  '(slurm default is "slurm-%%j.out").'))


class BridgesEnvironment(DefaultSlurmEnvironment):
    """Environment profile for the Bridges super computer.

    https://portal.xsede.org/psc-bridges
    """
    hostname_pattern = '.*\.bridges\.psc\.edu$'
    cores_per_node = 28

    @classmethod
    def calc_num_nodes(cls, np_total, ppn, force, partition, **kwargs):
        if 'shared' in partition.lower():
            return 1
        else:
            try:
                return super(BridgesEnvironment, cls).calc_num_nodes(np_total, ppn, force)
            except SubmitError as error:
                if error.args[0] == "Bad node utilization!":
                    print("Use a shared partition for incomplete node utilization!",
                          file=sys.stderr)
                    raise error

    @classmethod
    def script(cls, _id, ppn, partition, **kwargs):
        js = super(BridgesEnvironment, cls).script(_id=_id, ppn=ppn, **kwargs)
        js.writeline('#SBATCH --partition={}'.format(partition))
        return js

    @classmethod
    def add_args(cls, parser):
        super(BridgesEnvironment, cls).add_args(parser)
        parser.add_argument(
          '-p', '--partition',
          choices=['RM', 'RM-shared', 'RM-small', 'GPU', 'GPU-shared', 'LM'],
          default='RM-shared',
          help="Specify the partition to submit to.")


__all__ = ['CometEnvironment', 'Stampede2Environment', 'BridgesEnvironment']
