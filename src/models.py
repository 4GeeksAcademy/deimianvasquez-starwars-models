from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Table, Column, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

db = SQLAlchemy()


class MediaEnum(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


association_table = Table(
    "follower",
    db.metadata,
    Column("user_from_id", ForeignKey("user.id"), primary_key=True),
    Column("user_to_id", ForeignKey("user.id"), primary_key=True)
)


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    firstname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)

    following_assoc: Mapped[list["User"]] = relationship(
        "User",
        secondary=association_table,
        primaryjoin=id == association_table.c.user_from_id,
        secondaryjoin=id == association_table.c.user_to_id,
        foreign_keys=[association_table.c.user_from_id,
                      association_table.c.user_to_id],
        back_populates="followers_assoc"
    )

    followers_assoc: Mapped[list["User"]] = relationship(
        "User",
        secondary=association_table,
        primaryjoin=id == association_table.c.user_to_id,
        secondaryjoin=id == association_table.c.user_from_id,
        foreign_keys=[association_table.c.user_from_id,
                      association_table.c.user_to_id],
        back_populates="following_assoc"
    )
    posts: Mapped[list["Post"]] = relationship(back_populates="user")
    comments: Mapped[list["Comment"]] = relationship(back_populates="user")

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            # do not serialize the password, its a security breach
        }


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="posts")
    media: Mapped["Media"] = relationship(back_populates="post", uselist=False)
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")


class Media(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[MediaEnum] = mapped_column(
        Enum(MediaEnum), nullable=False, default=MediaEnum.IMAGE)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="media")


class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="comments")
    post: Mapped["Post"] = relationship(back_populates="comments")
