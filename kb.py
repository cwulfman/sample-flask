from SPARQLWrapper import SPARQLWrapper2, JSON
from rdflib import URIRef, Literal
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel
import rdflib



class QueryResult(BaseModel):
    count: int
    data: list[dict]


class Kb():
    def __init__(self, endpoint: str) -> None:
        self.client: SPARQLWrapper2 = SPARQLWrapper2(endpoint)
        # self.client: SPARQLWrapper = SPARQLWrapper(endpoint)


    def query(self, querystring) -> QueryResult:
        self.client.setQuery(querystring)
        res = self.client.query()
        results =  [{k : v.value for k,v in result.items()}
                for result in res.bindings]

        return QueryResult(count=len(results), data=results)        


    def languages(self) -> QueryResult:
        q = """PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
select distinct ?lang ?label ?key where { 
	?lang a crm:E56_Language;
       rdfs:label ?label ;
       dcterms:identifier ?key .
}"""
        return self.query(q)
        

    def dates(self) -> QueryResult:
        q="""PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
select distinct ?date where { 
?issuetype a crm:E55_Type ;
            dcterms:identifier "issue" .
?issue lrm:P2_has_type ?issuetype .
?issue spatrem:pubDate ?date .
} ORDER BY ?date"""
        return self.query(q)


    def genres(self) -> QueryResult:
        q="""PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
select distinct ?genre where {
	?s spatrem:genre ?genre .    
} order by ?genre"""
        return self.query(q)


    def magazines(self) -> QueryResult:
        q = """PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct ?magazine ?label ?key
WHERE {
	?type dcterms:identifier "journal" .
	?magazine a lrm:F18_Serial_Work ;
    	          lrm:P2_has_type ?type ;
                  dcterms:identifier ?key ;
		  rdfs:label ?label .
}"""
        return self.query(q)


    def magazine(self, key: str) -> dict:

        q = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct ?magLabel
WHERE {{
        ?magazine dcterms:identifier "{key}" ;
                  rdfs:label ?magLabel .
}}"""
        infodata = self.query(q).data[0]
        info = { "id": key,
                 "title": infodata['magLabel']
                }

        issueq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>        
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct ?issue ?issueLabel ?issueId ?issueNo ?pubDate
WHERE {{
        ?magazine dcterms:identifier "{key}" ;
                  rdfs:label ?label ;
                  lrm:R67_has_part ?issue .
        ?issue rdfs:label ?issueLabel ;
               dcterms:identifier ?issueId ;
               spatrem:number ?issueNo ;
               spatrem:pubDate ?pubDate .

}} order by ?issueId"""

        issues = []
        for i in self.query(issueq).data:
            issue = {
                "id" : i['issueId'],
                "label" : i['issueLabel'],
                "number": i['issueNo'],
                "pubDate" : i['pubDate'],
            }
            issues.append(issue)

        return { "info" : info, "issues": issues }

    def issues(self, mag_key: str) -> QueryResult:
        q = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>        
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct *
WHERE {{
        ?magazine dcterms:identifier "{mag_key}" ;
                  rdfs:label ?label ;
                  lrm:R67_has_part ?issue .
        ?issue rdfs:label ?issueLabel ;
               dcterms:identifier ?id ;
               spatrem:number ?no ;
               spatrem:pubDate ?pubDate .

}}"""
        return self.query(q)

    def issue(self, issue_key:str):

        infoq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>        
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct *
WHERE {{
        ?issue dcterms:identifier "{issue_key}" ;
                  lrm:R67i_is_part_of ?magazine ;
                  rdfs:label ?issueLabel ;
                  spatrem:number ?issueNo ;
                  spatrem:pubDate ?pubDate .
        ?magazine rdfs:label ?magLabel ;
                  dcterms:identifier ?magId .
}}"""

        constituentq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>        
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct ?title ?langLabel ?translator ?name ?genre ?author ?authorName ?olangLabel
WHERE {{
        ?issue dcterms:identifier "{issue_key}" .
        ?constituent lrm:R67i_is_part_of ?issue .
        
        ?constituent rdfs:label ?label ;
               lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator ;
               crm:P1_is_identified_by / lrm:R33_has_string ?title ;
               lrm:R3i_is_realised_by / crm:P72_has_language ?tlang ;
               lrm:R68_is_inspired_by ?original ;
               spatrem:genre ?genre .

        ?original lrm:R16i_was_created_by / crm:P14_carried_out_by ?author ;
                  lrm:R3i_is_realised_by / crm:P72_has_language ?olang .
        ?author rdfs:label ?authorName .


        ?tlang rdfs:label ?langLabel .
        ?olang rdfs:label ?olangLabel .
        ?translator rdfs:label ?name .

}}"""
        info = self.query(infoq).data[0]

        constituentdata = self.query(constituentq).data
        constituents = []
        for data in constituentdata:
            c = { "title": data['title'],
                  "language": data['langLabel'],
                  "olanguage": data['olangLabel'],
                  "translator": data['translator'],
                  "name": data['name'],
                  "author": data['author'],
                  "authorName": data['authorName'],
                  "genre": data['genre'] }
            constituents.append(c)
        result = {}
        result['info'] = { "label": info["issueLabel"],
                            "magazine": info["magazine"],
                            "magLabel": info["magLabel"],
                            "magId": info["magId"],
                           "number": info["issueNo"],
                            "pubDate": info["pubDate"]}
        result['constituents'] = constituents
        return result

    def constituents(self, issue_key: str) -> QueryResult:
        q = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>        
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct *
WHERE {{
        ?issue dcterms:identifier "{issue_key}" ;
               lrm:R67_has_part ?constituent .
        ?constituent rdfs:label ?issueLabel ;
               lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator ;
               lrm:R3i_is_realised_by / crm:P72_has_language ?tlang .
        ?tlang rdfs:label ?langLabel .
        ?translator rdfs:label ?name .
}}"""
        return self.query(q)

    def constituent(self, con_id: str) -> QueryResult:
        q = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT distinct *
