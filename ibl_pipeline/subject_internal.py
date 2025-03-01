import datajoint as dj

from ibl_pipeline import mode
from ibl_pipeline.subject_shared import Subject

if mode == "update":
    schema = dj.schema("ibl_subject")
else:
    schema = dj.schema(dj.config.get("database.prefix", "") + "ibl_subject")


@schema
class SubjectCullMethod(dj.Manual):
    definition = """
    -> Subject
    ---
    cull_method:    varchar(255)
    cull_method_ts=CURRENT_TIMESTAMP:   timestamp
    """
