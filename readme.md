# Super Mario All-Stars Launcher for Super Mario World

This is a simple launcher for the Super Mario All-Stars branch of the Super Mario World port by snesrev. It allows you to easily run the game on your system. 

**Note: The releases and source code are updated in tandem. Please choose the option that suits you best, as both options provide the same functionality.**

## Prerequisites

Before using this launcher, make sure you have the following installed:

- Super Mario All-Stars ROM (smas.sfc)
- Super Mario World ROM (smw.sfc)

## Option 1: Using the Executable (Simpler and Cleaner)

Executable versions for Mac and Linux will be forthcoming.

1. Go to the "Releases" section of the repository.
2. Download the latest release.
3. Create a new folder and place the downloaded executable in it.
4. Copy the Super Mario All-Stars ROM (smas.sfc) and Super Mario World ROM (smw.sfc) into the same folder.
5. Run the executable file.
6. The launcher will launch the game, and you can start playing.

## Option 2: Using Python (Recommended for those familiar with Python)
(Please consult the section below on Installing Python)

[Python] has tentative support for Mac and Linux. 


*Note: During the installation of Python make sure to check the box that adds Python to PATH.*

1. Download the source code from the repository.
2. Create a new folder and place the downloaded source code in it.
3. Copy the Super Mario All-Stars ROM (smas.sfc) and Super Mario World ROM (smw.sfc) into the same folder.
4. On Windows run the "Install-Dependencies-for-Windows.bat" file to download the required Python packages.
4. On Mac or Linux run the "Install-Dependencies-for-Mac-and-Linux.sh" file to download the required Python packages.
5. After downloading the dependencies, run the "launcher.pyw" script on windows or "Run on Mac and Linux.sh" on Mac and Linux.
6. The launcher will install the needed backend and then launch the game, and you can start playing.

## Troubleshooting

If you encounter any issues while using the launcher, please refer to the repository's issue tracker for known problems and solutions. You can also report new issues to help improve the launcher.

## Disclaimer

Please note that the usage of ROMs may infringe on copyright laws. Make sure you own the original game cartridges or have obtained the ROMs legally before using this launcher.

## Contributions

Contributions to this project are welcome. If you have any improvements or suggestions, feel free to submit a pull request or open an issue on the repository.

## License

This launcher is released under the [MIT License](LICENSE). Please refer to the license file for more information.

## Installing Python

**installer**
[Installer] : (https://www.python.org/downloads/)

## Package Mangager Installations

### Windows (using winget)

1. Open the Command Prompt or PowerShell.
2. Check if `winget` is installed by running `winget --version`. If not, install it by following the instructions [here](https://docs.microsoft.com/en-us/windows/package-manager/winget/).
3. Run the following command to install Python using winget:
   ```shell
   winget install --id Python.Python
   ```
4. Follow the prompts to complete the installation.

### Windows (using Chocolatey)

1. Open the Command Prompt or PowerShell with administrative privileges.
2. Check if `Chocolatey` is installed by running `choco --version`. If not, install it by following the instructions [here](https://chocolatey.org/install).
3. Run the following command to install Python using Chocolatey:
   ```shell
   choco install python
   ```
4. Follow the prompts to complete the installation.

### Linux (using package managers)

#### Debian-based systems (e.g., Ubuntu)

1. Open the Terminal.
2. Update the package manager's repository information by running:
   ```shell
   sudo apt update
   ```
3. Install Python by running:
   ```shell
   sudo apt install python3
   ```

#### Red Hat-based systems (e.g., Fedora)

1. Open the Terminal.
2. Update the package manager's repository information by running:
   ```shell
   sudo dnf update
   ```
3. Install Python by running:
   ```shell
   sudo dnf install python3
   ```

#### Arch-based systems (e.g., EndeavorOS, SteamOS)

1. Open the Terminal.
2. Install Python by running:
   ```shell
   sudo pacman -Sy python
   ```

#### OpenSUSE-based systems

1. Open the Terminal.
2. Install Python by running:
   ```shell
   sudo zypper install python3
   ```

#### Alpine-based systems

1. Open the Terminal.
2. Install Python by running:
   ```shell
   sudo apk add python3
   ```

### macOS (using Homebrew or MacPorts)

#### Homebrew

1. Open the Terminal.
2. Install Homebrew if you haven't already by running the following command:
   ```shell
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install Python by running:
   ```shell
   brew install python
   ```

#### MacPorts

1. Open the Terminal.
2. Install MacPorts if you haven't already by following the instructions [here](https://www.macports.org/install.php).
3. Update MacPorts by running:
   ```shell
   sudo port selfupdate
   ```
4. Install Python by running:
   ```shell
   sudo port install python39
   ```

## Verify Installation

To verify that Python is installed correctly, open a new terminal or command prompt and run the following command:

```shell
python --version
```

You should see the installed Python version printed on the screen.
```
