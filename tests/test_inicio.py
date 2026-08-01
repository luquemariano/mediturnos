def test_inicio(client):
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "mensaje": "¡Bienvenido a MediTurnos!"
    }