WHERE {{
        spatrem:{con_id} rdfs:label ?label ;
                   lrm:R67i_is_part_of ?issue ;
                   lrm:R68_is_inspired_by ?original ;
                   spatrem:genre ?genre ;
                   lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator ;
                   crm:P1_is_identified_by / lrm:R33_has_string ?title ;
                   lrm:R3i_is_realised_by / crm:P72_has_language ?tlang .
        ?tlang rdfs:label ?langLabel .
        ?original lrm:R16i_was_created_by / crm:P14_carried_out_by ?author ;
                  lrm:R3i_is_realised_by / crm:P72_has_language ?olang .
        ?author rdfs:label ?authorName .
        ?translator rdfs:label ?translatorName .
        ?olang rdfs:label ?olangLabel .
        ?issue rdfs:label ?issue_label ;
           dcterms:identifier ?issue_id ;
           spatrem:pubDate ?pubDate .

}}"""
        return self.query(q)


    def construct_translation_query(self, kwargs: dict) -> str:
        
        q: str = """PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>        
select distinct * where {
	?original lrm:R68_is_inspiration_for ?translation .
    ?original lrm:R16i_was_created_by / crm:P14_carried_out_by ?author .
    ?translation lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator .
    ?original lrm:R3i_is_realised_by / crm:P72_has_language ?olang .
    ?translation lrm:R3i_is_realised_by / crm:P72_has_language ?tlang .
        
    """
        if kwargs['sl'] and kwargs['sl'] != 'any':
            q += f"FILTER(?olang =  <{kwargs['sl']}> )\n"

        if kwargs['tl'] and kwargs['tl'] != 'any':
            q += f"FILTER(?tlang =  <{kwargs['tl']}> )\n"

        q += "?translation spatrem:genre ?genre .\n"

        if kwargs["genre"]  and kwargs['genre'] != 'any':
            q += f"FILTER(?genre =  '{kwargs['genre']}' )\n"


        q += "?issue  spatrem:pubDate ?pubDate .\n"


        if kwargs["after_date"] and kwargs['after_date'] != 'any':
            q += f"FILTER(xsd:integer(?pubDate) > {kwargs['after_date']})\n"

        if kwargs["before_date"] and kwargs['after_date'] != 'any':
            q += f"FILTER(xsd:integer(?pubDate) < {kwargs['before_date']})\n"


        q += """?translation lrm:R67i_is_part_of ?issue .
        ?issue lrm:R67i_is_part_of ?magazine .
        """

        if kwargs["magazine"] and kwargs['magazine'] != 'any':
            q += f"FILTER(?magazine = <{kwargs['magazine']}>)\n"


        q += """?translation crm:P1_is_identified_by / lrm:R33_has_string ?title . 
    ?issue rdfs:label ?issue_label ;
           dcterms:identifier ?issue_id .
    ?magazine rdfs:label ?magazine_label ;
           dcterms:identifier ?magazine_id .
    ?author rdfs:label ?author_name .
    ?translator rdfs:label ?translator_name .
    ?olang rdfs:label ?olangLabel .
    ?tlang rdfs:label ?tlangLabel .
    """
        q += "}"

        if "offset" in kwargs:
            q += f"OFFSET {kwargs['offset']} "
        
        if "limit" in kwargs:
            q += f"LIMIT {kwargs['limit']} "
        
        return q





    def translations(self, page: int, page_size: int, kwargs: dict = {}) -> QueryResult:
        kwargs["limit"] = page_size
        offset = page - 1
        if offset <= 0:
            offset = 0
        kwargs["offset"] = offset * page_size
        
        query = self.construct_translation_query(kwargs)
        return self.query(query)


    def translators(self) -> QueryResult:
        query = """PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>

SELECT distinct ?translator ?label ?birthDate  ?deathDate ?gender ?nationality ?language_area WHERE {
	?original lrm:R68_is_inspiration_for ?translation .
    ?translation lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator .
    ?translator rdfs:label ?label . 	
    FILTER(?label != "Anon.")
    OPTIONAL { ?translator spatrem:year_birth ?birthDate .}
    OPTIONAL { ?translator spatrem:year_death ?deathDate .}
    OPTIONAL { ?translator spatrem:gender ?gender .}
    OPTIONAL { ?translator spatrem:nationality ?nationality .}
    OPTIONAL { ?translator spatrem:language_area ?language_area .}
} ORDER BY ?label"""
        return self.query(query)
    
    def translator(self, uriref):
        infoq = f"""PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
PREFIX person: <http://spacesoftranslation.org/ns/people/> 

SELECT distinct ?label ?birthDate  ?deathDate ?gender ?nationality ?language_area WHERE {{
    person:{uriref} rdfs:label ?label . 	
    OPTIONAL {{ person:{uriref} spatrem:year_birth ?birthDate .}}
    OPTIONAL {{ person:{uriref} spatrem:year_death ?deathDate .}}
    OPTIONAL {{ person:{uriref} spatrem:gender ?gender .}}
    OPTIONAL {{ person:{uriref} spatrem:nationality ?nationality .}}
    OPTIONAL {{ person:{uriref} spatrem:language_area ?language_area .}}
}} ORDER BY ?label"""

        infodata = self.query(infoq).data[0]
        info = { "label" : infodata.get('label'),
                 "birthDate" : infodata.get('birthDate'),
                 "deathDate" : infodata.get('deathDate'),
                 "gender" : infodata.get('gender'),
                 "nationality" : infodata.get('nationality'),
                 "language_area" : infodata.get('language_area')
        }

            
        
        worksq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX person: <http://spacesoftranslation.org/ns/people/> 
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
select distinct * where {{
        ?translation lrm:R16i_was_created_by / crm:P14_carried_out_by person:{uriref} ;
                     crm:P1_is_identified_by / lrm:R33_has_string ?title ;
                     lrm:R3i_is_realised_by / crm:P72_has_language ?tlang ;
                     lrm:R67i_is_part_of ?issue .

        ?tlang rdfs:label ?language .
        ?issue rdfs:label ?issueLabel ;
           dcterms:identifier ?issueId ;
           spatrem:pubDate ?pubDate .

       }} ORDER BY ?title """


        works = []
        for data in self.query(worksq).data:
            work = {
                "title": data['title'],
                "language": data['language'],
                "issue": data["issue"],
                "issueId": data['issueId'],
                "issueLabel": data["issueLabel"],
                "pubDate": data["pubDate"],
                }            
            works.append(work)

        namesq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
        PREFIX person: <http://spacesoftranslation.org/ns/people/> 
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
select distinct ?name where {{
        person:{uriref} crm:P1_is_identified_by / lrm:R33_has_string ?name .
        }} """

        names = [n['name'] for n in self.query(namesq).data]

        return { "works": works, "names": names, "info": info }
        

    def author(self, uriref):
        worksq = f"""PREFIX lrm: <http://iflastandards.info/ns/lrm/lrmer/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX person: <http://spacesoftranslation.org/ns/people/> 
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX spatrem: <http://spacesoftranslation.org/ns/spatrem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select distinct * where {{
        person:{uriref} rdfs:label ?name .
        ?original lrm:R16i_was_created_by / crm:P14_carried_out_by person:{uriref} ;
                  lrm:R3i_is_realised_by / crm:P72_has_language ?olang .
    
        ?translation lrm:R68_is_inspired_by ?original ;
                     lrm:R16i_was_created_by / crm:P14_carried_out_by ?translator ;
                     rdfs:label ?title ;
                     lrm:R3i_is_realised_by / crm:P72_has_language ?tlang ;
                     lrm:R67i_is_part_of ?issue .

        ?tlang rdfs:label ?tlanguage .
    	?translator rdfs:label ?tname .
        ?olang rdfs:label ?olanguage .
        ?issue rdfs:label ?issueLabel ;
           dcterms:identifier ?issueId ;
           spatrem:pubDate ?pubDate .

        }}"""
        return self.query(worksq)
