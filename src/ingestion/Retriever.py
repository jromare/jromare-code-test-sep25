import flask
from weasyprint import HTML

from src.ingestion.config import SEC_GOV_BASE_URL, USER_AGENT, COMPANY_IDX_URL, YEAR_URL, QUARTERS_IN_YEAR_URL,SUBMISSIONS_URL, FILING_URL, QUARTERS_DIRECTORY_URL, PDF_PATH
import requests
from bs4 import BeautifulSoup
import re

class Retriever:
    _CIK_LENGTH = 10

    def __init__(self):
        self.__companies_to_cik = {}
        self.__cik_to_file = {}
        self.__company_has_10k = {}
        self.base_url = SEC_GOV_BASE_URL
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def companies_to_cik(self):
        return self.__companies_to_cik


    def company_has_10k(self):
        return self.__company_has_10k


    def _beautiful_soup_links(self, response):
        soup = BeautifulSoup(response, 'html.parser')

        main_content = soup.find(id="main-content")
        table = main_content.find("table")

        return table.find_all("a")


    def _get(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error fetching the webpage: {e}")
            raise


    def _get_years(self):
        try:
            response = self._get(YEAR_URL)
            links = self._beautiful_soup_links(response.text)

            years = []
            for link in links:
                year_text = link.text.strip()
                if year_text.isdigit():
                    years.append(int(year_text))

            return years
        except requests.RequestException:
            return []


    def _get_quarters(self, year):
        try:
            response = self._get(QUARTERS_IN_YEAR_URL.format(year))
            links = self._beautiful_soup_links(response.text)

            quarters = []
            for link in links:
                link_text = link.text.strip()
                if link_text.startswith("QTR"):
                    quarters.append(link_text)

            return quarters
        except requests.RequestException:
            return []


    def _subdirectory_is_available(self, url):
        try:
            self._get(url)
            return True
        except requests.RequestException:
            return False


    def _resolve_latest_available_qtr(self):
        years = self._get_years()
        years.sort(reverse=True)

        for year in years:
            quarters = self._get_quarters(year)
            quarters.sort(reverse=True)

            for qtr in quarters:
                url = QUARTERS_DIRECTORY_URL.format(year, qtr)

                if self._subdirectory_is_available(url):
                    return "{}/{}".format(year, qtr)

        return None


    def _retrieve_companies_ciks(self, url):
        try:
            response = self._get(url)
            response_as_rows = response.text.splitlines()
            company_names_to_cik = {}

            for line in response_as_rows[10:]:
                if not line.strip():
                    continue
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 5:
                    company_name = parts[0].lower()
                    cik = parts[2]
                    if company_name not in company_names_to_cik:
                        company_names_to_cik[company_name] = cik
                else:
                    print(f"Skipping malformed line: {line.strip()}")

            self.__companies_to_cik = company_names_to_cik
            return self.__companies_to_cik
        except requests.RequestException:
            print("Failed to retrieve company CIK data. The index file may not exist.")
            return None


    def _get_company_cik(self, company_name):
        standardized_name = company_name.lower()
        return self.__companies_to_cik.get(standardized_name)


    def _get_company_submissions(self, company_name):
        """
        Example of full url: # https://data.sec.gov/submissions/CIK0001849820.json
        :param company_name:
        :return:
        """
        company_cik = self._get_company_cik(company_name)
        if company_cik is None:
            return None

        number_of_0s = Retriever._CIK_LENGTH - len(company_cik)
        url = SUBMISSIONS_URL.format("0" * number_of_0s, company_cik)

        try:
            return self._get(url)
        except requests.RequestException:
            print(f"Failed to get submissions for company {company_name} (CIK: {company_cik}).")
            return None


    def _convert_company_10k_to_pdf(self, company_name):
        try:
            company_submissions_response = self._get_company_submissions(company_name)
            if not company_submissions_response:
                return None # No submissions found or failed to fetch

            filings = company_submissions_response.json().get("filings")
            if not filings:
                return None # No filings section in the JSON

            ten_k_index = self._find_10_k_index(filings)
            if ten_k_index == -1:
                return None

            ten_k_accession_number = filings.get("recent").get("accessionNumber")[ten_k_index]
            cik = self._get_company_cik(company_name)
            if not cik:
                return None

            cleaned_html = self._get_filing(cik, ten_k_accession_number)
            if not cleaned_html:
                return None

            pdf_path = PDF_PATH.format(
                company_name.lower().replace(" ", "-"),
                filings.get("recent").get("filingDate")[ten_k_index]
            )

            HTML(string=cleaned_html).write_pdf(pdf_path)
            return pdf_path

        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(f"An error occurred while converting 10-K to PDF for {company_name}: {e}")
            return None


    def convert_companies_10ks_to_pdfs(self, input_file):
        maybe_latest_available_qtr = self._resolve_latest_available_qtr()
        company_to_has_10k = {}

        if maybe_latest_available_qtr is not None:
            self._retrieve_companies_ciks(COMPANY_IDX_URL.format(maybe_latest_available_qtr))

            with open(input_file, 'r') as file:
                for line in file:
                    company_name = line.strip()
                    standardized_name = company_name.lower()
                    pdf_path = self._convert_company_10k_to_pdf(standardized_name)
                    if pdf_path is None:
                        company_to_has_10k[standardized_name] = False

                    else:
                        cik = self._get_company_cik(company_name)
                        self.__cik_to_file[cik] = pdf_path
                        company_to_has_10k[standardized_name] = True

        self.__company_has_10k = company_to_has_10k
        return self.__company_has_10k


    def _find_10_k_index(self, filings):
        submitted_forms = filings.get("recent").get("form")
        ten_k_index = 0
        is_found = False

        for idx, form in enumerate(submitted_forms ):
            if form == "10-K":
                is_found = True
                break
            else:
                ten_k_index += 1

        if is_found:
            return ten_k_index
        else:
            return -1


    def _get_filing(self, cik, accession_number):
        try:
            response = self._get(FILING_URL.format(cik, accession_number))
            html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')

            html_body = soup.find('html')
            if html_body:
                return str(html_body)

            return str(soup)

        except requests.RequestException:
            print(f"Failed to get filing for CIK {cik}, accession number {accession_number}.")
            return None


    def get_latest_10k_company_statement(self, company_name):
        try:
            cik = self._get_company_cik(company_name)
            if cik is None:
                return "Company: {} not found".format(company_name)

            pdf_path = self.__cik_to_file[cik]

            if pdf_path is None:
                return "10-K filing not found for company: {}".format(company_name)

            return "10-K filing can be found at: {}".format(pdf_path)

        except Exception as e:
            raise e

    def get_latest_10k_company_statement_with_flask(self, company_name):
        """
        :param company_name:
        :return:
        """
        try:
            cik = self._get_company_cik(company_name)
            if cik is None:
                response = flask.Response("Company: {} not found".format(company_name), 404)
                return response

            pdf_path = self.__cik_to_file[cik]

            if pdf_path is None:
                response = flask.Response("10-K filing not found for company", 404)
                return response

            print(f"Serving file: {pdf_path}")
            return flask.send_file(pdf_path, as_attachment=True)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return flask.Response("An unexpected server error occurred", 500)