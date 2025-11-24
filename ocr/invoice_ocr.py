from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
import re
from dateutil import parser as dateparser
from datetime import date

def ocr_image(path):
    img = Image.open(path).convert('L')  # grayscale
    text = pytesseract.image_to_string(img, lang='eng')
    return text

def ocr_pdf(path):
    pages = convert_from_path(path, dpi=300)
    all_text = "\n".join([pytesseract.image_to_string(pg) for pg in pages])
    return all_text

def extract_invoice_fields(text):
    # Invoice number
    invoice_id_match = re.search(r'(Invoice\s*No|Inv\.?|Invoice)\s*[:\-]?\s*([A-Z0-9\-\/]+)', text, re.I)
    invoice_no = invoice_id_match.group(2).strip() if invoice_id_match else None

    # Amount
    amount_match = re.search(r'(Total(?:\s*Due)?|Grand Total|Amount Due)\s*[:\-]?\s*([₹$£]?\s*[\d,]+(?:\.\d{1,2})?)', text, re.I)
    amount_raw = amount_match.group(2) if amount_match else None
    try:
        amount = float(re.sub(r'[^\d.]', '', amount_raw)) if amount_raw else None
    except:
        amount = None

    # Currency
    currency_match = re.search(r'(INR|USD|EUR|GBP|₹|\$|£)', text)
    currency_raw = currency_match.group(0).upper() if currency_match else None
    if currency_raw:
        currency = currency_raw.replace('₹', 'INR').replace('$', 'USD').replace('£', 'GBP')
    else:
        currency = None

    # Date
    date_candidates = re.findall(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})\b', text)
    date_ = None
    for d in date_candidates:
        try:
            date_ = dateparser.parse(d, fuzzy=True).date().isoformat()
            break
        except:
            continue
    # Optional: fallback to today's date if nothing found (remove if you want None)
    # if not date_:
    #     date_ = date.today().isoformat()

    # Vendor
    vendor_match = re.search(r'(Seller|Vendor|Company)[\s\:]*([\w\s\.,&;\-]+)', text, re.I)
    if vendor_match:
        vendor = vendor_match.group(2).strip()
    else:
        vendor = text.strip().split('\n')[0][:50]

    return {
        "invoice_no": invoice_no,
        "amount": amount,
        "currency": currency,
        "date": date_,
        "vendor": vendor
    }
