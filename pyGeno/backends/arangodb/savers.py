from ..backend_abs import GenomeSaver_ABS
from pyGeno.configuration import system_message
from .objects import schemas

class GenomeSaver(GenomeSaver_ABS):
    """
    Saves genome into database
    """
    def __init__(self, database_configuration):
        super(GenomeSaver, self).__init__(database_configuration)
        self.db = self.database_configuration.database
        self.accepted_contigs = ["Cds", "Ccds", "Exon", "Start_codon", "Stop_codon", "Utr", "Gene", "Transcript"]

    def init_db(self):
        for col1 in schemas.ALL_COLLECTIONS:
            colname = col1.__name__
            if colname not in self.db:
                self.db.createCollection(colname)
            else :
                print("TRUNCATING (temporary for tests, should be removed)", colname)
                self.db[colname].truncate()
            for col2 in schemas.ALL_COLLECTIONS:
                if not col2 is col1 :
                    edges = self.database_configuration.get_link_collection_name(colname, col2.__name__)
                    print("TRUNCATING (temporary for tests, should be removed)", edges)
                    try:
                        self.db[edges].truncate()
                    except:
                        print("\tNot TRUNCATABLE")

    def create_objects(self):
        for colname, objs in self.data.items():
            for key, obj in objs.items():
                try :
                    doc = self.db[colname][key]
                except :
                    doc = self.db[colname].createDocument()
                    doc["_key"] = key
                    doc["unique_id"] = key
                doc.set(obj)
                if colname in self.accepted_contigs:
                    doc["contig"] = self.get_subsequence(doc["seqname"], doc["start"], doc["end"])
                doc.save()

    def create_links(self):
        def _get_collection(from_type, to_type):
            name = self.database_configuration.get_link_collection_name(from_type, to_type)
            try :
                return self.db[name]
            except :
                return self.db.createCollection(name=name, className="Edges")

        for link in self.links:
            from_key = "%s/%s" % (link["from"]["type"], link["from"]["id"])
            to_key = "%s/%s" % (link["to"]["type"], link["to"]["id"])
            edge = _get_collection(link["from"]["type"], link["to"]["type"]).createEdge()
            edge["_from"] = from_key
            edge["_to"] = to_key
            edge.save()

    def save(self) :
        self.init_db()
        self.create_objects()
        self.create_links()
