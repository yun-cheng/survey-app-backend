from common.common import *


def get_answer_value(row):
    if row['type'] == 'string':
        return row['stringValue']
    elif row['type'] == 'choice':
        return row['choiceValue']
    elif row['type'] == 'int':
        return row['intValue']
    elif row['type'] == 'choiceList':
        return row['choiceListValue']
    else:
        return None


def wide_question_id(row):
    question_id = row['questionId']
    if row['moduleType'] == 'visitReport':
        question_id = f"{row['moduleType']}__{row['idInGroup']}__{question_id}"
    else:
        question_id = f"{row['moduleType']}__{question_id}"

    if row['isNote']:
        question_id += '__note_' + str(row['noteOf'])

    return question_id


def public_audio_link(self, row):
    responseId = row['responseId']
    audio_link = ''
    if row['moduleType'] == 'main':
        blob = self.bucket.blob(f'audio/{responseId}/{responseId}.m4a')
        try:
            if blob.exists():
                blob.make_public()
                audio_link = blob.public_url
        except:
            audio_link = ''

    return audio_link
