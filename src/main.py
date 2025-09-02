from flask import Flask, request

from src.ingestion.Retriever import Retriever

app = Flask(__name__)

retriever = Retriever()
print(retriever.convert_companies_10ks_to_pdfs("ingestion/companies.txt"))
print(retriever.get_latest_10k_company_statement("Paychex Inc"))
print(retriever.get_latest_10k_company_statement("Not a company"))

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/convert-10ks-for-companies")
def convert_10ks_for_companies():
    retriever.convert_companies_10ks_to_pdfs("ingestion/companies.txt")
    return retriever.company_has_10k()

@app.route("/get-latest-10k/")
def get_latest_10k():
    requested_company = request.args.get("data")
    return retriever.get_latest_10k_company_statement_with_flask(requested_company)





