import json
import os
from collections import defaultdict
import pytz
import re
from dateutil.parser import parse

import firebase_admin
import pygsheets
import pandas as pd
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from google.cloud.firestore_v1 import DocumentReference, CollectionReference, Query


# NOTE 切換 prod/dev
if os.environ['ENV'] == 'dev':
    main_url = 'https://interviewer-quiz-backend-hhbdnactua-de.a.run.app'
else:
    main_url = 'https://interviewer-quiz-lrqnbewzdq-de.a.run.app/'


def get_worksheet_df(spreadsheet, worksheet_title):
    df = spreadsheet.worksheet_by_title(worksheet_title).get_as_df(numerize=False)

    return df


def df_to_dict(df, new_column_names):
    df.columns = new_column_names
    dict = {'list': df.to_dict(orient='records')}

    return dict


def dict_to_firestore(dict, doc):
    doc.set(dict)
    result_dict = doc.doc_to_dict()

    return result_dict


def doc_to_dict(self):
    doc = self.get()
    doc_dict = doc.to_dict()
    return doc_dict


def query_to_dict(self):
    docs = self.stream()
    query_dict = {doc.id: doc.to_dict() for doc in docs}
    return query_dict


DocumentReference.doc_to_dict = doc_to_dict
CollectionReference.query_to_dict = query_to_dict
Query.query_to_dict = query_to_dict
