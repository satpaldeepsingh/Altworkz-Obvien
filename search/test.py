from edgar import Company, TXTML, XBRL, XBRLElement
from bs4 import BeautifulSoup
import sys

sec_companies = {
    "oracle": {
        "name": "Oracle Corp",
        "cik": "0001341439"
    },
    "google": {
        "name": "Alphabet Inc",
        "cik": "0001652044"
    },
    "apple": {
        "name": "Apple Inc.",
        "cik": "0000320193"
    },
    "ibm": {
        "name": "INTERNATIONAL BUSINESS MACHINES CORP",
        "cik": "0000051143"
    },
    "dell": {
        "name": "Dell Technologies Inc.",
        "cik": "0001571996"
    }
}

company_name = sys.argv[1]

if (company_name == "oracle"):
    company = Company("Oracle Corp", "0001341439")
    tree = company.get_all_filings(filing_type="10-K")
    docs = Company.get_documents(tree,
     +=1)
    doc_html = BeautifulSoup(TXTML.to_xml(docs), 'html.parser')
else:
    docs = open("sample-10Ks/"+company_name+".html", encoding="utf8")
    doc_html = BeautifulSoup(docs, 'html.parser')
    # print(docs.read())
    # exit()


#print(last_2_tables[1])
#print("len "+str(len(last_2_tables)))
#print("type "+str(type(last_2_tables)))

# if "Name" in str(last_2_tables):
#     print("--- PRESENT ---")
# else:
#     print("--- NOT PRESENT ---")

# for i in range(len(last_2_tables)):

table_headers = ('Name', 'Title', 'Date')
person_list = []

for t_num, table in enumerate(doc_html.find_all('table')[-4:]): #tables_list

    thtml = str(table)

    if ("Name" in thtml or "Signature" in thtml) and ("Title" in thtml):

        non_empty_tr = 1
        for tr in table.find_all('tr')[1:]: #tr_list

            #print("Starting row "+str(tr_i))

            person = {}
            col_index = 0

            if (tr.get_text().strip() != ''):

                for td_i, td in enumerate(tr.find_all('td')): #td_list

                    td_txt = td.get_text().strip()

                    if (td_txt != ''):

                        #print(td_txt + ' ('+ str(td_i) + ') ', end = " | ")

                        if (non_empty_tr % 2 == 0):

                            if (col_index == 0):

                                person_list[len(person_list) - 1][table_headers[col_index]] = td_txt

                        else:

                            if (col_index > 0):

                                person[table_headers[col_index]] = td_txt

                        col_index += 1

                non_empty_tr += 1

                if (len(person) != 0):

                    person_list.append(person)

        print("\n")
    else:
        print("NO table found\n")

print("---- Person List ----  \n")
print(person_list)
