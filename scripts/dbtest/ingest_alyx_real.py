"""
This script copies tuples in the shadow tables into the real tables for alyx.
"""

import datajoint as dj
from table_names import *

from ibl_pipeline import acquisition, action, reference, subject
from ibl_pipeline.ingest import acquisition as acquisition_ingest
from ibl_pipeline.ingest import action as action_ingest
from ibl_pipeline.ingest import reference as reference_ingest
from ibl_pipeline.ingest import subject as subject_ingest
from ibl_pipeline.ingest.ingest_utils import copy_table

if __name__ == "__main__":

    mods = [
        [reference, reference_ingest, REF_TABLES],
        [subject, subject_ingest, SUBJECT_TABLES],
        [action, action_ingest, ACTION_TABLES],
        [acquisition, acquisition_ingest, ACQUISITION_TABLES],
        [data, data_ingest, DATA_TABLES],
    ]

    for (target, source, table_list) in mods:
        for table in table_list:
            print(table)
            copy_table(target, source, table)
