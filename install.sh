#!/usr/bin/env bash
set -e

COMMAND_NAME="flow"
ENTRY_SCRIPT="main.py"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
INSTALL_DIR="$HOME/.local/bin"
WRAPPER_PATH="$INSTALL_DIR/$COMMAND_NAME"

echo "Setting up $COMMAND_NAME..."

if ! command -v python3 &> /dev/null; then
    echo "python3 is required but was not found. Install it and re-run this script."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

if [ -f "$REPO_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt" --quiet
fi

mkdir -p "$INSTALL_DIR"
cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$REPO_DIR/$ENTRY_SCRIPT" "\$@"
EOF
chmod +x "$WRAPPER_PATH"

echo "Installed: $WRAPPER_PATH"

case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        echo "Done. You can now run '$COMMAND_NAME' from anywhere."
        ;;
    *)
        echo ""
        echo "NOTE: $INSTALL_DIR is not on your PATH yet."
        echo "Add this line to your ~/.bashrc or ~/.zshrc, then restart your terminal:"
        echo ""
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        ;;
esac