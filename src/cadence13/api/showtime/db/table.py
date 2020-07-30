from sqlalchemy.orm import relationship
from cadence13.db.tables import (
    Podcast, PodcastConfig, Network,
    CategoryPodcastMap, Category)


class ApiPodcast(Podcast):
    config = relationship(PodcastConfig, uselist=False)
    network = relationship(Network, uselist=False)
    categories = relationship(
        Category,
        secondary=CategoryPodcastMap.__table__,
        primaryjoin='ApiPodcast.id == CategoryPodcastMap.podcast_id'
    )
