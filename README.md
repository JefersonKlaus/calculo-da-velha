# Cálculo da Velha

Jogo da velha em Python com desafios de matemática e interface
em Flet.

## Executar

```powershell
python -m pip install -e .
python -m calculo_da_velha.app
```

## Testar

```powershell
pytest
```

O núcleo está em `calculo_da_velha/game.py` e não depende de Flet, permitindo
testar as regras sem abrir uma janela. A interface atual é apenas o primeiro
esqueleto; modos, computador, roubo, perfis e placar serão adicionados nas
próximas etapas.