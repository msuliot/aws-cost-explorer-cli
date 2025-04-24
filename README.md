# AWS Cost Explorer CLI

A command-line tool for analyzing AWS costs using the AWS Cost Explorer API. This tool provides detailed cost breakdowns by service and usage type, with beautiful console output or JSON format options.

## Features

- 📊 Beautiful rich console output with formatted tables
- 💰 Detailed cost breakdown by AWS service and usage type
- 📈 Percentage-based analysis of costs
- 🔄 JSON output option for programmatic use
- ⏱️ Customizable time period for analysis
- 🔍 Filters out negligible costs (less than $0.01)

## Prerequisites

- Python 3.7 or higher
- AWS credentials configured (via AWS CLI or environment variables)
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd aws-cost-explorer-cli
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the tool with default settings (last 30 days):
```bash
python app.py
```

### Command-line Options

- `--json`: Output data in JSON format
- `--days <number>`: Specify the number of days to analyze (default: 30)

### Examples

1. View costs for the last 30 days with rich console output:
   ```bash
   python app.py
   ```

2. Get JSON output for the last 7 days:
   ```bash
   python app.py --json --days 7
   ```

3. Analyze the last 90 days:
   ```bash
   python app.py --days 90
   ```

## Output Format

### Console Output

The console output includes:
- A summary panel showing the analysis period
- A services overview table with total costs and percentages
- Detailed breakdown tables for each service showing usage types and costs

### JSON Output

When using the `--json` flag, the output is a structured JSON object containing:
- Total cost
- List of services with their costs and percentages
- Daily cost breakdowns
- Usage type details for each service

## Dependencies

- boto3>=1.26.0: AWS SDK for Python
- pandas>=2.0.0: Data manipulation and analysis
- rich>=13.7.0: Beautiful terminal formatting

## AWS Permissions

This tool requires the following AWS permissions:
- `ce:GetCostAndUsage`

Make sure your AWS credentials have the necessary permissions to access the Cost Explorer API.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

[Your chosen license]
