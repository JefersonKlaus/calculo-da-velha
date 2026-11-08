from random import Random

from calculo_da_velha.questions import QuestionGenerator


def test_division_questions_are_exact() -> None:
    generator = QuestionGenerator([7], Random(4))
    for _ in range(30):
        question = generator.generate()
        if question.operation == "division":
            dividend, divisor = (int(value.strip()) for value in question.prompt.split("÷"))
            assert dividend % divisor == 0
            assert dividend // divisor == question.answer


def test_question_uses_selected_tables_for_multiplication() -> None:
    generator = QuestionGenerator([7], Random(1))
    for _ in range(20):
        question = generator.generate()
        if question.operation == "multiplication":
            left, _ = (int(value.strip()) for value in question.prompt.split("×"))
            assert left == 7


def test_choices_include_one_correct_answer_and_are_distinct() -> None:
    question = QuestionGenerator([2], Random(2)).generate()
    assert question.answer in question.choices
    assert len(question.choices) == 4
    assert len(set(question.choices)) == 4
