import json
import string
import os
from collections import defaultdict
import pytz
import re
import ast
from dateutil.parser import parse

import firebase_admin
import pygsheets
import pandas as pd
import numpy as np
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from google.cloud.firestore_v1 import DocumentReference, CollectionReference, Query


# NOTE 切換 prod/dev
if os.environ['ENV'] == 'dev':
    main_url = 'https://survey-app-backend-hhbdnactua-de.a.run.app/'
else:
    main_url = 'https://interviewer-quiz-lrqnbewzdq-de.a.run.app/'


def get_worksheet_df(spreadsheet, worksheet_title, **kwargs):
    df = spreadsheet.worksheet_by_title(worksheet_title)\
        .get_as_df(numerize=False, include_tailing_empty=True, **kwargs)
    df = df.loc[:, df.columns != '']

    return df


def df_to_dict(df, new_column_names, index_column):
    df.columns = new_column_names
    df.index = df[index_column]
    dict = df.to_dict(orient='index')

    return dict


def dict_to_firestore(dict, doc, **kwargs):
    doc.set(dict, **kwargs)
    result_dict = doc.doc_to_dict()

    return result_dict


def doc_to_dict(self):
    doc = self.get()
    doc_dict = doc.to_dict()
    return doc_dict


def query_to_dict(self, first=False):
    docs = self.stream()

    query_dict = {}
    for doc in docs:
        if first:
            query_dict = doc.to_dict()
            break
        query_dict[doc.id] = doc.to_dict()

    return query_dict


DocumentReference.doc_to_dict = doc_to_dict
CollectionReference.query_to_dict = query_to_dict
Query.query_to_dict = query_to_dict
