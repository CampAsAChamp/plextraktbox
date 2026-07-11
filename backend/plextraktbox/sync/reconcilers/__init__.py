"""Per-data-type reconcilers."""

from plextraktbox.sync.reconcilers.base import Reconciler
from plextraktbox.sync.reconcilers.ratings import RatingsReconciler, letterboxd_to_normalized
from plextraktbox.sync.reconcilers.watched import WatchedReconciler
from plextraktbox.sync.reconcilers.watchlist import WatchlistReconciler

DEFAULT_RECONCILERS: list[Reconciler] = [
    WatchlistReconciler(),
    RatingsReconciler(),
    WatchedReconciler(),
]

__all__ = [
    "DEFAULT_RECONCILERS",
    "RatingsReconciler",
    "Reconciler",
    "WatchlistReconciler",
    "WatchedReconciler",
    "letterboxd_to_normalized",
]
