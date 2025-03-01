import datajoint as dj
from tqdm import tqdm

from ibl_pipeline.ingest import acquisition, action, alyxraw, data, ephys, subject

if __name__ == "__main__":

    with dj.config(safemode=False):
        # delete alyxraw for data.filerecord if exists = 0
        print("Deleting alyxraw entries corresponding to file records...")
        file_record_fields = (
            alyxraw.AlyxRaw.Field & 'fname = "exists"' & 'fvalue = "False"'
        )

        for key in tqdm(file_record_fields):
            (alyxraw.AlyxRaw.Field & key).delete_quick()

        # delete water tables and related alyxraw entries
        print("Deleting alyxraw entries of shadow weighing and water tables...")
        (
            alyxraw.AlyxRaw
            & 'model in ("actions.weighing", "actions.waterrestriction", \
            "actions.wateradministration")'
        ).delete()

        # delete the lab, user, user_history, death_date,
        # and caging field of the subject
        print("Deleting subject fields lab, user, user_hisotry and death date...")
        subject_fields = (
            alyxraw.AlyxRaw.Field
            & (alyxraw.AlyxRaw & 'model="subjects.subject"')
            & 'fname in ("projects", "sex", "birth_date", "source", \
                    "strain", "line", "lab", \
                    "death_date", "responsible_user", "json")'
        )
        subject_fields.delete_quick()

        print("Deleting project records...")
        projects = alyxraw.AlyxRaw & 'model="subjects.project"'
        projects.delete()

        session_project = (
            alyxraw.AlyxRaw.Field
            & (alyxraw.AlyxRaw & 'model="actions.session"')
            & 'fname in ("project")'
        )
        session_project.delete_quick()

        print("Deleting trajectories estimates time stamp...")
        (
            alyxraw.AlyxRaw.Field
            & (alyxraw.AlyxRaw & 'model="experiments.trajectoryestimate"')
            & 'fname="datetime"'
        ).delete(force=True)

        # delete some shadow membership tables
        print("Deleting shadow membership tables...")
        subject.Death.delete()
        action.WaterRestrictionProcedure.delete()
        action.WaterRestrictionUser.delete()
        acquisition.WaterAdministrationSession.delete()
        subject.SubjectLab.delete()
        subject.SubjectProject.delete()
        acquisition.SessionProject.delete()
