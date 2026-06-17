#!/usr/bin/env bash
set -e

COMMAND_NAME="flow"
ENTRY_SCRIPT="main.py"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
INSTALL_DIR="$HOME/.local/bin"
WRAPPER_PATH="$INSTALL_DIR/$COMMAND_NAME"

echo "Setting up $COMMAND_NAME..."

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Neither python3 nor python was found. Install Python and re-run this script."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

if [ -f "$REPO_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    if [ -f "$VENV_DIR/Scripts/python" ]; then
        VENV_PYTHON="$VENV_DIR/Scripts/python"
    elif [ -f "$VENV_DIR/Scripts/python.exe" ]; then
        VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
    else
        VENV_PYTHON="$VENV_DIR/bin/python"
    fi

    if ! "$VENV_PYTHON" -m pip --version &> /dev/null; then
        echo "pip not found in venv, bootstrapping..."
        "$VENV_PYTHON" -m ensurepip --upgrade --quiet
    fi

    "$VENV_PYTHON" -m pip install --upgrade pip --quiet
    "$VENV_PYTHON" -m pip install -r "$REPO_DIR/requirements.txt" --quiet
fi

mkdir -p "$INSTALL_DIR"
cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
if [ -f "$VENV_DIR/Scripts/python" ]; then
    PYTHON="$VENV_DIR/Scripts/python"
elif [ -f "$VENV_DIR/Scripts/python.exe" ]; then
    PYTHON="$VENV_DIR/Scripts/python.exe"
else
    PYTHON="$VENV_DIR/bin/python"
fi
if [ -z "\$PYTHON" ]; then
    echo "Error: No Python executable found in virtual environment at $VENV_DIR"
    exit 1
fi
exec "\$PYTHON" "$REPO_DIR/$ENTRY_SCRIPT" "\$@"
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