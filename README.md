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

We will use [ServeRWX](https://github.com/VL4DR/server/tree/basic-server-functionality) to upgrade our read/write primitive to actual code execution.
For convenience, precompiled server binaries are provided for each firmware version in their respective directories.
If you would like to build it yourself, visit the [ServerWX](https://github.com/VL4DR/server/tree/basic-server-functionality) repository and follow the instructions. Then, put the resulting binary in `resources/your_firmware_version` directory. Make sure your server binary is consistent with how the executor sends and receives commands over NVMe.

## Supported Versions
The SSDs and firmwares we have tested (and are thus currently the only ones supported by the executor):
- PNY CS3030 (Phison E12; ECFM32.2)
- MSI Spatium M470 (Phison E16; EGFM13.2)
- Kingston KC3000 (Phison E18; EIFK51.2)
- Sabrent Rocket 4 Plus (Phison E18; EIFM80.0)

This was also tested successfully on a Crucial P2 drive (Phison E13T), but exploitation there is completely different since that drive's FW code significantly differs from the aforementioned drives, so it will not be included in this repository.

Code execution can surely be achieved on many other Phison-based SSDs, but only what we have managed to test and verify successfully is included here.

## Usage
PhisonExecutor can be run on Windows and Linux machines (Windows 10 and Ubuntu 24.04 were tested). Python3 >3.5 should be used for executing the script. Please also note the requirements.txt file that should be used to install dependencies.

Execute as admin/root:
```
sudo -E python3 phison_shell.py /dev/nvmeX (Linux)
py phison_shell.py \\.\PhysicalDriveX (Windows, as Admin)

usage: phison_shell.py [-h] device

positional arguments:
  device      the path to the Phison NVMe device

options:
  -h, --help  show this help message and exit
```

Upon executing the script, an IPython shell will spawn, after which the executor's functionality can be accessed via the 'pe' object.

To read from memory:
```
pe.memory_read(0x40100000, 0x10)
```

To write to memory:
```
pe.memory_write(0x40100000, b'\xAA\xBB\xCC\xDD')
```

To call a function (up to 4 parameters) and receive the 64-bit return value:
```
pe.call_function(0xD40, 0xAABBCCDD, 0x55555555)
```

To execute a flat binary:
```
pe.execute_shellcode('my_shellcode.bin')
```

## FAQ
### If admin/root privileges are needed, then why bother discussing any of the vulnerabilities mentioned here? Don't you have full control over the drive anyway?
It depends on the end goal of a potential attacker. If all they want is full read/write access to your drive's storage, then being inside your PC is already sufficient. However, what if that attacker wants to take this a few steps further? If a drive's FW is digitally signed, then arbitrary code execution can enable an attacker to bypass the firmware's signature verification, potentially enabling the attacker inserting a malicious payload into the drive's firmware. Once inside, such payload is hidden very well, survives drive formats and can even make sure to survive controller firmware updates. What such payload could actually do is beyond the scope of this document, so it won't be discussed.

### That sounds serious! Should I worry about this, then?
It is likely that the answer would be a big NO. The amount of R&D needed to actually perform such attack is very high, and would (VERY likely) be possible by very serious threat actors. Unless you're wanted by governments, it is extremely unlikely for this to affect you in any way.

## Notes
If you have identified inaccuracies or mistakes in the description or that you are having trouble running the script, you can reach me at log1kxd at gmail.com.
