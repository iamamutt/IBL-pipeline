from ibl_pipeline import mode
from ibl_pipeline.behavior_shared import *

if mode != "public":
    from ibl_pipeline.behavior_internal import *
