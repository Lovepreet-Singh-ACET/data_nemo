class MongoDB:
    def __init__(self, client, db_name, collection_name):
        self.client = client
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_document(self, document):
        result = self.collection.insert_one(document)
        return result.inserted_id

    def find_documents(self, query):
        return self.collection.find(query)

    def update_documents(self, query, new_values):
        result = self.collection.update_many(query, {'$set': new_values})
        return result.modified_count

    def delete_documents(self, query):
        result = self.collection.delete_many(query)
        return result.deleted_count