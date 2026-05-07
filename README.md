# PhisonExecutor

## Introduction
PhisonExecutor is a Python infrastructure that allows executing arbitrary code on many Phison SSD controllers.

## How?
Generally, executing code on SSD controllers is not a feature vendors allow, so to do that, the controller must be researched thoroughly to find vulnerabilities or some vendor-specific commands (VSCs) that can enable an attacker constructing primitives to achieve that.

In many Phison firmwares, there exists a Security Access mechanism, that exposes a variety of Phison vendor-specific commands if the host communicating with the controller manages to complete a challenge-response-based authentication. This authentication scheme consists of 4 steps in total, in which the last 2 correspond to the actual challenge-response phase; in a nutshell, the controller sends a challenge in which some of it is encrypted by RSA. To complete the challenge, the controller expects to receive a response in which part of it should be AES-encrypted using a key that is generated based on the challenge and one of the RSA parameters.

As it turns out, there exist utility binary applications which expose the RSA parameters for the firmwares we currently support. One such binary is Crucial’s Storage Executive command-line application. The Linux-based binary contains many symbols, which makes understanding what kind of Phison vendor-specific commands exist and how they work fairly easy, as well as the RSA parameters for many firmwares.
Once the RSA parameters are known, an attacker can complete the authentication and have access to many additional Phison vendor-specific commands. Some of the available vendor-specific commands are the arbitrary read-write commands, in which an attacker can supply an address and size and then either read or write from/to the requested memory region (this covers the entire address space of the controller, including SRAM, registers, etc.).

## Exploitation
Given arbitrary read/write to the controller's SRAM and seeing that the code sections are not even protected by the core's MPU, exploitation here is fairly trivial; One can install a trampoline in one of the command handlers that points to some other writable location where we can put our own code to execute, and then return to the original flow from there.
We will use <SERVER> to upgrade our read/write primitive to actual code execution.

The tested SSDs we tested (and are thus currently the only ones supported by the executor):
- PNY CS3030 (ECFM32.2)
- MSI Spatium M470 (EGFM13.2)
- Kingston KC3000 (EIFK51.2)
- Sabrent Rocket 4 Plus (EIFM80.0)

## Usage
PhisonExecutor can be run on Windows and Linux machines (Windows 10 and Ubuntu 24.04 were tested). Python3 >3.5 should be used for executing the script. Please also note the requirements.txt file that should be used to install dependencies.

```
usage: phison_shell.py [-h] device

positional arguments:
  device      the path to the Phison NVMe device

options:
  -h, --help  show this help message and exit
```

Upon executing the script, an IPython shell will spawn, after which the executor's functionality can be access via the 'pe' object.

To read from memory:
```
pe.memory_read(0x40100000, 0x10)
```

To write to memory:
```
pe.memory_write(0x40100000, b'\xAA\xBB\xCC\xDD')
```

To call a function (up to 4 parameters) and receive 64-bit return value:
```
pe.call_function(0xD40, 0xAABBCCDD, 0x55555555)
```

To execute a flat binary:
```
pe.execute_shellcode('my_shellcode.bin')
```