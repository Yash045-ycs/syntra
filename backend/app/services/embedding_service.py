import math

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingService:

    MODEL = "gemini-embedding-001"
    DIMENSION = 768

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    @classmethod
    def generate_embedding(
        cls,
        text: str,
    ) -> list[float]:

        if not text.strip():
            raise ValueError(
                "Cannot generate embedding for empty text"
            )

        result = cls.client.models.embed_content(
            model=cls.MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=cls.DIMENSION,
            ),
        )

        if not result.embeddings:
            raise RuntimeError(
                "Gemini returned no embedding"
            )

        values = result.embeddings[0].values

        if not values:
            raise RuntimeError(
                "Gemini returned an empty embedding"
            )

        if len(values) != cls.DIMENSION:
            raise RuntimeError(
                f"Expected {cls.DIMENSION} dimensions, "
                f"received {len(values)}"
            )

        return cls._normalize(values)

    @classmethod
    def generate_embeddings(
        cls,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        result = cls.client.models.embed_content(
            model=cls.MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=cls.DIMENSION,
            ),
        )

        if not result.embeddings:
            raise RuntimeError(
                "Gemini returned no embeddings"
            )

        embeddings = []

        for embedding in result.embeddings:

            values = embedding.values

            if not values:
                raise RuntimeError(
                    "Gemini returned an empty embedding"
                )

            if len(values) != cls.DIMENSION:
                raise RuntimeError(
                    f"Expected {cls.DIMENSION} dimensions, "
                    f"received {len(values)}"
                )

            embeddings.append(
                cls._normalize(values)
            )

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Gemini returned an unexpected number "
                "of embeddings"
            )

        return embeddings

    @staticmethod
    def _normalize(
        values: list[float],
    ) -> list[float]:

        magnitude = math.sqrt(
            sum(value * value for value in values)
        )

        if magnitude == 0:
            raise RuntimeError(
                "Cannot normalize a zero-length embedding"
            )

        return [
            value / magnitude
            for value in values
        ]