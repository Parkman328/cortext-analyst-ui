#!/bin/bash

# Cortex Analyst UI - Setup Script
# This script sets up the application on macOS/Linux

echo "🚀 Cortex Analyst UI - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs static
touch uploads/.gitkeep outputs/.gitkeep
echo "✅ Directories created"
echo ""

# Create .env template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOF
# Snowflake Configuration (Optional - can be set via UI)
# SNOWFLAKE_ACCOUNT=your_account.region
# SNOWFLAKE_USER=your_user
# SNOWFLAKE_PASSWORD=your_password
# SNOWFLAKE_WAREHOUSE=COMPUTE_WH
# SNOWFLAKE_DATABASE=CORTEX_ANALYST_DEMO
# SNOWFLAKE_SCHEMA=OMNICHEM
# SEMANTIC_MODEL=@CORTEX_ANALYST_DEMO.OMNICHEM.RAW_DATA/OMNICHEM_V2_1_ENHANCED.yaml
EOF
    echo "✅ .env template created"
else
    echo "⚠️  .env file already exists. Skipping..."
fi
echo ""

# Setup complete
echo "======================================"
echo "✨ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the app: python main.py"
echo "3. Open browser: http://localhost:8000"
echo ""
echo "Or use this one-liner:"
echo "  source venv/bin/activate && python main.py"
echo ""
echo "Need help? Check README.md or open an issue on GitHub"
echo "======================================"
