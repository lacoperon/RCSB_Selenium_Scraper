'''
Elliot Williams
January 10th, 2018
RCSB API Structure Searcher

If you end up using this code, let me know! I'd probably find what you're doing
very cool.
'''

import requests
import pandas as pd
from lxml import etree
from io import StringIO

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

'''
This function takes in a correctly formatted XML query to the RCSB Search API,
and returns the resulting PDB IDs received from said API in the response

Input:
    queryText : string  -- the XML query to be sent to the API
    url       : ?string -- the URL the query should be POSTed to
    verbose   : ?bool   -- Flag for verbose output from function
Output:
    pdb id list : string list -- a list of PDB IDs returned from the API
'''
def query_for_pdb_ids(queryText=queryText, url="http://www.rcsb.org/pdb/rest/search",
    verbose=False):

    if verbose:
        print("query:\n", queryText)
        print("querying PDB...\n")

    # Makes HTTP POST Request to RCSB API
    response = requests.post(
    url,
    data=queryText.encode(),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if not response.status_code == 200:
        print("Response did not receive OK HTTP Response")
        print("{}:{}".format(response.status_code, response.reason))
        return None

    pdb_id_list = response.text.strip().split("\n")

    if len(pdb_id_list) == 0:
        print("Empty PDB ID list returned from API")
        return

    if len(pdb_id_list[0]) != 4:
        print("Returned PDB ID list appears invalid")
        print("For Example, {}".format(pdb_id_list[0]))
        return pdb_id_list

    return pdb_id_list

'''
This function takes in a list of PDB IDs, and queries the RCSB API for fields of
interest regarding those structures. To alter the fields you want information
on, go to the RCSB API documentation.

Input:
    pdb_ids        : string list  -- List of PDB IDs to be queried
    url            : ?string      -- URL to send HTTP GET request to
    desired_fields : ?string list -- List of fields to request
'''
def get_info_from_ids(pdb_ids, url="http://www.rcsb.org/pdb/rest/customReport.xml",

    # Formats the URL as required by the API definition
    desired_fields=["structureId", "structureTitle", "resolution", "depositionDate", "experimentalTechnique", "residueCount", "resolution"]):
    req_url = url + "?pdbids={}".format(",".join(pdb_ids))
    req_url += "&customReportColumns={}".format(",".join(desired_fields))
    req_url += "&format=csv&service=wsfile"

    # Makes HTTP GET Request to RCSB API
    response = requests.get(req_url)

    if not response.status_code == 200:
        print("Response did not receive OK HTTP Response")
        print("{}:{}".format(response.status_code, response.reason))
        return None

    # Reads in API response as a 'dummy file', allowing pandas to read as csv
    text_dummy_file = StringIO(response.text.strip())
    df = pd.read_csv(text_dummy_file)

    return df

'''
This function obtains chain information (like chain name, id, taxonomy,
description, and sequence) from the RCSB API given a particular PDB Accession ID

Input:
    pdb_id : string  -- PDB Accession ID to look up
    url    : ?string -- URL of RCSB API to query
Output:
    result_df : DataFrame -- pandas DataFrame with chain descriptors
'''
def describe_chains(pdb_id, url="https://www.rcsb.org/pdb/rest/describeMol"):
    # Formats the URL as required by the API definition
    req_url = url + "?structureId={}".format(pdb_id)
    req_url += "&format=csv&service=wsfile"

    # Makes HTTP GET Request to RCSB API
    response = requests.get(req_url)

    if not response.status_code == 200:
        print("Response did not receive OK HTTP Response")
        print("{}:{}".format(response.status_code, response.reason))
        return None

    # Parses XML Response data using lxml
    data = etree.fromstring(response.text)
    results = {}

    # For each resulting chain, gets the name, ID, taxonomy, and description
    chain_names = []
    chain_ids = []
    chain_taxonomies = []
    chain_descriptions = []
    # TODO: Consider refactoring
    for node in data.xpath("//molDescription//structureId//polymer"):
        macroMolecNodes = node.xpath("child::macroMolecule")
        if len(macroMolecNodes) > 0:
            chain_names.append(macroMolecNodes[0].attrib['name'])
        else:
            chain_names.append('')

        chainNodes = node.xpath("child::chain")
        if len(chainNodes) > 0:
            chain_ids.append(chainNodes[0].attrib['id'])
        else:
            chain_ids.append('')

        taxonomyNodes = node.xpath("child::Taxonomy")
        if len(taxonomyNodes) > 0:
            chain_taxonomies.append(taxonomyNodes[0].attrib['name'])
        else:
            chain_taxonomies.append('')

        descriptionNodes = node.xpath("child::polymerDescription")
        if len(descriptionNodes) > 0:
            chain_descriptions.append(descriptionNodes[0].attrib['description'])
        else:
            chain_descriptions.append('')

    # Formats above obtained data as pandas DataFrame
    chain_df = pd.DataFrame({
        "Name":chain_names,
        "ID":chain_ids,
        "Taxonomy":chain_taxonomies,
        "Description":chain_descriptions
    })

    # Sorts DataFrame, and joins with FASTA-derived sequence data
    chain_df.sort_values("ID")
    fasta_df = get_fasta_seqs(pdb_id)
    result_df = chain_df.set_index('ID').join(fasta_df.set_index('ID'))

    return result_df

'''
This function gets a DataFrame representation of FASTA sequences obtained from
the RCSB API for a particular PDB ID, where sequences are separated by chain
Input:
    pdb_id : string  -- PDB ID to look up in API
    url    : ?string -- URL of RCSB FASTA API
Output:
    result_df : DataFrame -- pandas DataFrame of FASTA sequence + chain info
'''
def get_fasta_seqs(pdb_id, url="https://www.rcsb.org/pdb/download/downloadFastaFiles.do?structureIdList="):
    req_url = url + pdb_id + "&compressionType=uncompressed"

    response = requests.get(req_url)

    if not response.status_code == 200:
        print("Response did not receive OK HTTP Response")
        print("{}:{}".format(response.status_code, response.reason))
        return None

    result_df = fasta_to_df(response.text)
    return result_df

'''
This function converts a string containing FASTA encoded information into a
pandas DataFrame with chain ID and sequence columns
Input:
    fasta_text : string
Output:
    fasta_df   : pandas DataFrame
'''
def fasta_to_df(fasta_text):
    # Splits FASTA file on '>' (ie to distinct sequence elements)
    seq_string_list = fasta_text.strip().split(">")[1:]

    # Parses each sequence element into a chain ID and a sequence, respectively
    chain_ids = []
    sequences = []
    for seq_string in seq_string_list:
        line_list = seq_string.split("\n")
        chain_id = line_list[0].split("|")[0].split(":")[1]
        chain_ids.append(chain_id)
        sequences.append("".join(line_list[1:]))

    # Formats result as pandas DataFrame
    fasta_df = pd.DataFrame({
        "ID":chain_ids,
        "Sequence":sequences
    })
    fasta_df.sort_values("ID")

    return fasta_df
