
# %%

from pathlib import Path
from itertools import combinations
from itertools import combinations_with_replacement
import logging
from time import sleep
import sys,os,re

# %%
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from spec17 import config
# %%
for scheme in ["all_shared", "all_partitioned", "all_adaptive", "all_asymmetric__"]:
  for i in range(2,3):
        for j in range(1,2):
          gem5_base_cmd = f"""{config.GEM5_BIN} \
                --outdir={config.ROOT}/results/sec_results/m5out/xz_{scheme}  \
                --stats-file=stats.txt  \
                {config.GEM5_CONFIG}  \
                  -I 100000000 --smt\
                  --caches --l2cache  --l1d_size=32kB --l1d_assoc=8 --l1i_size=32kB --l1i_assoc=8\
                  --cpu-type=Skylake_3 --maxinsts_threadID=0 \
                  --mem-type=DDR4_2400_16x4 --mem-size=64GB --mem-channels=2 """
          # gem5_cmd = gem5_base_cmd + f"-c '~/spec2017/benchspec/CPU/605.mcf_s/run/run_base_test_mytest-m64.0000/mcf_s_base.mytest-m64 ~/spec2017/benchspec/CPU/605.mcf_s/run/run_base_test_mytest-m64.0000/inp.in;~/spec2017/benchspec/CPU/605.mcf_s/run/run_base_test_mytest-m64.0000/mcf1_s_base.mytest-m64 ~/spec2017/benchspec/CPU/605.mcf_s/run/run_base_test_mytest-m64.0000/inp1.in' "
          # 600.perlbench_s
          # gem5_cmd = gem5_base_cmd + f"-c 'perlbench_s_base.mytest-m64 -I./lib checkspam.pl 2500 5 25 11 150 1 1 1 1;perlbench_s_base.mytest-m64 -I./lib checkspam.pl 2500 5 25 11 150 1 1 1 1' "
          # 602.gcc_s
          # gem5_cmd = gem5_base_cmd + f"-c 'sgcc_base.mytest-m64 gcc-pp.c -O5 -fipa-pta -o gcc-pp.opts-O5_-fipa-pta.s;sgcc_base.mytest-m64 gcc-pp.c -O5 -fipa-pta -o gcc-pp.opts-O5_-fipa-pta.s' "
          # 605.mcf_s
              # gem5_cmd = gem5_base_cmd + f"-c 'sgcc_base.mytest-64 gcc-pp.c -O5 -fipa-pta -o gcc-pp.opts-O5_fipa-pta.s;sgcc_base.mytest-64 gcc-pp.c -O5 -fipa-pta -o gcc-pp.opts-O5_fipa-pta.s' "
          # 620.omnetpp_S *
          # gem5_cmd = gem5_base_cmd + f"-c 'omnetpp_s_base.mytest-m64 -c General -r 0;omnetpp_s_base.mytest-m64 -c General -r 0' "
          # 623.xalancbmk_s
          # gem5_cmd = gem5_base_cmd + f"-c 'xalancbmk_s_base.mytest-m64 -v t5.xml xalanc.xsl;xalancbmk_s_base.mytest-m64 -v t5.xml xalanc.xsl' "
          # 625.x264_s
          # gem5_cmd = gem5_base_cmd + f"-c 'x264_s_base.mytest-m64 --pass 1 --stats x264_stats.log --bitrate 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720;x264_s_base.mytest-m64 --pass 1 --stats x264_stats.log --bitrate 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720' "
          # 631.deepsjeng
          # gem5_cmd = gem5_base_cmd + f"-c 'deepsjeng_s_base.mytest-m64 ref.txt;deepsjeng_s_base.mytest-m64 ref.txt' "
          # 641.leala_r
          # gem5_cmd = gem5_base_cmd + f"-c 'leela_s_base.mytest-m64 ref.sgf;leela_s_base.mytest-m64 ref.sgf' "
          # 648.exchange2_s *
          # gem5_cmd = gem5_base_cmd + f"-c 'exchange2_s_base.mytest-m64 6;exchange2_s_base.mytest-m64 6' "
          # 657.xz_s
          gem5_cmd =gem5_base_cmd + f"-c 'xz_s_base.mytest-m64 cpu2006docs.tar.xz 6643 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 1036078272 1111795472 4;xz_s_base.mytest-m64 cpu2006docs.tar.xz 6643 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 1036078272 1111795472 4' "
          gem5_cmd += "-o 'thread0;thread1' "
          partitioning_args = (row["gem5_args"] for row in config.jobs if row["name"]==scheme)
          gem5_cmd += next(partitioning_args)
          gem5_cmd = gem5_cmd.replace("Interval=100000", "Interval=100000000")

          print("gem5_cmnd:", gem5_cmd)
          print('\n')
          os.makedirs(f"{config.ROOT}/results/sec_results/", exist_ok=True)
          print (sys.argv)
          if len(sys.argv) > 1 and  sys.argv[1]=="slurm":
            res = config.nonblocking_out(f"srun --exclude=lynx[08-12] {gem5_cmd}  &> {config.ROOT}/results/sec_results/results_{i}_{j}_{scheme}.log")
          else:
            # res = config.out(f"{gem5_cmd}  &> {config.ROOT}/results/sec_results/results_{i}_{j}_{scheme}.log")
            res = config.out(f"{gem5_cmd}")
            res_file = f"{config.ROOT}/results/sec_results/mcf_{scheme}"
            #with open(res_file,'w') as file:
            #    file.write(res)
            #if(file.closed):
            #    print("\n")
            #    print(res_file)
            #file.close()
            print(res)
            print("%s ============>completed \n\n\n\n",res_file)

# %%
