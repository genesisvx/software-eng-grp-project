from SPARQLWrapper import SPARQLWrapper, JSON

agrovoc_endpoint = "http://agrovoc.uniroma2.it:3030/agrovoc/sparql"

def getConceptTag(prefLabel):
    print("doing tagging for {}\n".format(prefLabel))
    sparql = SPARQLWrapper(agrovoc_endpoint)
    sparql.setQuery("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX agro: <http://aims.fao.org/aos/agrontology#>
        SELECT ?concept
        WHERE {{
            ?concept skos:prefLabel "{}"@en
        }}
    """.format(prefLabel))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

