import uuid

import datajoint as dj
from datajoint.errors import DataJointError

from ibl_pipeline.ingest import ShadowIngestionError, alyxraw
from ibl_pipeline.ingest import get_raw_field as grf
from ibl_pipeline.ingest import reference, subject

schema = dj.schema(dj.config.get("database.prefix", "") + "ibl_ingest_action")


@schema
class ProcedureType(dj.Computed):
    definition = """
    (procedure_type_uuid) -> alyxraw.AlyxRaw
    ---
    procedure_type_name:                varchar(255)
    procedure_type_description=null:    varchar(1024)
    proceduretype_ts=CURRENT_TIMESTAMP:   timestamp
    """

    key_source = (alyxraw.AlyxRaw & 'model="actions.proceduretype"').proj(
        procedure_type_uuid="uuid"
    )

    def make(self, key):
        key_pt = key.copy()
        key["uuid"] = key["procedure_type_uuid"]
        key_pt["procedure_type_name"] = grf(key, "name")

        description = grf(key, "description")
        if description != "None":
            key_pt["procedure_type_description"] = description

        self.insert1(key_pt)


@schema
class Weighing(dj.Computed):
    # <class 'actions.models.Weighing'>
    definition = """
    (weigh_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:       uuid
    weighing_time:		datetime		# date time
    weight:	            float			# weight in grams
    weighing_user=null: varchar(255)
    weighing_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model="actions.weighing"').proj(weigh_uuid="uuid")

    def make(self, key):
        key_weigh = key.copy()
        key["uuid"] = key["weigh_uuid"]
        key_weigh["subject_uuid"] = uuid.UUID(grf(key, "subject"))

        if not len(subject.Subject & key_weigh):
            raise ShadowIngestionError(
                "subject {} is not in the Subject table".format(
                    key_weigh["subject_uuid"]
                )
            )

        key_weigh["weighing_time"] = grf(key, "date_time")

        weight = grf(key, "weight")
        if weight != "None":
            key_weigh["weight"] = float(weight)

        user_uuid = grf(key, "user")
        if user_uuid != "None":
            key_weigh["weighing_user"] = (
                reference.LabMember & dict(user_uuid=uuid.UUID(user_uuid))
            ).fetch1("user_name")

        self.insert1(key_weigh)


@schema
class WaterType(dj.Computed):
    definition = """
    (watertype_uuid) -> alyxraw.AlyxRaw
    ---
    watertype_name:     varchar(255)
    watertype_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model = "actions.watertype"').proj(
        watertype_uuid="uuid"
    )

    def make(self, key):
        key_type = key.copy()
        key["uuid"] = key["watertype_uuid"]

        key_type["watertype_name"] = grf(key, "name")
        self.insert1(key_type)


@schema
class WaterAdministration(dj.Computed):
    # <class 'actions.models.WaterAdministration'>
    definition = """
    (wateradmin_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:                   uuid
    administration_user=null:       varchar(255)
    administration_time:	        datetime		# date time
    water_administered=null:		float			# water administered
    watertype_name:		            varchar(255)    # type of water
    adlib:                          boolean
    wateradministration_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (
        alyxraw.AlyxRaw
        & alyxraw.AlyxRaw.Field
        & 'model = "actions.wateradministration"'
    ).proj(wateradmin_uuid="uuid")

    def make(self, key):
        key_wa = key.copy()
        key["uuid"] = key["wateradmin_uuid"]

        key_wa["subject_uuid"] = uuid.UUID(grf(key, "subject"))

        if not len(subject.Subject & key_wa):
            raise ShadowIngestionError(
                "subject {} is not in the Subject table".format(key_wa["subject_uuid"])
            )

        key_wa["administration_time"] = grf(key, "date_time")
        wa = grf(key, "water_administered")
        if wa != "None":
            key_wa["water_administered"] = wa

        water_type = grf(key, "water_type")
        key_wa["watertype_name"] = (
            WaterType & dict(watertype_uuid=uuid.UUID(water_type))
        ).fetch1("watertype_name")

        user_uuid = grf(key, "user")
        if user_uuid != "None":
            key_wa["administration_user"] = (
                reference.LabMember & dict(user_uuid=uuid.UUID(user_uuid))
            ).fetch1("user_name")

        key_wa["adlib"] = grf(key, "adlib") == "True"

        self.insert1(key_wa)


@schema
class WaterRestriction(dj.Computed):
    # <class 'actions.models.WaterRestriction'>
    definition = """
    (restriction_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:               uuid
    restriction_start_time:     datetime	# start time
    restriction_end_time=null:  datetime	# end time
    restriction_narrative=null: varchar(1024)
    reference_weight:           float
    restriction_lab=null:       varchar(255)
    restriction_location=null:  varchar(255)
    waterrestriction_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model = "actions.waterrestriction"').proj(
        restriction_uuid="uuid"
    )

    def make(self, key):
        key_res = key.copy()
        key["uuid"] = key["restriction_uuid"]

        key_res["subject_uuid"] = uuid.UUID(grf(key, "subject"))
        if not (subject.Subject & key_res):
            raise ShadowIngestionError(
                "subject {} is not in the Subject table".format(key_res["subject_uuid"])
            )

        key_res["restriction_start_time"] = grf(key, "start_time")

        end_time = grf(key, "end_time")
        if end_time != "None":
            key_res["restriction_end_time"] = end_time

        narrative = grf(key, "narrative")
        if narrative and narrative != "None":
            key_res["restriction_narrative"] = narrative

        location_uuid = grf(key, "location")
        if location_uuid != "None":
            key_res["restriction_lab"], key_res["restriction_location"] = (
                reference.LabLocation & dict(location_uuid=uuid.UUID(location_uuid))
            ).fetch1("lab_name", "location_name")

        key_res["reference_weight"] = grf(key, "reference_weight")

        self.insert1(key_res)


