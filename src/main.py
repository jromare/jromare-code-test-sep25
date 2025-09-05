from flask import Flask, request

from src.ingestion.PdfReportFetcher import PdfReportFetcher
from src.ingestion.SecEdgarCrawler import SecEdgarCrawler
from src.ingestion.ReportReporter import ReportReporter

app = Flask(__name__)

secEdgarCrawler = SecEdgarCrawler()
pdfReportFetcher = PdfReportFetcher()
reportReporter = ReportReporter(secEdgarCrawler, pdfReportFetcher)
reportReporter.convert_reports_to_pdfs("ingestion/companies.txt")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/convert-10ks-for-companies")
def convert_10ks_for_companies():
    return reportReporter.convert_reports_to_pdfs("ingestion/companies.txt")

@app.route("/get-latest-10k/")
def get_latest_10k():
    requested_company = request.args.get("data")
    return reportReporter.download_pdf_report_for_company_name(requested_company)






