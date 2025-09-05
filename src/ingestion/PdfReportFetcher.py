import flask
from src.ingestion.FormatUtil import standardize_name

class PdfReportFetcher:

    def __init__(self):
        pass

    def get_latest_10k_company_statement(self, company_names_to_companies, company_name):
        try:
            standardized_name = standardize_name(company_name)
            company = company_names_to_companies[standardized_name]

            if company is None:
                return "10-K filing not found for company: {}".format(company_name)

            return "10-K filing can be found at: {}".format(company.get_forms().get("10-K")[0].get_path())

        except KeyError as e:
            return "No company found called: {}".format(company_name)
        except Exception as e:
            raise e


    def get_latest_10k_company_statement_with_flask(self, company_names_to_companies, company_name):
        """
        :param company_name:
        :return:
        """
        try:
            standardized_name = standardize_name(company_name)
            company = company_names_to_companies[standardized_name]

            if company is None:
                response = flask.Response("Company: {} not found".format(company_name), 404)
                return response

            pdf_path = company.get_forms().get("10-K")[0].get_path()

            if pdf_path is None:
                response = flask.Response("10-K filing not found for company", 404)
                return response

            print(f"Serving file: {pdf_path}")
            return flask.send_file(pdf_path, as_attachment=True)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return flask.Response("An unexpected server error occurred", 500)