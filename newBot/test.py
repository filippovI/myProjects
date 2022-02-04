import openpyxl

book = openpyxl.Workbook()
sheet = book.active

sheet['A1'] = 'ID'
sheet['B1'] = 'TIME'
sheet['C1'] = 'ERROR_HANDLED'
sheet['D1'] = 'ERROR'
sheet['E1'] = 'USER'
book.save('my_book.xlsx')
book.close()
