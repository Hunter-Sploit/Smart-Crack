# Import necessary libraries
import pikepdf  # For handling PDF files
from termcolor import colored  # For printing colored output in the terminal

# Open the wordlist file containing potential passwords
file = open("wordlist.txt")

# Iterate through each password in the wordlist
for password in file:
    try:
        # Attempt to open the encrypted PDF file with the current password
        with pikepdf.open("remote.pdf", password.strip()) as p:
            # If successful, print the found password in green and exit the loop
            print(colored("Password Found: {}".format(password), "green"))
            break
    except:
        # If the password is incorrect, print a red message and continue to the next password
        print(colored("Trying Password: {}".format(password), "red"), end="")
        continue
