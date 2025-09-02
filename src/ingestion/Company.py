class Company:
    """
    This class represents a company with its cik and associated forms/files.
    """

    def __init__(self, name, cik):
        self.__name = name
        self.__cik = cik
        self.__forms = {}


    def add_file(self, form_type):
        pass