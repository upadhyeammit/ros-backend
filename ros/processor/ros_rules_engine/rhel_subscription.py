"""
RhelSubscriptionInfo - Combiner
===============================
T.B.D
"""
from insights import SkipComponent
from insights.core.plugins import combiner
from insights.combiners.rhsm_release import RhsmRelease
from insights.parsers.yum import YumRepoList
from ros.processor.ros_rules_engine.rhel_release import RhelRelease

APPSTREAM_REPO_FIX = {
    8: 'rhel-8-for-{arch_name}-appstream{sub_type}rpms',
    9: 'rhel-9-for-{arch_name}-appstream{sub_type}rpms'
}

BASE_REPO_FIX = {
    9: 'rhel-9-for-{arch_name}-baseos{sub_type}rpms',
    8: 'rhel-8-for-{arch_name}-baseos{sub_type}rpms',
    7: 'rhel-7-{arch_name}{sub_type}rpms',
    6: 'rhel-6-{arch_name}{sub_type}rpms',
}

REPO_ARCH_NAME_MAP = {
    9: {
        "x86_64": "x86_64",
        "ppc64le": "ppc64le",
        "s390x": "s390x",
        "aarch64": "aarch64",
    },
    8: {
        "x86_64": "x86_64",
        "ppc64le": "ppc64le",
        "s390x": "s390x",
        "aarch64": "aarch64",
    },
    7: {
        "x86_64": "server",
        "ppc64": "for-power",
        "ppc64le": "for-power-le",
        "s390x": "for-system-z",
    },
    6: {
        "i686": "server",
        "x86_64": "server",
        "ppc64": "for-power",
        "s390x": "for-system-z",
    }
}


@combiner(RhelRelease, YumRepoList, optional=[RhsmRelease])
class RhelSubscriptionInfo(object):
    """
    The combiner to check the subscription information of the host.

    """
    def __init__(self, rhel, repo, rhsm):
        # Only supported RHEL
        if (not rhel.rhel) or (rhel.major not in BASE_REPO_FIX):
            raise SkipComponent

        # Only supported Arch
        if rhel.arch not in REPO_ARCH_NAME_MAP[rhel.major]:
            raise SkipComponent

        self.rhel = rhel.rhel
        """str: The Red Hat release, e.g. '7.9'"""
        self.rhel_major = rhel.major
        """int: The major version of Red Hat release, e.g. 7"""
        self.rhel_minor = rhel.minor
        """int: The minor version of Red Hat release, e.g. 9"""

        base_repo_tmp = BASE_REPO_FIX[rhel.major]
        arch_name = REPO_ARCH_NAME_MAP[rhel.major][rhel.arch]
        self.base_repo_id = base_repo_tmp.format(arch_name=arch_name, sub_type='-')
        self.appstream_repo_id = None
        if rhel.major >= 8:
            self.appstream_repo_id = APPSTREAM_REPO_FIX[rhel.major].format(arch_name=arch_name, sub_type='-')
        """
        str: The base repo id of the RHEL e.g. "rhel-8-for-x86_64-baseos-rpms".
        """
        self.rhel_repos = repo.rhel_repos
        """List: List of the name of the RHEL repos, e.g. "rhel-7-server-rpms" w/o Arch or 7Server."""
        self.is_base = base_repo_tmp.format(arch_name=arch_name, sub_type='-') in repo.rhel_repos
        """Boolean: If the base subscription is enabled or not."""
        self.is_eus = base_repo_tmp.format(arch_name=arch_name, sub_type='-eus-') in repo.rhel_repos
        """Boolean: If "EUS" subscription is enabled or not."""
        self.is_els = base_repo_tmp.format(arch_name=arch_name, sub_type='-els-') in repo.rhel_repos
        """Boolean: If "ELS" subscription is enabled or not."""
        self.is_aus = base_repo_tmp.format(arch_name=arch_name, sub_type='-aus-') in repo.rhel_repos
        """Boolean: If "AUS" subscription is enabled or not."""
        self.is_tus = base_repo_tmp.format(arch_name=arch_name, sub_type='-tus-') in repo.rhel_repos
        """Boolean: If "TUS" subscription is enabled or not."""
        self.is_e4s = base_repo_tmp.format(arch_name=arch_name, sub_type='-e4s-') in repo.rhel_repos
        """Boolean: If "E4S" subscription is enabled or not."""
        # set it to True as default for subsequent comparation, then no need to check rhel version
        self.is_appstream = True
        self.is_appstream_eus = True
        self.is_appstream_els = True
        self.is_appstream_aus = True
        self.is_appstream_tus = True
        self.is_appstream_e4s = True
        if rhel.major >= 8:
            appstream_repo_tmp = APPSTREAM_REPO_FIX[rhel.major]
            self.is_appstream = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-') in repo.rhel_repos
            self.is_appstream_eus = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-eus-') in repo.rhel_repos
            self.is_appstream_els = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-els-') in repo.rhel_repos
            self.is_appstream_aus = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-aus-') in repo.rhel_repos
            self.is_appstream_tus = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-tus-') in repo.rhel_repos
            self.is_appstream_e4s = appstream_repo_tmp.format(arch_name=arch_name, sub_type='-e4s-') in repo.rhel_repos
        self.lock = None
        """str: The RHSM release set, e.g. '7.9', '7Server', '8'.
                None when not locked (No `major release` is locked)"""
        self.lock_major = None
        """int: The major version of the RHSM release set, e.g. 7
                None when no `major release` is locked"""
        self.lock_minor = None
        """int: The minor version of the RHSM release set, e.g. 9
                None when no `major release` or `minor release` is locked"""
        self.is_major_locked = False
        """Boolean: If the RHSM release is set to a ``major release``
                    No matter weather `minor` is locked or not"""
        self.is_minor_locked = False
        """Boolean: If the RHSM release is set to a ``minor release``
                    False when locking to `major` release only"""
        if rhsm:
            self.lock = rhsm.set
            self.lock_major = rhsm.major
            self.lock_minor = rhsm.minor
            self.is_major_locked = rhsm.major is not None
            self.is_minor_locked = self.is_major_locked and rhsm.minor is not None
