Installation
------------
Run the install script in a terminal as below and follow the prompts to continue 
(Use sudo to install in non-user directory).

```sh
./RasCAL-2-installer.run
```

To install without interactive prompts, pass the following parameters:
- `--accept` - Accept the license agreement
- `--install-dir PATH` - Location to install RasCAL-2 (e.g. /opt/RasCAL-2)
- `--install-examples` - Install example projects
- `--matlab PATH` - Matlab location (e.g. /usr/local/MATLAB/R2023a)

For example:
```sh
~/RasCAL-2-installer.run -- --accept --install-dir /opt/RasCAL-2 --install-examples --matlab /usr/local/MATLAB/R2023a
```
Omitting these parameters will cause the installer to ask for input.

After the installer is completed, run the application by typing the following:

```sh
rascal
```

Known Issues
-----------
When running on an old machine, you may run into the problem were Matlab needs a newer version of libstdc++ than the
one on the machine. This can be addressed by preloading the libstdc++ version needed by Matlab when you start RasCAL as
shown below (replace the path to matlab as appropriate)

```sh
LD_PRELOAD=/usr/local/MATLAB/R2024b/sys/os/glnxa64/libstdc++.so.6 rascal
```

Uninstall RasCAL 2
------------------
To uninstall the RasCAL package, simply delete the installation folder, desktop entry and symbolic link.
If the software is installed with the default paths, for a "sudo" install, the symbolic link and desktop
entry will be installed in "/usr/local/bin/RasCAL-2" and "/usr/share/applications/RasCAL-2.desktop" respectively
otherwise they would be in "$HOME/.local/bin/RasCAL-2" and "$HOME/.local/share/applications/RasCAL-2.desktop".
