from datetime import datetime, timedelta, timezone

from nose.tools import assert_equal, assert_dict_equal, assert_list_equal, assert_raises
from nose_parameterized import parameterized

from . import param_datastore_objects

from aw_core.models import Event
from aw_core.query import QueryException, query


"""

    Bucket

"""


@parameterized(param_datastore_objects())
def test_query_unspecified_bucket(datastore):
    """
        Asserts that a exception is raised when a query doesn't have a specified bucket
    """
    example_query = {
        'chunk': True,
        'transforms': [{}]
    }
    # Query and handle QueryException
    try:
        result = query(example_query, datastore)
    except QueryException:
        pass
    else:
        raise "Test didn't catch a 'no bucket specified' QueryException which is was supposed to"


@parameterized(param_datastore_objects())
def test_query_invalid_bucket(datastore):
    """
        Asserts that a exception is raised when a query has specified a bucket that is not a string
    """
    example_query = {
        'chunk': True,
        'transforms': [{
            'bucket': 123,
        }]
    }
    # Query and handle QueryException
    try:
        result = query(example_query, datastore)
    except QueryException:
        pass
    else:
        raise "Test didn't catch a 'Invalid bucket' QueryException which is was supposed to"


@parameterized(param_datastore_objects())
def test_query_nonexisting_bucket(datastore):
    """
        Asserts that a exception is raised when a query has specified a bucket that does not exist
    """
    example_query = {
        'chunk': True,
        'transforms': [{
            'bucket': "There is no bucket with this name",
        }]
    }
    # Query and handle QueryException
    try:
        result = query(example_query, datastore)
    except QueryException:
        pass
    else:
        raise "Test didn't catch a 'No such bucket' QueryException which is was supposed to"

"""

    Filter

"""

@parameterized(param_datastore_objects())
def test_query_unspecified_filter(datastore):
    """
        Asserts that a exception is raised when a query has a filter where the filtername is not specified
    """
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    try:
        bucket1 = datastore.create_bucket(bucket_id=bid1, type="test", client="test", hostname="test", name=name)
        example_query = {
            'chunk': True,
            'transforms': [{
                'bucket': bid1,
                'filters': [{}],
            }]
        }
        # Query and handle QueryException
        try:
            result = query(example_query, datastore)
        except QueryException:
            pass
        else:
            raise "Test didn't catch a 'filter name not specified' QueryException which is was supposed to"
    finally:
        datastore.delete_bucket(bid1)


@parameterized(param_datastore_objects())
def test_query_invalid_filter(datastore):
    """
        Asserts that a exception is raised when a query has a filter name that is not a string
    """
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    try:
        bucket1 = datastore.create_bucket(bucket_id=bid1, type="test", client="test", hostname="test", name=name)
        example_query = {
            'chunk': True,
            'transforms': [{
                'bucket': bid1,
                'filters': [{
                    'name': 123,
                }],
            }]
        }
        # Query and handle QueryException
        try:
            result = query(example_query, datastore)
        except QueryException:
            pass
        else:
            raise "Test didn't catch a 'Invalid filter' QueryException which is was supposed to"
    finally:
        datastore.delete_bucket(bid1)


@parameterized(param_datastore_objects())
def test_query_nonexisting_filter(datastore):
    """
        Asserts that a exception is raised when a query tries to use a filter that doesn't exist
    """
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    try:
        bucket1 = datastore.create_bucket(bucket_id=bid1, type="test", client="test", hostname="test", name=name)
        example_query = {
            'chunk': True,
            'transforms': [{
                'bucket': bid1,
                'filters': [{
                    'name': 'There is no filter with this name',
                }],
            }]
        }
        # Query and handle QueryException
        try:
            result = query(example_query, datastore)
        except QueryException:
            pass
        else:
            raise "Test didn't catch a 'No such filter' QueryException which is was supposed to"
    finally:
        datastore.delete_bucket(bid1)


@parameterized(param_datastore_objects())
def test_query_filter_labels_with_chunking(datastore):
    """
        Test include/exclude label filters as well as eventcount limit and start/end filtering
    """
    print(type(datastore.storage_strategy))
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    bid2 = "bucket2"
    now = datetime.now(timezone.utc)
    try:
        bucket1 = datastore.create_bucket(bucket_id=bid1, type="test", client="test", hostname="test", name=name)
        bucket2 = datastore.create_bucket(bucket_id=bid2, type="test", client="test", hostname="test", name=name)
        e1 = Event(label=["test1"],
                   timestamp=now - timedelta(hours=100),
                   duration=timedelta(seconds=1))
        e2 = Event(label=["test2"],
                   timestamp=now,
                   duration=timedelta(seconds=2))
        bucket1.insert(10 * [e1])
        bucket1.insert(5 * [e2])
        bucket2.insert(5 * [e1])
        bucket2.insert(10 * [e2])
        example_query = {
            'chunk': True,
            'transforms': [{
                'bucket': bid1,
                'filters': [{
                    'name': 'include_labels',
                    'labels': ['test1'],
                }]
            }, {
                'bucket': bid2,
                'filters': [{
                    'name': 'exclude_labels',
                    'labels': ['test1'],
                }],
            }]
        }
        # Test that output is correct
        result = query(example_query, datastore)
        assert_dict_equal(result['chunks']['test1'], {'other_labels': [], 'duration': {'value': 10, 'unit': 's'}})
        assert_dict_equal(result['chunks']['test2'], {'other_labels': [], 'duration': {'value': 20, 'unit': 's'}})
        assert_dict_equal(result['duration'], {'value': 30, 'unit': 's'})
        # Test that limit works
        assert_equal(1, query(example_query, datastore, limit=1)["eventcount"])
        # Test that starttime works
        assert_equal(10, query(example_query, datastore, start=now - timedelta(hours=1))["eventcount"])
        # Test that endtime works
        assert_equal(10, query(example_query, datastore, end=now - timedelta(hours=1))["eventcount"])
    finally:
        datastore.delete_bucket(bid1)
        datastore.delete_bucket(bid2)


@parameterized(param_datastore_objects())
def test_query_filter_labels(datastore):
    """
        Timeperiod intersect and eventlist
    """
    print(type(datastore.storage_strategy))
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    bid2 = "bucket2"
    try:
        bucket1 = datastore.create_bucket(bucket_id=bid1, type="test", client="test", hostname="test", name=name)
        bucket2 = datastore.create_bucket(bucket_id=bid2, type="test", client="test", hostname="test", name=name)
        currtime = datetime.now(timezone.utc)
        e1 = Event(label=["test1"],
                   timestamp=currtime,
                   duration=timedelta(seconds=1))
        e2 = Event(label=["test2"],
                   timestamp=currtime + timedelta(seconds=2),
                   duration=timedelta(seconds=1))
        et = Event(label=["intersect-label"],
                   timestamp=currtime,
                   duration=timedelta(seconds=1))

        bucket1.insert(e1)
        bucket1.insert(e2)
        bucket2.insert(et)
        example_query = {
            'chunk': False,
            'transforms': [{
                'bucket': bid1,
                'filters': [{
                    'name': 'timeperiod_intersect',
                    'transforms': [{
                        'bucket': bid2,
                    }]
                }],
            }]
        }
        # Test that output is correct
        result = query(example_query, datastore)
        print(result)
        assert_equal(1, len(result['eventlist']))
        assert_dict_equal(result['eventlist'][0], e1.to_json_dict())
        assert_dict_equal(result['duration'], {'value': 1.0, 'unit': 's'})
    finally:
        datastore.delete_bucket(bid1)
        datastore.delete_bucket(bid2)
