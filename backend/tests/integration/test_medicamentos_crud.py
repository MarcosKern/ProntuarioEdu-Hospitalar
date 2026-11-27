from uuid import uuid4

from prontuario_backend.models.medicamentos import (
    atualizar,
    buscar_por_id,
    criar,
    desativar,
    listar_ativos,
)


def test_criar_medicamentos(medicamentos):
    row = criar(
        {
            "nome": "Paracetamol",
            "principio_ativo": "Paracetamol",
            "nome_comercial": "Tylenol",
            "forma_farmaceutica": "Comprimido",
            "descricao": "Analgesico e antitermico",
        }
    )

    assert row["id"]
    assert row["nome"] == "Paracetamol"
    assert row["principio_ativo"] == "Paracetamol"
    assert row["nome_comercial"] == "Tylenol"
    assert row["forma_farmaceutica"] == "Comprimido"
    assert row["descricao"] == "Analgesico e antitermico"
    assert row["ativo"] == 1
    assert row["criado_em"] is not None
    assert buscar_por_id(row["id"]) == row


def test_criar_medicamento_nome_repetido(medicamentos):
    primeiro = criar({"nome": "Dipirona"})
    segundo = criar({"nome": "Dipirona"})

    assert primeiro["id"] != segundo["id"]
    assert primeiro["nome"] == segundo["nome"]


def test_criar_medicamento_campos_opcionais_nulos(medicamentos):
    row = criar({"nome": "Medicamento sem detalhes"})

    assert row["nome"] == "Medicamento sem detalhes"
    assert row["principio_ativo"] is None
    assert row["nome_comercial"] is None
    assert row["forma_farmaceutica"] is None
    assert row["descricao"] is None


def test_atualizar_medicamento(medicamentos):
    row = atualizar(
        medicamentos[0]["id"],
        {
            "nome": "Paracetamol atualizada", 
            "principio_ativo": "Paracetamol",
            "nome_comercial": "Nova Marca",
            "forma_farmaceutica": "Gotas",
            "descricao": "Descricao atualizada"
        },
    )

    assert row["id"] == medicamentos[0]["id"]
    assert row["nome"] == "Paracetamol atualizada"
    assert row["nome_comercial"] == "Nova Marca"
    assert row["forma_farmaceutica"] == "Gotas"


def test_atualizar_medicamento_inexistente(medicamentos):
    assert atualizar(
        str(uuid4()), {"nome": "Inexistente"}
    ) is None


def test_desativar_medicamento(medicamentos):
    medicamento_id = medicamentos[0]["id"]

    row = desativar(medicamento_id)

    assert row["id"] == medicamento_id
    assert row["ativo"] == 0
    assert buscar_por_id(medicamento_id)["ativo"] == 0
    assert medicamento_id not in {
        item["id"] for item in listar_ativos(10, 0)
    }

def test_desativar_medicamento_inexistente(medicamentos):
    assert desativar(str(uuid4())) is None