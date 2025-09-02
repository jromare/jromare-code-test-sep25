
## Pre-req

- Python3

`python3 --version`
I have version `3.13.7`. IRL and for tech health, I believe it's important that we move to the latest stable. 

- pip3 

`pip3 --version`
I have version `25.2`. 

## Setting up

1. Create virtualenv in root directory (sibling to this README): `python3 -m venv .venv` 
2. Activate virtualenv: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt` 

Don't forget to run following to shut down the local environment properly: 

1. `deactivate`
2. `rm -rf .venv`
3. `rm -rf dummy-db/*` 

## How to run 

1. Go to `src` directory 

### Run as Flask app

`flask --app main run` 

Here I have hardcoded the conversion of the 10-K reports and the retrieval of one existing and a non-existing. 

You can also trigger the conversion by entering following in your browser: 

`http://127.0.0.1:5000/companies`

You can try to retrieve and download a 10-K report by querying:   
`http://127.0.0.1:5000/get-latest-10k/?data=<YOUR NAME HERE>`

## Reflections and open questions 

Since I was still a bit unsure about how _you_ would review/expect to interact with this assessment, I was considering just 
providing the Retriever without wrapping it in Flask. I encountered import/path issues when trying to use `Retriever` in
both (and I thought it was better to not duplicate the code in case). I was a bit unsure about how _you_ were planning to 
evaluate if we have successfully fetched the latest 10-K reports from each company and convert them to a PDF format. So
I thought that maybe you would like the possibility of fetching a 10-K report PDF.  

I have provided both the `get_latest_10k_company_statement` and `get_latest_10k_company_statement_with_flask` methods to 
trying to achieve the same purpose. The first returns to the path where the PDF exist, but it only returns strings which is
more human-readable but would not be preferable to programmatically test against. The second returns a flask response 

### Known flaws/open questions

- `get_latest_10k_company_statement()`:

We are not returning any message if file is found. This is a limitation with `flask.send_file()`. So if you're first 
requesting a 10k for a non-existent company and then one for an existing company (with an existing 10K), the current "UI"
looks a bit confusing. 

- `get_latest_10k_company_statement()`: 

Decide if we want to try to generate 10k on the fly. 

- How do we want to deal with the 10 RPS rate limit

It is important to note that the EDGAR APIs has 10 RPS rate limit. I have not tested our implementation under "load", i.e., 
converting the latest 10-Ks for all available companies. This is relevant since it might inform if we want to retrieve and convert 
the 10-Ks sequentially (as per the list provided) or parallelize it somehow.


- Integrate `Company` and `Form`   

I think that we can relatively easy consolidate the `Retriever`'s dictionaries

```
self.__companies_to_cik = {}
self.__cik_to_file = {}
self.__company_has_10k = {}
```

To better usage/composition of the included, but unused `Company` and `Form` classes. These classes are currently just in draft, but
I think they could be a good starting point for discussing how we can extend this to support historical reports and different kinds of forms.

- Logging and metrics

There's currently no logging or metrics support. Note that the `__company_has_10k` is a starting point to get some data for what companies were
able to get and convert a 10-K PDF for. 

### Database integration 

I currently save all converted 10K PDFs into the dummy-db folder, since we don't want to unnecessarily convert each
10-K report on-the-fly, per-customer read-path/request. In production, assuming that our customers are internal teams, 
I would expose the path to the file/or the file itself via an API. 

We could also have different write and read replicas for the database. I also guess that we would like the capability of storing
other form types as well as all the converted 10-K reports PDF, not just the latest. 

### The official company name vs. mouth-to-mouth name

One of my biggest questions is that if we expect to provide to be given a list with the company names listed exactly like
they are registered in SEC's EDGAR data. For example, for **Goldman Sachs**, there are at least: 

- GOLDMAN SACHS & CO. LLC 
- GOLDMAN SACHS GROUP INC 

Same concern holds upon retrieval given a company name. In this implementation we are honoring the exact naming 
(including non-alphanumeric characters), but ignoring upper and lower case. In production, I would discuss with my colleagues
and stakeholder about their requirements and preferences and then probably have a dedicated "component" to hold this mapping/grouping. 

### Non-consistency in constants vs. configs
Different teams and different people have different standard how they want to provide configs and/or constants. 

## Thoughts about tests

### General thoughts (not specific to this project)
We write tests both for our current and future selves. But we can also use it as a type of documentation. For example, 
`_subdirectory_is_available` might seem a bit redundant given that we're only calling get. However, here I want to convey
some of the logical structure of the SEC archive structure that we need to crawl. I.e., a directory or `company.idx` can exist, 
but that doesn't mean that it's available for consumption.

I know that people have various views on how and what to test. For unit testing, some people want to test the majority of functions whereas other prefer
only testing user-facing*/public methods (user-facing meaning other components in the code itself).

#### Example of what I would test: `_resolve_latest_available_qtr`
Imagine that we have years: [2023,2024]

**Scenario A:**

- If 2023 has [QTR1, QTR2, QTR3, QTR4]
- If 2024 has [QTR1, QTR2]
- AND `_subdirectory_is_available` returns True for 2024/QTR2

=> Return 2024/QTR2

**Scenario B:** 

- If 2023 has [QTR1, QTR2, QTR3, QTR4]
- If 2024 has [QTR1, QTR2]
- AND `_subdirectory_is_available` returns False for 2024/QTR2 but true for 2024/QTR1 

=> Return 2024/QTR1

**Scenario C:** 
- If 2023 has [QTR1, QTR2, QTR3, QTR4]
- If 2024 has [QTR1]
- AND `_subdirectory_is_available` returns False for 2024/QTR1 but true for 2023/QTR4

=> Return 2023/QTR4

## Relevant links
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data