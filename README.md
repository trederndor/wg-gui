# wg-gui

A lightweight web interface for managing **WireGuard** on Raspberry Pi.\
Easily configure, monitor, and control your VPN peers directly from your
browser.

------------------------------------------------------------------------

## Configuration

Before running the application, you need to update two variables at the
start of `wg_gui.py`:

``` python
app.secret_key = 'CHANGE_THIS_SECRET_KEY_FOR_PRODUCTION'  
WG_CONFIG_DIR = "/home/USER/configs"
```

### Details

#### app.secret_key

Replace with a strong, unique secret key for production.\
This key is used by Flask to secure sessions and must be kept private.

#### WG_CONFIG_DIR

Replace `USER` with the username used during the PiVPN/WireGuard
installation.\
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

## Requirements

-   Raspberry Pi with PiVPN/WireGuard installed.
-   Python 3.x
-   Flask
-   qrcode Python library

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

------------------------------------------------------------------------

## License

MIT License
