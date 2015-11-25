# cinderdriver

Please keep the driver files in this repo up to date, especially when the driver has not yet been merged into the upstream cinder repo. If you make changes to the code during the code review, be sure to make the same changes in this repo as well.

The CI jobs named *-custom are designed to directly download these driver files (using wget) so that they can be merged with the upstream cinder repo. For details see ci-config-main/jenkins/jobs/macros-common.yaml. If you create any additional driver files and push them to this repo, you must also update macros-common.yaml to make sure the new file is downloaded alongside the others.
