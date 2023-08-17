from dask import dataframe as dd
import cv2
import boto3
from botocore.config import Config
import os
import pandas as pd
import dask.delayed as dl
import numpy as np
import dask
from dask.distributed import Client


import config


def get_dask_client():
    return Client(address=config.DASK_SCHEDULER_URL)