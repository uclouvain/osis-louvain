import xlsxwriter

def optimized_write_xlsx(info_to_write):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output, {'strings_to_urls': False})
    worksheet = workbook.add_worksheet()
    for i, row in enumerate(info_to_write):
        new_row = []
        for content in row:
            if type(content) in (str, unicode) and ('\n' in content or '\r' in content):
                content = content.replace('\n',' ').replace('\r', '')
            new_row.append(content)
        worksheet.write_row('A' + str(i+1), new_row)
    workbook.close()
    return output
