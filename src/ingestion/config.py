import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SEC_GOV_BASE_URL = os.getenv('SEC_GOV_BASE_URL')
USER_AGENT = os.getenv('USER_AGENT')
COMPANY_IDX_URL = os.getenv("COMPANY_IDX_URL")
YEAR_URL = os.getenv("YEAR_URL")
QUARTERS_IN_YEAR_URL = os.getenv("QUARTERS_IN_YEAR_URL")
QUARTERS_DIRECTORY_URL = os.getenv("QUARTERS_DIRECTORY_URL")
SUBMISSIONS_URL = os.getenv("SUBMISSIONS_URL")
FILING_URL = os.getenv("FILING_URL")
PDF_PATH = os.getenv("PDF_PATH")