'''
Elliot Williams
January 10th, 2018
RCSB API Structure Searcher

If you end up using this code, let me know! I'd probably find what you're doing
very cool.
'''

import requests

url = "http://www.rcsb.org/pdb/rest/search"

# Alter this, based on the docs for the RCSB RESTful API described
# here: https://www.rcsb.org/pdb/software/rest.do, to search for other things
queryText = """
<orgPdbQuery>
<queryType>org.pdb.query.simple.StructTitleQuery</queryType>
<description>StructTitleQuery: struct.title.comparator=contains struct.title.value=ribosome</description>
<struct.title.comparator>contains</struct.title.comparator>
<struct.title.value>ribosome</struct.title.value>
</orgPdbQuery>
"""

def query_for_pdb_ids(url, queryText):
    print("query:\n", queryText)
    print("querying PDB...\n")

    response = requests.post(
    url,
    data=queryText.encode(),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    pdb_id_list = response.text.strip().split("\n")
    return pdb_id_list

print(query_for_pdb_ids(url, queryText)) # TODO: Remove


test_ids = ["5JUP", "5JUU"]
desired_fields = ["structureId", "structureTitle", "resolution", "depositionDate", "experimentalTechnique", "residueCount", "resolution"]

url = "http://www.rcsb.org/pdb/rest/customReport.xml"
def get_info_from_ids(url, pdb_ids, desired_fields):
    req_url = url + "?pdbids={}".format(",".join(pdb_ids))
    req_url += "&customReportColumns={}".format(",".join(desired_fields))
    req_url += "&format=csv&service=wsfile"
    response = requests.get(req_url)
    print(response.text)

get_info_from_ids(url, test_ids, desired_fields) # TEMP: remove later
get_info_from_ids(url, test_ids, ["chainLength", "db_name", "entityMacromoleculeType"])

url = "https://www.rcsb.org/pdb/rest/describeMol"
def describe_chains(url, pdb_ids):
    req_url = url + "?structureId={}".format(",".join(pdb_ids))
    req_url += "&format=csv&service=wsfile"
    response = requests.get(req_url)
    # print(response.text)
    # return response.text

    from lxml import etree
    data = etree.fromstring(response.text)
    results = {}
    for node in data.xpath("//molDescription//structureId"):
        struct_name = node.attrib['id']
        chain_names = [node.attrib['name']
            for node in data.xpath("//molDescription//structureId//macroMolecule")]
        chain_ids   = [node.attrib['id']
            for node in data.xpath("//molDescription//structureId//chain")]
        chain_tax   = [node.attrib['name']
            for node in data.xpath("//molDescription//structureId//Taxonomy")]
        chain_description = [node.attrib['description']
            for node in data.xpath("//molDescription//structureId//polymerDescription")]
        results[struct_name] = list(zip(chain_names, chain_ids, chain_tax, chain_description))

    return results

result = describe_chains(url, test_ids)
subset_result = result['5JUP']
subset_organisms = [x[2] for x in subset_result]
print(list(set(subset_organisms)))
# Now, can join chains, sequences, and their descriptions




# https://www.rcsb.org/pages/webservices/rest-fetch#descEntity
