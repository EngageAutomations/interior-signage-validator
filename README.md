# Interior Signage Validator

A FastAPI service that validates and normalizes interior signage design specifications with automatic font size calculation.

## Features

- **Specification Validation**: Validates required fields and data types
- **Constraint Enforcement**: Ensures thickness ≥ 2mm, bevel ≤ half thickness
- **Font Size Calculation**: Automatically calculates maximum font size using Matplotlib
- **Normalization**: Converts string numbers to floats, applies defaults
- **RESTful API**: Clean JSON responses with detailed error messages
- **Type Safety**: Full Pydantic model validation

## Project Structure

```
interior_signage/
├── __init__.py              # Package initialization
├── validator.py             # Core validation logic
└── autosize_service.py      # FastAPI service
test_validator.py            # Validator unit tests
test_autosize_service.py     # API endpoint tests
requirements.txt             # Dependencies
README.md                   # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd interior-signage-validator
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally

1. **Start the FastAPI server**:
   ```bash
   uvicorn interior_signage.autosize_service:app --reload
   ```

2. **Access the API**:
   - **Service**: http://localhost:8000
   - **Interactive Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST /validate

Validates and normalizes a signage design specification.

**Request Body**:
```json
{
  "text": "CEO Office",
  "font": "Montserrat",
  "plate": {
    "width_mm": "200",
    "height_mm": "80", 
    "thickness_mm": "3"
  },
  "bevel_mm": "0.5",
  "material": "brushed_metal",
  "finish": "satin",
  "color": "silver",
  "stand": "none",
  "text_style": "raised"
}
```

**Success Response** (200):
```json
{
  "ok": true,
  "design_spec": {
    "text": "CEO Office",
    "font": "Montserrat",
    "plate": {
      "width_mm": 200.0,
      "height_mm": 80.0,
      "thickness_mm": 3.0
    },
    "bevel_mm": 0.5,
    "material": "brushed_metal",
    "finish": "satin",
    "color": "silver",
    "stand": "none",
    "text_style": "raised",
    "font_size_pt": 24.5
  },
  "needs": []
}
```

**Error Response** (200):
```json
{
  "ok": false,
  "issues": [
    "Thickness must be ≥ 2 mm",
    "Bevel must be ≤ half the thickness"
  ]
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "interior-signage-validator"
}
```

### GET /

API information and available endpoints.

## Testing

**Run all tests**:
```bash
pytest
```

**Run with coverage**:
```bash
pytest --cov=interior_signage
```

**Run specific test file**:
```bash
pytest test_validator.py -v
```

## Deployment to Railway

### Method 1: Using Railway CLI with Token

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Set Railway Token** (use your own token):
   ```bash
   # Windows PowerShell
   $env:RAILWAY_TOKEN="your-railway-token-here"
   
   # Linux/Mac
   export RAILWAY_TOKEN="your-railway-token-here"
   ```

3. **Deploy directly**:
   ```bash
   railway up
   ```

### Method 2: GitHub Integration (Recommended)

1. **Push code to GitHub repository**
2. **Connect to Railway**:
   - Go to [railway.app](https://railway.app)
   - Login with your Railway account
   - Create new project from GitHub repository
   - Railway will automatically detect the FastAPI app and deploy

3. **Configuration files included**:
   - `railway.json` - Railway project configuration
   - `Procfile` - Process definition for web service
   - `.gitignore` - Prevents sensitive files from being committed

### Railway Configuration

The service is configured to:
- **Auto-detect**: Railway automatically detects FastAPI applications
- **Port binding**: Uses Railway's `$PORT` environment variable
- **Health checks**: Built-in `/health` endpoint for monitoring
- **Logs**: Structured logging for debugging

## Validation Rules

### Required Fields
- `text`: Non-empty string (max 100 characters)
- `font`: Valid font name (alphanumeric, spaces, hyphens, underscores)
- `plate`: Object with `width_mm`, `height_mm`, `thickness_mm`

### Constraints
- **Thickness**: Must be ≥ 2mm
- **Bevel**: Must be ≤ half the thickness
- **Dimensions**: All must be > 0
- **Text fitting**: Must fit within plate with 5mm margins

### Valid Options
- **Materials**: brushed_metal, acrylic, wood, plastic, glass, aluminum
- **Finishes**: satin, matte, gloss, brushed, polished, textured
- **Colors**: silver, gold, black, white, bronze, copper, clear
- **Stands**: none, desktop, wall_mount, floor_stand, magnetic
- **Text Styles**: raised, engraved, printed, etched, embossed

### Default Values
- **Material**: brushed_metal
- **Finish**: satin
- **Color**: silver
- **Stand**: none
- **Text Style**: raised
- **Bevel**: 0.5mm

## Development

### Code Style
- **PEP 8**: Python code style guide
- **Type Hints**: Full type annotations
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Graceful error responses

### Dependencies
- **FastAPI**: Modern web framework
- **Pydantic**: Data validation and serialization
- **Matplotlib**: Font size calculations
- **Pytest**: Testing framework

## Security Considerations

### Important Security Notes
- **Never commit tokens or API keys** to version control
- **Use environment variables** for sensitive configuration
- **Railway tokens should be kept private** and rotated regularly
- **Review .gitignore** to ensure no sensitive files are tracked

### Safe Deployment Practices
1. **Use Railway's web interface** for connecting GitHub repositories
2. **Set environment variables** through Railway's dashboard, not in code
3. **Enable Railway's built-in security features** like automatic HTTPS
4. **Monitor deployment logs** for any exposed sensitive information

## Troubleshooting

### Common Issues

1. **Font not found**: Ensure font name is correct and available
2. **Text too large**: Reduce text length or increase plate dimensions
3. **Validation errors**: Check required fields and data types
4. **Import errors**: Verify all dependencies are installed

### Debug Mode

Run with debug logging:
```bash
uvicorn interior_signage.autosize_service:app --reload --log-level debug
```

### Health Check

Verify service is running:
```bash
curl http://localhost:8000/health
```

## License

This project is licensed under the MIT License.