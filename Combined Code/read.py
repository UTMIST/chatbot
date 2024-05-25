import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope and credentials to access Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet by its URL
sheet_url = 'https://docs.google.com/spreadsheets/d/1fE1R276S10PkgP6O4zrhtCzCxhtnekBfaXt-EdYeLW4/edit#gid=0'
sheet = client.open_by_url(sheet_url)

# Assume the first sheet in the workbook
worksheet = sheet.get_worksheet(0)

# Iterate over each column in the transposed data
columns = enumerate(worksheet.get_all_values(), start=1)
with open(f'test.txt', 'w') as file:
    for cell in columns:
        file.write(str(cell[1][0]) + " " + str(cell[1][1]) + "\n")