import datetime


class DataFile:
    def __init__(self, file_name):
        self.file_name = self.add_date_to_file_name(file_name)
        self.file = open(self.file_name, "a+")

    def add_date_to_file_name(self, filename):
        now_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{now_date}_{filename}"

    def save(self, data):
        try:
            now_date = str(datetime.datetime.now())
            self.file.write(f"timestamp: {now_date} data: {data}\n")
            self.file.flush()
        except IOError as e:
            print(f"Error saving data: {e}")
