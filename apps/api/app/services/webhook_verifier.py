import hmac
import hashlib
from app.core.logging import logger


class WebhookSignatureVerifier:
    """Cryptographic HMAC-SHA256 signature verifier for Razorpay webhooks.

    Guarantees raw body byte-level verification with constant-time equality checks
    to prevent timing side-channel attacks.
    """

    @staticmethod
    def compute_signature(raw_body: bytes, secret: str) -> str:
        """Computes the expected HMAC-SHA256 hex digest for the given raw body bytes."""
        if not secret:
            raise ValueError("Webhook secret cannot be empty.")
        return hmac.new(
            key=secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

    @classmethod
    def verify(cls, raw_body: bytes, signature: str | None, secret: str) -> bool:
        """Verifies that the provided Razorpay signature matches the computed HMAC-SHA256.

        Args:
            raw_body: Exact raw HTTP request body bytes as received over the wire.
            signature: Value of the 'X-Razorpay-Signature' header.
            secret: Configured merchant webhook secret.

        Returns:
            bool: True if signature is valid and authentic, False otherwise.
        """
        if not signature or not secret:
            logger.warning(
                "Webhook signature verification failed: missing signature or secret",
                has_signature=bool(signature),
                has_secret=bool(secret),
            )
            return False

        try:
            expected_signature = cls.compute_signature(raw_body, secret)
            # Constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(signature.strip(), expected_signature)
            if not is_valid:
                logger.warning("Webhook signature verification failed: signature mismatch")
            return is_valid
        except Exception as e:
            logger.error("Error during webhook signature verification", error=str(e))
            return False
