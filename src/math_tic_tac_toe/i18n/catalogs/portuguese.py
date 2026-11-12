"""Portuguese texts."""

from ..text_key import TextKey

TEXTS = {
    TextKey.APP_TITLE: "Cálculo da Velha",
    TextKey.TURN: "Vez de {player}",
    TextKey.GAME_OVER_WIN: "Fim de jogo: {player} venceu!",
    TextKey.GAME_OVER_DRAW: "Fim de jogo: empate!",
    TextKey.RAN_OUT_OF_TIME: "{player} ficou sem tempo.",
    TextKey.WRONG_ANSWER: "Resposta incorreta.",
    TextKey.TIME_UP: "Tempo esgotado!",
    TextKey.SOLVE_QUESTION: "Resolva a conta",
    TextKey.CANCEL: "Cancelar",
    TextKey.RESTART: "Recomeçar",
    TextKey.PLAY_AGAIN: "Jogar novamente",
    TextKey.CONFIRM_RESTART_TITLE: "Recomeçar a partida?",
    TextKey.CONFIRM_LEAVE_TITLE: "Sair da partida?",
    TextKey.MATCH_WILL_BE_LOST: "A partida atual será perdida.",
    TextKey.LEAVE: "Sair",
    TextKey.SETTINGS_TITLE: "Configurações",
    TextKey.SETTINGS_HINT: (
        "Em rosa: opções selecionadas. Toque em uma opção para marcar ou desmarcar."
    ),
    TextKey.OPERATION: "Operação",
    TextKey.TIMES_TABLE: "Tabuada",
    TextKey.PLAY: "Jogar",
    TextKey.HARD_MODE: "Modo difícil",
    TextKey.HARD_MODE_MESSAGE: (
        "Cada jogador tem este tempo para a partida inteira. Quem ficar sem tempo perde."
    ),
    TextKey.TIME_PER_PLAYER: "Tempo por jogador",
    TextKey.START: "Começar",
    TextKey.OPEN_SETTINGS: "Configurações",
    TextKey.BEST_OF_FIVE: "Melhor de 5",
    TextKey.POINTS_TO_WIN: "Vence quem fizer {points}",
    TextKey.POINT_FOR: "Ponto para {player}!",
    TextKey.POINTS_FOR: "{points} pontos para {player}!",
}
