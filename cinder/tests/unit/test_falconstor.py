# Copyright (c) 2015 FalconStor, Inc.
# All Rights Reserved.
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import mock

from cinder import context
from cinder import exception
from cinder import test
from cinder.tests.unit import fake_snapshot
from cinder.volume import configuration as conf
from cinder.volume.drivers.falconstor import iscsi
from cinder.volume.drivers.falconstor import rest_proxy as proxy

FAKE_ID = 321

FAKE = "fake"
API_RESPONSE = {'rc': 0}
VOLUME_BACKEND_NAME = "FSSISCSIDriver"
SESSION_ID = "a76d506c-abcd-1234-efgh-710e1fd90527"
VOLUME_ID = '6068ea6d-f221-4213-bde9-f1b50aecdf36'
ADD_VOLUME_ID = '6068ed7f-f231-4283-bge9-f1b51aecdf36'
GROUP_ID = 'd03338a9-9115-48a3-8dfc-35cdfcdc15a7'
INITIATOR = 'iqn.2013-08.org.debian:01:aaaaaaaa'
PORTAL_RESPONSE = {'rc': 0, 'ipaddress': FAKE}

VOLUME_METADATA = {'metadata': {'FSS-vid': 1}}
EXTENT_NEW_SIZE = 3
CONNECTOR = {'initiator': INITIATOR}
DATA_SERVER_INFO = 0, {
    'metadata': {'vendor': 'FalconStor',
                 'version': '1.5'}}

MOD_OUTPUT = {'status': 'available'}

CONSISTGROUP = {'id': GROUP_ID,
                'name': 'fake_group',
                'description': 'fake_group_des',
                'status': ''}

VOLUME = {'id': VOLUME_ID,
          'name': "volume-" + VOLUME_ID,
          'display_name': 'fake_volume',
          'display_description': '',
          'size': 1,
          'host': "hostname@backend#%s" % FAKE_ID,
          'volume_type': None,
          'volume_type_id': None,
          'consistencygroup_id': None,
          'volume_metadata': [],
          'metadata': ''}

SRC_VOL_ID = "abcdabcd-1234-abcd-1234-abcdeffedcbc"
SRC_VOL = {
    "name": "volume-" + SRC_VOL_ID,
    "id": SRC_VOL_ID,
    "display_name": "fake_src_vol",
    "size": 1,
    "host": "hostname@backend#%s" % FAKE_ID,
    "volume_type": None,
    "volume_type_id": None,
    "volume_size": 1
}

VOLUME_NAME = 'cinder-' + VOLUME['id']
SRC_VOL_NAME = 'cinder-' + SRC_VOL['id']
DATA_OUTPUT = VOLUME_NAME, VOLUME_METADATA

SNAPSHOT_METADATA = {'fss-tm-comment': None}

ADD_VOLUME_IN_CG = {
    'id': ADD_VOLUME_ID,
    'display_name': 'abc123',
    'display_description': '',
    'size': 1,
    'consistencygroup_id': GROUP_ID,
    'status': 'available',
    'host': "hostname@backend#%s" % FAKE_ID}

REMOVE_VOLUME_IN_CG = {
    'id': 'fe2dbc515810451dab2f8c8a48d15bee',
    'display_name': 'fe2dbc515810451dab2f8c8a48d15bee',
    'display_description': '',
    'size': 1,
    'consistencygroup_id': GROUP_ID,
    'status': 'available',
    'host': "hostname@backend#%s" % FAKE_ID}

CG_SNAPSHOT = {
    'consistencygroup_id': GROUP_ID,
    'id': '3c61b0f9-842e-46bf-b061-5e0031d8083f',
    'name': 'cgsnapshot1',
    'description': 'cgsnapshot1',
    'status': ''}

SNAPSHOT_ID = "abcdabcd-1234-abcd-1234-abcdeffedcbb"
SNAPSHOT = {
    "name": "snapshot-" + SNAPSHOT_ID,
    "id": SNAPSHOT_ID,
    "volume_id": VOLUME_ID,
    "volume_name": "volume-" + VOLUME_ID,
    "volume_size": 2,
    "display_name": "fake_snapshot",
    'display_description': '',
    "volume": VOLUME,
    "metadata": SNAPSHOT_METADATA,
    'status': ''
}

