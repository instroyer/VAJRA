# Linux Desktop Integration

This folder contains scripts to integrate VAJRA with your Linux desktop environment.

## Option A: Installation (Shortcut)
Use this if you just want a menu shortcut to run the tool from the source code.

1.  Open terminal in this folder.
2.  Run:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
3.  Launch "Vajra Security Platform" from your app menu.

---

## Option B: Build with PyInstaller
Creates a standalone executable (faster build, but easier to reverse-engineer).

```bash
chmod +x build_linux.sh
./build_linux.sh
```

---

## Option C: Build with Nuitka (Recommended for Protection)
Compiles Python to native C++ code (slower build, but **much harder to reverse-engineer**).

```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```

⚠️ First build will take **5-15 minutes** as Nuitka compiles everything to C++.

---

## Files

- **`vajra_launcher.sh`**: Helper script to launch from source.
- **`install.sh`**: Installs the .desktop shortcut.
- **`build_linux.sh`**: Builds executable using PyInstaller.
- **`build_nuitka.sh`**: Builds executable using Nuitka (better protection).
- **`hook-vajra.py`**: PyInstaller hook file.
