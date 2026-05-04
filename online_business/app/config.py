from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DigitalMarket - Online Business Platform"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./digitalmarket.db"

    secret_key: str = "change-me-in-production-use-256-bit-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Stripe (set real keys in .env)
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"

    # Email (set real SMTP credentials in .env)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Business rules
    platform_commission_rate: float = 0.15       # 15% for free sellers
    pro_commission_rate: float = 0.10            # 10% for Pro subscribers
    pro_subscription_price_cents: int = 2900     # $29/month
    featured_listing_price_cents: int = 999      # $9.99/week boost

    class Config:
        env_file = ".env"


settings = Settings()
