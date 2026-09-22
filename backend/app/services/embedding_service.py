import time

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingService:

    MODEL = "gemini-embedding-001"
    DIMENSION = 768

    BATCH_SIZE = 50

    MAX_RETRIES = 4
    RETRY_DELAYS = [5, 10, 20, 40]

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    @classmethod
    def generate_embedding(
        cls,
        text: str,
    ) -> list[float]:

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty"
            )

        last_error = None

        for attempt in range(
            cls.MAX_RETRIES + 1
        ):
            try:
                response = cls.client.models.embed_content(
                    model=cls.MODEL,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=cls.DIMENSION,
                    ),
                )

                if not response.embeddings:
                    raise RuntimeError(
                        "Gemini returned no embedding"
                    )

                embedding = response.embeddings[0].values

                if not embedding:
                    raise RuntimeError(
                        "Gemini returned an empty embedding"
                    )

                return cls._normalize(
                    list(embedding)
                )

            except Exception as exc:
                last_error = exc

                if not cls._is_retryable_error(exc):
                    raise

                if attempt >= cls.MAX_RETRIES:
                    break

                delay = cls.RETRY_DELAYS[attempt]

                print(
                    f"[EmbeddingService] Embedding request failed "
                    f"with {type(exc).__name__}. "
                    f"Retrying in {delay} seconds "
                    f"({attempt + 1}/{cls.MAX_RETRIES})"
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini embedding request failed after retries"
        ) from last_error

    @classmethod
    def generate_embeddings(
        cls,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        normalized_texts = []

        for text in texts:
            if not text or not text.strip():
                raise ValueError(
                    "Embedding text cannot be empty"
                )

            normalized_texts.append(
                text
            )

        all_embeddings = []

        for start in range(
            0,
            len(normalized_texts),
            cls.BATCH_SIZE,
        ):

            batch = normalized_texts[
                start:start + cls.BATCH_SIZE
            ]

            batch_embeddings = (
                cls._generate_batch_embeddings(
                    batch
                )
            )

            all_embeddings.extend(
                batch_embeddings
            )

        return all_embeddings

    @classmethod
    def _generate_batch_embeddings(
        cls,
        batch: list[str],
    ) -> list[list[float]]:

        last_error = None

        for attempt in range(
            cls.MAX_RETRIES + 1
        ):
            try:
                response = cls.client.models.embed_content(
                    model=cls.MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        output_dimensionality=cls.DIMENSION,
                    ),
                )

                if not response.embeddings:
                    raise RuntimeError(
                        "Gemini returned no embeddings"
                    )

                if len(response.embeddings) != len(batch):
                    raise RuntimeError(
                        "Gemini returned an unexpected "
                        "number of embeddings"
                    )

                embeddings = []

                for embedding in response.embeddings:

                    if not embedding.values:
                        raise RuntimeError(
                            "Gemini returned an empty embedding"
                        )

                    embeddings.append(
                        cls._normalize(
                            list(embedding.values)
                        )
                    )

                return embeddings

            except Exception as exc:
                last_error = exc

                if not cls._is_retryable_error(exc):
                    raise

                if attempt >= cls.MAX_RETRIES:
                    break

                delay = cls.RETRY_DELAYS[attempt]

                print(
                    f"[EmbeddingService] Batch embedding request "
                    f"failed with {type(exc).__name__}. "
                    f"Batch size: {len(batch)}. "
                    f"Retrying in {delay} seconds "
                    f"({attempt + 1}/{cls.MAX_RETRIES})"
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini batch embedding request failed after retries"
        ) from last_error

    @staticmethod
    def _is_retryable_error(
        error: Exception,
    ) -> bool:

        message = str(error).lower()

        retryable_markers = (
            "429",
            "resource_exhausted",
            "rate limit",
            "rate_limit",
            "quota",
            "503",
            "service unavailable",
            "temporarily unavailable",
            "deadline exceeded",
            "timeout",
            "timed out",
        )

        return any(
            marker in message
            for marker in retryable_markers
        )

    @staticmethod
    def _normalize(
        embedding: list[float],
    ) -> list[float]:

        magnitude = sum(
            value * value
            for value in embedding
        ) ** 0.5

        if magnitude == 0:
            raise RuntimeError(
                "Cannot normalize a zero-length embedding"
            )

        return [
            value / magnitude
            for value in embedding
        ]
