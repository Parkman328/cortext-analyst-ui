# Cortex Analyst UI

A beautiful FastAPI-based web interface for processing questions through Snowflake Cortex Analyst API.

![Cortex Analyst UI](screenshot.png)

## Features

- 🎨 **Beautiful Modern UI** - Clean, responsive interface built with Tailwind CSS
- 📤 **CSV Upload** - Drag & drop or browse to upload question files
- 📊 **Real-time Progress** - Live status updates during processing
- 📥 **Multiple Export Formats** - Download results as JSON or CSV
- 🔄 **Job Management** - Track and manage multiple processing jobs
- ⚡ **Error Handling** - Comprehensive error tracking including error 392708
- 🔒 **Secure** - Credentials never stored, session-based only

## Prerequisites

- Python 3.8 or higher
- Snowflake account with Cortex Analyst access
- macOS, Linux, or Windows

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cortex-analyst-ui.git
cd cortex-analyst-ui
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open Browser

Navigate to: http://localhost:8000

## Usage

### Step 1: Configure Snowflake Connection

1. Fill in your Snowflake credentials:
   - Account (e.g., `abc123.us-east-1`)
   - Username
   - Password
   - Warehouse
   - Database (default: `CORTEX_ANALYST_DEMO`)
   - Schema (default: `OMNICHEM`)
   - Semantic Model Path

2. Click "Configure Connection"
3. Wait for the green "Connected" status

### Step 2: Prepare Your CSV

Your CSV file should have two columns:

```csv
Id,Question
1,What is the total sales for 2023?
2,Which region had the highest revenue?
3,Show me top 10 products by units sold
```

### Step 3: Upload and Process

1. Drag & drop your CSV file or click "Browse Files"
2. Click "Start Processing"
3. Watch real-time progress updates
4. Download results as JSON or CSV when complete

## CSV Format

The input CSV must have these columns:

- `Id` - Unique identifier for each question
- `Question` - The question text to process

Example:

```csv
Id,Question
101,"What is the total net sales in global currency for 2023?"
102,"Which customer region generated the highest gross sales?"
103,"Show me products with flammable elements"
```

## Output Format

### JSON Output

```json
[
  {
    "question_id": 101,
    "question": "What is the total net sales...",
    "interpretation": "This is our interpretation...",
    "sql": "SELECT SUM(net_sales_gc)...",
    "query_results": "[{\"total\": 1234567}]",
    "api_duration_ms": 8234,
    "sql_duration_ms": 145,
    "status": "success"
  }
]
```

### CSV Output

| question_id | question | interpretation | sql | query_results | status |
|-------------|----------|----------------|-----|---------------|--------|
| 101 | What is... | This is... | SELECT... | [{...}] | success |

## API Endpoints

### Configure Connection
```http
POST /api/configure
Content-Type: application/json

{
  "account": "abc123.us-east-1",
  "user": "username",
  "password": "password",
  "warehouse": "COMPUTE_WH",
  "database": "CORTEX_ANALYST_DEMO",
  "schema": "OMNICHEM",
  "semantic_model": "@.../model.yaml"
}
```

### Upload CSV
```http
POST /api/upload
Content-Type: multipart/form-data

file: questions.csv
```

### Check Status
```http
GET /api/status/{job_id}
```

### Download Results
```http
GET /api/results/{job_id}/json
GET /api/results/{job_id}/csv
```

### List Jobs
```http
GET /api/jobs
```

## Configuration

### Environment Variables

You can use a `.env` file for default configuration:

```env
SNOWFLAKE_ACCOUNT=abc123.us-east-1
SNOWFLAKE_USER=your_user
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=CORTEX_ANALYST_DEMO
SNOWFLAKE_SCHEMA=OMNICHEM
SEMANTIC_MODEL=@CORTEX_ANALYST_DEMO.OMNICHEM.RAW_DATA/OMNICHEM_V2_1_ENHANCED.yaml
```

### Processing Settings

Edit `cortex_processor.py` to adjust:

```python
self.api_timeout = 600000  # 10 minutes
self.max_retries = 3
self.delay_between_requests = 5  # seconds
```

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Snowflake"

**Solutions**:
- Verify your account identifier format: `account_name.region`
- Check username and password
- Ensure warehouse is running
- Verify network access to Snowflake

### Error 392708

**Problem**: Questions failing with error 392708

**Solutions**:
- Upload the enhanced semantic model (see `OMNICHEM_V2_1_ENHANCED.yaml`)
- Simplify question text
- Check semantic model path is correct
- Review error logs for specific issues

### CSV Upload Errors

**Problem**: "CSV must have 'Id' and 'Question' columns"

**Solution**: Ensure your CSV has exactly these column names (case-insensitive)

### Memory Issues

**Problem**: Application crashes with large CSV files

**Solution**: Process files in batches. Split large CSV into smaller files.

## Development

### Project Structure

```
cortex-analyst-ui/
├── main.py                 # FastAPI application
├── cortex_processor.py     # Core processing logic
├── requirements.txt        # Python dependencies
├── static/
│   └── index.html         # Frontend UI
├── uploads/               # Uploaded CSV files
├── outputs/               # Generated results
└── README.md
```

### Running Tests

```bash
pytest tests/
```

### Building for Production

```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t cortex-analyst-ui .
docker run -p 8000:8000 cortex-analyst-ui
```

### Deploy to Cloud

#### Heroku

```bash
heroku create cortex-analyst-ui
git push heroku main
```

#### AWS EC2

1. Launch EC2 instance
2. Install Python and dependencies
3. Run with gunicorn behind nginx

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting guide above

## Acknowledgments

- Built with FastAPI
- UI styled with Tailwind CSS
- Powered by Snowflake Cortex Analyst

## Changelog

### v1.0.0 (2024-12-05)
- Initial release
- CSV upload and processing
- Real-time progress tracking
- JSON and CSV export
- Job management
- Error handling for 392708

---

Made with ❤️ for Snowflake Cortex Analyst users
