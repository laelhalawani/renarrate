from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class VideoInfo:
    id: str
    title: str
    description: str
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    webpage_url: Optional[str] = None
    downloaded_file: Optional[str] = None

    @classmethod
    def from_dict(cls, info: Dict) -> 'VideoInfo':
        return cls(
            id=info['id'],
            title=info['title'],
            description=info['description'],
            uploader=info.get('uploader'),
            upload_date=info.get('upload_date'),
            duration=info.get('duration'),
            view_count=info.get('view_count'),
            like_count=info.get('like_count'),
            comment_count=info.get('comment_count'),
            webpage_url=info.get('webpage_url'),
            downloaded_file=info.get('downloaded_file'),
        )

    def to_dict(self) -> Dict:
        """
        Returns a dictionary representation of the VideoInfo instance.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'uploader': self.uploader,
            'upload_date': self.upload_date,
            'duration': self.duration,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'webpage_url': self.webpage_url,
            'downloaded_file': self.downloaded_file,
        }
