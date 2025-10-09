from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	# App
	app_env: str = "dev"
	log_level: str = "INFO"

	# API Provider selection (default: azure)
	api_provider: str = "azure"  # Options: azure, openai

	# Azure OpenAI
	azure_openai_endpoint: str | None = None
	azure_openai_api_version: str = "2024-06-01"
	azure_openai_deployment_scorer: str = "gpt-4o-mini"
	azure_openai_deployment_vision: str = "gpt-4o"
	azure_openai_api_key: str | None = None

	# OpenAI-compatible API (includes direct OpenAI API and other providers)
	openai_base_url: str | None = None  # None = use OpenAI's default endpoint
	openai_api_key: str | None = None
	openai_model_scorer: str = "deepseek/deepseek-r1-0528-qwen3-8b"
	#openai_model_scorer: str = "microsoft/phi-4"

	# Storage (Phase 1+)
	azure_storage_connection_string: str | None = None
	azure_storage_container: str = "runs"

	model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()
