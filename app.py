
from common.load_credentials import *
from team import Team
from project.project import Project
# from quiz import Quiz
from survey.survey import Survey
from survey_module import SurveyModule

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    # H_1 parameters
    action = request.args.get('action', '')
    on = request.args.get('on', '')
    gsid = request.args.get('gsid', '')
    project_gsid = request.args.get('project_gsid', '')
    interviewer_id = request.args.get('interviewer_id', '')
    # TODO
    email = request.args.get('email', '')

    # H_2 credentials
    # HIGHLIGHT 需開啟 Google Sheets API、Google Drive API
    gsheets = load_gsheets()
    db = load_firestore()
    bucket = load_storage()

    # TEST 測試用
    # on = 'survey'
    # gsid = '1EZyy8mtp7Ce-Q09p_L6lHxNkw444fQDUDmkDzb2L2vw'
    # action = 'update'

    # on = 'project'
    # gsid = '1MYKhzY9g7AZHxbIUN8-oUCPEEXUWHRy4U-1Pe2pbRRE'
    # action = 'update'

    # gsid = '1XdDOKK8i1fPpw1UnmTQGydYDSsxZj-OvuvYCdBDXmZY'
    # gsid = '1sC26FL_R-zPWm9EMGaNEFgU0ClDJFeb8CqaUTCPgA9U'


    # H_3 action
    if on == 'team':
        target = Team(gsheets=gsheets, db=db)
    elif on == 'project':
        target = Project(gsheets=gsheets, db=db)
    # elif on == 'quiz':
    #     target = Quiz(gsheets=gsheets, db=db)
    elif on == 'survey':
        target = Survey(gsheets=gsheets, db=db, bucket=bucket)
    elif on == 'module':
        target = SurveyModule(gsheets=gsheets, db=db)
    elif on == 'recode_module':
        target = SurveyModule(gsheets=gsheets, db=db, module='recode')
    # elif on == 'samplingWithinHousehold_module':
    #     target = SurveyModule(gsheets=gsheets, db=db, module='samplingWithinHousehold')

    if on:
        if action == 'create' and email:
            return target.create(email=email)

        elif action == 'update' and gsid:
            return target.update(gsid=gsid)

        elif action == 'delete' and gsid:
            return target.delete(gsid=gsid)

        # elif on == 'survey' and action == 'update_result' and gsid and project_gsid and interviewer_id:
        #     return target.update_result(gsid=gsid, project_gsid=project_gsid, interviewer_id=interviewer_id)

        # elif on == 'survey' and action == 'delete_result' and gsid:
        #     return target.delete_result(gsid=gsid)

        # elif on == 'quiz' and action == 'update_result' and gsid and project_gsid and interviewer_id:
        #     return target.update_result(gsid=gsid, project_gsid=project_gsid, interviewer_id=interviewer_id)
        #
        # elif on == 'quiz' and action == 'delete_result' and gsid:
        #     return target.delete_result(gsid=gsid)

    return '失敗了....'


if __name__ == '__main__':
    app.run(host='localhost', port=80, debug=True, use_reloader=False)
