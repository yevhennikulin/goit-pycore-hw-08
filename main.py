from collections import UserDict
from datetime import datetime, timedelta
import pickle

# AddressBookRepository for persistence
class AddressBookRepository:
    def __init__(self, filename="addressbook.pkl"):
        self.filename = filename

    def save(self, book):
        with open(self.filename, "wb") as f:
            pickle.dump(book, f)

    def load(self):
        try:
            with open(self.filename, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return AddressBook()

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
		pass

class Birthday(Field):
    def __init__(self, value):
        try:
            self.date = datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits and contain only numbers.")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def edit_phone(self, old_phone, new_phone):
        for key, phone in enumerate(self.phones):
            if phone.value == old_phone:
                try:
                    self.phones[key] = Phone(new_phone)
                    return "Phone number updated."
                except ValueError as e:
                    return str(e)
        return "Phone number not found."

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p.value
        return "Phone number not found."

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday_str = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def find(self, name):
        return self.data.get(name)

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.today().date()

        for record in self.data.values():
            if record.birthday:
                birthday_date = record.birthday.date.date()
                birthday_this_year = birthday_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_date.replace(year=today.year + 1)

                days_until_birthday = (birthday_this_year - today).days
                if 0 <= days_until_birthday <= 7:
                    congratulation_date = birthday_this_year
                    if birthday_this_year.weekday() == 5:
                        congratulation_date = birthday_this_year + timedelta(days=2)
                    elif birthday_this_year.weekday() == 6:
                        congratulation_date = birthday_this_year + timedelta(days=1)

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                    })

        return upcoming_birthdays


# Decorator to handle input errors
def input_error(func):
    def inner(args, book):
        # No command entered
        if args is None:
            return "Please enter a command."
        # check for specific command errors some require one argument, some two
        if func.__name__ == "add_contact":
            if len(args) == 0:
                return "Please provide both name and phone number."
            elif len(args) == 1:
                return "Please provide a phone number."
        elif func.__name__ == "change_contact":
            if len(args) < 3:
                return "Please provide name, old phone, and new phone."
        elif func.__name__ in ("show_phone", "add_birthday"):
            if len(args) == 0:
                return "Please provide a contact name."
        # Handle exceptions from the command functions
        try:
            return func(args, book)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except Exception as e:
            return f"Unexpected error: {e}"
    return inner
# Parses user input into command and arguments
def parse_input(user_input):
    cmd, *args = user_input.split() if user_input.strip() else (None, [])
    if not cmd:
        return None, []
    cmd = cmd.strip().lower()
    return cmd, *args
# Adds a new contact
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

# Changes an existing contact's phone number
@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        result = record.edit_phone(old_phone, new_phone)
        return result
    else:
        return "Contact not found."
# Shows a contact's phone number
@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}: {'; '.join(p.value for p in record.phones)}"
    else:
        return "Contact not found."

# Shows all contacts
def show_all(book):
    if not book.data:
        return "No contacts found."
    result = []
    for record in book.data.values():
        result.append(str(record))
    return "\n".join(result)

# Adds birthday to a contact
@input_error
def add_birthday(args, book):
    if len(args) < 2:
        return "Please provide name and birthday (DD.MM.YYYY)."
    name, birthday = args[0], args[1]
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}."
    else:
        return "Contact not found."

# Shows birthday of a contact
@input_error
def show_birthday(args, book):
    if len(args) < 1:
        return "Please provide a contact name."
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday.value}"
    elif record:
        return f"{name} has no birthday set."
    else:
        return "Contact not found."

# Shows upcoming birthdays
@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        result = []
        for birthday_info in upcoming:
            result.append(f"Congratulate {birthday_info['name']} on {birthday_info['congratulation_date']}")
        return "\n".join(result)
    else:
        return "No upcoming birthdays in the next week."
def main():
    repo = AddressBookRepository()
    book = repo.load()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            repo.save(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
