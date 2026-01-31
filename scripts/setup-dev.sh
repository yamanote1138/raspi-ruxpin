#!/bin/bash
# Development setup script for Raspi Ruxpin 2.0
# Uses uv for fast Python dependency management

set -e

echo "🐻 Raspi Ruxpin 2.0 - Development Setup"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo ""
    echo "Install uv with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  or"
    echo "  brew install uv"
    echo ""
    exit 1
fi

echo "✓ Found uv $(uv --version)"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    USE_MOCK="true"
else
    PLATFORM="Linux"
    USE_MOCK="false"
fi

echo "Platform: $PLATFORM"
echo ""

# Create virtual environment with uv
if [ -d ".venv" ]; then
    echo "✓ Found existing virtual environment"
else
    echo "Creating virtual environment with uv..."
    uv venv
    echo "✓ Created .venv"
fi
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env

    # Set mock GPIO for macOS
    if [ "$PLATFORM" == "macOS" ]; then
        echo "" >> .env
        echo "# Mac Development Override" >> .env
        echo "HARDWARE__USE_MOCK_GPIO=true" >> .env
    fi

    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi
echo ""

# Install Python dependencies with uv
echo "Installing Python dependencies with uv..."
if [ "$PLATFORM" == "macOS" ]; then
    uv pip install -e ".[dev,mock]"
else
    uv pip install -e ".[dev,hardware]"
fi
echo "✓ Python dependencies installed"
echo ""

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✓ Frontend dependencies installed"
echo ""

# Create TTS output directory
mkdir -p sounds/tts
echo "✓ Created TTS output directory"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    uv run python -m backend.main"
echo "    # or: source .venv/bin/activate && python -m backend.main"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend && npm run dev"
echo ""
echo "  Then open: http://localhost:5173"
echo ""
