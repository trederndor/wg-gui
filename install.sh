#!/bin/bash
set -e

echo "=== 🛠 INSTALLAZIONE DIPENDENZE PER WG-GUI ==="

# Controlla Python 3
if ! command -v python3 &> /dev/null; then
    echo "⚠️ Python3 non trovato. Installazione in corso..."
    sudo apt update
    sudo apt install -y python3
else
    echo "✅ Python3 già installato"
fi

# Controlla pip3
if ! command -v pip3 &> /dev/null; then
    echo "⚠️ pip3 non trovato. Installazione in corso..."
    sudo apt install -y python3-pip
else
    echo "✅ pip3 già installato"
fi

# Aggiorna pip e installa le dipendenze Python dal requirements.txt usando --break-system-packages
echo "📦 Installazione dipendenze Python da requirements.txt"
pip3 install --break-system-packages --upgrade pip
pip3 install --break-system-packages -r requirements.txt

echo "✅ Installazione completata."
