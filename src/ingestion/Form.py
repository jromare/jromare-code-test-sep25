class Form:
    def __init__(self, form_type, date, file_path):
        self.__form_type = form_type
        self.__date = date
        self.__file_path = file_path

    def get_form_type(self):
        return self.__form_type

    def get_date(self):
        return self.__date

    def get_path(self):
        return self.__file_path
