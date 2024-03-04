def tipoPregunta(tipo):
    id_tipo = 0
    if tipo == "Abierta":
        id_tipo = 1
    elif tipo == "Cerrada de opción simple":
        id_tipo = 2
    elif tipo == "Cerrada de opción múltiple":
        id_tipo = 3
    elif tipo == "Semicerrada de opción simple":
        id_tipo = 4
    elif tipo == "Semicerrada de opción múltiple":
        id_tipo = 5
    elif tipo == "Escala":
        id_tipo = 6
    return id_tipo
