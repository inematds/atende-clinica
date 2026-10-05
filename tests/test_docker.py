"""Seção 19: entrega em Docker para a VPS (checagem estática; o build real fica no verificar-independente)."""
import re

from conftest import RAIZ


def ler(nome):
    p = RAIZ / nome
    assert p.exists(), f"falta {nome}"
    return p.read_text()


def test_dockerfile():
    d = ler("Dockerfile")
    assert re.search(r"^FROM\s+python:3", d, re.M)
    assert "pip install" not in d
    assert re.search(r"serve.*--host.*0\.0\.0\.0.*--porta.*8080.*--dados.*/dados", d.replace("\n", " ").replace('"', "").replace(",", " "))
    assert "HEALTHCHECK" in d and "/api/saude" in d


def test_compose():
    c = ler("docker-compose.yml")
    for trecho in ("atende:", "build: .", "unless-stopped", "env_file", ".env", "/dados", "127.0.0.1:8080:8080"):
        assert trecho in c, trecho


def test_env_exemplo_tem_todas_as_variaveis_sem_segredo_real():
    e = ler(".env.exemplo")
    for var in ("EVOLUTION_URL", "EVOLUTION_API_KEY", "EVOLUTION_INSTANCIA", "WEBHOOK_SEGREDO",
                "TELEGRAM_API_URL", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_SEGREDO"):
        assert re.search(rf"^{var}=", e, re.M), var
    assert not re.search(r"\d{8,10}:[A-Za-z0-9_-]{30,}", e)  # formato de token real do Telegram


def test_readme_explica_deploy():
    r = ler("README.md")
    assert "Deploy na VPS" in r
    for trecho in ("/webhook/evolution/", "MESSAGES_UPSERT", "setWebhook", "secret_token", "./atende backup"):
        assert trecho in r, trecho
