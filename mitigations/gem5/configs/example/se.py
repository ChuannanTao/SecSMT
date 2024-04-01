# Copyright (c) 2012-2013 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2006-2008 The Regents of The University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Simple test script
#
# "m5 test.py"

from __future__ import print_function
from __future__ import absolute_import

import optparse
import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import addToPath, fatal, warn

addToPath('../')

from ruby import Ruby

from common import Options
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import ObjectList
from common import MemConfig
from common.FileSystemConfig import config_filesystem
from common.Caches import *
from common.cpu2000 import *

def get_processes(options):
    """Interprets provided options and returns a list of processes"""

    multiprocesses = []
    inputs = []
    outputs = []
    errouts = []
    pargs = []
    words = []

    workloads = options.cmd.split(';')
    if options.input != "":
        inputs = options.input.split(';')
    if options.output != "":
        outputs = options.output.split(';')
    if options.errout != "":
        errouts = options.errout.split(';')
    if options.options != "":
        pargs = options.options.split(';')

    current_dir = os.getcwd()
    idx = 0
    for wrkld in workloads:
        process = Process(pid = 100 + idx)
        words = wrkld.split()

        process.executable = words[0]
        print('\n\n')
        print("process.executable = %s",words[0])
        

        sub_dir1 = "run_base_refspeed_mytest-m64.0000"
        sub_dir2 = "run_base_refspeed_mytest-m64.0001"


        if idx == 0:
            next_dir = os.path.join(current_dir, sub_dir1)
        elif idx == 1:
            next_dir = os.path.join(current_dir, sub_dir2)
        os.chdir(next_dir)
        process.cwd = os.getcwd()

        if options.env:
            with open(options.env, 'r') as f:
                process.env = [line.rstrip() for line in f]

        if len(words) > 1:
            process.cmd = words
        else:
            process.cmd = words

        if len(pargs) > idx: 
            process.cmd = process.cmd + pargs[idx].split()
        # else:
        #    process.cmd = [wrkld]
        print('\n\n')
        print("process.cmd = %s",process.cmd)

        if len(inputs) > idx:
            process.input = inputs[idx]
        if len(outputs) > idx:
            process.output = outputs[idx]
        if len(errouts) > idx:
            process.errout = errouts[idx]
        # process.executable = 'perlbench_s_base.mytest-m64'
        # process.cmd = ['perlbench_s_base.mytest-m64','-I./lib','checkspam.pl','2500','5','25','11','150','1','1','1','1']+ pargs[idx].split()
        # process.executable = 'sgcc_base.mytest-m64'
        # process.cmd = ['sgcc_base.mytest-m64','gcc-pp.c','-O5','-fipa-pta','-o','gcc-pp.opts-O5_-fipa-pta.s']+ pargs[idx].split()
        
         #   process.executalbe
        multiprocesses.append(process)
        idx += 1

    if options.smt:
        assert(options.cpu_type == "DerivO3CPU" or
            options.cpu_type == "Skylake_3")
        return multiprocesses, idx
    else:
        return multiprocesses, 1


parser = optparse.OptionParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

if '--ruby' in sys.argv:
    Ruby.define_options(parser)

(options, args) = parser.parse_args()

if args:
    print("Error: script doesn't take any positional arguments")
    sys.exit(1)

multiprocesses = []
numThreads = 1

if options.bench:
    apps = options.bench.split("-")
    if len(apps) != options.num_cpus:
        print("number of benchmarks not equal to set num_cpus!")
        sys.exit(1)

    for app in apps:
        try:
            if buildEnv['TARGET_ISA'] == 'arm':
                exec("workload = %s('arm_%s', 'linux', '%s')" % (
                        app, options.arm_iset, options.spec_input))
            else:
                exec("workload = %s(buildEnv['TARGET_ISA', 'linux', '%s')" % (
                        app, options.spec_input))
            multiprocesses.append(workload.makeProcess())
        except:
            print("Unable to find workload for %s: %s" %
                  (buildEnv['TARGET_ISA'], app),
                  file=sys.stderr)
            sys.exit(1)
elif options.cmd:
    print("\n\nget_process()\n\n")
    multiprocesses, numThreads = get_processes(options)
else:
    print("No workload specified. Exiting!\n", file=sys.stderr)
    sys.exit(1)


