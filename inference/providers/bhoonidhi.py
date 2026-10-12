"""Bhoonidhi satellite catalogue and download adapter.

The official Bhoonidhi API requires registered credentials and a JWT. Product
search fields and download payloads can vary by catalogue/product, so those
parts remain configurable rather than being hidden assumptions in the ML code.
"""

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


JsonObject = dict[str, Any]
RequestFunction = Callable[..., tuple[int, Mapping[str, str], bytes]]


class BhoonidhiError(RuntimeError):
    """Raised when Bhoonidhi authentication, search, or download fails."""


@dataclass(frozen=True)
class BhoonidhiConfig:
    """Connection and endpoint settings for one Bhoonidhi client."""

    base_url: str = "https://bhoonidhi-api.nrsc.gov.in"
    token_path: str = "/auth/token"
    search_path: str = "/data/search"
    download_path: str = "/download"
    timeout_seconds: float = 120.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0


@dataclass(frozen=True)
class BhoonidhiCredentials:
    """Credentials supplied by a secret store or environment variables."""

    user_id: str
    password: str


@dataclass(frozen=True)
class BhoonidhiScene:
    """Normalized scene metadata retained by a detection job."""

    product_id: str
    acquisition_date: date | None
    metadata: JsonObject
    download_reference: str | None = None


def select_closest_scene(
    scenes: list[BhoonidhiScene],
    target_date: date,
) -> BhoonidhiScene:
    """Select the dated scene closest to a requested baseline/comparison date."""
    dated_scenes = [scene for scene in scenes if scene.acquisition_date is not None]
    if not dated_scenes:
        raise BhoonidhiError(
            "Bhoonidhi returned no scenes with a usable acquisition date."
        )
    return min(
        dated_scenes,
        key=lambda scene: abs(scene.acquisition_date - target_date),
    )


