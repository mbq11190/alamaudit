

from . import qaco_audit
from . import audit_stages
from . import audit_attachment
from . import audit_year
from . import firm_name
from . import auto_follower
from . import audit_engagement
from . import res_partner
from . import audit_changelog
from . import lock_approval
# Temporary debug monkeypatch to surface ordering / unknown-model issues during upgrade/UI load
# Remove after debugging once root cause is identified
from .. import monkeypatch_debug  # noqa: F401