(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(options)
CPUClass.numThreads = numThreads
if FutureClass is not None:
    FutureClass.numThreads = numThreads

# Check -- do not allow SMT with multiple CPUs
if options.smt and options.num_cpus > 1:
    fatal("You cannot use SMT with multiple CPUs!")

np = options.num_cpus
system = System(cpu = [CPUClass(cpu_id=i) for i in range(np)],
                mem_mode = test_mem_mode,
                mem_ranges = [AddrRange(options.mem_size)],
                cache_line_size = options.cacheline_size,
                workload = NULL)

if numThreads > 1:
    system.multi_thread = True

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage = options.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(clock =  options.sys_clock,
                                   voltage_domain = system.voltage_domain)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(clock = options.cpu_clock,
                                       voltage_domain =
                                       system.cpu_voltage_domain)

# If elastic tracing is enabled, then configure the cpu and attach the elastic
# trace probe
if options.elastic_trace_en:
    CpuConfig.config_etrace(CPUClass, system.cpu, options)

# All cpus belong to a common cpu_clk_domain, therefore running at a common
# frequency.
for cpu in system.cpu:
    cpu.clk_domain = system.cpu_clk_domain

if ObjectList.is_kvm_cpu(CPUClass) or ObjectList.is_kvm_cpu(FutureClass):
    if buildEnv['TARGET_ISA'] == 'x86':
        system.kvm_vm = KvmVM()
        for process in multiprocesses:
            process.useArchPT = True
            process.kvmInSE = True
    else:
        fatal("KvmCPU can only be used in SE mode with x86")

# Sanity check
if options.simpoint_profile:
    if not ObjectList.is_noncaching_cpu(CPUClass):
        fatal("SimPoint/BPProbe should be done with an atomic cpu")
    if np > 1:
        fatal("SimPoint generation not supported with more than one CPUs")


policy_obj = ObjectList.policy_obj
for i in range(np):
    if options.smt:
        system.cpu[i].workload = multiprocesses

        if buildEnv['TARGET_ISA'] != 'x86':
            fatal("SMT Policies only work for x86")

        cpuList = [system.cpu[i]]
        if  FutureClass is not None: 
            cpuList += [FutureClass]

        for cpuclass in cpuList:

            cpuclass.smtIQPolicy = policy_obj("smtIQPolicy", options)
            cpuclass.smtLQPolicy = policy_obj("smtLQPolicy", options)
            cpuclass.smtSQPolicy = policy_obj("smtSQPolicy", options)
            cpuclass.smtROBPolicy = policy_obj("smtROBPolicy", options)
            cpuclass.itb.smtTLBPolicy = policy_obj("smtTLBPolicy", options)
            cpuclass.dtb.smtTLBPolicy = policy_obj("smtTLBPolicy", options)       
            cpuclass.smtIntRegPolicy = policy_obj("smtPhysRegPolicy", options)
            cpuclass.smtVecRegPolicy = policy_obj("smtPhysRegPolicy", options)
            cpuclass.smtFloatRegPolicy = policy_obj("smtPhysRegPolicy", options)
            cpuclass.branchPred.smtPolicy = policy_obj("smtBTBPolicy", options)


            if hasattr(cpuclass, "smtMainThread"):
                cpuclass.smtMainThread = options.maxinsts_threadID

            if options.smtPhysRegPolicy == "AsymmetricSMTPolicy":
                cpuclass.smtFloatRegPolicy.min_free = 20
                cpuclass.smtIntRegPolicy.min_free = 20
                cpuclass.smtVecRegPolicy.min_free = 20
           
            #Stateless resources:
            if hasattr(cpuclass, "smtIssuePolicy"):
                cpuclass.smtIssuePolicy = options.smtIssuePolicy
                cpuclass.smtIssueInterval = options.smtAdaptiveInterval
                cpuclass.smtIssueLimit = options.smtIssuePolicy_limit
                cpuclass.smtIssueMult = options.smtIssuePolicy_mult

            if hasattr(cpuclass, "smtFetchPolicy"):
                cpuclass.smtFetchInterval = options.smtAdaptiveInterval
                cpuclass.smtFetchPolicy = options.smtFetchPolicy
                cpuclass.smtFetchLimit = options.smtFetchPolicy_limit
                cpuclass.smtFetchMult = options.smtFetchPolicy_mult
            
            if hasattr(cpuclass, "smtCommitPolicy"):
                cpuclass.smtFetchInterval = options.smtAdaptiveInterval
                cpuclass.smtCommitPolicy = options.smtCommitPolicy
                cpuclass.smtCommitLimit = options.smtCommitPolicy_limit
                cpuclass.smtCommitMult = options.smtCommitPolicy_mult

    elif len(multiprocesses) == 1:
        system.cpu[i].workload = multiprocesses[0]
    else:
        system.cpu[i].workload = multiprocesses[i]

    if options.simpoint_profile:
        system.cpu[i].addSimPointProbe(options.simpoint_interval)

    if options.checker:
        system.cpu[i].addCheckerCpu()

    if options.bp_type:
        bpClass = ObjectList.bp_list.get(options.bp_type)
        system.cpu[i].branchPred = bpClass()

    if options.indirect_bp_type:
        indirectBPClass = \
            ObjectList.indirect_bp_list.get(options.indirect_bp_type)
        system.cpu[i].branchPred.indirectBranchPred = indirectBPClass()

    system.cpu[i].createThreads()

if options.ruby:
    Ruby.create_system(options, False, system)
    assert(options.num_cpus == len(system.ruby._cpu_ports))

    system.ruby.clk_domain = SrcClockDomain(clock = options.ruby_clock,
                                        voltage_domain = system.voltage_domain)
    for i in range(np):
        ruby_port = system.ruby._cpu_ports[i]

        # Create the interrupt controller and connect its ports to Ruby
        # Note that the interrupt controller is always present but only
        # in x86 does it have message ports that need to be connected
        system.cpu[i].createInterruptController()

        # Connect the cpu's cache ports to Ruby
        system.cpu[i].icache_port = ruby_port.slave
        system.cpu[i].dcache_port = ruby_port.slave
        if buildEnv['TARGET_ISA'] == 'x86':
            system.cpu[i].interrupts[0].pio = ruby_port.master
            system.cpu[i].interrupts[0].int_master = ruby_port.slave
            system.cpu[i].interrupts[0].int_slave = ruby_port.master
            system.cpu[i].itb.walker.port = ruby_port.slave
            system.cpu[i].dtb.walker.port = ruby_port.slave
else:
    MemClass = Simulation.setMemClass(options)
    system.membus = SystemXBar()
    system.system_port = system.membus.slave
    CacheConfig.config_cache(options, system)
    MemConfig.config_mem(options, system)
    config_filesystem(system, options)

if options.wait_gdb:
    for cpu in system.cpu:
        cpu.wait_for_remote_gdb = True

root = Root(full_system = False, system = system)
Simulation.run(options, root, system, FutureClass)