class BhoonidhiClient:
    """Small standard-library client for the Bhoonidhi API."""

    def __init__(
        self,
        credentials: BhoonidhiCredentials,
        config: BhoonidhiConfig | None = None,
        request_function: RequestFunction | None = None,
    ) -> None:
        self.credentials = credentials
        self.config = config or BhoonidhiConfig()
        self._request_function = request_function or self._request
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def authenticate(self) -> None:
        """Obtain and retain a JWT access/refresh token pair."""
        response = self._request_json(
            "POST",
            self.config.token_path,
            payload={
                "userId": self.credentials.user_id,
                "password": self.credentials.password,
                "grant_type": "password",
            },
            authenticated=False,
        )
        if not isinstance(response, Mapping):
            raise BhoonidhiError("Bhoonidhi token response must be a JSON object.")
        self._access_token = self._first_string(
            response,
            "access_token",
            "accessToken",
            "token",
        )
        self._refresh_token = self._first_string(
            response,
            "refresh_token",
            "refreshToken",
        )
        if not self._access_token:
            raise BhoonidhiError("Bhoonidhi token response did not contain an access token.")

    def search(
        self,
        geometry: Mapping[str, Any],
        start_date: date,
        end_date: date,
        *,
        extra_filters: Mapping[str, Any] | None = None,
    ) -> list[BhoonidhiScene]:
        """Search scenes intersecting a GeoJSON AOI and date interval.

        The base payload uses broadly documented concepts. Use
        ``extra_filters`` for product-specific fields confirmed by Bhoonidhi.
        """
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date.")
        if not self._access_token:
            self.authenticate()

        payload: JsonObject = {
            "datetime": (
                f"{start_date.isoformat()}T00:00:00Z/"
                f"{end_date.isoformat()}T23:59:59Z"
            ),
            "intersects": geometry,
            "limit": 500,
        }
        if extra_filters:
            payload.update(extra_filters)

        response = self._request_json(
            "POST",
            self.config.search_path,
            payload=payload,
            authenticated=True,
        )
        return self._normalize_scenes(response)

    def download(
        self,
        scene: BhoonidhiScene,
        destination: str | Path,
    ) -> Path:
        """Download a selected scene to a private job directory."""
        if not self._access_token:
            self.authenticate()

        collection = self._scene_collection(scene)
        query = urlencode({"id": scene.product_id, "collection": collection})
        download_url = (
            f"{self.config.base_url.rstrip('/')}"
            f"{self.config.download_path}?{query}"
        )

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        status, _, body = self._request_function(
            "GET",
            download_url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            payload=None,
        )
        if status == 401:
            self.authenticate()
            status, _, body = self._request_function(
                "GET",
                download_url,
                headers={"Authorization": f"Bearer {self._access_token}"},
                payload=None,
            )
        if status < 200 or status >= 300:
            message = body.decode("utf-8", errors="replace")[:500]
            raise BhoonidhiError(
                f"Bhoonidhi file download failed with HTTP {status}: {message}"
            )
        destination.write_bytes(body)
        return destination

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: JsonObject,
        authenticated: bool,
    ) -> Any:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if authenticated and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        status, _, body = self._request_function(
            method,
            path,
            headers=headers,
            payload=payload,
        )
        if status < 200 or status >= 300:
            message = body.decode("utf-8", errors="replace")[:500]
            raise BhoonidhiError(f"Bhoonidhi API HTTP {status}: {message}")
        try:
            value = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise BhoonidhiError("Bhoonidhi returned invalid JSON.") from exc
        if not isinstance(value, (dict, list)):
            raise BhoonidhiError("Expected a JSON object or array from Bhoonidhi.")
        return value

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        headers: Mapping[str, str],
        payload: JsonObject | None,
    ) -> tuple[int, Mapping[str, str], bytes]:
        url = path_or_url if path_or_url.startswith("http") else (
            self.config.base_url.rstrip("/") + "/" + path_or_url.lstrip("/")
        )
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=body, headers=dict(headers), method=method)

        opener = build_opener(_BhoonidhiRedirectHandler())
        for attempt in range(self.config.max_retries):
            try:
                with opener.open(request, timeout=self.config.timeout_seconds) as response:
                    return response.status, response.headers, response.read()
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == self.config.max_retries:
                    return exc.code, exc.headers, exc.read()
            except URLError as exc:
                if attempt + 1 == self.config.max_retries:
                    raise BhoonidhiError(f"Bhoonidhi request failed: {exc.reason}") from exc
            time.sleep(self.config.retry_backoff_seconds * (2**attempt))

        raise BhoonidhiError("Bhoonidhi request failed after retries.")

    @staticmethod
    def _first_string(response: Mapping[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = response.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    @classmethod
    def _normalize_scenes(
        cls,
        response: Mapping[str, Any] | list[Any],
    ) -> list[BhoonidhiScene]:
        if isinstance(response, list):
            raw_items = response
        else:
            raw_items = response.get(
                "features",
                response.get("results", response.get("data", [])),
            )
        if isinstance(raw_items, Mapping):
            raw_items = raw_items.get("items", [])
        if not isinstance(raw_items, list):
            raise BhoonidhiError("Could not identify scene records in Bhoonidhi response.")

        scenes = []
        for item in raw_items:
            if not isinstance(item, Mapping):
                continue
            properties = item.get("properties", {})
            if not isinstance(properties, Mapping):
                properties = {}
            merged = {**properties, **item}
            product_id = cls._first_string(
                merged,
                "productId",
                "product_id",
                "id",
            )
            if not product_id:
                continue
            acquisition_value = cls._first_string(
                merged,
                "acquisitionDate",
                "acquisition_date",
                "datetime",
                "date",
            )
            acquisition_date = None
            if acquisition_value:
                try:
                    acquisition_date = date.fromisoformat(acquisition_value[:10])
                except ValueError:
                    pass
            scenes.append(
                BhoonidhiScene(
                    product_id=product_id,
                    acquisition_date=acquisition_date,
                    metadata=dict(item),
                    download_reference=cls._first_string(
                        merged,
                        "downloadUrl",
                        "download_url",
                        "url",
                    ),
                )
            )
        return scenes

    @staticmethod
    def _find_download_url(response: Mapping[str, Any]) -> str | None:
        for key in ("downloadUrl", "download_url", "url", "downloadLink"):
            value = response.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        nested = response.get("data")
        if isinstance(nested, Mapping):
            return BhoonidhiClient._find_download_url(nested)
        return None

    @staticmethod
    def _scene_collection(scene: BhoonidhiScene) -> str:
        collection = scene.metadata.get("collection")
        if isinstance(collection, str) and collection:
            return collection
        collections = scene.metadata.get("collections")
        if isinstance(collections, list) and collections:
            first = collections[0]
            if isinstance(first, str) and first:
                return first
        raise BhoonidhiError(
            f"Scene {scene.product_id!r} did not include a STAC collection."
        )


class _BhoonidhiRedirectHandler(HTTPRedirectHandler):
    """Preserve auth when Bhoonidhi redirects a download to its file host."""

    _allowed_hosts = {"bhoonidhi-api.nrsc.gov.in", "bhoonidhi.nrsc.gov.in"}

    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any):
        redirected = super().redirect_request(req, fp, code, msg, headers)
        if redirected is None:
            return None
        source_host = req.host.split(":", 1)[0].lower()
        target_host = redirected.host.split(":", 1)[0].lower()
        authorization = req.get_header("Authorization")
        if (
            authorization
            and source_host in self._allowed_hosts
            and target_host in self._allowed_hosts
        ):
            redirected.add_unredirected_header("Authorization", authorization)
        return redirected
