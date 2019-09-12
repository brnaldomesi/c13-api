from sqlalchemy.orm import relationship
from cadence13.db.tables import (
    Podcast, PodcastConfig, Network,
    PodcastCategory, PodcastCategoryType)


class ApiPodcast(Podcast):
    config = relationship(PodcastConfig, uselist=False)
    network = relationship(Network, uselist=False)
    categories = relationship(
        PodcastCategoryType,
        secondary=PodcastCategory.__table__,
        primaryjoin='ApiPodcast.id == PodcastCategory.podcast_id'
    )
