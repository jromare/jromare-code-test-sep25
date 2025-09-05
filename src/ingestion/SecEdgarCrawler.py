from weasyprint import HTML

from src.ingestion.Company import Company
from src.ingestion.Form import Form
from src.ingestion.FormatUtil import standardize_name
from src.ingestion.config import SEC_GOV_BASE_URL, USER_AGENT, COMPANY_IDX_URL, YEAR_URL, QUARTERS_IN_YEAR_URL,SUBMISSIONS_URL, FILING_URL, QUARTERS_DIRECTORY_URL, PDF_PATH
import requests
from bs4 import BeautifulSoup
import re

class SecEdgarCrawler:
    _CIK_LENGTH = 10


    def __init__(self):
        self.base_url = SEC_GOV_BASE_URL
        self.headers = {
            "User-Agent": USER_AGENT
        }


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


    def _extract_company(self, company_idx_line):
        parts = re.split(r'\s{2,}', company_idx_line.strip())
        if len(parts) >= 5:
            company_name = standardize_name(parts[0])
            cik = parts[2]
            return Company(company_name, cik)

        else:
            print(f"Skipping malformed line: {company_idx_line.strip()}")
            return None


    def _company_names_to_companies(self, url):
        try:
            response = self._get(url)
            response_as_rows = response.text.splitlines()
            company_names_to_companies = {}

            for line in response_as_rows[10:]:
                if not line.strip():
                    continue
                company = self._extract_company(line)
                company_names_to_companies[company.get_name()] = company

            return company_names_to_companies
        except requests.RequestException:
            print("Failed to retrieve company CIK data. The index file may not exist.")
            return None


    def _get_company_submissions(self, company_cik):
        """
        Example of full url: # https://data.sec.gov/submissions/CIK0001849820.json
        :param company_name:
        :return:
        """
        if company_cik is None:
            return None

        number_of_0s = SecEdgarCrawler._CIK_LENGTH - len(company_cik)
        url = SUBMISSIONS_URL.format("0" * number_of_0s, company_cik)

        try:
            return self._get(url)
        except requests.RequestException:
            print(f"Failed to get submissions for company with CIK={company_cik}).")
            return None

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

            soup = BeautifulSoup(response.text, 'html.parser')

            html_body = soup.find('html')
            if html_body:
                return str(html_body)

            return str(soup)

        except requests.RequestException:
            print(f"Failed to get filing for CIK {cik}, accession number {accession_number}.")
            return None


    def convert_10k_to_pdf(self, company):
        try:
            cik = company.get_cik()
            company_submissions_response = self._get_company_submissions(cik)
            if not company_submissions_response:
                return None

            filings = company_submissions_response.json().get("filings")
            if not filings:
                return None

            ten_k_index = self._find_10_k_index(filings)
            if ten_k_index == -1:
                return None

            ten_k_accession_number = filings.get("recent").get("accessionNumber")[ten_k_index]

            cleaned_html = self._get_filing(cik, ten_k_accession_number)
            if not cleaned_html:
                return None

            company_name = company.get_name()
            filing_date = filings.get("recent").get("filingDate")[ten_k_index]
            pdf_path = PDF_PATH.format(
                company_name.replace(" ", "-"),
                filing_date
            )

            HTML(string=cleaned_html).write_pdf(pdf_path)

            return Form("10-K", filing_date, pdf_path)

        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(f"An error occurred while converting 10-K to PDF for {company_name}: {e}")
            return None


    def convert_companies_reports_to_pdfs_on_start(self, file_with_companies):
        maybe_latest_available_qtr = self._resolve_latest_available_qtr()
        output_company_names_to_companies = {}

        if maybe_latest_available_qtr is not None:
            result = self._company_names_to_companies(COMPANY_IDX_URL.format(maybe_latest_available_qtr))
            output_company_names_to_companies = result

            with open(file_with_companies, 'r') as file:
                for line in file:
                    company_name = line.strip()
                    standardized_name = standardize_name(company_name)
                    if standardized_name in output_company_names_to_companies:
                        form = self.convert_10k_to_pdf(output_company_names_to_companies[standardized_name])

                        if form is not None:
                            company = output_company_names_to_companies[standardized_name]
                            company.add_form(form)
                            output_company_names_to_companies[standardized_name] = company

        return output_company_names_to_companies




