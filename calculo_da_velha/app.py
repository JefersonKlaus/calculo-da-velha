"""Interface inicial em Flet."""

from __future__ import annotations

import flet as ft

from .game import Game, GameStatus


def main(page: ft.Page) -> None:
    page.title = "Cálculo da Velha"
    page.theme_mode = ft.ThemeMode.LIGHT
    game = Game()

    status = ft.Text(f"Vez de {game.current_player.value}", size=20)
    feedback = ft.Text()
    cells: list[ft.Button] = []

    def refresh() -> None:
        for position, cell in enumerate(cells):
            mark = game.board[position]
            cell.content = mark.value if mark else game.questions[position].prompt
            cell.disabled = mark is not None or game.status is not GameStatus.IN_PROGRESS
        if game.status is GameStatus.IN_PROGRESS:
            status.value = f"Vez de {game.current_player.value}"
        else:
            status.value = "Fim de jogo"
        page.update()

    def submit(position: int, response: int) -> None:
        try:
            result = game.answer(position, response)
        except ValueError as error:
            feedback.value = str(error)
        else:
            feedback.value = result.message
        refresh()

    def select_cell(position: int) -> None:
        question = game.questions[position]
        answer = ft.TextField(label=f"Resposta para {question.prompt}", autofocus=True)

        def confirm(_: ft.ControlEvent) -> None:
            try:
                response = int(answer.value or "")
            except ValueError:
                feedback.value = "Digite uma resposta inteira."
                page.update()
                return
            submit(position, response)
            page.dialog = None
            page.update()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Resolva a conta"),
            content=answer,
            actions=[ft.TextButton("Responder", on_click=confirm)],
        )
        page.dialog.open = True
        page.update()

    for position in range(Game.BOARD_SIZE):
        cell = ft.FilledButton(
            content=game.questions[position].prompt,
            on_click=lambda _, selected=position: select_cell(selected),
            height=110,
            expand=True,
        )
        cells.append(cell)

    page.add(
        ft.Text("Cálculo da Velha", size=32, weight=ft.FontWeight.BOLD),
        status,
        feedback,
        ft.Column(
            [
                ft.Row(cells[0:3], expand=True),
                ft.Row(cells[3:6], expand=True),
                ft.Row(cells[6:9], expand=True),
            ],
            expand=True,
        ),
    )


if __name__ == "__main__":
    ft.run(main)
