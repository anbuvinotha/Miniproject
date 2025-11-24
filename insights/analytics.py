import pandas as pd

def expense_trends(invoice_records):
    """
    Calculate monthly spending per vendor and category.
    
    invoice_records: list of dicts with keys: 'invoice_date', 'vendor', 'category', 'amount'
    Returns: pandas DataFrame grouped by month and vendor/category
    """
    df = pd.DataFrame(invoice_records)
    df['month'] = pd.to_datetime(df['invoice_date']).dt.to_period('M')
    
    trends = df.groupby(['month', 'vendor', 'category'])['amount'].sum().reset_index()
    return trends

def top_vendors(invoice_records, top_n=5):
    """
    Top vendors by expense amount.
    """
    df = pd.DataFrame(invoice_records)
    summary = df.groupby('vendor')['amount'].sum()
    return summary.sort_values(ascending=False).head(top_n)
