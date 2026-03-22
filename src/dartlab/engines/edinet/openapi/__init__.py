"""EDINET OpenAPI facade.

from dartlab.engines.edinet.openapi import EdinetClient

client = EdinetClient()
docs = client.listDocuments("2024-06-01")
client.downloadDocument(docs[0]["docID"], savePath)
"""

from dartlab.engines.edinet.openapi.client import EdinetApiError, EdinetClient

__all__ = ["EdinetClient", "EdinetApiError"]
