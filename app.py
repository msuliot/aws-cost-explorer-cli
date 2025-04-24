import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
import json
import sys
import argparse

console = Console()

def get_cost_data(start_date, end_date):
    """
    Get cost data from AWS Cost Explorer for the specified date range
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching AWS cost data...", total=None)
        
        ce = boto3.client('ce')
        
        try:
            # Get costs by service
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )
            
            # Process and format the results
            costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                for group in result['Groups']:
                    service = group['Keys'][0]
                    usage_type = group['Keys'][1] if len(group['Keys']) > 1 else 'N/A'
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:  # Only include non-zero costs
                        costs.append({
                            'Date': date,
                            'Service': service,
                            'UsageType': usage_type,
                            'Cost': cost
                        })
            
            progress.update(task, completed=True)
            return costs
        
        except ClientError as e:
            console.print(f"[red]Error getting cost data: {e}[/red]")
            return []

def process_cost_data(costs_df):
    """
    Process the cost data and return structured information
    """
    # Remove rows with zero or very small costs (less than 1 cent)
    df = costs_df[costs_df['Cost'] > 0.01]
    
    # Group by service and calculate total cost, filter out zero costs
    service_costs = df.groupby('Service')['Cost'].sum()
    service_costs = service_costs[service_costs > 0.01].sort_values(ascending=False)
    
    total_cost = service_costs.sum()
    
    # Create structured data
    result = {
        'totalCost': float(total_cost),
        'services': [],
        'dailyCosts': []
    }
    
    # Process services and their usage types
    for service, cost in service_costs.items():
        if cost > 0.01:
            service_usage = df[df['Service'] == service].groupby('UsageType')['Cost'].sum()
            service_usage = service_usage[service_usage > 0.01].sort_values(ascending=False)
            
            service_data = {
                'name': service,
                'cost': float(cost),
                'percentage': float((cost/total_cost*100)),
                'usageTypes': [
                    {
                        'name': usage_type,
                        'cost': float(usage_cost)
                    }
                    for usage_type, usage_cost in service_usage.items()
                    if usage_cost > 0.01
                ]
            }
            result['services'].append(service_data)
    
    # Process daily costs
    daily_costs = df.groupby(['Date', 'Service'])['Cost'].sum().reset_index()
    for date in sorted(daily_costs['Date'].unique()):
        day_data = {
            'date': date,
            'services': [
                {
                    'name': row['Service'],
                    'cost': float(row['Cost'])
                }
                for _, row in daily_costs[daily_costs['Date'] == date].iterrows()
                if row['Cost'] > 0.01
            ]
        }
        result['dailyCosts'].append(day_data)
    
    return result

def main():
    parser = argparse.ArgumentParser(description='AWS Cost Explorer Analysis')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    args = parser.parse_args()

    # Get cost data for the specified number of days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    if not args.json:
        console.print(Panel.fit(
            f"[bold cyan]AWS Cost Analysis[/bold cyan]\n[yellow]Period: {start_date} to {end_date}[/yellow]",
            box=box.ROUNDED,
            title="AWS Cost Explorer",
            border_style="blue"
        ))
    
    costs = get_cost_data(start_date, end_date)
    
    if not costs:
        if args.json:
            print(json.dumps({'error': 'No cost data found'}))
        else:
            console.print("[red]No cost data found or error occurred.[/red]")
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(costs)
    
    if args.json:
        # Return JSON format
        result = process_cost_data(df)
        print(json.dumps(result))
        return
    
    # Remove rows with zero or very small costs (less than 1 cent)
    df = df[df['Cost'] > 0.01]
    
    # Group by service and calculate total cost, filter out zero costs
    service_costs = df.groupby('Service')['Cost'].sum()
    service_costs = service_costs[service_costs > 0.01].sort_values(ascending=False)
    
    total_cost = service_costs.sum()
    
    # Create main services table
    services_table = Table(
        title="Services Overview",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    services_table.add_column("Service", style="cyan")
    services_table.add_column("Cost", justify="right", style="green")
    services_table.add_column("% of Total", justify="right", style="yellow")
    
    # Add all services with cost > $0.01
    for service, cost in service_costs.items():
        if cost > 0.01:  # Only show services with cost > 1 cent
            percentage = (cost/total_cost*100)
            services_table.add_row(
                service,
                f"${cost:,.2f}",
                f"{percentage:.1f}%"
            )
    
    # Add total row with bold formatting
    services_table.add_row(
        "[bold]Total[/bold]",
        f"[bold]${total_cost:,.2f}[/bold]",
        "[bold]100.0%[/bold]"
    )
    
    console.print(services_table)
    console.print()
    
    # Create detailed breakdown for each service
    console.print(Panel.fit(
        "[bold cyan]Detailed Cost Breakdown by Service[/bold cyan]", 
        box=box.ROUNDED,
        border_style="blue"
    ))
    
    for service, cost in service_costs.items():
        if cost > 0.01:
            service_df = df[df['Service'] == service]
            usage_costs = service_df.groupby('UsageType')['Cost'].sum().sort_values(ascending=False)
            
            usage_table = Table(
                title=f"{service} Usage Types",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            usage_table.add_column("Usage Type", style="cyan")
            usage_table.add_column("Cost", justify="right", style="green")
            usage_table.add_column("% of Service", justify="right", style="yellow")
            
            for usage_type, usage_cost in usage_costs.items():
                if usage_cost > 0.01:
                    percentage = (usage_cost/cost*100)
                    usage_table.add_row(
                        usage_type,
                        f"${usage_cost:,.2f}",
                        f"{percentage:.1f}%"
                    )
            
            console.print(usage_table)
            console.print()

if __name__ == "__main__":
    main()