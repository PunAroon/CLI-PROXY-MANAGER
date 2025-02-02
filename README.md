Proxy Management Script

This Python script provides a command-line interface (CLI) for managing proxy configurations. The script allows you to:

Add new proxies
Edit existing proxies
Delete proxies
Paste proxies in bulk
Sort proxies by ID, Name, or Type
Test if proxies are active
Import/export proxy configurations
Display proxies with user-friendly navigation
It uses the curses library to provide a text-based interface for interacting with proxies, making it suitable for terminal-based environments.

Features

Add New Proxy: Easily add a new proxy through a simple form.
Edit Proxy: Modify the configuration of existing proxies.
Delete Proxy: Delete a selected proxy (with a confirmation prompt).
Paste Proxies: Paste multiple proxies at once (one per line, in the format hostname:port@username:password).
Sort Proxies: Sort proxies by ID, Name, or Type for easier management.
Test Proxies: Test if a selected proxy is reachable and functional.
Import/Export Proxies: Import proxies from a file and export the current list of proxies to a file.
ASCII Art: Displays a fun ASCII banner upon launching the script.
Requirements

Python 3.x
requests library (for testing proxies)
curses library (usually comes with Python by default in Unix-based systems)
You can install the requests library by running:

pip install requests
How to Use

1. Run the Script
To run the script, navigate to the folder where the script is located and run:

python proxy_manager.py
2. Navigation
Use the Up and Down arrow keys to navigate through the list of proxies.
Press Enter to toggle the active state of the selected proxy.
Press A to add a new proxy.
Press E to edit the selected proxy.
Press D to delete the selected proxy (confirmation required).
Press P to paste a list of proxies (one per line, in hostname:port@username:password format).
Press S to sort proxies by ID, Name, or Type.
Press T to test the selected proxy's connectivity.
Press X to export proxies to a file.
Press I to import proxies from a file.
Press Q to quit the application.
3. Proxy Format
The proxy format used for adding and pasting proxies is:

hostname:port@username:password
Example:

proxy.example.com:8080@user:password
4. Example of Proxy File
When the script runs, it uses a proxies.json file to store the proxy configurations. Here is an example format of the proxies.json file:

[
  {
    "id": 1,
    "name": "Proxy 1",
    "server": "proxy.example.com",
    "port": 8080,
    "type": "HTTP",
    "active": true,
    "user": "user",
    "password": "password"
  },
  {
    "id": 2,
    "name": "Proxy 2",
    "server": "proxy2.example.com",
    "port": 1080,
    "type": "SOCKS5",
    "active": false,
    "user": "user2",
    "password": "password2"
  }
]
Key Files

proxy_manager.py: The main script file for proxy management.
proxies.json: The JSON file where proxy configurations are saved.
proxies_export.json: The file used to import/export proxies.
License

This script is open source and available for modification. Use it as per your needs, and feel free to contribute improvements!

Troubleshooting

Terminal too small: If you get a "Terminal too small" error, ensure your terminal window is large enough to handle the interface (at least 80x30).
Proxies not saved: If proxies are not saving, ensure that you have write permissions in the directory where the proxies.json file is stored.
