from src.ingestion.Form import Form

class Company:
    """
    This class represents a company with its cik and associated forms/files.
    """

    def __init__(self, name, cik):
        self.__name = name
        self.__cik = cik
        self.__forms = {}

    def add_form(self, form: Form):
        form_type = form.get_form_type()
        if self.__forms.keys().__contains__(form_type):
            self.__forms[form_type].append(form)
        else:
            self.__forms[form_type] = [form]

    def get_forms(self):
        return self.__forms

    def get_cik(self):
        return self.__cik

    def get_name(self):
        return self.__name
