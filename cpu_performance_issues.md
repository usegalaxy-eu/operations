# A Debugging Manual for CPU related Performance Issues

# Background
After migrating our major infrastructure servers (headnode and database) to AMD EPYC-7742 machines, we discovered the following issues:
- handler restarts take > 1 hour
- htop is very slow and takes ~10s to load
- ssh login is slow
- on the database server, a postgres restore took more than 10 hours

See also original [issue](https://github.com/usegalaxy-eu/issues/issues/763)
# 🎯 Goals
The goal is stability, not maximum performance. We try to keep the CPU cores and the overall system from massively clocking down due to overheating. With the previous settings, we have seen the cores clocking down to 400MHz. Some cores got stuck there, only a reboot helped.
# 📖 Manual + Firmware
For the mentioned servers (sn{09-12}), the hardware platform is Gigabyte H262-Z63, Revision 100 and
the user manual and firmware can be found [here](https://www.gigabyte.com/Enterprise/High-Density-Server/H262-Z63-rev-100)
**However** the currently running Firmware on the machines is newer than on Gigabyte's web page, because Dalco, our service partner
updated them.
The original manual provided by Gigabyte is outdated as well, and the [Rev. A00 manual](https://www.gigabyte.com/Enterprise/High-Density-Server/H262-Z63-rev-A00#Support-Manual) should be more reliable with regards to BIOS settings.
# 🔎 Debugging Strategy
## Software Interrupts
`top -H` which displays threads, showed an unusually high activity of `ksoftirqd`, the deamon that manages software interrupts. There is one daemon process per CPU.
Another symptom were kernel log messages about unusual long interrupts:
~~~
root@sn09:~$ journalctl -k -n 50
Aug 02 01:06:40 sn09.galaxyproject.eu kernel: Scheduler frequency invariance went wobbly, disabling!
Aug 02 12:44:43 sn09.galaxyproject.eu kernel: hrtimer: interrupt took 4577254 ns
~~~

High software interrupts could be caused by a high network activity, e.g. a [TCP-SYN-Flood Attac](https://www.baeldung.com/linux/ksoftirqd-processes-high-cpu), thus we should check the network activity using e.g.
~~~
sar -n DEV 1 3
~~~
Our package rates are usually below 100.000 per second.
In the case of issue 763 this was not the reason.

## Disks
Slow handler restarts could be also related to low disk read speed, which can be checked e.g. using `fio`.
~~~
fio --name=seqwrite --filename=/tmp/fio.test --size=4G --bs=1M  --rw=write --iodepth=32 --direct=1 --numjobs=1 --time_based=0
~~~

## ⏱️ CPU Clock speed
Single core processes suffer more from decreased clock speed than multithreaded processes. We can monitor the clock speed per CPU using
~~~
# live for all CPUs
watch -n 1 'grep "MHz" /proc/cpuinfo | sort -nr'

# show the slowest with tail
watch -n 1 'grep "MHz" /proc/cpuinfo | sort -nr | tail'

# mpstat -P ALL shows CPU usage per core
# 1 3 displays three reports of statistics for all processors at a one second interval.

mpstat -P ALL 1 3 | grep Average | awk '{print$3}' | grep -v "0.00" | wc -l

# Here we grep for cores that have any user process usage
mpstat -P ALL 1 3 | grep Average | awk '{print$3}' | grep -v "0.00" | wc -l

# Another tool is cpupower monitor
cpupower monitor
~~~

Testing the CPUs with `stress-ng` can lead to very counterintuitive results:
<video width=720 controls>
  <source src="images/stress-ng.mp4" type="video/mp4">
</video>

# 🪛 Settings
On the sn{09-12} these settings are our current approach to the problem.
## CPU Related BIOS Settings
Following settings might be changed when observing throttled CPU cores
* AMD CBS
  * `Core Performance Boost` has been `disabled` by us (This is AMD’s version of Intel’s Turbo Boost technology)
  * `Global C-State Control`  has been `disabled` by us (see [explanation in German](https://www.technikaffe.de/anleitung-32-c_states_p_states_s_states__energieverwaltung_erklaert/))
  * `Power Supply Idle Control` has been set to `Typical Current Idle`
  * `SMU Common Options` → `Power Policy Quick Setting` `Standard`
  * `Performance` → `CCD/Core/Enablement` → `SMT Control` has been `disabled` (Intel calls it Hyper-Threading, a detailed [manual](http://wiki.hpcmate.com/index.php/BIOS/SMT_Control))

Not yet tested, but has potential ...
* AMD CBS
  * `NBIO Common Options` --> `SMU Common options` --> `Determinism Control`  could be set to `manual`?
## OS Settings
Check how the CPU govenor is set:
~~~
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u
~~~
If it is not set to `schedutil` for all CPUs, make sure `Global C-State Control` has been disabled in BIOS.
This command lets the system decide to run the cores between 1.5, 2.0 and 2.25Ghz:
~~~
cpupower frequency-set -g schedutil
~~~
To set this permanently, i.e. after reboot, `cpupower` service needs to be activated and configured.
