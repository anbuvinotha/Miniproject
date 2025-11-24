from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import shutil, os
from db.db_utils import SessionLocal, engine
from db.models import Base, Vendor, Invoice
from ocr.invoice_ocr import ocr_image, ocr_pdf, extract_invoice_fields
from insights.analytics import expense_trends as expense_trends_func, top_vendors
from fraud.detect import detect_duplicates, detect_amount_anomalies
from forecast.prophet_model import run_prophet_forecast
from datetime import datetime

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart AI CFO API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # OCR
    if file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raw_text = ocr_image(file_path)
    elif file.filename.lower().endswith(".pdf"):
        raw_text = ocr_pdf(file_path)
    else:
        raise HTTPException(status_code=400, detail="Invalid file format")
    fields = extract_invoice_fields(raw_text)
    vendor_name = fields.get("vendor") or "Unknown Vendor"
    vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
    if not vendor:
        vendor = Vendor(name=vendor_name)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

    # Extract and convert date string to datetime.date
    raw_date = fields.get("invoice_date") or fields.get("date")
    date_obj = None
    if raw_date:
        try:
            # Adjust format as per your OCR output, here it's MM/DD/YYYY
            date_obj = datetime.strptime(raw_date, "%m/%d/%Y").date()
        except Exception as e:
            # If date parsing fails, optionally log error or default to None
            print(f"Date parsing error: {e}")
            date_obj = None

    invoice = Invoice(
        vendor_id=vendor.id,
        invoice_no=fields.get("invoice_no") or "N/A",
        invoice_date=date_obj,
        amount=fields.get("amount") or 0.0,
        currency=fields.get("currency") or "N/A",
        line_items=[],
        confidence=0.9,
        parsed_at=None
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    os.remove(file_path)
    return JSONResponse(
        content={
            "message": "Invoice uploaded and processed successfully",
            "invoice_id": invoice.id,
            "parsed_fields": fields
        }
    )

@app.get("/insights/expense-trends")
def expense_trends_endpoint(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    data = [{
        'invoice_date': inv.invoice_date,
        'vendor': inv.vendor.name if inv.vendor else 'Unknown',
        'category': 'General',
        'amount': inv.amount
    } for inv in invoices]
    trends = expense_trends_func(data)
    return trends.to_dict(orient='records')

@app.get("/fraud/detect-duplicates")
def detect_duplicates_endpoint(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    data = [{
        'vendor': inv.vendor.name if inv.vendor else 'Unknown',
        'invoice_no': inv.invoice_no,
        'amount': inv.amount
    } for inv in invoices]
    duplicates_df = detect_duplicates(data)
    return duplicates_df.to_dict(orient='records')

@app.get("/fraud/detect-anomalies")
def detect_anomalies_endpoint(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    data = [{'amount': inv.amount} for inv in invoices]
    anomalies_df = detect_amount_anomalies(data)
    return anomalies_df.to_dict(orient='records')

@app.get("/forecast")
def forecast_expenses(periods: int = 6, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    data = [{'invoice_date': inv.invoice_date, 'amount': inv.amount} for inv in invoices]
    forecast_df = run_prophet_forecast(data, periods)
    result = forecast_df.to_dict(orient='records')
    return JSONResponse(content=result)
