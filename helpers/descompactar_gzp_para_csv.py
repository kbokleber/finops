import gzip
import csv


def transform_gz_to_dict(data_content: bytes):
    """Descompacta o arquivo gz para csv"""
    content = gzip.decompress(data_content)
    return csv.DictReader(content.decode().splitlines(), delimiter=',')