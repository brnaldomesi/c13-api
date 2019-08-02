from sqlalchemy.orm import relationship

from cadence13.db.tables import (
    Podcast, PodcastConfig, Network,
    PodcastCategory, PodcastCategoryMap)


class ApiPodcast(Podcast):
    config = relationship(PodcastConfig, uselist=False)
    network = relationship(Network, uselist=False)
    categories = relationship(
        PodcastCategory,
        secondary=PodcastCategoryMap.__table__,
        primaryjoin='ApiPodcast.guid == PodcastCategoryMap.podcast_id'
    )
