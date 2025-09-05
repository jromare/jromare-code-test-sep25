from src.ingestion.FormatUtil import standardize_name


class ReportReporter:

    def __init__(self, sec_edgar_crawler, pdf_report_fetcher):
        self.__reporter_converter = sec_edgar_crawler
        self.__pdf_report_fetcher = pdf_report_fetcher
        self.__company_names_to_company = {}


    def _get_company_cik(self, company_name):
        standardized_name = standardize_name(company_name)
        return self.__company_names_to_company[standardized_name].get_cik()


    def _could_retrieve_reports(self, input_file_with_company_names):
        retrieved_reports_for_input = {}

        with open(input_file_with_company_names, 'r') as file:
            for line in file:
                company_name = line.strip()
                standardized_name = standardize_name(company_name)
                if standardized_name in self.__company_names_to_company.keys():
                    retrieved_reports_for_input[standardized_name] = True

                else:
                    retrieved_reports_for_input[standardized_name] = False

        return retrieved_reports_for_input

    # CAN DO UPON CREATION AND THEN ADD ON
    def convert_reports_to_pdfs(self, input_file_with_company_names):
        self.__company_names_to_company = (self.__reporter_converter
                                           .convert_companies_reports_to_pdfs_on_start(input_file_with_company_names))
        return self._could_retrieve_reports(input_file_with_company_names)


    def get_pdf_report_for_company_name(self, company_name):
        return self.__pdf_report_fetcher.get_latest_10k_company_statement(self.__company_names_to_company, company_name)

    def download_pdf_report_for_company_name(self, company_name):
        return self.__pdf_report_fetcher.get_latest_10k_company_statement_with_flask(self.__company_names_to_company, company_name)
