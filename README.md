# wg-gui

A lightweight web interface for managing **WireGuard** on Raspberry Pi.\
Easily configure, monitor, and control your VPN peers directly from your
browser.

------------------------------------------------------------------------

## Requirements

-   Raspberry Pi with PiVPN/WireGuard installed.  < -- This is a MUST have
-   Python 3.x
-   Flask
-   qrcode Python library


-----------------------------------------------------------------------
## Quick Installation

```bash
curl -sSL https://raw.githubusercontent.com/trederndor/wg-gui/refs/heads/main/fastinstall.sh | bash
```
## Manual Installation
```bash
git clone https://github.com/trederndor/wg-gui.git ~/wg_gui
cd ~/wg_gui
chmod +x ./install.sh
sudo ./install.sh
python wg_gui.py
```
## Configuration

Before running the application, you need to update two variables at the
start of `wg_gui.py`:

``` python
app.secret_key = 'CHANGE_THIS_SECRET_KEY_FOR_PRODUCTION'  #if u want
WG_CONFIG_DIR = "/home/USER/configs" #only if the user is not correctly detected
```

### Details

#### app.secret_key

Replace with a strong, unique secret key for production.\
This key is used by Flask to secure sessions and must be kept private.

#### WG_CONFIG_DIR

Replace `USER` with the username used during the PiVPN/WireGuard
installation, if not correctly detected.\
Examples:

    /home/marco/configs
    /home/john/configs

------------------------------------------------------------------------

## Features

-   Web-based management of WireGuard clients.
-   Create, edit, download, and delete client configurations.
-   Generate QR codes for mobile client setup.
-   Real-time status monitoring of clients.
-   Restart the WireGuard service from the interface.



------------------------------------------------------------------------

## Security Notice

This tool does **not** implement authentication by default.\
If exposed to the internet, **anyone** could access and manage your VPN.

It is strongly recommended to:

-   Run it only on trusted networks.
-   Protect it with authentication or reverse proxy security (e.g.,
    Nginx + HTTP Auth).
-   Keep your `WG_CONFIG_DIR` private, as it contains your client
    private keys.
<img width="1902" height="911" alt="image" src="https://github.com/user-attachments/assets/5142a703-7fff-43ba-a5e9-5fb8e78a46da" />

------------------------------------------------------------------------

## License

MIT License

This project is distributed under the Creative Commons BY-NC 4.0 license for non-commercial use.

➡️ Commercial use is prohibited without authorization or a paid license.
