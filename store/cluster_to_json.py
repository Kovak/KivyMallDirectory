import xlrd
import re
import kivy
from kivy.storage.jsonstore import JsonStore
workbook = xlrd.open_workbook('store_data.xlsx', encoding_override="utf-8")
worksheet = workbook.sheet_by_name('Sheet1')
num_rows = worksheet.nrows
num_cells = worksheet.ncols
new_dict = {}
for x in range(num_rows-1):
	row = worksheet.row(x+1)
	print row[0]
	store_key = unicode(row[0]).split("text:u")[1]
	print row[1]
	sentence_data = unicode(row[1]).split("text:u")
	print sentence_data[1]
	#print store_key, store_sentence
 	new_dict[store_key[1:-1]] = unicode(sentence_data[1][1:-1])

json = JsonStore('store_data.json')
json['store_data'] = new_dict