# PDF Password Cracker

This Python script attempts to crack the password of a protected PDF file using a wordlist. It leverages the `pikepdf` library for PDF manipulation and `termcolor` for colored terminal output.

## Prerequisites

Before running the script, ensure you have the following installed:

* **Python 3.x:** You can download it from [python.org](https://www.python.org/).
* **pikepdf:** Install it using pip:
    ```bash
    pip install pikepdf
    ```
* **termcolor:** Install it using pip:
    ```bash
    pip install termcolor
    ```

## Usage

1.  **Prepare a Wordlist:** Create a text file (e.g., `wordlist.txt`) containing a list of potential passwords, one password per line.
2.  **Place the PDF:** Put the protected PDF file (e.g., `remote.pdf`) in the same directory as the Python script.
3.  **Run the Script:** Execute the Python script.
    ```bash
    python pdf_cracker.py
    ```
4.  **Observe the Output:** The script will attempt each password from the wordlist and display the results in the terminal.
    * If a password is incorrect, it will be printed in red.
    * If a password is correct, it will be printed in green, and the script will terminate.
5.  **Modify the script:**
    * Change `"remote.pdf"` to the path of your pdf
    * Change `"wordlist.txt"` to the path of your wordlist.

## Example

Assuming you have a PDF file named `my_protected.pdf` and a wordlist named `passwords.txt`, and your python script is named `pdf_cracker.py`, you would:

1.  Place `my_protected.pdf`, `passwords.txt`, and `pdf_cracker.py` in the same folder.
2.  Run: `python pdf_cracker.py`
3.  Modify the python script to:
    ```python
    import pikepdf
    from termcolor import colored

    file = open("passwords.txt")

    for password in file:
        try:
            with pikepdf.open("my_protected.pdf", password.strip()) as p:
                print(colored("Password Found: {}".format(password), "green"))
                break
        except:
            print(colored("Trying Password: {}".format(password), "red"), end="")
            continue
    ```

## Important Notes

* This script is intended for ethical use only. Do not use it to crack passwords for PDFs that you do not have authorization to access.
* The success of this script depends on the strength and comprehensiveness of your wordlist.
* For very strong passwords, this method may take a significant amount of time or may not be successful.
* Consider using more advanced password cracking tools if you need to crack very strong passwords.
* This is a dictionary attack. For stronger passwords, a brute force attack or other more sophisticated methods would be needed.

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.
