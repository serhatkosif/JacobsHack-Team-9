# SPDX-FileCopyrightText: 2022 Earth System Data Exploration (ESDE), Jülich Supercomputing Center (JSC)
#
# SPDX-License-Identifier: MIT

"""
Basic class for Rasdaman queries.
"""

__author__ = "Michael Langguth"
__date__ = "2022-03-03"

# import modules
import io
import time
import datetime as dt
import requests
from urllib.error import HTTPError
import numpy as np
import xarray as xr
import pandas as pd


class Rasdaman_Query(object):
    cls_name = "Rasdaman_Query"

    def __init__(self, service_endpoint="http://zam10213.zam.kfa-juelich.de/rasdaman/ows"):

        self.service_endpoint = service_endpoint
        _ = self.check_endpoint()
        self.query_history = {}
        self.nquery = 0

    def check_endpoint(self, wait_time: int = 10):
        """
        Checks if service endpoint can be reached.
        :param wait_time: Maximum wait time to get response from service endpoint.
        :return bool: True when connection was successful
        """
        method = Rasdaman_Query.check_endpoint.__name__

        try:
            _ = requests.get(self.service_endpoint, timeout=wait_time)
            print("%{0}: Selected service endpoint '{1}' reached successfully.".format(method, self.service_endpoint))
        except (requests.ConnectionError, requests.Timeout) as exception:
            print("%{0}: Service endpoint '{1}' could not be reached. Please check URL as well as internet connection."
                  .format(method, self.service_endpoint))

        return True

    def get_query(self, query_str: str):
        """
        Function returns a query as a netcdf byte-encoded response.
        :param query_str: WCPS query.
        :turns xarray.Dataset
        """
        method = Rasdaman_Query.get_query.__name__

        assert isinstance(query_str, str), \
            "%{0}: Query must be a string-object, but is of type '{1}'.".format(method, type(query_str))

        try:
            time0 = time.time()
            print("%{0}: Start query...".format(method))
            query_response = requests.post(self.service_endpoint, data={'query': query_str})
            query_response.raise_for_status()
            # Convert bytes to file-like object
            netcdf_file = io.BytesIO(query_response.content)
            # Convert the netcdf_file like object to a xarray dataset.
            ds = xr.open_dataset(netcdf_file)
            # track time and populate query history
            time_tot = time.time() - time0
            query_dict = {"query string": query_str, "loading time": time_tot,
                          "size data (MB)": ds.nbytes / (1024 * 1024)}
            self.query_history["query_{0:d}".format(self.nquery)] = query_dict
            self.nquery += 1
            print("%{0}: Data query took {1:5.2f} seconds.".format(method, time_tot))
        except HTTPError as err:
            print("%{0}: Query '{1}' failed. See raised HTTPError-message.".format(method, query_str))
            raise err
        except Exception as err:
            print("%{0}: Unknown error occurred with query '{1}'.".format(method, query_str))
            raise err

        return ds

    @staticmethod
    def one_ansi_to_datetime(one_ansi):
        """
        Convert one ansi number to a datetime object.
        :param one_ansi: the ansi-value provided by Rasdaman
        :return: corresponding datetime-object
        """
        if isinstance(one_ansi, (dt.datetime, np.datetime64)):
            date_obj = one_ansi
        else:
            # date_obj = dt.datetime(1600, 1, 2, 3, 0) + dt.timedelta(one_ansi-1)
            date_obj = dt.datetime(1601, 1, 1, 0, 0) + dt.timedelta(one_ansi - 1)
        return date_obj

    @staticmethod
    def ansi_to_datetime(ansis):
        """
        Converts iterable of ansis to a list of datetime objetcs.
        :param ansis: iterable of ansis (e.g. list or numpy-arrays)
        :return: list of datetime-objects from ansi-values
        """
        if np.isscalar(ansis):
            date_list = Rasdaman_Query.one_ansi_to_datetime(ansis)
        else:
            date_list = [Rasdaman_Query.one_ansi_to_datetime(ansi) for ansi in ansis]
        return date_list


# Other methods for data processing (not directly related to rasdaman)
def get_cdf_of_x(sample_in, prob_in):
    """
    Wrappper for interpolating CDF-value for given data
    sample_in : input values to derive discrete CDF
    prob_in   : corresponding CDF
    """
    return lambda xin: np.interp(xin, sample_in, prob_in)


def get_cdf_func(data):
    """
    Converts input xarray to pandas dataframe and sorts the data to obtain wrapper function for the data's CDF.
    """
    method = get_cdf_func.__name__

    df = pd.DataFrame({'time': data.coords["ansi"], 'data': data.values})
    df = df.sort_values(by='data')
    nvalid_nh = np.count_nonzero(~np.isnan(df['data'].values))
    if nvalid_nh < 500:
        if nvalid_nh == 0:
            raise ValueError("%{0}: No data points could be extracted.".format(method))
        else:
            print("%{0}: WARNING: Only {1:3d} data points extracted. Discrete CDF will be rather coarse..."
                  .format(method, nvalid_nh))

    df = df[:nvalid_nh]
    # calculate the probability of the sorted sample values (=CDF functional values)
    p_data = 1. * np.arange(nvalid_nh) / (nvalid_nh - 1)

    return get_cdf_of_x(df['data'].values, p_data)
