# cinderdriver

Please keep the driver files in this repo up to date, especially when the driver has not yet been merged into the upstream cinder repo. If you make changes to the code during the code review, be sure to make the same changes in this repo as well.

The CI jobs named `*-custom` are designed to directly download these driver files (using wget) so that they can be merged with the upstream cinder repo. For details see [ci-config-main/jenkins/jobs/dsvm-falc-fss-iscsi-custom.yaml](https://github.com/falcopenstack/ci-config-main/blob/master/jenkins/jobs/dsvm-falc-fss-iscsi-custom.yaml). 

If you create any additional driver files and push them to this repo, you must also update the file `dsvm-falc-fss-iscsi-custom.yaml` to make sure the new file is downloaded alongside the others.
