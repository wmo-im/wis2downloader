###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################
# Original source:
# https://github.com/wmo-im/wis2box/blob/main/wis2box-management/wis2box/log.py
###############################################################################

from datetime import datetime as dt
import logging
from pathlib import Path
import sys

LOGGER = logging.getLogger(__name__)


def setup_logger(loglevel: str = 'ERROR', save=False, log_path = None) -> None:
    """
    Setup logger

    :param loglevel: `str`, logging level
    :param logfile: `str`, logging output file

    :returns: `None` (creates logging instance)
    """

    log_format = \
        '[%(asctime)s] %(levelname)s - %(message)s'
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    loglevels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET,
    }

    loglevel = loglevels[loglevel]

    args = {
        'level': loglevel,
        'datefmt': date_format,
        'format': log_format,
    }

    if save:
        # set path
        current_time = dt.now().strftime("%Y%m%d_%H%M%S")
        if log_path is None:
            log_path = "."
        logfile = 'wis2downloader' + current_time + '.log'
        logfile = Path(log_path) / logfile
        logfile.parent.mkdir(parents=True, exist_ok=True)
        args['filename'] = logfile
    else:
        args['stream'] = sys.stdout

    logging.basicConfig(**args)

    LOGGER.debug('Logging initialized')
