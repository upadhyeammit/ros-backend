from insights.core import filters
import six

GLOBAL_PRODUCTS = []
PRODUCT_NAMES = []
DEFAULT_VERSION = ["-1", "-1"]
DEFAULT_RELEASE = "Red Hat Enterprise Linux Server release 7.2 (Maipo)"
DEFAULT_HOSTNAME = "hostname.example.com"


def create_product(metadata, hostname):
    current_system = get_system(metadata, hostname)
    for p in GLOBAL_PRODUCTS:
        if metadata.get("product", "").lower() == p.name and current_system:
            instance = p()
            instance.__dict__ = current_system
            if hasattr(instance, "type"):
                instance.role = instance.type
            return instance
        

class Context(object):
    def __init__(self, **kwargs):
        self.version = kwargs.pop("version", DEFAULT_VERSION)
        self.metadata = kwargs.pop("metadata", {})
        self.loaded = True
        self.cmd = None
        optional_attrs = [
            "content", "path", "hostname", "release",
            "machine_id", "target", "last_client_run", "relative_path",
            "args", "engine", "image", "container_id"
        ]
        for k in optional_attrs:
            setattr(self, k, kwargs.pop(k, None))

        self.relative_path = self.path

        for p in GLOBAL_PRODUCTS:
            if p.name in kwargs:
                setattr(self, p.name, kwargs.pop(p.name))
            else:
                setattr(self, p.name, create_product(self.metadata, self.hostname))

    def stream(self):
        return iter(self.content)

    def product(self):
        for pname in PRODUCT_NAMES:
            if hasattr(self, pname):
                return getattr(self, pname)

    def __repr__(self):
        return repr(dict((k, str(v)[:30]) for k, v in self.__dict__.items()))
    

def context_wrap(lines,
                 path="path",
                 hostname=DEFAULT_HOSTNAME,
                 release=DEFAULT_RELEASE,
                 version="-1.-1",
                 machine_id="machine_id",
                 strip=True,
                 split=True,
                 filtered_spec=None,
                 **kwargs):
    if isinstance(lines, six.string_types):
        if strip:
            lines = lines.strip()
        if split:
            lines = lines.splitlines()

    if filtered_spec is not None and filtered_spec in filters.FILTERS:
        lines = [l for l in lines if any([f in l for f in filters.FILTERS[filtered_spec]])]

    return Context(content=lines,
                   path=path, hostname=hostname,
                   release=release, version=version.split("."),
                   machine_id=machine_id, relative_path=path, **kwargs)