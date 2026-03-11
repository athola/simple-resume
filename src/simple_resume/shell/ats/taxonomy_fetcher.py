"""Live taxonomy API fetchers (shell layer).

These fetchers handle network I/O for taxonomy APIs. They are opt-in
and require environment variables for authentication.

O*NET: Free registration at https://services.onetcenter.org/
LinkedIn: Requires OAuth app approval (stub only for now).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class OnetApiFetcher:
    """Fetch skills from O*NET Web Services API.

    Requires ONET_API_USERNAME and ONET_API_PASSWORD environment variables.
    Register for free at https://services.onetcenter.org/
    """

    def fetch(self) -> list[str]:
        """Fetch technology skills from O*NET API.

        Raises:
            NotImplementedError: Until live API integration is implemented.

        """
        username = os.environ.get("ONET_API_USERNAME")
        password = os.environ.get("ONET_API_PASSWORD")
        if not username or not password:
            raise NotImplementedError(
                "O*NET API integration requires ONET_API_USERNAME and "
                "ONET_API_PASSWORD environment variables. Register for free "
                "at https://services.onetcenter.org/"
            )
        raise NotImplementedError(
            "O*NET live API fetching is not yet implemented. "
            "Use the bundled O*NET skills data instead."
        )


class LinkedInApiFetcher:
    """Fetch skills from LinkedIn Skills API.

    LinkedIn's API requires OAuth app approval which is restrictive.
    This class documents the integration path for future implementation.
    """

    def fetch(self) -> list[str]:
        """Fetch skills from LinkedIn API.

        Raises:
            NotImplementedError: LinkedIn API requires OAuth app approval.

        """
        raise NotImplementedError(
            "LinkedIn Skills API integration requires OAuth app approval. "
            "Use the bundled LinkedIn skills data instead."
        )