@schema
class WaterRestrictionUser(dj.Manual):
    definition = """
    subject_uuid:           uuid
    restriction_start_time: datetime
    user_name:              varchar(255)
    ---
    waterrestrictionuser_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class WaterRestrictionProcedure(dj.Manual):
    definition = """
    subject_uuid:           uuid
    restriction_start_time: varchar(255)
    procedure_type_name:    varchar(255)
    ---
    waterrestrictionprocedure_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class Surgery(dj.Computed):
    # <class 'actions.models.Surgery'>
    definition = """
    (surgery_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:               uuid
    surgery_lab=null:           varchar(255)    # lab for sugery
    surgery_location=null:      varchar(255)    # foreign key inherited from reference.LabLocation
    surgery_start_time:	        datetime        # surgery start time
    surgery_end_time=null:	    datetime        # surgery end time
    surgery_outcome_type:		enum('None', 'a', 'n', 'r')	    # outcome type
    surgery_narrative=null:     varchar(2048)    	# narrative
    surgery_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model = "actions.surgery"').proj(
        surgery_uuid="uuid"
    )

    def make(self, key):
        key_surgery = key.copy()
        key["uuid"] = key["surgery_uuid"]

        key_surgery["subject_uuid"] = uuid.UUID(grf(key, "subject"))
        if not len(subject.Subject & key_surgery):
            raise ShadowIngestionError(
                "Subject {} is not in the table subject.Subject".format(
                    key_surgery["subject_uuid"]
                )
            )

        key_surgery["surgery_start_time"] = grf(key, "start_time")

        end_time = grf(key, "end_time")
        if end_time != "None":
            key_surgery["surgery_end_time"] = end_time

        key_surgery["surgery_outcome_type"] = grf(key, "outcome_type")

        narrative = grf(key, "narrative")
        if narrative != "None":
            key_surgery["surgery_narrative"] = narrative

        location_uuid = grf(key, "location")
        if location_uuid != "None":
            key_surgery["surgery_lab"], key_surgery["surgery_location"] = (
                reference.LabLocation & dict(location_uuid=uuid.UUID(location_uuid))
            ).fetch1("lab_name", "location_name")

        self.insert1(key_surgery)


@schema
class SurgeryUser(dj.Manual):
    definition = """
    subject_uuid:       uuid
    surgery_start_time: datetime
    user_name:          varchar(255)
    ---
    surgeryuser_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class SurgeryProcedure(dj.Manual):
    definition = """
    subject_uuid:           uuid
    surgery_start_time:     datetime
    procedure_type_name:    varchar(255)
    surgeryprocedure_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class VirusInjection(dj.Computed):
    # <class 'actions.models.VirusInjection'>
    definition = """
    (virus_injection_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:           uuid
    injection_time:		    datetime        	# injection time
    injection_volume:		float   		    # injection volume
    rate_of_injection:		float               # rate of injection
    injection_type:		    varchar(255)    	# injection type
    virusinjection_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = alyxraw.AlyxRaw & 'model = "actions.virusinjection"'
    # data missing


@schema
class OtherAction(dj.Computed):
    # <class 'actions.models.OtherAction'>
    definition = """
    (other_action_uuid) -> alyxraw.AlyxRaw
    ---
    subject_uuid:               uuid
    other_action_start_time:    datetime	    # start time
    other_action_end_time=null: datetime	    # end time
    other_action_lab=null:      varchar(255)
    other_action_location=null: varchar(255)    # refer to reference.Location
    otheraction_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model = "actions.otheraction"').proj(
        other_action_uuid="uuid"
    )

    def make(self, key):
        key_other = key.copy()
        key["uuid"] = key["other_action_uuid"]
        key_other["subject_uuid"] = uuid.UUID(grf(key, "subject"))

        if not len(subject.Subject & key_other):
            raise ShadowIngestionError(
                "subject {} is not in the table subject.Subject".format(
                    key_other["subject_uuid"]
                )
            )

        key_other["other_action_start_time"] = grf(key, "start_time")

        end_time = grf(key, "end_time")
        if end_time != "None":
            key_other["other_action_end_time"] = end_time

        location_uuid = grf(key, "location")
        if location_uuid != "None":
            key_other["other_action_lab"], key_other["other_action_location"] = (
                reference.LabLocation & dict(location_uuid=uuid.UUID(location_uuid))
            ).fetch1("lab_name", "location_name")

        self.insert1(key_other)


@schema
class OtherActionUser(dj.Manual):
    # <class 'actions.models.OtherAction'>
    definition = """
    subject_uuid:               uuid
    other_action_start_time:    datetime	    # start time
    user_name:        varchar(255)
    otheractionuser_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class OtherActionProcedure(dj.Manual):
    # <class 'actions.models.OtherAction'>
    definition = """
    subject_uuid:               uuid
    other_action_start_time:    datetime	    # start time
    procedure_type_name:        varchar(255)
    otheractionprocedure_ts=CURRENT_TIMESTAMP:   timestamp
    """


@schema
class CullMethod(dj.Computed):
    definition = """
    -> alyxraw.AlyxRaw.proj(cull_method_uuid='uuid')
    ---
    cull_method:    varchar(64)
    cull_method_description='':    varchar(255)
    cull_method_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model="actions.cullmethod"').proj(
        cull_method_uuid="uuid"
    )

    def make(self, key):
        key_cm = key.copy()
        key["uuid"] = key["cull_method_uuid"]
        key_cm["cull_method"] = grf(key, "name")

        description = grf(key, "description")
        if description != "None":
            key_cm["cull_method_description"] = description

        self.insert1(key_cm)


@schema
class CullReason(dj.Computed):
    definition = """
    -> alyxraw.AlyxRaw.proj(cull_reason_uuid='uuid')
    ---
    cull_reason:    varchar(64)
    cull_reason_description='':    varchar(255)
    cull_reason_ts=CURRENT_TIMESTAMP:   timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model="actions.cullreason"').proj(
        cull_reason_uuid="uuid"
    )

    def make(self, key):
        key_cr = key.copy()
        key["uuid"] = key["cull_reason_uuid"]
        key_cr["cull_reason"] = grf(key, "name")

        description = grf(key, "description")
        if description != "None":
            key_cr["cull_reason_description"] = description

        self.insert1(key_cr)