INITIATOR = 'iqn.2015-08.org.falconstor:01:ipstor'
CONNECTOR = {'initiator': INITIATOR}
TARGET_IQN = "iqn.2015-06.com.falconstor:freestor.fss-12345abc"
TARGET_PORT = "3260"
ISCSI_PORT_NAMES = ["ct0.eth2", "ct0.eth3", "ct1.eth2", "ct1.eth3"]
ISCSI_IPS = ["10.0.0." + str(i + 1) for i in range(len(ISCSI_PORT_NAMES))]

ISCSI_PORTS = {"iqn": TARGET_IQN,
               "lun": 0
               }
FSS_SINGLE_TYPE = 'single'
RAWTIMESTAMP = '1324975390'


class TestFSSISCSIDriver(test.TestCase):
    def __init__(self, method):
        super(TestFSSISCSIDriver, self).__init__(method)

    def setUp(self):
        super(TestFSSISCSIDriver, self).setUp()

        configuration = mock.Mock(conf.Configuration)
        configuration.volume_backend_name = VOLUME_BACKEND_NAME
        configuration.san_ip = FAKE
        configuration.san_login = FAKE
        configuration.san_password = FAKE
        configuration.fss_pool = FAKE_ID
        configuration.iscsi_port = 3260
        configuration.san_is_local = False
        configuration.additional_retry_list = None
        self.driver = iscsi.FSSISCSIDriver(configuration=configuration)

    def tearDown(self):
        super(TestFSSISCSIDriver, self).tearDown()

    def test_initialized_should_set_fss_info(self):
        self.assertEqual(self.driver.proxy.fss_host,
                         self.driver.configuration.san_ip)
        self.assertEqual(self.driver.proxy.fss_username,
                         self.driver.configuration.san_login)
        self.assertEqual(self.driver.proxy.fss_password,
                         self.driver.configuration.san_password)
        self.assertEqual(self.driver.proxy.fss_defined_pool,
                         self.driver.configuration.fss_pool)

    def test_check_for_setup_error(self):
        self.assertRaises(exception.VolumeBackendAPIException,
                          self.driver.check_for_setup_error)

    def test_create_volume(self):
        volume = {"metadata": {"Type": "work"},
                  "display_name": "Volume-1141619199", "size": 1}
        self.driver.proxy.create_vdev = mock.Mock(return_value=DATA_OUTPUT)
        self.driver.create_volume(volume)
        self.driver.proxy.create_vdev.assert_called_once_with(volume)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_extend_volume(self, mock__get_fss_volume_name):
        """Volume extended_volume successfully."""
        mock__get_fss_volume_name.return_value = VOLUME_NAME
        self.driver.proxy.extend_vdev = mock.Mock()
        result = self.driver.extend_volume(VOLUME, EXTENT_NEW_SIZE)
        mock__get_fss_volume_name.assert_called_once_with(VOLUME)
        self.driver.proxy.extend_vdev.assert_called_once_with(VOLUME_NAME,
                                                              VOLUME["size"],
                                                              EXTENT_NEW_SIZE)
        self.assertTrue(result is None)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_clone_volume(self, mock__get_fss_volume_name):
        mock__get_fss_volume_name.side_effect = [VOLUME_NAME, SRC_VOL_NAME]
        self.driver.proxy.clone_volume = mock.Mock(
            return_value=VOLUME_METADATA)
        self.driver.proxy.extend_vdev = mock.Mock()

        self.driver.create_cloned_volume(VOLUME, SRC_VOL)
        self.driver.proxy.clone_volume.assert_called_with(VOLUME_NAME,
                                                          SRC_VOL_NAME)
        mock__get_fss_volume_name.assert_any_call(VOLUME)
        mock__get_fss_volume_name.assert_any_call(SRC_VOL)
        assert 2 == mock__get_fss_volume_name.call_count

        self.driver.proxy.extend_vdev(VOLUME_NAME, VOLUME["size"],
                                      SRC_VOL["size"])
        self.driver.proxy.extend_vdev.assert_called_with(VOLUME_NAME,
                                                         VOLUME["size"],
                                                         SRC_VOL["size"])

    def test_delete_volume(self):
        self.driver.proxy.delete_vdev = mock.Mock()
        result = self.driver.delete_volume(VOLUME)
        self.driver.proxy.delete_vdev.assert_called_once_with(VOLUME)
        self.assertTrue(result is None)

    def test_create_snapshot(self):
        snap_name = SNAPSHOT.get('display_name')
        SNAPSHOT_METADATA["FSS-TM-comment"] = snap_name

        self.driver.proxy.create_snapshot = mock.Mock(
            return_value=API_RESPONSE)
        result = self.driver.create_snapshot(SNAPSHOT)
        self.driver.proxy.create_snapshot.assert_called_once_with(SNAPSHOT)
        self.assertEqual(result, {'metadata': SNAPSHOT_METADATA})

    def test_delete_snapshot(self):
        self.driver.proxy.delete_snapshot = mock.Mock()
        result = self.driver.delete_snapshot(SNAPSHOT)
        self.driver.proxy.delete_snapshot.assert_called_once_with(SNAPSHOT)
        self.assertTrue(result is None)

    @mock.patch.object(proxy.RESTProxy, 'create_volume_from_snapshot')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_create_volume_from_snapshot(self, mock__get_fss_volume_name,
                                         mock_create_volume_from_snapshot):
        vol_size = VOLUME['size']
        snap_size = SNAPSHOT['volume_size']

        mock_create_volume_from_snapshot.return_value = (VOLUME_NAME,
                                                         VOLUME_METADATA)
        mock__get_fss_volume_name.return_value = VOLUME_NAME
        self.driver.proxy.extend_vdev = mock.Mock()
        self.driver.create_volume_from_snapshot(VOLUME, SNAPSHOT)
        mock_create_volume_from_snapshot.\
            assert_called_once_with(VOLUME, SNAPSHOT)
        if vol_size != snap_size:
            mock__get_fss_volume_name.assert_called_once_with(VOLUME)
            self.driver.proxy.extend_vdev(VOLUME_NAME, snap_size, vol_size)
            self.driver.proxy.extend_vdev.assert_called_with(VOLUME_NAME,
                                                             snap_size,
                                                             vol_size)

    @mock.patch.object(proxy.RESTProxy, 'create_group')
    def test_create_consistency_group(self, mock_create_group):
        ctxt = context.get_admin_context()
        model_update = self.driver.create_consistencygroup(ctxt, CONSISTGROUP)
        mock_create_group.assert_called_once_with(CONSISTGROUP)
        self.assertDictMatch({'status': 'available'}, model_update)

    @mock.patch.object(proxy.RESTProxy, 'destroy_group')
    @mock.patch.object(proxy.RESTProxy, 'delete_vdev')
    def test_delete_consistency_group(self, mock_delete_vdev,
                                      mock_destroy_group):
        ctxt = context.get_admin_context()

        self.driver.db = mock.Mock()
        mock_volume = mock.MagicMock()
        expected_volumes = [mock_volume]
        CONSISTGROUP["status"] = "deleted"

        self.driver.db.volume_get_all_by_group.return_value = expected_volumes
        model_update, volumes = self.driver.\
            delete_consistencygroup(ctxt, CONSISTGROUP)

        mock_destroy_group.assert_called_with(CONSISTGROUP)
        self.assertEqual(expected_volumes, volumes)
        self.assertDictMatch({'status': 'deleted'}, model_update)
        mock_delete_vdev.assert_called_with(mock_volume)

    @mock.patch.object(proxy.RESTProxy, 'set_group')
    def test_update_consistency_group(self, mock_set_group):
        ctxt = context.get_admin_context()
        add_vols = [
            {'name': 'vol1', 'id': 'vol1', 'display_name': ''},
            {'name': 'vol2', 'id': 'vol2', 'display_name': ''}
        ]

        remove_vols = [
            {'name': 'vol3', 'id': 'vol3', 'display_name': ''},
            {'name': 'vol4', 'id': 'vol4', 'display_name': ''}
        ]

        expected_addvollist = ["cinder-%s" % volume['id'] for volume in
                               add_vols]
        expected_remvollist = ["cinder-%s" % vol['id'] for vol in remove_vols]

        self.driver.update_consistencygroup(ctxt, CONSISTGROUP,
                                            add_volumes=add_vols,
                                            remove_volumes=remove_vols)
        mock_set_group.assert_called_with(CONSISTGROUP,
                                          addvollist=expected_addvollist,
                                          remvollist=expected_remvollist)

    @mock.patch.object(proxy.RESTProxy, 'create_cgsnapshot')
    @mock.patch('cinder.objects.snapshot.SnapshotList.get_all_for_cgsnapshot')
    def test_create_cgsnapshot(self, mock_get_all_for_cgsnapshot,
                               mock_create_cgsnapshot):
        ctxt = context.get_admin_context()
        self.driver.db = mock.Mock()
        snapshot_obj = fake_snapshot.fake_snapshot_obj(ctxt)
        snapshot_obj = CG_SNAPSHOT
        self.driver.db.snapshot_get_all_for_cgsnapshot = mock.Mock(
            return_value=[snapshot_obj])

        model_update, snapshots = self.driver.create_cgsnapshot(ctxt,
                                                                snapshot_obj)
        mock_create_cgsnapshot.assert_called_once_with(snapshot_obj)
        self.driver.db.snapshot_get_all_for_cgsnapshot.assert_called_once_with(
            ctxt, snapshot_obj['id'])
        self.assertDictMatch({'status': 'available'}, model_update)

    @mock.patch.object(proxy.RESTProxy, 'delete_cgsnapshot')
    @mock.patch('cinder.objects.snapshot.SnapshotList.get_all_for_cgsnapshot')
    def test_delete_cgsnapshot(self, mock_get_all_for_cgsnapshot,
                               mock_delete_cgsnapshot):
        ctxt = context.get_admin_context()
        self.driver.db = mock.Mock()
        snapshot_obj = fake_snapshot.fake_snapshot_obj(ctxt)
        snapshot_obj = CG_SNAPSHOT
        self.driver.db.snapshot_get_all_for_cgsnapshot = mock.Mock(
            return_value=[snapshot_obj])

        model_update, snapshots = self.driver.delete_cgsnapshot(ctxt,
                                                                snapshot_obj)
        mock_delete_cgsnapshot.assert_called_once_with(snapshot_obj)
        self.driver.db.snapshot_get_all_for_cgsnapshot.assert_called_once_with(
            ctxt, snapshot_obj['id'])
        self.assertDictMatch({'status': 'deleted'}, model_update)

    @mock.patch.object(proxy.RESTProxy, 'get_default_portal')
    @mock.patch.object(proxy.RESTProxy, 'initialize_connection_iscsi')
    def test_initialize_connection(self, mock_initialize_connection_iscsi,
                                   mock_get_default_portal):

        mock_initialize_connection_iscsi.return_value = ISCSI_PORTS
        mock_get_default_portal.return_value = PORTAL_RESPONSE

        res = self.driver.initialize_connection(VOLUME, CONNECTOR)
        mock_initialize_connection_iscsi.assert_called_once_with(VOLUME,
                                                                 CONNECTOR)
        mock_get_default_portal.assert_called_once_with()

        self.assertEqual('iscsi', res['driver_volume_type'])
        self.assertFalse(res['data']['target_discovered'])
        self.assertFalse(res['data']['encrypted'])
        self.assertEqual('rw', res['data']['access_mode'])
        self.assertEqual(VOLUME['id'], res['data']['volume_id'])

    @mock.patch.object(proxy.RESTProxy, 'terminate_connection_iscsi')
    def test_terminate_connection(self, mock_terminate_connection_iscsi):
        self.driver.terminate_connection(VOLUME, CONNECTOR)
        mock_terminate_connection_iscsi.assert_called_once_with(VOLUME,
                                                                CONNECTOR)

    @mock.patch.object(proxy.RESTProxy, '_manage_existing_volume')
    @mock.patch.object(proxy.RESTProxy, '_get_existing_volume_ref_vid')
    def test_manage_existing(self, mock__get_existing_volume_ref_vid,
                             mock__manage_existing_volume):
        ref_vid = 1
        volume_ref = {'source-id': ref_vid}
        self.driver.manage_existing(VOLUME, volume_ref)
        mock__get_existing_volume_ref_vid.assert_called_once_with(volume_ref)
        mock__manage_existing_volume.assert_called_once_with(
            volume_ref['source-id'], VOLUME)

    @mock.patch.object(proxy.RESTProxy, '_get_existing_volume_ref_vid')
    def test_manage_existing_get_size(self, mock__get_existing_volume_ref_vid):
        ref_vid = 1
        volume_ref = {'source-id': ref_vid}
        expected_size = 5
        mock__get_existing_volume_ref_vid.return_value = 5120

        size = self.driver.manage_existing_get_size(VOLUME, volume_ref)
        mock__get_existing_volume_ref_vid.assert_called_once_with(volume_ref)
        self.assertEqual(expected_size, size)

    @mock.patch.object(proxy.RESTProxy, 'unmanage')
    def test_unmanage(self, mock_unmanage):
        self.driver.unmanage(VOLUME)
        mock_unmanage.assert_called_once_with(VOLUME)


