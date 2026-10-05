"""Arquivo portátil com configuração e snapshot consistente do SQLite."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile


def copiar(dados, saida):
    dados, saida = Path(dados), Path(saida)
    if saida.resolve() in ((dados / 'estado.sqlite3').resolve(), (dados / 'clinica.json').resolve()):
        raise ValueError('O backup não pode sobrescrever o estado')
    with tempfile.TemporaryDirectory(dir=saida.parent) as tmp:
        snapshot = Path(tmp) / 'estado.sqlite3'
        origem = sqlite3.connect((dados / 'estado.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
        destino = sqlite3.connect(snapshot)
        try:
            origem.backup(destino)
        finally:
            destino.close()
            origem.close()
        arquivo = Path(tmp) / 'backup.zip'
        with zipfile.ZipFile(arquivo, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(snapshot, 'estado.sqlite3')
            z.write(dados / 'clinica.json', 'clinica.json')
        os.replace(arquivo, saida)


def restaurar(dados, entrada):
    dados = Path(dados)
    dados.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dados) as tmp:
        with zipfile.ZipFile(entrada) as z:
            config = z.read('clinica.json')
            json.loads(config)
            banco = Path(tmp) / 'estado.sqlite3'
            banco.write_bytes(z.read('estado.sqlite3'))
        db = sqlite3.connect(banco)
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup inválido')
            db.execute('SELECT chave FROM meta LIMIT 1')
        finally:
            db.close()
        cfg = Path(tmp) / 'clinica.json'
        cfg.write_bytes(config)
        # Restauração exige servidor parado, conforme contrato.
        for sufixo in ('-wal', '-shm', '-journal'):
            (dados / ('estado.sqlite3' + sufixo)).unlink(missing_ok=True)
        os.replace(banco, dados / 'estado.sqlite3')
        os.replace(cfg, dados / 'clinica.json')
