"""Ponto de entrada usado pelo PyInstaller pra gerar o binario standalone.

Existe separado de `audioguard/cli.py` porque o PyInstaller trabalha melhor
com um script top-level simples do que analisando imports relativos dentro
do pacote diretamente.
"""
from audioguard.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