class TestRESTProxy(test.TestCase):
    """Test REST Proxy Driver."""

    def setUp(self):
        super(TestRESTProxy, self).setUp()

        configuration = mock.Mock(conf.Configuration)
        configuration.san_ip = FAKE
        configuration.san_login = FAKE
        configuration.san_password = FAKE
        configuration.fss_pool = FAKE_ID

        self.proxy = proxy.RESTProxy(configuration)

        self.FSS_MOCK = mock.MagicMock()
        self.proxy.FSS = self.FSS_MOCK
        self.FSS_MOCK._fss_request.return_value = API_RESPONSE

    def tearDown(self):
        super(TestRESTProxy, self).tearDown()

    def test_do_setup(self):
        self.proxy.do_setup()
        self.FSS_MOCK.fss_login.assert_called_once_with()
        self.assertNotEqual(self.proxy.session_id, SESSION_ID)

    def test_create_volume(self):
        sizemb = self.proxy._convert_size_to_mb(VOLUME['size'])
        volume_name = self.proxy._get_fss_volume_name(VOLUME)

        params = dict(storagepoolid=self.proxy.fss_defined_pool,
                      sizemb=sizemb,
                      category="virtual",
                      name=volume_name)
        volume_name, api_res = self.proxy.create_vdev(VOLUME)
        self.FSS_MOCK.create_vdev.assert_called_once_with(params)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    def test_extend_volume(self, mock__get_fss_vid_from_name):
        size = self.proxy._convert_size_to_mb(EXTENT_NEW_SIZE - VOLUME['size'])
        params = dict(
            action='expand',
            sizemb=size
        )
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        volume_name = self.proxy._get_fss_volume_name(VOLUME)
        self.proxy.extend_vdev(volume_name, VOLUME["size"], EXTENT_NEW_SIZE)

        mock__get_fss_vid_from_name.assert_called_once_with(volume_name,
                                                            FSS_SINGLE_TYPE)
        self.FSS_MOCK.extend_vdev.assert_called_once_with(FAKE_ID, params)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    def test_delete_volume(self, mock__get_fss_vid_from_name):
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        volume_name = self.proxy._get_fss_volume_name(VOLUME)
        self.proxy.delete_vdev(VOLUME)
        mock__get_fss_vid_from_name.assert_called_once_with(volume_name,
                                                            FSS_SINGLE_TYPE)
        self.FSS_MOCK.delete_vdev.assert_called_once_with(FAKE_ID)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    def test_clone_volume(self, mock__get_fss_vid_from_name):
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        self.FSS_MOCK.create_mirror.return_value = API_RESPONSE
        self.FSS_MOCK.sync_mirror.return_value = API_RESPONSE
        mirror_params = dict(
            category='virtual',
            selectioncriteria='anydrive',
            mirrortarget="virtual",
            storagepoolid=self.proxy.fss_defined_pool
        )
        ret = self.proxy.clone_volume(VOLUME_NAME, SRC_VOL_NAME)
        self.FSS_MOCK.create_mirror.assert_called_once_with(FAKE_ID,
                                                            mirror_params)
        self.FSS_MOCK.sync_mirror.assert_called_once_with(FAKE_ID)
        self.FSS_MOCK.promote_mirror.assert_called_once_with(FAKE_ID,
                                                             VOLUME_NAME)
        self.assertNotEqual(ret, VOLUME_METADATA)

    @mock.patch.object(proxy.RESTProxy, 'create_vdev_snapshot')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_vol_name_from_snap')
    def test_create_snapshot(self, mock__get_vol_name_from_snap,
                             mock__get_fss_vid_from_name,
                             mock_create_vdev_snapshot):

        mock__get_vol_name_from_snap.return_value = VOLUME_NAME
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        self.FSS_MOCK._check_if_snapshot_tm_exist.return_value =\
            [False, False, SNAPSHOT['volume_size']]

        self.proxy.create_snapshot(SNAPSHOT)
        self.FSS_MOCK._check_if_snapshot_tm_exist.assert_called_once_with(
            FAKE_ID)
        sizemb = self.proxy._convert_size_to_mb(SNAPSHOT['volume_size'])
        mock_create_vdev_snapshot.assert_called_once_with(FAKE_ID, sizemb)
        self.FSS_MOCK.create_timemark_policy.\
            assert_called_once_with(FAKE_ID,
                                    storagepoolid=self.proxy.fss_defined_pool)
        self.FSS_MOCK.create_timemark.\
            assert_called_once_with(FAKE_ID, SNAPSHOT["display_name"])

    @mock.patch.object(proxy.RESTProxy, '_get_timestamp')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_vol_name_from_snap')
    def test_delete_snapshot(self, mock__get_vol_name_from_snap,
                             mock__get_fss_vid_from_name,
                             mock__get_timestamp):

        mock__get_vol_name_from_snap.return_value = VOLUME_NAME
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        mock__get_timestamp.return_value = RAWTIMESTAMP
        timestamp = '%s_%s' % (FAKE_ID, RAWTIMESTAMP)

        self.proxy.delete_snapshot(SNAPSHOT)
        mock__get_vol_name_from_snap.assert_called_once_with(SNAPSHOT)
        self.FSS_MOCK.delete_timemark.assert_called_once_with(timestamp)
        self.FSS_MOCK.get_timemark.assert_any_call(FAKE_ID)
        assert 2 == self.FSS_MOCK.get_timemark.call_count

    @mock.patch.object(proxy.RESTProxy, '_get_timestamp')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_vol_name_from_snap')
    def test_create_volume_from_snapshot(self, mock__get_vol_name_from_snap,
                                         mock__get_fss_vid_from_name,
                                         mock__get_timestamp):
        tm_info = {"rc": 0,
                   "data":
                       {
                           "guid": "497bad5e-e589-bb0a-e0e7-00004eeac169",
                           "name": "SANDisk-001",
                           "total": "1",
                           "timemark": [
                               {
                                   "size": 131072,
                                   "comment": "123test456",
                                   "hastimeview": False,
                                   "priority": "low",
                                   "quiescent": "yes",
                                   "timeviewdata": "notkept",
                                   "rawtimestamp": "1324975390",
                                   "timestamp": "2015-10-11 16:43:10"
                               }]
                       }
                   }

        mock__get_vol_name_from_snap.return_value = VOLUME_NAME
        new_vol_name = self.proxy._get_fss_volume_name(VOLUME)
        mock__get_fss_vid_from_name.return_value = FAKE_ID

        self.FSS_MOCK.get_timemark.return_value = tm_info
        mock__get_timestamp.return_value = RAWTIMESTAMP
        timestamp = '%s_%s' % (FAKE_ID, RAWTIMESTAMP)

        self.proxy.create_volume_from_snapshot(VOLUME, SNAPSHOT)
        self.FSS_MOCK.get_timemark.assert_called_once_with(FAKE_ID)
        mock__get_timestamp.assert_called_once_with(tm_info,
                                                    SNAPSHOT['display_name'])
        self.FSS_MOCK.copy_timemark.\
            assert_called_once_with(timestamp,
                                    storagepoolid=self.proxy.fss_defined_pool,
                                    name=new_vol_name)

    @mock.patch.object(proxy.RESTProxy, '_get_group_name_from_id')
    def test_create_consistency_group(self, mock__get_group_name_from_id):

        mock__get_group_name_from_id.return_value = CONSISTGROUP['name']
        params = dict(
            name=CONSISTGROUP['name']
        )
        self.proxy.create_group(CONSISTGROUP)
        self.FSS_MOCK.create_group.assert_called_once_with(params)
        # self.assertEqual(ret, API_RESPONSE)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_gid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_group_name_from_id')
    def test_delete_consistency_group(self, mock__get_group_name_from_id,
                                      mock__get_fss_gid_from_name):
        mock__get_group_name_from_id.return_value = CONSISTGROUP['name']
        mock__get_fss_gid_from_name.return_value = FAKE_ID

        self.proxy.destroy_group(CONSISTGROUP)
        mock__get_group_name_from_id.assert_called_once_with(
            CONSISTGROUP['id'])
        mock__get_fss_gid_from_name.assert_called_once_with(
            CONSISTGROUP['name'])
        self.FSS_MOCK.destroy_group.assert_called_once_with(FAKE_ID)

    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_gid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_group_name_from_id')
    def test_update_consistency_group(self, mock__get_group_name_from_id,
                                      mock__get_fss_gid_from_name,
                                      mock__get_fss_vid_from_name):
        JOIN_VID_LIST = [1, 2]
        LEAVE_VID_LIST = [3, 4]
        mock__get_group_name_from_id.return_value = CONSISTGROUP['name']
        mock__get_fss_gid_from_name.return_value = FAKE_ID
        mock__get_fss_vid_from_name.side_effect = [JOIN_VID_LIST,
                                                   LEAVE_VID_LIST]
        add_vols = [
            {'name': 'vol1', 'id': 'vol1'},
            {'name': 'vol2', 'id': 'vol2'}
        ]
        remove_vols = [
            {'name': 'vol3', 'id': 'vol3'},
            {'name': 'vol4', 'id': 'vol4'}
        ]
        expected_addvollist = ["cinder-%s" % volume['id'] for volume in
                               add_vols]
        expected_remvollist = ["cinder-%s" % vol['id'] for vol in remove_vols]

        self.proxy.set_group(CONSISTGROUP, addvollist=expected_addvollist,
                             remvollist=expected_remvollist)

        if expected_addvollist:
            mock__get_fss_vid_from_name.assert_any_call(expected_addvollist)

        if expected_remvollist:
            mock__get_fss_vid_from_name.assert_any_call(expected_remvollist)
        assert 2 == mock__get_fss_vid_from_name.call_count

        join_params = dict()
        leave_params = dict()

        join_params.update(
            action='join',
            virtualdevices=JOIN_VID_LIST
        )
        leave_params.update(
            action='leave',
            virtualdevices=LEAVE_VID_LIST
        )
        self.FSS_MOCK.set_group.assert_called_once_with(FAKE_ID, join_params,
                                                        leave_params)

    @mock.patch.object(proxy.RESTProxy, 'create_vdev_snapshot')
    @mock.patch.object(proxy.RESTProxy, 'create_group_timemark_policy')
    @mock.patch.object(proxy.RESTProxy, 'create_group_timemark')
    @mock.patch.object(proxy.RESTProxy, '_get_vdev_id_from_group_id')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_gid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_group_name_from_id')
    def test_create_cgsnapshot(self, mock__get_group_name_from_id,
                               mock__get_fss_gid_from_name,
                               mock__get_vdev_id_from_group_id,
                               mock_create_group_timemark,
                               mock_create_group_timemark_policy,
                               mock_create_vdev_snapshot
                               ):
        VID_LIST = [1]

        group_name = "cinder-consisgroup-%s" % CG_SNAPSHOT[
            'consistencygroup_id']
        mock__get_group_name_from_id.return_value = group_name
        mock__get_fss_gid_from_name.return_value = FAKE_ID
        mock__get_vdev_id_from_group_id.return_value = VID_LIST
        gsnap_name = self.proxy._encode_name(CG_SNAPSHOT['id'])
        self.FSS_MOCK.\
            _check_if_snapshot_tm_exist.return_value = (False, False, 1024)

        self.proxy.create_cgsnapshot(CG_SNAPSHOT)
        mock__get_group_name_from_id.assert_called_once_with(
            CG_SNAPSHOT['consistencygroup_id'])
        mock__get_fss_gid_from_name.assert_called_once_with(group_name)
        mock__get_vdev_id_from_group_id.assert_called_once_with(FAKE_ID)

        for vid in VID_LIST:
            self.FSS_MOCK._check_if_snapshot_tm_exist.assert_called_with(vid)
            mock_create_vdev_snapshot.assert_called_once_with(vid, 1024)
            self.FSS_MOCK.create_timemark_policy.\
                assert_called_once_with(vid,
                                        storagepoolid=
                                        self.proxy.fss_defined_pool)

        mock_create_group_timemark.assert_called_once_with(FAKE_ID, gsnap_name)

    @mock.patch.object(proxy.RESTProxy, 'delete_group_timemark')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_gid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_group_name_from_id')
    def test_delete_cgsnapshot(self, mock__get_group_name_from_id,
                               mock__get_fss_gid_from_name,
                               mock_delete_group_timemark):
        tm_info = {
            "rc": 0,
            "data":
                {
                    "name": "GroupTestABC",
                    "total": 1,
                    "timemark": [{
                        "size": 65536,
                        "comment": "cinder-PGGw+YQuRr+wYV4AMdgIPw",
                        "priority": "low",
                        "quiescent": "yes",
                        "hastimeview": "false",
                        "timeviewdata": "notkept",
                        "rawtimestamp": "1324974940",
                        "timestamp": "2015-10-15 16:35:40"}]
                }
        }

        final_tm_data = {
            "rc": 0,
            "data":
                {"name": "GroupTestABC",
                 "total": 1,
                 "timemark": []
                 }}

        mock__get_group_name_from_id.return_value = CG_SNAPSHOT[
            'consistencygroup_id']
        mock__get_fss_gid_from_name.return_value = FAKE_ID
        self.FSS_MOCK.get_group_timemark.side_effect = [tm_info, final_tm_data]
        encode_snap_name = self.proxy._encode_name(CG_SNAPSHOT['id'])

        self.proxy.delete_cgsnapshot(CG_SNAPSHOT)
        assert 2 == self.FSS_MOCK.get_group_timemark.call_count
        self.FSS_MOCK.get_group_timemark.assert_any_call(FAKE_ID)
        rawtimestamp = self.proxy._get_timestamp(tm_info, encode_snap_name)
        timestamp = '%s_%s' % (FAKE_ID, rawtimestamp)

        mock_delete_group_timemark.assert_called_once_with(timestamp)
        self.FSS_MOCK.delete_group_timemark_policy.assert_called_once_with(
            FAKE_ID)

    @mock.patch.object(proxy.RESTProxy, 'assign_vdev')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    @mock.patch.object(proxy.RESTProxy, '_get_host')
    @mock.patch.object(proxy.RESTProxy, '_check_iscsi_option')
    def test_initialize_connection(self, mock__check_iscsi_option,
                                   mock__get_host,
                                   mock__get_fss_volume_name,
                                   mock__get_fss_vid_from_name,
                                   mock_assign_vdev):
        lun = 0
        target_name = INITIATOR

        iscsi_target_info = dict(lun=lun,
                                 iqn=target_name)

        mock__get_host.return_value = FAKE_ID, FAKE_ID
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        self.FSS_MOCK._get_target_info.return_value = (lun, target_name)

        ret = self.proxy.initialize_connection_iscsi(VOLUME, CONNECTOR)
        mock__check_iscsi_option.assert_called_once_with()
        mock__get_host.assert_called_once_with(CONNECTOR)
        mock__get_fss_volume_name.assert_called_once_with(VOLUME)

        self.FSS_MOCK._get_target_info.assert_called_once_with(FAKE_ID,
                                                               FAKE_ID)
        self.assertEqual(ret, iscsi_target_info)

    @mock.patch.object(proxy.RESTProxy, 'unassign_vdev')
    @mock.patch.object(proxy.RESTProxy, '_get_host')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_terminate_connection(self, mock__get_fss_volume_name,
                                  mock__get_host,
                                  mock_unassign_vdev):
        mock__get_fss_volume_name.return_value = VOLUME_NAME
        mock__get_host.return_value = FAKE_ID, FAKE_ID
        self.FSS_MOCK._get_target_info.return_value = (FAKE_ID, INITIATOR)

        self.proxy.terminate_connection_iscsi(VOLUME, CONNECTOR)
        mock__get_fss_volume_name.assert_called_once_with(VOLUME)
        mock__get_host.assert_called_once_with(CONNECTOR)
        mock_unassign_vdev.assert_called_once_with(FAKE_ID, '')
        self.FSS_MOCK._get_target_info.\
            assert_called_once_with(FAKE_ID, '')

    @mock.patch.object(proxy.RESTProxy, 'rename_vdev')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_manage_existing(self, mock__get_fss_volume_name,
                             mock_rename_vdev):
        new_vol_name = 'rename-vol'
        mock__get_fss_volume_name.return_value = new_vol_name

        self.proxy._manage_existing_volume(FAKE_ID, VOLUME)
        mock__get_fss_volume_name.assert_called_once_with(VOLUME)
        mock_rename_vdev.assert_called_once_with(FAKE_ID, new_vol_name)

    @mock.patch.object(proxy.RESTProxy, 'list_volume_info')
    def test_manage_existing_get_size(self, mock_list_volume_info):
        volume_ref = {'source-id': FAKE_ID}
        vdev_info = {
            "rc": 0,
            "data": {
                "name": "cinder-2ab1f70a-6c89-432c-84e3-5fa6c187fb92",
                "type": "san",
                "category": "virtual",
                "sizemb": 1020
            }}

        mock_list_volume_info.return_value = vdev_info
        self.proxy._get_existing_volume_ref_vid(volume_ref)
        mock_list_volume_info.assert_called_once_with(FAKE_ID)

    @mock.patch.object(proxy.RESTProxy, 'rename_vdev')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_vid_from_name')
    @mock.patch.object(proxy.RESTProxy, '_get_fss_volume_name')
    def test_unmanage(self, mock__get_fss_volume_name,
                      mock__get_fss_vid_from_name,
                      mock_rename_vdev):

        mock__get_fss_volume_name.return_value = VOLUME_NAME
        mock__get_fss_vid_from_name.return_value = FAKE_ID
        unmanaged_vol_name = VOLUME_NAME + "-unmanaged"

        self.proxy.unmanage(VOLUME)
        mock__get_fss_volume_name.assert_called_once_with(VOLUME)
        mock__get_fss_vid_from_name.assert_called_once_with(VOLUME_NAME,
                                                            FSS_SINGLE_TYPE)
        mock_rename_vdev.assert_called_once_with(FAKE_ID, unmanaged_vol_name)