@schema
class Cull(dj.Computed):
    definition = """
    -> alyxraw.AlyxRaw.proj(cull_uuid='uuid')
    ---
    subject_uuid:                   uuid
    cull_date:                      date
    cull_user=null:                 varchar(255)
    cull_reason=null:               varchar(64)
    cull_method=null:               varchar(64)
    cull_description='':            varchar(1024)
    cull_ts=CURRENT_TIMESTAMP:      timestamp
    """
    key_source = (alyxraw.AlyxRaw & 'model = "actions.cull"').proj(cull_uuid="uuid")

    def make(self, key):
        key_cull = key.copy()
        key["uuid"] = key["cull_uuid"]

        key_cull["subject_uuid"] = uuid.UUID(grf(key, "subject"))
        if not len(subject.Subject & key_cull):
            raise ShadowIngestionError(
                "Subject {} is not in the table subject.Subject".format(
                    key_cull["subject_uuid"]
                )
            )

        user_uuid = grf(key, "user")
        if user_uuid != "None":
            key_cull["cull_user"] = (
                reference.LabMember & {"user_uuid": user_uuid}
            ).fetch1("user_name")

        cull_method_uuid = grf(key, "cull_method")
        if cull_method_uuid != "None":
            key_cull["cull_method"] = (
                CullMethod & {"cull_method_uuid": cull_method_uuid}
            ).fetch1("cull_method")

        cull_reason_uuid = grf(key, "cull_reason")
        if cull_reason_uuid != "None":
            key_cull["cull_reason"] = (
                CullReason & {"cull_reason_uuid": cull_reason_uuid}
            ).fetch1("cull_reason")

        description = grf(key, "description")
        if description != "None":
            key_cull["cull_description"] = description

        key_cull["cull_date"] = grf(key, "date")

        self.insert1(key_cull)
