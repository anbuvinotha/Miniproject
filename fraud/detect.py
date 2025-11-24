from sklearn.ensemble import IsolationForest
import pandas as pd

def detect_duplicates(invoice_records):
    """
    Simple rule-based duplicate detection by same vendor, invoice_no, and amount.
    """
    df = pd.DataFrame(invoice_records)
    duplicates = df[df.duplicated(subset=['vendor', 'invoice_no', 'amount'], keep=False)]
    return duplicates

def detect_amount_anomalies(invoice_records, contamination=0.02):
    """
    IsolationForest anomaly detection on amounts.
    """
    df = pd.DataFrame(invoice_records)
    clf = IsolationForest(contamination=contamination)
    df['anomaly'] = clf.fit_predict(df[['amount']])
    anomalies = df[df['anomaly'] == -1]
    return anomalies
