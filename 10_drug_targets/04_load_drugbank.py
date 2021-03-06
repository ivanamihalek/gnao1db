#!/usr/bin/python3 -u

from utils.mysql  import *

#########################################
def main():

	db = connect_to_mysql("/home/ivana/.tcga_conf")
	cursor = db.cursor()
	search_db(cursor, "set autocommit=1")
	db.set_character_set('utf8mb4')
	cursor.execute('SET NAMES utf8mb4')
	cursor.execute('SET CHARACTER SET utf8mb4')
	cursor.execute('SET character_set_connection=utf8mb4')
	switch_to_db(cursor,"gnao1")

	inf = open("raw_tables/drugbank.txt", "r")
	drug = {}
	drug_name = ""
	target_name = ""
	target = {}
	d =0
	for line in inf:
		field = line.strip().split('\t')
		if field[0] == "drug":
			d += 1
			# store targets for the previous name
			if drug_name and len(target)>0:
				drug[drug_name]["targets"] = target
			# new name
			drug_name = field[1]
			drug[drug_name] = {}
			target = {}
		elif field[0] == "target":
			target_name = field[1]
			target[target_name] = {}
		else:
			if target_name:
				for keyword in ["identifier", "gene-name", "action"]:
					if field[0] == keyword and  field[1] and len(field[1])>0:
						target[target_name][keyword] = field[1]
			if drug_name:
				if field[0] == "pubchem":
					drug[drug_name]["pubchem"] = field[1]
				elif field[0] == "prodrug":
					drug[drug_name]["is_prodrug_of"] = field[1]
				elif field[0] == "drugbank_id":
					if field[1][:2] != "DB":
						print("unexpected drugbank id {} for name {}".format(field[1], drug_name))
					drug[drug_name]["drugbank_id"] = field[1]
				else:
					for keyword in ["synonym", "product", "brand"]:
						if field[0] == keyword and  field[1] and len(field[1])>0:
							plural = keyword+"s"
							if plural not in drug[drug_name]:
								drug[drug_name][plural] = set()
							drug[drug_name][plural].add(field[1])

	for name, data in drug.items():
		if not data: continue # this is a stub entry (work in progress) from Databank

		tgt_list= []
		if "targets" in data:
			for tgt, tgt_info in data["targets"].items():
				if "gene-name" in tgt_info:
					tgt_info_chunk = tgt_info["gene-name"]
				else:
					tgt_info_chunk = tgt
				if "action"  in tgt_info:
					tgt_info_chunk += ":"+ tgt_info["action"].strip()
				tgt_list.append(tgt_info_chunk)
		name = name.replace("'","")
		fixed_fields  = {"name":name.lower()}
		update_fields = {}
		for fnm in ["pubchem", "is_prodrug_of", "drugbank_id"]:
			if fnm in data:
				update_fields[fnm] = data[fnm]

		if "synonyms" in data:
			# use semicolon at the beginning and end so we can search by similarity for '%;qry;%'
			update_fields["synonyms"] = ";" + ";".join(list(data["synonyms"])).strip().replace("'","") + ";"
		if "products" in data:
			# prouct names are often garbage, like naems for cough drops and such, I don't know how to handle this
			update_fields["products"] = ";" + ";".join(list(data["products"])[:100]).strip().replace("'","")+ ";"
		if "brands" in data:
			update_fields["brands"] = ";" + ";".join(list(data["brands"])).strip().replace("'","")+ ";"
		if tgt_list:
			update_fields["targets"] = ";".join(tgt_list).replace("'","")
		if not update_fields: continue

		if not store_or_update(cursor, "drugs", fixed_fields, update_fields):
			print(name)
			for k, v in  data["targets"].items():
				print(k,v)
			exit()


	# fixes:
	qry = "update drugs set brands = concat(';Hydroaltesone;Hidroaltesona', brands ) where name = 'Hydrocortisone'"
	error_intolerant_search(cursor, qry)
	# surrogates, I don't know what to do when somebody quotes in the case description that they used "curare"
	# of "benzodiazepines' - that's too generic
	qry = "update drugs set  products = concat(';curare', products) where name = 'Pancuronium'"
	error_intolerant_search(cursor, qry)
	qry = "update drugs set  products = concat(';benzodiazepine;benzodiazepines', products) where name = 'Clonazepam'"
	error_intolerant_search(cursor, qry)
	# Benzodiazepine by itself is investigational drug (?! I don't really care)
	qry = "delete from drugs where name='Benzodiazepine'"
	error_intolerant_search(cursor, qry)

	cursor.close()
	db.close()



#########################################
if __name__ == '__main__':
	main()
